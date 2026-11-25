"""延遲階梯（專題任務的評分與練習）：同一支策略，從低到高一階一階加延遲。

起始階自己選（--start-ms），從那一階往上連續測，最多測 --max-levels 階（預設 5）。

上傳一次 RLControl，這支程式用序列埠指令 'L<ms>' 設定每一階的延遲（取代
latency_profile.h），每一階都重新甩上：

  1. 送 'L<ms>' 設好這一階的延遲；
  2. 等使用者把手臂轉回正中間、擺錘靜止垂下，按 Enter → 'E'（Nano 抓零點並開始甩）；
  3. 從 engage 起 --window-s 秒內，只要「連續平衡」滿 --hold-s 秒就算通過，馬上停下來進下一階；
     撞到限位、或剩下的時間已經不可能湊滿 --hold-s，就算這一次沒過；
  4. 沒過可以重試 --retries 次，還是沒過就停；測滿 --max-levels 階也停。
     成績 = 最後通過的那一階；起始那一階就沒過，就沒有成績。

平衡的定義和 analyze_onboard／analyze_sim 相同（balance_metrics：|θ| ≤ 15° 且 |θ̇| ≤ 4 rad/s）。
每一次嘗試的遙測存成 npz，整體結果存成 summary.json。

Usage:
    python latency_ladder.py --port /dev/cu.usbserial-110 --out-dir recordings/ladder_x
    python latency_ladder.py --port ... --start-ms 20     # 練習：從 +20 開始
    python latency_ladder.py --port ... --swingup 3       # 甩上到平衡計時：+0 甩 3 次

甩上到平衡計時（--swingup N）：不加延遲，甩 N 次。每一次從 engage 起 --window-s 秒內，
要有一段連續平衡滿 --hold-s 秒才算數；甩上時間 = engage 到「那一段連續平衡開始」的秒數
（中途接住又掉下來不算，要等到真正站穩的那一段）。成績 = N 次的中位數，
沒算數的那一次當成無限大（所以 3 次裡有 2 次沒站穩就沒有成績）。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import serial

import balance_metrics

# ms，加在原本約 16 ms 的延遲上面。+35 到 +50 是細階（2、3 ms 交替，平均 2.5 ms）：
# 實測 +35 → +40 之間是懸崖（2026-11-24，R4 過 +36、倒 +37），細階讓推進一點的組也拿得到分。
# 都是整數 ms，RLControl 的 'L' 指令不用改。最高階 +55（130 分，2026-11-25 決定），
# RLControl 的上限是 70，涵蓋得到。
DEFAULT_LEVELS = [0, 10, 15, 20, 25, 30, 35, 37, 40, 42, 45, 47, 50, 55]


def wait_boot(ser: serial.Serial) -> None:
    t_end = time.monotonic() + 10.0
    while time.monotonic() < t_end:
        if b"policy(upright)" in ser.readline():
            break
    else:
        print("沒看到開機訊息，Nano 上是 RLControl 嗎？先繼續。")
    time.sleep(1.5)   # 開機後 1 秒會自己 engage
    ser.reset_input_buffer()
    ser.write(b"D")
    time.sleep(0.2)


def set_latency(ser: serial.Serial, ms: int, jitter: int) -> None:
    ser.reset_input_buffer()
    ser.write(f"L{ms},{jitter}\n".encode())
    t_end = time.monotonic() + 1.5
    while time.monotonic() < t_end:
        line = ser.readline().decode(errors="ignore").strip()
        if line.startswith("[latency]"):
            if "extra=" in line:
                return
            raise SystemExit(f"Nano 拒絕這個延遲設定：{line}")
    raise SystemExit("Nano 沒有回應延遲設定。RLControl 太舊（沒有 'L' 指令），請重新上傳 repo 裡的 RLControl。")


def run_attempt(ser: serial.Serial, window_s: float, hold_s: float) -> dict:
    """engage 一次，回傳這一次的結果與遙測。"""
    ser.reset_input_buffer()
    ser.write(b"P")
    time.sleep(0.2)
    ser.write(b"E")
    rows: list[list[float]] = []
    i0 = None
    result = dict(passed=False, reason="時間到")
    last_eval = 0
    last_rx = time.monotonic()
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line.startswith("[DIR]"):
            result.update(reason="方向沒有標定（先用 LowLevelServer 跑 04_check_direction）")
            break
        parts = line.split(",")
        if len(parts) < 9:
            if time.monotonic() - last_rx > 3.0:
                result.update(reason="收不到遙測")
                break
            continue
        try:
            row = [float(v) for v in parts[:9]]
        except ValueError:
            continue
        last_rx = time.monotonic()
        rows.append(row)
        running = row[4] > 0.5
        if i0 is None:
            if running:
                i0 = len(rows) - 1
            elif len(rows) > 150:   # 約 3 秒都沒有 engage
                result.update(reason="Nano 沒有開始甩")
                break
            continue
        t = (row[0] - rows[i0][0]) * 1e-6
        if not running:
            result.update(reason="撞到限位，馬達斷電")
            break
        if len(rows) - last_eval >= 25 or t >= window_s:   # 約每 0.5 秒評一次
            last_eval = len(rows)
            seg = np.asarray(rows[i0:])
            m = balance_metrics.score(phi=seg[:, 2] / 1000, motor_pos=seg[:, 1] / 1000,
                                      action=seg[:, 3] / 1000, t_s=(seg[:, 0] - seg[0, 0]) * 1e-6)
            if m.longest_streak_s >= hold_s:
                result.update(passed=True, reason="通過")
                break
            cur = 0
            for b in m.balanced_mask[::-1]:
                if not b:
                    break
                cur += 1
            if cur * m.dt_s + (window_s - t) < hold_s:
                result.update(reason=f"剩下的時間湊不滿 {hold_s:g} 秒")
                break
        if t >= window_s:
            break
    ser.write(b"D")
    time.sleep(0.1)
    ser.write(b"P")   # 關掉遙測
    time.sleep(0.1)
    ser.reset_input_buffer()

    if i0 is None or len(rows) - i0 < 10:
        result.update(passed=False, streak_s=0.0, swingup_s=None, latency_ms=None, rows=np.zeros((0, 9)))
        return result
    seg = np.asarray(rows[i0:])
    m = balance_metrics.score(phi=seg[:, 2] / 1000, motor_pos=seg[:, 1] / 1000,
                              action=seg[:, 3] / 1000, t_s=(seg[:, 0] - seg[0, 0]) * 1e-6)
    result.update(streak_s=float(m.longest_streak_s), swingup_s=m.first_catch_s,
                  latency_ms=float(np.mean(seg[:, 7])) / 1000, rows=seg)
    return result


def settle_s(rows: np.ndarray, hold_s: float) -> float | None:
    """engage 到第一段「連續平衡 >= hold_s」開始的秒數；沒有這一段就是 None。"""
    if len(rows) < 10:
        return None
    t_s = (rows[:, 0] - rows[0, 0]) * 1e-6
    m = balance_metrics.score(phi=rows[:, 2] / 1000, motor_pos=rows[:, 1] / 1000,
                              action=rows[:, 3] / 1000, t_s=t_s)
    start = None
    for i, b in enumerate(m.balanced_mask):
        if not b:
            start = None
            continue
        if start is None:
            start = i
        if t_s[i] - t_s[start] + m.dt_s >= hold_s:
            return float(t_s[start])
    return None


def swingup(ser: serial.Serial, args: argparse.Namespace) -> int:
    set_latency(ser, 0, 0)
    times: list[float] = []
    summary = dict(mode="swingup", tries=args.swingup, window_s=args.window_s, hold_s=args.hold_s,
                   attempts=[], median_s=None)
    for k in range(1, args.swingup + 1):
        try:
            input(f"\n[甩上到平衡計時 第 {k}/{args.swingup} 次] 手臂轉回正中間、擺錘靜止垂下後按 Enter（之後不要碰）")
        except EOFError:
            pass
        r = run_attempt(ser, args.window_s, args.hold_s)
        rows = r.pop("rows")
        np.savez_compressed(args.out_dir / f"swingup_try{k}.npz", telemetry=rows)
        s = settle_s(rows, args.hold_s) if r["passed"] else None
        times.append(float("inf") if s is None else s)
        print(f"  {'甩上 %.2f s' % s if s is not None else '不算數（' + r['reason'] + '）'}"
              f"，最長連續平衡 {r['streak_s']:.1f} s")
        summary["attempts"].append(dict(attempt=k, settle_s=s, **r))
    ser.close()
    med = float(np.median(times))
    summary["median_s"] = med if np.isfinite(med) else None
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    print("\n結果")
    for a in summary["attempts"]:
        print(f"  第 {a['attempt']} 次：{'不算數' if a['settle_s'] is None else '%.2f s' % a['settle_s']}")
    print(f"\n甩上時間（中位數）：{'沒有成績' if summary['median_s'] is None else '%.2f s' % med}")
    print(f"紀錄：{args.out_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="延遲階梯：同一支策略，從低到高一階一階加延遲")
    p.add_argument("--port", required=True)
    p.add_argument("--baud", type=int, default=500000)
    p.add_argument("--levels", type=int, nargs="+", default=DEFAULT_LEVELS,
                   help="每一階的額外延遲（ms），由低到高")
    p.add_argument("--start-ms", type=int, default=0, help="從哪一階開始（自己選，demo 也一樣）")
    p.add_argument("--max-levels", type=int, default=5, help="最多測幾階（專題規則：5）")
    p.add_argument("--jitter-ms", type=int, default=0, help="每一階都另外加的每拍抖動（ms）")
    p.add_argument("--window-s", type=float, default=30.0, help="每次嘗試從 engage 起最多幾秒")
    p.add_argument("--hold-s", type=float, default=10.0, help="連續平衡幾秒算通過")
    p.add_argument("--retries", type=int, default=1, help="每一階沒過可以重試幾次")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--swingup", type=int, default=0, metavar="N",
                   help="甩上到平衡計時：不加延遲甩 N 次（預設每次 20 秒內要連續平衡滿 10 秒）")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])
    if args.swingup:
        if args.window_s == p.get_default("window_s"):
            args.window_s = 20.0
        if args.hold_s == p.get_default("hold_s"):
            args.hold_s = 10.0
        args.out_dir.mkdir(parents=True, exist_ok=True)
        print(f"甩上到平衡計時：不加延遲，甩 {args.swingup} 次；每次 {args.window_s:g} 秒內要連續平衡滿 "
              f"{args.hold_s:g} 秒才算數，成績是中位數。")
        print(f"打開 {args.port}（Nano 會重開）")
        ser = serial.Serial(args.port, args.baud, timeout=0.5)
        wait_boot(ser)
        return swingup(ser, args)

    levels = [x for x in sorted(set(args.levels)) if x >= args.start_ms][:args.max_levels]
    if not levels:
        raise SystemExit("沒有要測的階")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"延遲階梯：{'、'.join(f'+{x}' for x in levels)} ms"
          + (f"（每拍另加抖動 0–{args.jitter_ms} ms）" if args.jitter_ms else ""))
    print(f"每一階：engage 後 {args.window_s:g} 秒內連續平衡滿 {args.hold_s:g} 秒算通過；"
          f"沒過可以重試 {args.retries} 次。最多測 {len(levels)} 階，第一階（+{levels[0]}）沒過就沒有成績。")
    print(f"打開 {args.port}（Nano 會重開）")
    ser = serial.Serial(args.port, args.baud, timeout=0.5)
    wait_boot(ser)

    summary = dict(levels=levels, start_ms=levels[0], max_levels=args.max_levels, jitter_ms=args.jitter_ms, window_s=args.window_s, hold_s=args.hold_s,
                   retries=args.retries, attempts=[], best_ms=None)
    for ms in levels:
        set_latency(ser, ms, args.jitter_ms)
        passed = False
        for k in range(1, args.retries + 2):
            try:
                input(f"\n[+{ms} ms 第 {k} 次] 手臂轉回正中間、擺錘靜止垂下後按 Enter（Nano 會開始甩，之後不要碰）")
            except EOFError:
                pass
            r = run_attempt(ser, args.window_s, args.hold_s)
            rows = r.pop("rows")
            np.savez_compressed(args.out_dir / f"plus{ms:02d}ms_try{k}.npz", telemetry=rows)
            lat = "—" if r["latency_ms"] is None else f"{r['latency_ms']:.1f} ms"
            sw = "沒接住" if r["swingup_s"] is None else f"{r['swingup_s']:.1f} s"
            print(f"  {'通過' if r['passed'] else '沒過'}（{r['reason']}）：最長連續平衡 {r['streak_s']:.1f} s，"
                  f"甩上 {sw}，實測 sample→command {lat}")
            summary["attempts"].append(dict(extra_ms=ms, attempt=k, **r))
            if r["passed"]:
                passed = True
                break
        if not passed:
            break
        summary["best_ms"] = ms

    ser.close()
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    print("\n結果")
    for a in summary["attempts"]:
        print(f"  +{a['extra_ms']:>2} ms 第 {a['attempt']} 次：{'通過' if a['passed'] else '沒過'}　"
              f"最長連續平衡 {a['streak_s']:.1f} s")
    best = summary["best_ms"]
    print(f"\n通過的最高階：{'沒有（起始階沒過，沒有成績）' if best is None else f'+{best} ms'}"
          f"（從 +{levels[0]} 開始，測了 {len({a['extra_ms'] for a in summary['attempts']})} 階，最多 {len(levels)} 階）")
    print(f"紀錄：{args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

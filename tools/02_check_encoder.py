"""02_check_encoder：檢查 AS5600 的磁場強度、磁鐵對心與轉圈連續性。

搭配韌體 firmware/EncoderCheck。三段：
  1. 靜態 10 秒：狀態位元（MD/ML/MH）、AGC、magnitude
  2. 用手慢轉：順時針 3 圈、逆時針 3 圈（跳點、圈數、覆蓋、對心）
  3. 自由擺（選做）：週期與左右對稱
每一項印 PASS/FAIL，並把原始資料與圖存在 policy/encoder_runs/<時間>/。
"""
from __future__ import annotations

import threading
import time

import numpy as np
import serial

from _common import POLICY, ask_yes, banner, fail, finish, get_port, heading, info, ok, wait_enter, warn

# ---- 門檻（暫定值，助教用正常機台校準後更新） -------------------------------
JUMP_LSB = 500              # 相鄰取樣差超過這個值 = 跳點（同作者韌體的門檻）
AGC_SAT_FRAC_MAX = 0.01     # AGC 為 0 或 255 的取樣比例上限
AGC_RANGE_MAX = 12          # 靜態時 AGC 最大值 − 最小值
TURN_DEG_MIN, TURN_DEG_MAX = 900.0, 1260.0   # 每個方向累積角度（約 3 圈 = 1080°）
COVER_BINS = 64             # 一圈分成 64 格（5.6°），每格都要讀到
MAG_RIPPLE_MAX = 0.15       # 一圈內 magnitude 的 (最大−最小)/平均（偏心指標）
PERIOD_RANGE_S = (0.49, 0.53)   # 小振幅（< 20°）自由擺週期
SYMMETRY_MAX = 0.10         # 左右擺幅差異比例
# ----------------------------------------------------------------------------

BAUD = 500_000
MD, ML, MH = 0x20, 0x10, 0x08


class Reader:
    """在背景執行緒讀 EncoderCheck 的 CSV。"""

    def __init__(self, port: str):
        self.ser = serial.Serial(port, BAUD, timeout=0.2)
        self.rows: list[tuple[int, int, int, int, int]] = []
        self.lock = threading.Lock()
        self.stop = False
        self.header_seen = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        while not self.stop:
            line = self.ser.readline().decode("ascii", "replace").strip()
            if not line:
                continue
            if line.startswith("#"):
                if "EncoderCheck" in line:
                    self.header_seen = True
                elif "not connected" in line:
                    warn("韌體回報讀不到 AS5600：檢查 SDA→A4、SCL→A5、5V、GND")
                continue
            parts = line.split(",")
            if len(parts) != 5:
                continue
            try:
                row = tuple(int(x) for x in parts)
            except ValueError:
                continue
            with self.lock:
                self.rows.append(row)  # type: ignore[arg-type]

    def take(self) -> np.ndarray:
        with self.lock:
            rows, self.rows = self.rows, []
        return np.array(rows, dtype=np.int64).reshape(-1, 5)

    def close(self) -> None:
        self.stop = True
        self.thread.join(timeout=1)
        self.ser.close()


def unwrap_deg(raw: np.ndarray) -> np.ndarray:
    d = np.diff(raw.astype(np.int64))
    d = (d + 2048) % 4096 - 2048
    return np.concatenate([[0.0], np.cumsum(d) * 360.0 / 4096.0])


def jumps(raw: np.ndarray) -> int:
    d = np.diff(raw.astype(np.int64))
    d = (d + 2048) % 4096 - 2048
    return int(np.sum(np.abs(d) > JUMP_LSB))


def report(name: str, passed: bool, detail: str, results: list) -> None:
    (ok if passed else fail)(f"{name}：{'PASS' if passed else 'FAIL'}　{detail}")
    results.append((name, passed, detail))


def collect_until_enter(reader: Reader, max_s: float) -> np.ndarray:
    done = threading.Event()

    def _wait():
        try:
            input()
        except EOFError:
            pass
        done.set()

    threading.Thread(target=_wait, daemon=True).start()
    reader.take()
    t0 = time.time()
    chunks = []
    while not done.is_set() and time.time() - t0 < max_s:
        time.sleep(0.2)
        chunks.append(reader.take())
        a = np.concatenate(chunks) if chunks else np.zeros((0, 5))
        if len(a) > 1:
            print(f"\r  目前累積 {unwrap_deg(a[:, 1])[-1]:+8.0f}°   ", end="", flush=True)
    print()
    chunks.append(reader.take())
    return np.concatenate(chunks)


def main() -> int:
    banner("02 編碼器測試：磁場強度與對心", "firmware/EncoderCheck", needs_rig=True)
    port = get_port()
    out_dir = POLICY / "encoder_runs" / time.strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    info(f"序列埠：{port}（打開時 Nano 會重開，約 2 秒）")
    reader = Reader(port)
    time.sleep(2.5)
    reader.take()
    time.sleep(0.5)
    if not reader.header_seen and len(reader.take()) == 0:
        fail("沒有收到 EncoderCheck 的資料。確認燒的是 firmware/EncoderCheck，並關掉序列埠監控。")
        reader.close()
        return 1

    results: list = []
    data: dict[str, np.ndarray] = {}

    # ---------------- 1. 靜態
    heading("1/3 靜態磁場（10 秒）")
    wait_enter("讓擺錘靜止垂下、不要碰，按 Enter 開始")
    reader.take()
    time.sleep(10)
    st = reader.take()
    data["static"] = st
    if len(st) < 1000:
        fail(f"10 秒只收到 {len(st)} 筆資料（應約 2500 筆），serial 可能有問題")
    status, agc, mag = st[:, 2], st[:, 3], st[:, 4]
    md = np.mean((status & MD) > 0)
    ml = np.mean((status & ML) > 0)
    mh = np.mean((status & MH) > 0)
    report("偵測到磁鐵（MD=1）", md > 0.99, f"{md * 100:.1f}% 的取樣", results)
    report("磁場不會太弱（ML=0）", ml < 0.01, f"ML=1 佔 {ml * 100:.1f}%", results)
    report("磁場不會太強（MH=0）", mh < 0.01, f"MH=1 佔 {mh * 100:.1f}%", results)
    sat = np.mean((agc == 0) | (agc == 255))
    report("AGC 沒有飽和", sat <= AGC_SAT_FRAC_MAX,
           f"AGC 平均 {agc.mean():.0f}（範圍 {agc.min()}–{agc.max()}），0 或 255 佔 {sat * 100:.1f}%", results)
    report("AGC 穩定", int(agc.max() - agc.min()) <= AGC_RANGE_MAX,
           f"最大−最小 = {int(agc.max() - agc.min())}（上限 {AGC_RANGE_MAX}）", results)
    noise = np.std(unwrap_deg(st[:, 1]))
    info(f"  靜態角度雜訊：標準差 {noise:.3f}°；magnitude 平均 {mag.mean():.0f}")

    # ---------------- 2. 手轉
    heading("2/3 用手慢轉")
    turns = {}
    for key, label in (("cw", "順時針"), ("ccw", "逆時針")):
        info(f"用手捏著擺錘，{label}慢慢轉 3 圈（每圈約 2–3 秒）。")
        wait_enter("按 Enter 開始，轉完再按一次 Enter")
        a = collect_until_enter(reader, max_s=60)
        data[key] = a
        turns[key] = a
    for key, label in (("cw", "順時針"), ("ccw", "逆時針")):
        a = turns[key]
        if len(a) < 10:
            report(f"{label}有資料", False, "幾乎沒有收到資料", results)
            continue
        total = unwrap_deg(a[:, 1])[-1]
        report(f"{label}無跳點", jumps(a[:, 1]) == 0, f"相鄰取樣差 > {JUMP_LSB} LSB 共 {jumps(a[:, 1])} 次", results)
        report(f"{label}圈數", TURN_DEG_MIN <= abs(total) <= TURN_DEG_MAX,
               f"累積 {total:+.0f}°（3 圈應約 ±1080°）", results)
    if len(turns.get("cw", [])) > 10 and len(turns.get("ccw", [])) > 10:
        s1 = unwrap_deg(turns["cw"][:, 1])[-1]
        s2 = unwrap_deg(turns["ccw"][:, 1])[-1]
        report("兩個方向正負相反", s1 * s2 < 0, f"{s1:+.0f}° 與 {s2:+.0f}°", results)
        both = np.concatenate([turns["cw"], turns["ccw"]])
        bins = (both[:, 1] * COVER_BINS // 4096).astype(int)
        covered = len(np.unique(bins))
        report("一圈每個角度都讀得到", covered == COVER_BINS, f"{covered}/{COVER_BINS} 格", results)
        # 偏心：同一角度格子裡的 magnitude 平均，看一圈內起伏多少
        per_bin = np.array([both[bins == b, 4].mean() for b in range(COVER_BINS) if np.any(bins == b)])
        ripple = (per_bin.max() - per_bin.min()) / per_bin.mean()
        report("磁鐵對心", ripple <= MAG_RIPPLE_MAX,
               f"一圈內 magnitude 起伏 {ripple * 100:.1f}%（上限 {MAG_RIPPLE_MAX * 100:.0f}%）", results)

    # ---------------- 3. 自由擺（選做）
    heading("3/3 自由擺（選做）")
    if ask_yes("要做自由擺測試嗎？", default=False):
        info("把擺錘拉到約 60°，按 Enter 的同時放手。會錄 20 秒。")
        wait_enter("拉好就按 Enter 並放手")
        reader.take()
        time.sleep(20)
        fs = reader.take()
        data["swing"] = fs
        if len(fs) > 100:
            t = (fs[:, 0] - fs[0, 0]) * 1e-6
            ang = unwrap_deg(fs[:, 1])
            rest = np.median(ang[-500:])
            x = ang - rest
            amp = np.abs(x)
            # 小振幅段：最大振幅 < 20° 之後的零交越
            small = np.where(np.maximum.accumulate(amp[::-1])[::-1] < 20)[0]
            zc = np.where((x[:-1] < 0) & (x[1:] >= 0))[0]
            zc = zc[np.isin(zc, small)] if len(small) else np.array([], int)
            if len(zc) >= 4:
                tz = t[zc] + (t[zc + 1] - t[zc]) * (-x[zc] / (x[zc + 1] - x[zc]))
                period = float(np.median(np.diff(tz)))
                report("小振幅週期", PERIOD_RANGE_S[0] <= period <= PERIOD_RANGE_S[1],
                       f"{period:.4f} s（參考 0.50–0.51 s）", results)
            else:
                warn("擺動太快停下來，抓不到足夠的小振幅週期")
            pk = x[: len(x) // 3]
            pos, neg = pk.max(), -pk.min()
            asym = abs(pos - neg) / max(pos, neg, 1e-6)
            report("左右擺幅對稱", asym <= SYMMETRY_MAX, f"+{pos:.1f}° / −{neg:.1f}°（差 {asym * 100:.0f}%）", results)
    reader.close()

    # ---------------- 存檔與圖
    np.savez(out_dir / "encoder_check.npz", **data)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        for key, colr in (("cw", "tab:pink"), ("ccw", "tab:cyan"), ("swing", "tab:orange")):
            if key in data and len(data[key]) > 1:
                a = data[key]
                axes[0].plot((a[:, 0] - a[0, 0]) * 1e-6, unwrap_deg(a[:, 1]), color=colr, label=key)
                axes[1].scatter(a[:, 1] * 360 / 4096, a[:, 4], s=2, color=colr, label=key)
        axes[0].set_xlabel("time (s)")
        axes[0].set_ylabel("angle (deg, unwrapped)")
        axes[0].legend()
        axes[1].set_xlabel("raw angle (deg)")
        axes[1].set_ylabel("AS5600 magnitude")
        axes[1].set_title("flat = centred magnet")
        fig.tight_layout()
        fig.savefig(out_dir / "encoder_check.png", dpi=120)
    except Exception as e:  # noqa: BLE001
        warn(f"畫圖失敗（不影響結果）：{e}")

    heading("結果")
    n_fail = sum(1 for _, p, _ in results if not p)
    if n_fail == 0:
        ok(f"全部 {len(results)} 項 PASS")
    else:
        fail(f"{n_fail} 項 FAIL。照網站「編碼器測試」的 FAIL 處理表調整後，再雙擊 02_check_encoder。")
    info(f"資料與圖：{out_dir}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    finish(main())

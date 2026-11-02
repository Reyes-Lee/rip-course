"""擺錘方向標定（04_check_direction）與其他工具開工前的方向檢查。

只有「擺錘相對手臂」的方向會影響策略：整台機台左右鏡像沒關係（受控體對稱），
但只有擺錘反向時，策略推的方向剛好錯半拍，完全甩不上去。所以不靠人眼判斷
順時針／逆時針，直接量物理：手臂突然加速時，垂下的擺錘一定被往反方向帶。
在模擬的座標裡，「手臂角加速度」和「擺錘角加速度」的相關係數是負的
（同樣的雙脈衝動作在 MuJoCo 約 −0.98）。實機量到正的，就是擺錘方向反了。

方向值存在 Nano 的 EEPROM（LowLevelServer 的 CMD_SET_PEN_SIGN），
RLControl 開機時讀同一個位址。Arduino IDE 重新上傳 sketch 不會清掉 EEPROM。
"""
from __future__ import annotations

import json
import time

import numpy as np

from _common import fail, finish, info, ok, warn
from _rig import connect, move_pos

# 模擬座標裡「手臂角加速度 vs 擺錘角加速度」的相關係數正負號。
EXPECTED_SIGN = -1
CORR_MIN = 0.6          # 相關係數絕對值低於這個就判讀不出來（手臂沒動、擺錘被卡住）

# 雙脈衝：+A 持續 T、−A 持續 2T、+A 持續 T。結束時速度回到 0，位移也回到 0，
# 中途最大位移 A·T² ≈ 9°、最大速度 A·T = 4 rad/s（韌體上限 5 rad/s）。
PULSE_ACCEL = 100.0     # rad/s²
PULSE_T = 0.04          # s
N_DOUBLETS = 8
PAUSE_S = 0.35          # 每個雙脈衝之後回到 0° 並等擺錘的反應被記錄

NOT_CALIBRATED_MSG = "這台機台還沒做方向標定。先執行 tools/04_check_direction（燒 LowLevelServer）。"
OLD_FIRMWARE_MSG = ("Nano 上的 LowLevelServer 是舊版，不支援方向標定。"
                    "用 Arduino IDE 重新上傳 firmware/LowLevelServer，再執行一次。")


def _sample_until(cli, t_end: float, rows: list, flag: int) -> None:
    while time.perf_counter() < t_end:
        s = cli.get_state()
        rows.append((s.time_us, s.motor_vel_rad_s, s.pendulum_vel_rad_s, flag))


def measure(cli) -> dict:
    """手臂在 0° 附近做 N_DOUBLETS 個雙脈衝，回傳相關係數與原始資料。

    呼叫前：已用 _rig.connect 連線（手臂、擺錘已歸零），擺錘靜止垂下。
    """
    rows: list = []
    cli.engage_motor()
    time.sleep(0.3)
    for k in range(N_DOUBLETS):
        sgn = 1.0 if k % 2 == 0 else -1.0
        t = time.perf_counter()
        for a, dur in ((sgn, PULSE_T), (-sgn, 2 * PULSE_T), (sgn, PULSE_T)):
            cli.set_acceleration(a * PULSE_ACCEL)
            t += dur
            _sample_until(cli, t, rows, 1)
        cli.set_acceleration(0.0)
        _sample_until(cli, t + 0.12, rows, 1)      # 擺錘對最後一段加速度的反應
        cli.set_target(0.0)                        # 位置模式拉回正中間，不納入計算
        _sample_until(cli, time.perf_counter() + PAUSE_S, rows, 0)
    move_pos(cli, 0.0)
    cli.disengage_motor()

    d = np.array(rows, dtype=float)
    t = (d[:, 0] - d[0, 0]) * 1e-6
    keep = np.concatenate([[True], np.diff(t) > 0])   # 同一筆樣本可能被讀兩次
    d, t = d[keep], t[keep]
    arm_acc = np.gradient(d[:, 1], t)
    pen_acc = np.gradient(d[:, 2], t)
    m = d[:, 3] > 0
    corr = float(np.corrcoef(arm_acc[m], pen_acc[m])[0, 1]) if m.sum() > 20 else 0.0
    if not np.isfinite(corr):
        corr = 0.0
    return {"corr": corr, "t": t, "arm_vel": d[:, 1], "pen_vel": d[:, 2],
            "arm_acc": arm_acc, "pen_acc": pen_acc, "mask": m}


def verdict(corr: float) -> str:
    """'ok'：方向跟模擬一致；'flipped'：擺錘反了；'unclear'：判讀不出來。"""
    if abs(corr) < CORR_MIN:
        return "unclear"
    return "ok" if np.sign(corr) == EXPECTED_SIGN else "flipped"


def read_config(cli):
    """回傳 (已標定, 方向)；舊版韌體回傳 None。"""
    return cli.get_config()


def save_run(out_dir, results: list[dict], final_sign: int) -> None:
    """存數值與圖到 policy/direction_runs/<時間>/。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {"expected_sign": EXPECTED_SIGN, "final_pen_sign": final_sign,
               "runs": [{"label": r["label"], "pen_sign": r["pen_sign"], "corr": r["corr"]} for r in results]}
    (out_dir / "direction.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    np.savez(out_dir / "direction.npz", **{f"{r['label']}_{k}": r[k] for r in results
                                           for k in ("t", "arm_vel", "pen_vel", "arm_acc", "pen_acc", "mask")})
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(len(results), 1, figsize=(9, 3.2 * len(results)), squeeze=False)
        for ax, r in zip(axes[:, 0], results):
            m = r["mask"]
            ax.scatter(r["arm_acc"][m], r["pen_acc"][m], s=4, alpha=0.5)
            ax.axhline(0, color="0.7", lw=0.8)
            ax.axvline(0, color="0.7", lw=0.8)
            ax.set_xlabel("arm angular accel (rad/s²)")
            ax.set_ylabel("pendulum angular accel (rad/s²)")
            ax.set_title(f"{r['label']}: pen_sign {r['pen_sign']:+d}, corr {r['corr']:+.2f} "
                         f"(sim convention: negative)")
        fig.tight_layout()
        fig.savefig(out_dir / "direction.png", dpi=110)
        plt.close(fig)
    except Exception as e:  # noqa: BLE001  圖畫不出來不影響標定
        warn(f"方向圖沒有畫出來：{e}")


def require_direction(port: str, *, quick_check: bool = False) -> bool:
    """其他工具開工前呼叫：確認 Nano 已做方向標定。

    quick_check=True 時另外讓手臂動 4 秒，確認方向跟 EEPROM 的設定還一致
    （AS5600 的 DIR 腳沒接時，方向理論上可能改變）。不一致就停止，不要白跑。
    """
    with connect(port) as cli:
        cfg = read_config(cli)
        if cfg is None:
            fail(OLD_FIRMWARE_MSG)
            return False
        calibrated, sign = cfg
        if not calibrated:
            fail(NOT_CALIBRATED_MSG)
            return False
        if not quick_check:
            ok(f"方向標定：已完成（擺錘方向 {sign:+d}）")
            return True
        info("方向快速檢查：手臂會在正中間小幅來回抖動約 4 秒，擺錘保持垂下、不要碰。")
        time.sleep(1.0)
        r = measure(cli)
    v = verdict(r["corr"])
    if v == "ok":
        ok(f"方向快速檢查：一致（相關係數 {r['corr']:+.2f}）")
        time.sleep(3.0)   # 讓擺錘的小擺動停下來再開始
        return True
    if v == "flipped":
        fail(f"方向快速檢查：擺錘方向跟上次標定相反（相關係數 {r['corr']:+.2f}）。"
             "AS5600 的方向變了，先執行 04_check_direction 重新標定，並把這件事告訴助教。")
    else:
        fail(f"方向快速檢查：判讀不出來（相關係數 {r['corr']:+.2f}）。"
             "確認 12 V 有接、手臂和擺錘沒有被擋住，再試一次。")
    return False


def require_or_exit(port: str, *, quick_check: bool = False) -> None:
    if not require_direction(port, quick_check=quick_check):
        finish(1)

"""04_check_level：用擺錘當鉛錘，量底座傾斜的大小與方向。

原理：擺錘只能在「垂直於手臂」的平面擺動。底座往某個方向傾斜 β 時，手臂轉到
角度 φ，擺錘靜止的位置會偏 β·sin(ψ − φ)（ψ 是低的那一側）。手臂走 9 個角度，
每點量擺錘的平均位置，再擬合 a + b·cos φ + c·sin φ，就得到 β 與 ψ。
最後手臂會轉過去「指著低的那一側」，你在那一側的腳下墊東西即可。
"""
from __future__ import annotations

import math
import time

import numpy as np

from _common import POLICY, banner, fail, finish, get_port, heading, info, ok, wait_enter, warn
from _rig import connect, deg, move_pos, rad

ANGLES_DEG = [-120, -90, -60, -30, 0, 30, 60, 90, 120]
SETTLE_S = 3.0        # 到位後先等擺錘晃一下
AVERAGE_S = 2.0       # 再取 2 秒平均（約 4 個週期，還在晃也能取到中心）
TARGET_DEG = 1.0      # 目標：傾斜 < 1°
# 擺錘角度正負方向與實機的對應，由助教在正常機台上確認一次。
# 墊高後傾斜反而變大，就把這個值改成 -1。
TILT_SIGN = +1


def mean_pendulum(cli, seconds: float) -> float:
    vals = []
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        vals.append(cli.get_state().pendulum_pos_rad)
        time.sleep(0.005)
    return float(np.mean(vals))


def main() -> int:
    banner("04 底座傾斜測試", "firmware/LowLevelServer", needs_rig=True)
    info("準備：機台放在要做實驗的桌面上，四角著地。")
    info("用手把手臂轉到正中間（正前方），讓擺錘靜止垂下。")
    port = get_port()
    wait_enter("準備好就按 Enter（Nano 會重開約 2 秒，這段時間不要碰擺錘）")

    phis, thetas = [], []
    with connect(port) as cli:
        cli.engage_motor()
        time.sleep(0.3)
        theta_start = mean_pendulum(cli, 1.0)
        heading(f"手臂走 {len(ANGLES_DEG)} 個角度，約 1 分鐘，不要碰機台")
        for a in ANGLES_DEG:
            move_pos(cli, rad(a))
            time.sleep(SETTLE_S)
            th = mean_pendulum(cli, AVERAGE_S)
            phis.append(rad(a))
            thetas.append(th)
            print(f"  手臂 {a:+5d}°　擺錘靜止位置 {deg(th):+6.2f}°")
        move_pos(cli, 0.0)
        time.sleep(SETTLE_S)
        theta_end = mean_pendulum(cli, AVERAGE_S)

        phi = np.array(phis)
        th = np.array(thetas)
        A = np.column_stack([np.ones_like(phi), np.cos(phi), np.sin(phi)])
        (a0, b, c), *_ = np.linalg.lstsq(A, th, rcond=None)
        resid = th - A @ np.array([a0, b, c])
        tilt = math.degrees(math.hypot(b, c))
        psi = math.atan2(b, -c)               # 低的那一側（手臂角度座標）
        if TILT_SIGN < 0:
            psi += math.pi
        psi = (psi + math.pi) % (2 * math.pi) - math.pi

        heading("結果")
        info(f"傾斜大小：{tilt:.2f}°（目標 < {TARGET_DEG:.0f}°）")
        info(f"擬合殘差：{math.degrees(np.sqrt(np.mean(resid ** 2))):.2f}°　"
             f"（0° 位置前後差 {math.degrees(theta_end - theta_start):+.2f}°）")
        if math.degrees(np.sqrt(np.mean(resid ** 2))) > 0.8:
            warn("殘差偏大：量測時機台可能被碰到或桌面在晃，結果僅供參考，建議重測。")

        np.savez(POLICY / "level_check_last.npz", phi=phi, theta=th, tilt_deg=tilt, psi_rad=psi)

        if tilt < TARGET_DEG:
            ok(f"PASS：傾斜 {tilt:.2f}° < {TARGET_DEG:.0f}°，不用墊。")
            move_pos(cli, 0.0)
            return 0

        # 手臂轉過去指著低的那一側（後方約 ±125° 以外轉不過去，就指相反方向）
        point = psi
        opposite = False
        if abs(math.degrees(point)) > 120:
            point = (psi + math.pi + math.pi) % (2 * math.pi) - math.pi
            opposite = True
        move_pos(cli, point)
        if opposite:
            fail(f"FAIL：傾斜 {tilt:.2f}°。手臂現在指著的是「高」的那一側，"
                 f"請在手臂指向的「反方向」那一側的腳下墊東西。")
        else:
            fail(f"FAIL：傾斜 {tilt:.2f}°。手臂現在指著的那一側比較低，請在那一側的腳下墊東西。")
        info("先換一張桌子或確認四角著地；墊好後再雙擊 04_check_level 重測。")
        info("如果墊了之後傾斜反而變大，代表方向判斷相反，請告訴助教。")
        wait_enter("看清楚手臂指的方向後按 Enter，手臂會轉回中間")
        move_pos(cli, 0.0)
        return 1


if __name__ == "__main__":
    finish(main())

"""03_check_motor、04_check_level 共用：透過 LowLevelServer 控制手臂。"""
from __future__ import annotations

import math
import sys
import time
from contextlib import contextmanager

from _common import POLICY, fail, finish

sys.path.insert(0, str(POLICY))
from lowlevel_client import LowLevelClient  # noqa: E402  作者的 serial 用戶端


@contextmanager
def connect(port: str):
    """打開序列埠（Nano 會重開約 2 秒），確認是 LowLevelServer，並把手臂現在的位置設成 0。"""
    with LowLevelClient(port) as cli:
        if not cli.wait_until_ready():
            fail("LowLevelServer 沒有回應。確認燒的是 firmware/LowLevelServer，並關掉序列埠監控。")
            finish(1)
        cli.zero_motor()
        cli.tare_pendulum()
        try:
            yield cli
        finally:
            try:
                cli.set_acceleration(0.0)
                cli.disengage_motor()
            except Exception:  # noqa: BLE001
                pass


def move_accel(cli, target: float, a_max: float, v_max: float = 3.5, timeout_s: float = 5.0) -> float:
    """用加速度指令把手臂移到 target（rad），峰值加速度 a_max（rad/s²）。

    與策略相同的指令路徑（CMD_SET_ACCEL）。在主機端跑時間最佳的
    加速→等速→減速曲線，最後交給位置模式停在目標上。回傳實際峰值加速度。
    """
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout_s:
        s = cli.get_state()
        e = target - s.motor_pos_rad
        if abs(e) < 0.01 and abs(s.motor_vel_rad_s) < 0.3:
            break
        v_des = math.copysign(min(v_max, math.sqrt(2.0 * 0.85 * a_max * abs(e))), e)
        acc = max(-a_max, min(a_max, 60.0 * (v_des - s.motor_vel_rad_s)))
        cli.set_acceleration(acc)
        time.sleep(0.004)
    cli.set_acceleration(0.0)
    cli.set_target(target)          # 位置模式收尾，停在目標上
    time.sleep(0.25)
    return a_max


def move_pos(cli, target: float, timeout_s: float = 6.0) -> None:
    """位置模式移動（韌體內建約 98 rad/s² 的平滑曲線），等到到位。"""
    cli.set_target(target)
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout_s:
        s = cli.get_state()
        if abs(target - s.motor_pos_rad) < 0.005 and abs(s.motor_vel_rad_s) < 0.05:
            return
        time.sleep(0.01)


def deg(x: float) -> float:
    return math.degrees(x)


def rad(x: float) -> float:
    return math.radians(x)

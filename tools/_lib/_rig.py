"""03_check_motor 用：透過 LowLevelServer 控制手臂。"""
from __future__ import annotations

import math
import sys
import time
from contextlib import contextmanager

from _common import POLICY, fail, finish, info, warn

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
        raw_get_state = cli.get_state
        drops = 0

        def get_state_retry():
            # 序列埠偶爾掉一個位元組（馬達通電的雜訊），韌體就不會回這一筆。等韌體 5 ms 的讀取逾時過去，再要一次。
            nonlocal drops
            try:
                return raw_get_state()
            except RuntimeError as e:
                if not str(e).startswith("get_state:"):
                    raise
                drops += 1
                time.sleep(0.02)
                cli.ser.reset_input_buffer()
                return raw_get_state()

        ref_us = None
        try:
            ref_us = raw_get_state().time_us       # Nano 開機後的時間；之後變小就代表它重開過
            cli.get_state = get_state_retry
            yield cli
        except RuntimeError as e:
            if not str(e).startswith("get_state:"):
                raise
            drops = 0                              # 下面會說明，不用再印重試的次數
            explain_no_reply(cli, raw_get_state, ref_us)
            finish(1)
        finally:
            try:
                cli.set_acceleration(0.0)
                cli.disengage_motor()
            except Exception:  # noqa: BLE001
                pass
            if drops:
                warn(f"過程中有 {drops} 次沒收到 Nano 的回應，工具自動重新要了一次。")


def explain_no_reply(cli, raw_get_state, ref_us) -> None:
    """GET_STATE 連續兩次收不到回應：判斷 Nano 是卡住、重開、只是通訊掉資料，還是 USB 斷了，印出該怎麼做。"""
    print()
    fail("Nano 沒有回應（GET_STATE 連續兩次收不到資料）。")
    info("正在判斷是哪裡出問題，約 4 秒⋯")
    try:
        cli.disengage_motor()
        time.sleep(2.5)                      # 如果是重開，等它跑完開機程序
        back = cli.wait_until_ready(retries=4, retry_delay_s=0.4)
        now_us = raw_get_state().time_us if back else None
    except RuntimeError:
        now_us = None
    except Exception:  # noqa: BLE001  序列埠本身不見了
        fail("序列埠斷線了：Nano 的 USB 連線掉了。")
        info("  換一條 USB 線、換一個電腦上的 USB 孔，再執行一次。")
        info("還是一樣就在 Discord 開 ticket，把整個畫面截圖給助教。")
        return
    if not back:
        fail("Nano 卡住了：多半是讀編碼器（AS5600）的 I²C 被馬達通電的雜訊卡住。")
        info("  1. 用 git pull 拿新版，重新上傳 firmware/LowLevelServer（新版讀編碼器卡住時會自己恢復）。")
        info("  2. 再執行一次。")
    elif ref_us is not None and now_us is not None and now_us < ref_us:
        fail("Nano 重開了：馬達通電的時候 Nano 被重置（開機後的時間歸零了）。")
        info("  換一條 USB 線、換一個電腦上的 USB 孔，再執行一次。")
    elif now_us is not None:
        fail("Nano 沒有重開，但馬達通電時序列埠一直掉資料，收不到回應。")
        info("  換一條 USB 線、換一個電腦上的 USB 孔，再執行一次。")
    else:
        fail("Nano 有回應握手，但還是讀不到狀態。")
    info("還是一樣就在 Discord 開 ticket，把整個畫面截圖給助教。")


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

"""04_check_direction：擺錘方向標定，結果存進 Nano 的 EEPROM。

AS5600 模組的 DIR 腳出廠可能接 GND、接 VCC 或沒接，擺錘角度的正方向因此不一定
跟模擬一樣。這個工具讓手臂在正中間小幅抖動，看垂下的擺錘被往哪邊帶：
跟模擬一致就記下來；相反就把方向寫進 EEPROM，再測一次確認。
不需要判斷順時針或逆時針。原理見 tools/_direction.py。
"""
from __future__ import annotations

import time

from _common import POLICY, banner, fail, finish, get_port, heading, info, ok, rel, wait_enter, warn
from _direction import OLD_FIRMWARE_MSG, measure, read_config, save_run, verdict
from _rig import connect


def run_once(cli, label: str, sign: int, results: list) -> str:
    info("手臂會在正中間小幅來回抖動約 4 秒（左右各約 10°）。")
    time.sleep(1.0)
    r = measure(cli)
    r.update(label=label, pen_sign=sign)
    results.append(r)
    info(f"  手臂加速度 vs 擺錘加速度 相關係數：{r['corr']:+.2f}（跟模擬一致時是負的，約 −0.9）")
    return verdict(r["corr"])


def main() -> int:
    banner("04 方向標定：擺錘方向跟模擬一致", "firmware/LowLevelServer", needs_rig=True)
    info("準備：")
    info("  1. 12 V 接好；手臂轉到正中間（正前方），周圍淨空。")
    info("  2. 擺錘自然垂下、靜止。測試時不要碰機台。")
    port = get_port()
    wait_enter("準備好就按 Enter（Nano 會重開約 2 秒）")
    out_dir = POLICY / "direction_runs" / time.strftime("%Y%m%d_%H%M%S")
    results: list = []

    with connect(port) as cli:
        cfg = read_config(cli)
        if cfg is None:
            fail(OLD_FIRMWARE_MSG)
            return 1
        calibrated, sign = cfg
        info(f"目前 Nano 上的設定：{'已標定' if calibrated else '還沒標定'}，擺錘方向 {sign:+d}")

        heading("1/2 量測")
        v = run_once(cli, "before", sign, results)
        if v == "unclear":
            fail("判讀不出來：擺錘幾乎沒有跟著手臂反應。")
            info("  常見原因：12 V 沒接（手臂其實沒動）、擺錘被東西卡住、AS5600 讀值異常（先跑 02_check_encoder）。")
            save_run(out_dir, results, sign)
            return 1

        if v == "flipped":
            new_sign = -sign
            warn(f"擺錘方向跟模擬相反，改成 {new_sign:+d} 並寫入 EEPROM。")
            if not cli.set_pendulum_sign(new_sign):
                fail("Nano 沒有回應寫入指令。重新上傳 firmware/LowLevelServer 後再試一次。")
                return 1
            sign = new_sign
            heading("2/2 修正後再量一次")
            info("等擺錘停下來…")
            time.sleep(4.0)
            cli.tare_pendulum()
            v = run_once(cli, "after", sign, results)
            if v != "ok":
                fail("修正後仍然不一致。把 policy/direction_runs/ 最新資料夾拿給助教。")
                save_run(out_dir, results, sign)
                return 1
        else:
            heading("2/2 確認")
            if not calibrated:
                if not cli.set_pendulum_sign(sign):
                    fail("Nano 沒有回應寫入指令。重新上傳 firmware/LowLevelServer 後再試一次。")
                    return 1
            ok("方向本來就跟模擬一致，不用修正。")

    save_run(out_dir, results, sign)
    heading("結果")
    ok(f"PASS：擺錘方向 {sign:+d} 已存在 Nano 的 EEPROM。")
    info(f"紀錄：policy/{rel(out_dir)}（direction.png 是手臂加速度 vs 擺錘加速度，點應該排成往右下的斜線）")
    info("重新上傳 LowLevelServer 或 RLControl 不會清掉這個設定。換 Nano、重新安裝 AS5600 或磁鐵之後要重做。")
    if len(results) > 1:
        warn("方向剛被修正：之前在錯的方向下做的實機微調（runs/ftN）要丟掉，從教師重新微調。"
             "sysid 與模擬訓練不受影響。")
    return 0


if __name__ == "__main__":
    finish(main())

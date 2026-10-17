"""03_check_motor：加速度逐級升到 150 rad/s²，檢查步進馬達會不會失步。

步進馬達是開迴路的：失步時韌體的步數計數不會知道，所以要靠「手臂回到原點時
還對不對得齊記號」來判斷。每一級來回擺動後回到 0°，由你目視確認。
"""
from __future__ import annotations

import time

from _common import ask_yes, banner, fail, finish, get_port, heading, info, ok, wait_enter, warn
from _rig import connect, move_accel, move_pos, rad

LEVELS = [30, 60, 90, 120, 150]   # rad/s²；150 是策略會用到的上限
AMPLITUDE_DEG = 45                 # 每級在 ±45° 之間來回
CYCLES = 4


def main() -> int:
    banner("03 馬達失步測試", "firmware/LowLevelServer", needs_rig=True)
    info("準備：")
    info("  1. 用手把手臂轉到正中間（正前方）。")
    info("  2. 在底座上貼一小段膠帶，對齊手臂末端，當作原點記號。")
    info("  3. 擺錘讓它自然垂下；手臂周圍不要有東西擋到。")
    info("每一級跑完，手臂會回到 0°，請看末端是不是還對齊膠帶。")
    info("偏移超過約 1 mm（大約 1°）就算失步。")
    port = get_port()
    wait_enter("準備好就按 Enter（Nano 會重開約 2 秒）")

    results = []
    with connect(port) as cli:
        cli.engage_motor()
        time.sleep(0.3)
        for a in LEVELS:
            heading(f"加速度 {a} rad/s²")
            for _ in range(CYCLES):
                move_accel(cli, rad(AMPLITUDE_DEG), a)
                move_accel(cli, rad(-AMPLITUDE_DEG), a)
            move_accel(cli, 0.0, a)
            move_pos(cli, 0.0)
            aligned = ask_yes("手臂末端還對齊膠帶嗎？", default=True)
            quiet = ask_yes("剛才的聲音是平順的嗡嗡聲（沒有嘶嘶或磨擦聲）嗎？", default=True)
            results.append((a, aligned, quiet))
            if not (aligned and quiet):
                warn("這一級出現問題，停止測試，避免手臂越偏越多。")
                break

    heading("結果")
    for a, aligned, quiet in results:
        line = f"{a:>4} rad/s²：對齊 {'是' if aligned else '否'}，聲音 {'正常' if quiet else '異常'}"
        (ok if aligned and quiet else fail)(line)
    all_ok = len(results) == len(LEVELS) and all(al and q for _, al, q in results)
    if all_ok:
        ok("PASS：到 150 rad/s² 都沒有失步。")
        return 0
    fail("FAIL：有失步。把結果拿給助教，檢查 Vref 與韌體加速度設定；不要自己轉可變電阻。")
    return 1


if __name__ == "__main__":
    finish(main())

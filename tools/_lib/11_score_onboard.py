"""11_score_onboard：Nano 獨立執行，用誠實指標評分（作者的 analyze_onboard.py）。

評分秒數會在畫面上問，直接按 Enter 是作者的 60 秒。評分前先丟掉開始的 5 秒（甩上）。
"""
from __future__ import annotations

import time

from _common import RECORDINGS, ask_number, banner, finish, get_port, info, rel, run_policy_script

DURATION_S = 60


def main() -> int:
    banner("11 獨立執行評分", "firmware/RLControl", needs_rig=True)
    duration = ask_number("評分秒數（不含開始的 5 秒）", DURATION_S, 5, 600)
    info("打開序列埠會讓 Nano 重開。重開後工具會先讓馬達斷電，")
    info("等你把手臂轉回正中間、擺錘靜止垂下再按 Enter，Nano 才抓零點並開始。")
    port = get_port()
    RECORDINGS.mkdir(parents=True, exist_ok=True)
    log = RECORDINGS / f"onboard_{time.strftime('%Y%m%d_%H%M%S')}.npz"
    code, _ = run_policy_script(["analyze_onboard.py", "--port", port, "--duration-s", str(duration), "--rearm",
                                 "--log", rel(log)])
    print()
    info(f"紀錄檔：policy/{rel(log)}")
    info("照順序看：1. 第一行頻率約 50 Hz　2. sample→command 延遲　3. balanced fraction 等指標。")
    return code


if __name__ == "__main__":
    finish(main())

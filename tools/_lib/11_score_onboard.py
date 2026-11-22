"""11_score_onboard：Nano 獨立執行，用誠實指標評分（作者的 analyze_onboard.py）。

1 一般評分：評分秒數會在畫面上問，直接按 Enter 是作者的 60 秒。評分前先丟掉開始的 5 秒（甩上）。
2 延遲階梯（進階任務）：同一支策略，從 +0 ms 起一階一階加延遲，每一階重新甩上，
  連續平衡滿 20 秒算通過，成績是最後通過的那一階（policy/latency_ladder.py）。
3 甩上計時（進階任務）：不加延遲甩 3 次，每次 20 秒內要站穩（連續平衡滿 10 秒）才算數，
  甩上時間 = engage 到站穩那一段開始的秒數，成績是中位數（latency_ladder.py --swingup）。
"""
from __future__ import annotations

import time

from _common import RECORDINGS, ask_number, banner, choose, finish, get_port, info, rel, run_policy_script

DURATION_S = 60


LADDER_START = (0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70)


def ladder() -> int:
    info("延遲階梯：+0、+10、+15、+20 … +70 ms，由低往高測。每一階都要你把手臂轉回正中間再按 Enter。")
    info("每一階 engage 後 40 秒內連續平衡滿 20 秒就通過，馬上進下一階；沒過可以重試 1 次，還是沒過就停。")
    info("延遲直接用序列埠設定，不看 latency_profile.h，所以不用重新上傳。")
    start = choose("從哪一階開始？（demo 從 +0；練習可以從比較高的開始，但結果不算正式成績）",
                   list(LADDER_START), [f"+{x} ms" for x in LADDER_START], default=0)
    port = get_port()
    out = RECORDINGS / f"ladder_{time.strftime('%Y%m%d_%H%M%S')}"
    code, _ = run_policy_script(["latency_ladder.py", "--port", port, "--start-ms", str(start),
                                 "--out-dir", rel(out)])
    return code


def swingup() -> int:
    info("甩上計時：不加延遲，甩 3 次。每一次 20 秒內要站穩（連續平衡滿 10 秒）才算數。")
    info("甩上時間 = engage 到站穩那一段開始的秒數；成績是 3 次的中位數（有 2 次沒站穩就沒有成績）。")
    info("要先上傳你們的甩上策略（RLControl ＋ 甩上用的 policy_weights_student.h）。")
    port = get_port()
    out = RECORDINGS / f"swingup_{time.strftime('%Y%m%d_%H%M%S')}"
    code, _ = run_policy_script(["latency_ladder.py", "--port", port, "--swingup", "3",
                                 "--out-dir", rel(out)])
    return code


def main() -> int:
    banner("11 獨立執行評分", "firmware/RLControl", needs_rig=True)
    mode = choose("要做哪一種評分？", [1, 2, 3],
                  ["一般評分（60 秒）", "延遲階梯（進階任務）", "甩上計時（進階任務）"], default=0)
    if mode in (2, 3):
        RECORDINGS.mkdir(parents=True, exist_ok=True)
        return ladder() if mode == 2 else swingup()
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
    info("swing-up time 是按下 Enter（Nano 開始甩）到第一次連續平衡滿 1 秒的秒數；never caught 代表整段都沒接住。")
    return code


if __name__ == "__main__":
    finish(main())

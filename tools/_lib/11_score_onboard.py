"""11_score_onboard：Nano 獨立執行，用誠實指標評分（作者的 analyze_onboard.py）。

1 一般評分：評分秒數會在畫面上問，直接按 Enter 是作者的 60 秒。評分前先丟掉開始的 5 秒（甩上）。
2 延遲階梯（專題任務）：同一支策略，自己選 5 階（不一定連續），由低到高測，每一階重新甩上，
  30 秒內連續平衡滿 10 秒算通過，成績是最後通過的那一階（policy/latency_ladder.py）。
3 甩上到平衡計時（專題任務）：不加延遲甩 3 次，每次 20 秒內要站穩（連續平衡滿 10 秒）才算數，
  甩上時間 = engage 到站穩那一段開始的秒數，成績是中位數（latency_ladder.py --swingup）。
"""
from __future__ import annotations

import time

from _common import RECORDINGS, ask_number, banner, choose, finish, get_port, info, rel, run_policy_script, warn

DURATION_S = 60


# 和 policy/latency_ladder.py 的 DEFAULT_LEVELS 同一組（那邊會再檢查一次）。tools 的 Python 環境
# 沒有 serial／numpy，所以這裡另外寫一份；改階的時候兩邊要一起改。
LADDER_LEVELS = (0, 10, 15, 20, 25, 30, 35, 37, 40, 42, 45, 47, 50, 55)


def ask_levels(n: int = 5) -> list[int]:
    """問要測哪 n 階：用空白或逗號分開，+ 可加可不加。"""
    allowed = "、".join(f"+{x}" for x in LADDER_LEVELS)
    info(f"可以選的階：{allowed}")
    while True:
        try:
            ans = input(f"要測哪 {n} 階？用空白分開，例如 0 20 35 40 45: ").strip()
        except EOFError:
            raise SystemExit("沒有輸入，停止")
        for sep in (",", "，", "、", ";", "；"):
            ans = ans.replace(sep, " ")
        try:
            xs = [int(t.lstrip("+＋")) for t in ans.split()]
        except ValueError:
            warn("請輸入數字，例如 0 20 35 40 45")
            continue
        bad = [x for x in xs if x not in LADDER_LEVELS]
        if bad:
            warn(f"{'、'.join(f'+{x}' for x in bad)} 不是延遲階梯的階。可以選：{allowed}")
        elif len(set(xs)) != len(xs):
            warn("選的階有重複")
        elif len(xs) != n:
            warn(f"要選剛好 {n} 階，你選了 {len(xs)} 階")
        else:
            xs = sorted(xs)
            info("會依序測：" + "、".join(f"+{x}" for x in xs))
            return xs


def ladder() -> int:
    info("延遲階梯共 14 階：+0、+10、+15、+20、+25、+30、+35、+37、+40、+42、+45、+47、+50、+55（沒有 +5）。"
         "你們要選剛好 5 階，不一定連續，由低到高測，每一階都要你把手臂轉回正中間再按 Enter。")
    info("每一階 engage 後 30 秒內要數完 10 秒連續平衡（最晚約第 20 秒要接住）就通過，馬上進下一階。")
    info("沒過可以重試 1 次，還是沒過就停，後面選的階不測。成績是最後通過的那一階；選的第一階就沒過，就沒有成績。")
    info("延遲直接用序列埠設定，不看 latency_profile.h，所以不用重新上傳。")
    levels = ask_levels()
    port = get_port()
    out = RECORDINGS / f"ladder_{time.strftime('%Y%m%d_%H%M%S')}"
    code, _ = run_policy_script(["latency_ladder.py", "--port", port, "--levels", *[str(x) for x in levels],
                                 "--out-dir", rel(out)])
    return code


def swingup() -> int:
    info("甩上到平衡計時：不加延遲，甩 3 次。每一次 20 秒內要數完 10 秒連續平衡（最晚約第 10 秒要接住）才算數。")
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
                  ["一般評分（60 秒）", "延遲階梯（專題任務）", "甩上到平衡計時（專題任務）"], default=0)
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

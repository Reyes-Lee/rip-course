"""07_finetune：實機非同步微調（作者的 finetune_async.py），每執行一次跑一段。

第一次（ft1）：從你選的教師開始，50 回合。
之後（ft2、ft3…）：自動從最新一段接續，帶上它的 replay buffer，30 回合。
"""
from __future__ import annotations

import time

from _common import (RUNS, banner, choose, fail, finish, finetune_runs, get_port, heading, info, label,
                     mark_done, need_sysid, ok, rel, run_policy_script, teachers, wait_enter, warn)
from _direction import require_or_exit

FIRST_EPISODES = 50
NEXT_EPISODES = 30


def main() -> int:
    banner("07 實機微調", "firmware/LowLevelServer", needs_rig=True)
    params = need_sysid()
    done = finetune_runs()
    n_next = (int(done[-1].name[2:]) + 1) if done else 1
    run_dir = RUNS / f"ft{n_next}"

    if run_dir.exists():
        # 上次這一段沒跑完（Ctrl+C 或當掉）：改名保留，這一段重跑。
        keep = run_dir.with_name(f"{run_dir.name}_incomplete_{time.strftime('%Y%m%d_%H%M%S')}")
        run_dir.rename(keep)
        warn(f"上次的 {run_dir.name} 沒有跑完，已改名為 {keep.name} 保留，這一段重跑。")

    if not done:
        ts = teachers()
        if not ts:
            fail("找不到完成的教師。請先做 Step 1：執行 06_train_teacher。")
            return 1
        teacher = choose("選要微調的教師（Step 1 檢查點你判斷最好的那一支）：", ts, [label(t) for t in ts])
        args = ["finetune_async.py", "--policy", rel(teacher), "--episodes", str(FIRST_EPISODES)]
        heading(f"第一段 ft1：從 {label(teacher)} 開始，{FIRST_EPISODES} 回合")
    else:
        prev = done[-1]
        args = ["finetune_async.py", "--policy", rel(prev / "best_model.zip"),
                "--resume-buffer", rel(prev / "replay_buffer.pkl"), "--episodes", str(NEXT_EPISODES)]
        heading(f"接續段 {run_dir.name}：從 {prev.name} 接續（帶上它的 replay buffer），{NEXT_EPISODES} 回合")

    port = get_port()
    info("每回合 6 秒；回合之間馬達斷電 15 秒，讓擺錘自己停下來。")
    info("前幾個回合要聽馬達：嘶嘶或磨擦聲代表失步，立刻按 Ctrl + C 停止。")
    wait_enter("擺錘靜止垂下、手臂周圍淨空後按 Enter")
    # 每一段開始前都確認方向沒變（AS5600 的 DIR 腳沒接時方向可能改變），最多浪費一段。
    require_or_exit(port, quick_check=True)
    code, out = run_policy_script([*args, "--port", port, "--run-name", run_dir.name, "--params-path", params],
                                  capture=True)
    if code != 0 or not (run_dir / "best_model.zip").exists() or not (run_dir / "replay_buffer.pkl").exists():
        fail(f"{run_dir.name} 沒有完成（代碼 {code}）。處理好問題後再執行 07_finetune，會重跑這一段。")
        return code or 1
    mark_done(run_dir)
    ok(f"已存：runs/{run_dir.name}/best_model.zip")
    if "new best deterministic eval" in out:
        info("這一段的 best_model 有更新（評估回合分數變好）。")
    else:
        warn("這一段的 best_model 沒有更新（評估回合都沒有比之前好）。仍照網站 Step 2 的停止規則決定要不要加段。")
    # 每 10 回合的 replay buffer 快照每份約 80 MB，下一段只用最後的 replay_buffer.pkl。
    snaps = sorted(run_dir.glob("replay_buffer_ep*.pkl"))
    if snaps:
        freed = sum(p.stat().st_size for p in snaps) / 1e6
        for p in snaps:
            p.unlink()
        info(f"已刪除 {len(snaps)} 份中途的 replay buffer 快照（約 {freed:.0f} MB），保留最後的 replay_buffer.pkl。")
    info("每回合那一行的 violations= 持續大於 0 時，先關掉其他程式（尤其是同步、備份或訓練）。")
    info("下一步：執行 08_test_policy 測 30 秒，再依網站 Step 2 的表決定要不要再加一段。")
    return 0


if __name__ == "__main__":
    finish(main())

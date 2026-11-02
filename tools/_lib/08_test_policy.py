"""08_test_policy：接線（LowLevelServer）測一支策略 30 秒，印誠實指標（作者的 run_policy.py）。"""
from __future__ import annotations

from _common import (RECORDINGS, banner, choose, fail, finetune_runs, finish, get_port, info, label, rel,
                     run_policy_script, students, teachers, wait_enter)
from _direction import require_or_exit


def main() -> int:
    banner("08 接線測試策略 30 秒", "firmware/LowLevelServer", needs_rig=True)
    # 清單順序：教師 → 微調段 → 學生；預設是最新的一段微調。
    items = teachers() + [d / "best_model.zip" for d in finetune_runs()] + students()
    if not items:
        fail("還沒有任何策略。請先做 Step 1 或 Step 2。")
        return 1
    fts = finetune_runs()
    default = items.index(fts[-1] / "best_model.zip") if fts else len(items) - 1
    pol = choose("選要測的策略：", items, [label(p) for p in items], default=default)
    name = label(pol).replace("/best_model.zip", "").replace("/", "_").replace(".pt", "")
    RECORDINGS.mkdir(parents=True, exist_ok=True)
    log = RECORDINGS / f"{name}.npz"
    port = get_port()
    require_or_exit(port)
    wait_enter("擺錘靜止垂下後按 Enter；接下來 30 秒不要碰機台")
    code, _ = run_policy_script(["run_policy.py", "--policy", rel(pol), "--port", port,
                                 "--duration-s", "30", "--log", rel(log)])
    print()
    info(f"紀錄檔：policy/{rel(log)}")
    info("看 balanced fraction（|θ| ≤ 15° 且 |θ̇| ≤ 4 rad/s 的時間比例），對照網站 Step 2 的表決定下一步。")
    return code


if __name__ == "__main__":
    finish(main())

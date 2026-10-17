"""12_view_policy：在 MuJoCo 視窗播放一支策略 30 秒（作者的 train_sac.py --eval）。"""
from __future__ import annotations

from _common import (SYSID_JSON, all_checkpoints, banner, choose, fail, finish, info, label, mujoco_python,
                     rel, run_policy_script)


def main() -> int:
    banner("12 在 MuJoCo 視窗看策略（不需要機台）")
    cps = all_checkpoints()
    if not cps:
        fail("還沒有任何訓練結果。請先做 Step 1：執行 06_train_teacher。")
        return 1
    cp = choose("選要看的策略：", cps, [label(c) for c in cps])
    args = ["train_sac.py", "--eval", rel(cp)]
    if SYSID_JSON.exists():
        args += ["--params-path", rel(SYSID_JSON)]
    info("視窗操作：左鍵拖曳旋轉、滾輪縮放；點兩下擺錘選取後，按住 Ctrl 用右鍵拖曳可以推它。")
    info("30 秒後視窗自動關閉。")
    code, _ = run_policy_script(args, python=mujoco_python())
    return code


if __name__ == "__main__":
    finish(main())

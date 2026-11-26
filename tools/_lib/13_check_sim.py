"""13_check_sim：對任何一支策略重跑模擬檢查點（對稱性＋敏感度關卡），只印數字。"""
from __future__ import annotations

from _common import all_checkpoints, banner, choose, color, fail, finish, info, label, students
from _checks import print_sensitivity, sensitivity, symmetry


def main() -> int:
    banner("13 模擬檢查點（不需要機台）")
    items = all_checkpoints() + students()
    if not items:
        fail("還沒有任何訓練結果。")
        return 1
    pol = choose("選要檢查的策略：", items, [label(p) for p in items])
    if pol.suffix == ".zip":
        symmetry(pol)
        on, off = sensitivity(pol)
        if (pol.parent / "replay_buffer.pkl").exists():
            # 實機微調過的模型是在接線的時序下練的。預設的模擬時序是 Nano 獨立執行（device），
            # 微調後在這個時序下的分數可能很低、甚至全部是 0，所以也用接線時序（tethered）測一次。
            t_on, t_off = sensitivity(pol, transport="tethered", tag="（接線時序）")
            print_sensitivity(on, off, "敏感度關卡結果（預設：Nano 獨立執行的時序）")
            print_sensitivity(t_on, t_off, "敏感度關卡結果（接線時序，跟微調時一樣）")
            info(color("  微調過的模型，模擬分數可能比實機低很多，兩種時序都可能很低。以實機 08_test_policy 的結果為準。", "dim"))
            return 0
    else:
        on, off = sensitivity(pol, transport="device")   # 蒸餾後的模型用 Nano 獨立執行的傳輸條件
    print_sensitivity(on, off)
    return 0


if __name__ == "__main__":
    finish(main())

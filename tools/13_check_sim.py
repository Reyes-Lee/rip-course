"""13_check_sim：對任何一支策略重跑模擬檢查點（對稱性＋敏感度關卡），只印數字。"""
from __future__ import annotations

from _common import all_checkpoints, banner, choose, fail, finish, label, students
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
    else:
        on, off = sensitivity(pol, transport="device")   # 學生用 Nano 獨立執行的傳輸條件
    print_sensitivity(on, off)
    return 0


if __name__ == "__main__":
    finish(main())

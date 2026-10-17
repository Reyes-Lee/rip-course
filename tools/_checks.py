"""06_train_teacher、09_distill、13_check_sim 共用：模擬裡的檢查點（只印數字，不替你判斷）。"""
from __future__ import annotations

import re
from pathlib import Path

from _common import color, heading, info, rel, run_policy_script

SENS_GOOD = 0.7   # 作者的校準：關掉韌體量測模型後 ≥ 0.7 的策略部署全部成功
SENS_BAD = 0.3    # ≤ 0.3 的四支全部失敗

# analyze_sim 正常時印 "balanced fraction: 0.xxx"；完全平衡不了時只印 "(gate 0.xxx)"
_BF = re.compile(r"balanced fraction:\s+([0-9.]+)|calmness \(gate ([0-9.]+)\)")


def balanced(out: str) -> float | None:
    m = _BF.findall(out)
    if not m:
        return None
    a, b = m[-1]
    return float(a or b)


def symmetry(policy: Path) -> str:
    heading("對稱性：從垂下的狀態能不能自己甩上")
    code, out = run_policy_script(["analyze_symmetry.py", rel(policy)], capture=True)
    m = re.search(r"time to upright:\s+([0-9.]+) s", out)
    if m:
        info(color(f"從垂下自己甩上：是（{m.group(1)} 秒）", "green"))
    elif "never reached upright" in out:
        info(color("從垂下自己甩上：否（10 秒內沒有甩上）", "red"))
    else:
        info(color("從垂下自己甩上：無法判讀，請看上面的輸出", "yellow"))
    return out


def sensitivity(policy: Path, *, transport: str | None = None, params: str | None = None) -> tuple[float | None, float | None]:
    extra = []
    if transport:
        extra += ["--transport", transport]
    if params:
        extra += ["--params-path", params]
    heading("敏感度關卡 1/2：開著韌體量測模型（20 回合）")
    _, out_on = run_policy_script(["analyze_sim.py", rel(policy), "--episodes", "20", *extra], capture=True)
    heading("敏感度關卡 2/2：關掉韌體量測模型（20 回合）")
    _, out_off = run_policy_script(["analyze_sim.py", rel(policy), "--episodes", "20",
                                    "--no-firmware-obs-model", *extra], capture=True)
    return balanced(out_on), balanced(out_off)


def print_sensitivity(on: float | None, off: float | None) -> None:
    heading("敏感度關卡結果")
    f = lambda x: "—" if x is None else f"{x:.3f}"  # noqa: E731
    info(f"  開著韌體量測模型：balanced fraction {f(on)}")
    info(f"  關掉韌體量測模型：balanced fraction {f(off)}")
    info(color(f"  參考門檻（作者的校準）：關掉後 ≥ {SENS_GOOD} 的策略部署全部成功；"
               f"≤ {SENS_BAD} 的全部失敗。由你判斷。", "dim"))

"""10_export_weights：核對 RLControl.ino 常數與策略設定，匯出 policy_weights_student.h。"""
from __future__ import annotations

import re
import sys

from _common import (POLICY, REPO, banner, choose, fail, finish, heading, info, label, ok, rel,
                     run_policy_script, students)

sys.path.insert(0, str(POLICY))
from run_config import find_run_config  # noqa: E402

SKETCH = REPO / "firmware" / "RLControl" / "RLControl.ino"
HEADER = REPO / "firmware" / "RLControl" / "policy_weights_student.h"
# sketch 常數 → config.json 的欄位（MICROSTEPS 對驅動板接線，課程固定 32）
CHECKS = [
    ("CONTROL_FREQUENCY_HZ", "control_freq_hz"),
    ("ACTION_SMOOTH_WINDOW", "action_smooth_window"),
    ("OBS_FRAMES", "obs_history_len"),
    ("MAX_VELOCITY_RAD_S", "max_velocity_rad_s"),
    ("MICROSTEPS", "motor_microsteps"),
]


def sketch_const(src: str, name: str) -> float | None:
    m = re.search(rf"const\s+\w+\s+{name}\s*=\s*([0-9.]+)f?\s*;", src)
    return float(m.group(1)) if m else None


def main() -> int:
    banner("10 匯出學生權重（不需要機台）")
    ss = students()
    if not ss:
        fail("找不到學生。請先做 Step 3：執行 09_distill。")
        return 1
    st = choose("選要匯出的學生：", ss, [label(s) for s in ss])
    cfg = find_run_config(st) or {}
    src = SKETCH.read_text(encoding="utf-8")

    heading("核對 RLControl.ino 常數與策略設定")
    bad = False
    for const, key in CHECKS:
        s_val = sketch_const(src, const)
        c_val = cfg.get(key, 32 if key == "motor_microsteps" else None)
        same = s_val is not None and c_val is not None and abs(float(s_val) - float(c_val)) < 1e-6
        (ok if same else fail)(f"{const:<22} sketch = {s_val}　策略 = {c_val}")
        bad |= not same
    if bad:
        fail("有常數不一致，停止匯出。請找助教，不要自己改 sketch。")
        return 1

    source = label(st).replace("/student.pt", "")
    code, _ = run_policy_script(["export_weights.py", "--student", rel(st),
                                 "--header", "../firmware/RLControl/policy_weights_student.h",
                                 "--source-name", source])
    if code != 0:
        fail("匯出失敗。")
        return code
    ok(f"已匯出 {HEADER.relative_to(REPO).as_posix()}（來源：{source}）")
    info("下一步：用 Arduino IDE 開 firmware/RLControl/RLControl.ino，按「上傳」。")
    return 0


if __name__ == "__main__":
    finish(main())

"""09_distill：把微調好的教師蒸餾成 16 個神經元的學生（作者 distill_student.sh 的 Python 版）。

1/4 行為克隆（distill.py）→ 2/4 DAgger（dagger_distill.py，Nano 獨立執行的傳輸條件）
→ 3/4 學生的模擬分數與敏感度關卡 → 4/4 教師自己的模擬分數（拿來比較）。

教師用微調段的哪個模型、行為克隆 epoch 數、DAgger 輪數與每輪步數都會在畫面上問，
直接按 Enter 是作者的預設值。不是預設值的設定會寫進資料夾名稱，不同設定的結果不會互相覆蓋。
"""
from __future__ import annotations

import re

from _common import (ask, ask_number, ask_yes, banner, color, fail, finetune_runs, finish, heading, info, label,
                     ok, rel, run_policy_script, choose)
from _checks import balanced, print_sensitivity, sensitivity

HIDDEN = 16
TRANSPORT = "device"
BC_EPOCHS = 800
ROUNDS = 5
STEPS_PER_ROUND = 40_000


def main() -> int:
    banner("09 蒸餾學生（約 3 分鐘，不需要機台）")
    fts = finetune_runs()
    if not fts:
        fail("找不到完成的微調段。請先做 Step 2：執行 07_finetune。")
        return 1
    run = choose("選要蒸餾的微調段（預設是最後一段）：", fts, [d.name for d in fts])
    seed = ask("SEED", "0")
    if not seed.isdigit():
        fail("SEED 要是整數。")
        return 1
    models = [run / "best_model.zip"] + ([run / "last.zip"] if (run / "last.zip").exists() else [])
    teacher = choose(f"教師用 {run.name} 的哪個模型：", models, [m.name for m in models], default=0)
    epochs, rounds, steps = BC_EPOCHS, ROUNDS, STEPS_PER_ROUND
    if ask_yes("要改進階設定（行為克隆 epoch 數、DAgger 輪數、每輪步數）嗎？", default=False):
        epochs = ask_number("行為克隆 epoch 數", BC_EPOCHS, 1)
        rounds = ask_number("DAgger 輪數（0 = 只做行為克隆）", ROUNDS, 0)
        steps = ask_number("DAgger 每輪步數", STEPS_PER_ROUND, 1000)
    # 資料夾名稱：預設設定維持作者的名稱，改過的設定加在後面。
    bc_sfx = ("" if teacher.name == "best_model.zip" else "_last") + ("" if seed == "0" else f"_s{seed}") \
        + ("" if epochs == BC_EPOCHS else f"_e{epochs}")
    dg_sfx = bc_sfx + ("" if (rounds, steps) == (ROUNDS, STEPS_PER_ROUND) else f"_r{rounds}x{steps}")
    bc_dir = run / f"distill_h{HIDDEN}_aug{bc_sfx}"
    dagger_dir = run / f"distill_h{HIDDEN}_dagger_dev{dg_sfx}"
    student = dagger_dir / "student.pt"
    buf = run / "replay_buffer.pkl"

    heading(f"1/4 行為克隆 → {label(bc_dir)}")
    if (bc_dir / "student.pt").exists():
        info("已經做過，跳過。")
    else:
        args = ["distill.py", "--teacher", rel(teacher), "--out-dir", rel(bc_dir), "--hidden", str(HIDDEN),
                "--epochs", str(epochs), "--seed", seed]
        if buf.exists():
            args += ["--buffer", rel(buf)]
        code, _ = run_policy_script(args)
        if code != 0:
            fail("行為克隆失敗。")
            return code

    heading(f"2/4 DAgger（{TRANSPORT} 傳輸）→ {label(dagger_dir)}")
    code, out = run_policy_script(["dagger_distill.py", "--teacher", rel(teacher), "--bc-dir", rel(bc_dir),
                                   "--out-dir", rel(dagger_dir), "--transport", TRANSPORT,
                                   "--rounds", str(rounds), "--steps-per-round", str(steps),
                                   "--seed", seed], capture=True)
    if code != 0 or not student.exists():
        fail("DAgger 失敗。")
        return code or 1
    m = re.findall(r"best gate ([0-9.]+)", out) or re.findall(r"round 0 \(BC student\): gate ([0-9.]+)", out)
    dagger_gate = float(m[-1]) if m else None

    heading("3/4 學生：敏感度關卡")
    s_on, s_off = sensitivity(student, transport=TRANSPORT)

    heading("4/4 教師自己的模擬分數（拿來跟學生比）")
    _, t_out = run_policy_script(["analyze_sim.py", rel(teacher)], capture=True)
    t_gate = balanced(t_out)

    heading("結果（由你判斷，對照網站 Step 3 的檢查點）")
    f = lambda x: "—" if x is None else f"{x:.3f}"  # noqa: E731
    info(f"  DAgger gate（學生）：{f(dagger_gate)}")
    info(f"  教師自己的模擬分數：{f(t_gate)}")
    info(color("  參考：學生接近教師就好（我們建議相差 0.05 以內）。模擬會低估微調過的策略，不要跟絕對數字比。", "dim"))
    print_sensitivity(s_on, s_off)
    ok(f"學生：runs/{label(student)}")
    info("下一步：執行 10_export_weights 匯出權重。不滿意就再執行 09_distill，SEED 輸入 1。")
    return 0


if __name__ == "__main__":
    finish(main())

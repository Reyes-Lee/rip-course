"""09_distill：把微調好的模型（蒸餾前）蒸餾成 16 個神經元的小網路（蒸餾後的模型）（作者 distill_student.sh 的 Python 版）。

1/4 行為克隆（distill.py）→ 2/4 DAgger（dagger_distill.py，Nano 獨立執行的傳輸條件）
→ 3/4 蒸餾後模型的模擬分數與敏感度關卡 → 4/4 蒸餾前模型自己的模擬分數（拿來比較）。

蒸餾前的模型用微調段的哪個檔、行為克隆 epoch 數、DAgger 輪數與每輪步數、DAgger 的延遲條件都會在畫面上問，
直接按 Enter 是作者的預設值。不是預設值的設定會寫進資料夾名稱，不同設定的結果不會互相覆蓋。
"""
from __future__ import annotations

import re

from _common import (ask, ask_number, ask_yes, banner, color, fail, finetune_runs, finish, heading, info, label,
                     ok, rel, run_policy_script, choose, warn)
from _checks import balanced, print_sensitivity, sensitivity

HIDDEN = 16
TRANSPORT = "device"
BC_EPOCHS = 800
ROUNDS = 5
STEPS_PER_ROUND = 40_000
# DAgger 的延遲條件（ms）。預設：練習時用模擬的預設範圍 2–10 ms，評分用 Nano 實測的 15.6 ms。
ROLL_STALE_MS = (2.0, 10.0)
GATE_STALE_MS = (15.6,)


def ask_latency():
    """DAgger 的延遲條件。回傳 (練習範圍, 評分用的值們)，都是毫秒。"""
    lo = ask_number("DAgger 練習時的觀測延遲下限（ms；每回合在上下限之間抽一個）", ROLL_STALE_MS[0], 0.0, 100.0)
    hi = ask_number("DAgger 練習時的觀測延遲上限（ms）", max(ROLL_STALE_MS[1], lo), lo, 100.0)
    while True:
        ans = ask("選蒸餾後模型的評分延遲（ms，可以給好幾個、用逗號隔開，分數取平均）",
                  ",".join(f"{x:g}" for x in GATE_STALE_MS))
        try:
            gates = tuple(float(x) for x in ans.replace("，", ",").split(",") if x.strip())
        except ValueError:
            gates = ()
        if gates and all(0.0 <= g <= 100.0 for g in gates):
            return (lo, hi), gates
        warn("請輸入 0 到 100 之間的數字，用逗號隔開。")


def main() -> int:
    banner("09 蒸餾（約 3 分鐘，不需要機台）")
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
    teacher = choose(f"蒸餾前的模型用 {run.name} 的哪個檔：", models, [m.name for m in models], default=0)
    epochs, rounds, steps = BC_EPOCHS, ROUNDS, STEPS_PER_ROUND
    if ask_yes("要改進階設定（行為克隆 epoch 數、DAgger 輪數、每輪步數）嗎？", default=False):
        epochs = ask_number("行為克隆 epoch 數", BC_EPOCHS, 1)
        rounds = ask_number("DAgger 輪數（0 = 只做行為克隆）", ROUNDS, 0)
        steps = ask_number("DAgger 每輪步數", STEPS_PER_ROUND, 1000)
    roll, gates = ROLL_STALE_MS, GATE_STALE_MS
    if ask_yes("要改 DAgger 的延遲條件嗎？（專題任務用；不改就直接按 Enter）", default=False):
        roll, gates = ask_latency()
    # 資料夾名稱：預設設定維持作者的名稱，改過的設定加在後面。
    bc_sfx = ("" if teacher.name == "best_model.zip" else "_last") + ("" if seed == "0" else f"_s{seed}") \
        + ("" if epochs == BC_EPOCHS else f"_e{epochs}")
    dg_sfx = bc_sfx + ("" if (rounds, steps) == (ROUNDS, STEPS_PER_ROUND) else f"_r{rounds}x{steps}") \
        + ("" if roll == ROLL_STALE_MS else f"_lat{roll[0]:g}-{roll[1]:g}") \
        + ("" if gates == GATE_STALE_MS else "_g" + "-".join(f"{g:g}" for g in gates))
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
    info(f"DAgger 練習時的觀測延遲 {roll[0]:g}–{roll[1]:g} ms；評分用 "
         + "、".join(f"{g:g}" for g in gates) + " ms" + ("（平均）" if len(gates) > 1 else ""))
    lat_args = []
    if roll != ROLL_STALE_MS:
        lat_args += ["--dr-obs-staleness-min", f"{roll[0] / 1000:g}", "--dr-obs-staleness-max", f"{roll[1] / 1000:g}"]
    if gates != GATE_STALE_MS:
        lat_args += ["--gate-obs-staleness", *(f"{g / 1000:g}" for g in gates)]
    code, out = run_policy_script(["dagger_distill.py", "--teacher", rel(teacher), "--bc-dir", rel(bc_dir),
                                   "--out-dir", rel(dagger_dir), "--transport", TRANSPORT,
                                   "--rounds", str(rounds), "--steps-per-round", str(steps),
                                   "--seed", seed, *lat_args], capture=True)
    if code != 0 or not student.exists():
        fail("DAgger 失敗。")
        return code or 1
    m = re.findall(r"best gate ([0-9.]+)", out) or re.findall(r"round 0 \(BC student\): gate ([0-9.]+)", out)
    dagger_gate = float(m[-1]) if m else None
    # dagger_distill.py 只在某一輪的 gate 超過目前最好的才換掉存下來的模型（印 "new best"）。
    # 一次都沒換，存下來的就是第 0 輪只用行為克隆（BC）的模型。
    kept_bc = rounds > 0 and "new best" not in out

    heading("3/4 蒸餾後的模型：敏感度關卡")
    s_on, s_off = sensitivity(student, transport=TRANSPORT)

    heading("4/4 蒸餾前模型自己的模擬分數（拿來跟蒸餾後的比）")
    _, t_out = run_policy_script(["analyze_sim.py", rel(teacher)], capture=True)
    t_gate = balanced(t_out)

    heading("結果（由你判斷，對照網站 Step 3 的檢查點）")
    f = lambda x: "—" if x is None else f"{x:.3f}"  # noqa: E731
    info(f"  DAgger gate（蒸餾後）：{f(dagger_gate)}")
    info(f"  蒸餾前模型自己的模擬分數：{f(t_gate)}")
    info(color("  參考：蒸餾後接近蒸餾前就好，由你判斷。模擬會低估微調過的策略，不要跟絕對數字比。", "dim"))
    info(color("  兩個分數都是在 Nano 獨立執行的時序（device）下算的；兩個都是 0 或接近 0，不算「接近」，見下面的提醒。", "dim"))
    print_sensitivity(s_on, s_off)
    if kept_bc:
        print()
        warn("DAgger 每一輪的分數都沒有超過第 0 輪，所以存下來的模型就是第 0 輪只用行為克隆（BC）的那支。")
        warn("作者實測只用 BC 的模型在閉迴路只有約 0.12：燒進 Nano 很可能一直繞圈、接不住。")
        if t_gate is not None and t_gate < 0.05:
            warn(f"蒸餾前的模型自己在這個時序下的模擬分數也只有 {t_gate:.3f}：DAgger 沒有能模仿的好動作，換 SEED 通常不會變好。")
        info("  可以先照網站 Step 3 的選做步驟，用 08_test_policy 接線測這支蒸餾後的模型，再決定換哪一段微調當蒸餾前的模型，")
        info("  或回到 Step 2 再加一段微調。分析方式見網站 Step 3「看檢查點」。")
    ok(f"蒸餾後的模型：runs/{label(student)}")
    info("下一步：執行 10_export_weights 匯出權重。不滿意就再執行 09_distill，SEED 輸入 1。")
    return 0


if __name__ == "__main__":
    finish(main())

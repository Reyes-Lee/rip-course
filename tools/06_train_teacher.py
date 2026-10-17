"""06_train_teacher：三階段模擬訓練（作者 curriculum_train.sh 的 Python 版）＋檢查點。

設定照作者的標準配方：velocity 模式、50 Hz、±3.5 rad/s、150 rad/s²、K=4、gSDE、
靜止獎勵 5、韌體量測模型、4-tap 動作平滑、鏡像增強、觀測延遲 DR 到 20 ms。
"""
from __future__ import annotations

import re

from _common import (RUNS, ask, ask_yes, banner, color, fail, finish, heading, info, is_done, mark_done,
                     need_sysid, ok, run_policy_script, warn)
from _checks import print_sensitivity, sensitivity, symmetry

STEPS_PER_STAGE = 100_000
CONTROL_FREQ = 50
MAX_ACCEL = 150
STAGES = {
    2: dict(lag=("0.000", "0.020"), delay=("0", "1")),
    3: dict(lag=("0.000", "0.015"), delay=("1", "1")),
}


def common_args(params: str) -> list[str]:
    return [
        "--action-mode", "velocity",
        "--max-velocity-rad-s", "3.5",
        "--use-sde",
        "--obs-history-len", "4",
        "--firmware-obs-model",
        "--mirror-augment",
        "--action-smooth-window", "4",
        "--dr-obs-staleness-max", "0.020",
        "--params-path", params,
        "--reward-stillness-bonus-weight", "5",
    ]


def print_header(params: str, name: str, seed: str) -> None:
    heading("設定 header（作者的標準配方）")
    lines = [
        "action mode: velocity",
        "exploration: gSDE",
        "firmware measurement model: ON",
        "mirror augmentation: ON (every transition stored with its mirror)",
        "obs staleness DR: up to 0.02 s (measured rig value 0.0156)",
        "reward_stillness_bonus_weight: 5",
        f"rig sysid: {params}",
        f"control rate: {CONTROL_FREQ} Hz, max accel: {MAX_ACCEL} rad/s²",
        "stage 2 delay: [0, 1] ticks + lag tau [0, 20] ms",
        "stage 3 delay: [1, 1] ticks + lag tau [0, 15] ms",
        "action_smooth_window: 4 (firmware boxcar on the action)",
        f"run: {name}_stage1..3　seed: {seed}　device: cpu",
    ]
    for ln in lines:
        print("  " + ln)


def main() -> int:
    banner("06 模擬訓練教師（約 25 分鐘，不需要機台）")
    params = need_sysid()
    info("筆電接上電源、不要闔上蓋子，睡眠會讓訓練中斷。")
    name = ask("run 名稱", "v1")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        fail("run 名稱只能用英文、數字、底線、連字號。")
        return 1
    seed = ask("SEED", "0")
    if not seed.isdigit():
        fail("SEED 要是整數。")
        return 1

    done = [s for s in (1, 2, 3) if is_done(RUNS / f"{name}_stage{s}")]
    start = 1
    if done:
        last = max(done)
        if last == 3:
            warn(f"{name} 三個階段都已完成。要重新訓練請換一個 run 名稱（例如 v2）。")
            if ask_yes("要直接重跑檢查點嗎？", default=True):
                return run_checks(name, params)
            return 0
        if ask_yes(f"已完成第 {last} 階段，從第 {last + 1} 階段接續？", default=True):
            start = last + 1

    print_header(params, name, seed)
    for stage in (1, 2, 3):
        if stage < start:
            continue
        run_dir = RUNS / f"{name}_stage{stage}"
        heading(f"Stage {stage}" + (" (no DR)" if stage == 1 else
                f" (delay {STAGES[stage]['delay']} ticks, lag tau {STAGES[stage]['lag']} s)"))
        args = ["train_sac.py", "--total-steps", str(STEPS_PER_STAGE), "--device", "cpu",
                "--control-freq", str(CONTROL_FREQ), "--max-accel-rad-s2", str(MAX_ACCEL),
                *common_args(params), "--run-name", run_dir.name, "--seed", seed]
        if stage > 1:
            cfg = STAGES[stage]
            args += ["--domain-randomization",
                     "--dr-action-lag-tau-min", cfg["lag"][0], "--dr-action-lag-tau-max", cfg["lag"][1],
                     "--dr-delay-min", cfg["delay"][0], "--dr-delay-max", cfg["delay"][1],
                     "--resume", f"runs/{name}_stage{stage - 1}/best_model.zip"]
        code, _ = run_policy_script(args)
        if code != 0:
            fail(f"Stage {stage} 沒有完成（代碼 {code}）。再執行 06_train_teacher、輸入同一個名稱就能接續。")
            return code
        mark_done(run_dir)
        ok(f"Stage {stage} 完成：runs/{run_dir.name}/best_model.zip")

    return run_checks(name, params)


def run_checks(name: str, params: str) -> int:
    teacher = RUNS / f"{name}_stage3" / "best_model.zip"
    heading(f"檢查點：{teacher.parent.name}")
    symmetry(teacher)
    on, off = sensitivity(teacher, params=params)
    print_sensitivity(on, off)
    info("")
    info(color("下一步：對照網站 Step 1 的檢查點自己判斷。", "yellow"))
    info(color("  覺得可以 → 進 Step 2，執行 07_finetune。", "yellow"))
    info(color("  想換一支 → 再執行 06_train_teacher，run 名稱輸入 v2、SEED 輸入 1。", "yellow"))
    info("想看策略怎麼動：執行 12_view_policy。")
    return 0


if __name__ == "__main__":
    finish(main())

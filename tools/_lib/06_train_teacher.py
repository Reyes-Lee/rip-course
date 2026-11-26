"""06_train_teacher：三階段模擬訓練（作者 curriculum_train.sh 的 Python 版）＋檢查點。

設定照作者的標準配方：velocity 模式、50 Hz、±3.5 rad/s、150 rad/s²、K=4、gSDE、
靜止獎勵 5、韌體量測模型、4-tap 動作平滑、鏡像增強、觀測延遲 DR 到 20 ms。
每階段步數、reward 權重、延遲設定會在畫面上問，直接按 Enter 是作者的設定。
reward 權重存進每個階段的 config.json，07_finetune 會自動沿用；
延遲設定存進每個階段的 06_settings.json，從第 2、3 階段接續時沿用。
"""
from __future__ import annotations

import json
import re

from _common import (RUNS, ask, ask_number, ask_yes, banner, check_reward, choose, color, fail, finish, heading,
                     info, is_done, label, mark_done, need_sysid, ok, rel, run_policy_script, save_reward_copy,
                     teachers, warn)
from _checks import print_sensitivity, sensitivity, symmetry
from _progress import StageProgress

STEPS_PER_STAGE = 100_000
CONTROL_FREQ = 50
MAX_ACCEL = 150
# reward 權重：(train_sac.py 的選項, config.json 的欄位, 畫面上的名稱, 作者的值)
REWARD_WEIGHTS = [
    ("--reward-alive-offset", "reward_alive_offset", "存活偏移", 15.0),
    ("--reward-upright-alive-weight", "reward_upright_alive_weight", "接住的直立獎勵", 5.0),
    ("--reward-stillness-bonus-weight", "reward_stillness_bonus_weight", "靜止獎勵", 5.0),
    ("--reward-motor-pos-weight", "reward_motor_pos_weight", "手臂角度² 懲罰", 0.5),
    ("--reward-motor-vel-weight", "reward_motor_vel_weight", "手臂角速度² 懲罰", 0.005),
    ("--reward-motor-jerk-weight", "reward_motor_jerk_weight", "手臂角速度變化² 懲罰（實機微調不支援）", 0.0),
    ("--reward-action-rate-weight", "reward_action_rate_weight", "動作變化² 懲罰", 0.0),
]
# 延遲設定（專題任務用）：(06_settings.json 的欄位, 畫面上的問題, 作者的值, 下限, 上限)
LATENCY = [
    ("obs_staleness_min_ms", "觀測延遲下限（ms；模擬每回合在上下限之間抽一個，第 2、3 階段）", 2.0, 0.0, 100.0),
    ("obs_staleness_max_ms", "觀測延遲上限（ms）", 20.0, 0.0, 100.0),
    ("stage3_delay_ticks", "第 3 階段的動作延遲（幾拍，1 拍 = 20 ms）", 1, 0, 3),
    ("stage3_lag_min_ms", "第 3 階段的動作 lag 時間常數下限（ms）", 0.0, 0.0, 60.0),
    ("stage3_lag_max_ms", "第 3 階段的動作 lag 時間常數上限（ms）", 15.0, 0.0, 60.0),
]
SETTINGS = "06_settings.json"

STAGES = {
    2: dict(lag=("0.000", "0.020"), delay=("0", "1")),
    3: dict(lag=("0.000", "0.015"), delay=("1", "1")),
}


def common_args(params: str, lat: dict) -> list[str]:
    return [
        "--action-mode", "velocity",
        "--max-velocity-rad-s", "3.5",
        "--use-sde",
        "--obs-history-len", "4",
        "--firmware-obs-model",
        "--mirror-augment",
        "--action-smooth-window", "4",
        "--dr-obs-staleness-min", f"{lat['obs_staleness_min_ms'] / 1000:g}",
        "--dr-obs-staleness-max", f"{lat['obs_staleness_max_ms'] / 1000:g}",
        "--params-path", params,
    ]


def ask_reward(prev) -> dict:
    """reward 權重。接續時（prev = 前一階段的資料夾）沿用它 config.json 的值，前後才一致。"""
    if prev is not None:
        try:
            cfg = json.loads((prev / "config.json").read_text(encoding="utf-8"))
            w = {key: float(cfg[key]) for _, key, _, _ in REWARD_WEIGHTS if cfg.get(key) is not None}
        except (OSError, ValueError):
            w = {}
        if len(w) == len(REWARD_WEIGHTS):
            info(f"reward 權重沿用 {label(prev)} 的設定。")
            return w
        warn(f"讀不到 {label(prev)} 的 reward 權重，改用作者的值。")
        return {key: d for _, key, _, d in REWARD_WEIGHTS}
    w = {key: d for _, key, _, d in REWARD_WEIGHTS}
    if ask_yes("要改 reward 權重嗎？（每一項的意思見網站 Step 1 的 Reward 一節）", default=False):
        for _, key, lab, d in REWARD_WEIGHTS:
            w[key] = ask_number(lab, d, 0.0)
    return w


def ask_latency(prev) -> dict:
    """延遲設定。同一個 run 名稱接續時（prev = 前一階段的資料夾）沿用它 06_settings.json 的值。"""
    default = {key: d for key, _, d, _, _ in LATENCY}
    if prev is not None:
        try:
            saved = json.loads((prev / SETTINGS).read_text(encoding="utf-8"))
            lat = {key: type(d)(saved[key]) for key, _, d, _, _ in LATENCY}
            info(f"延遲設定沿用 {label(prev)} 的設定。")
            return lat
        except (OSError, ValueError, KeyError):
            info(f"{label(prev)} 沒有存延遲設定，用作者的值。")
            return default
    if not ask_yes("要改延遲設定嗎？（專題任務用；不改就直接按 Enter）", default=False):
        return default
    while True:
        lat = {key: ask_number(q, d, lo, hi) for key, q, d, lo, hi in LATENCY}
        if lat["obs_staleness_min_ms"] <= lat["obs_staleness_max_ms"] and \
                lat["stage3_lag_min_ms"] <= lat["stage3_lag_max_ms"]:
            return lat
        warn("下限不能大於上限，請重新輸入。")


def reward_args(w: dict) -> list[str]:
    return [a for flag, key, _, _ in REWARD_WEIGHTS for a in (flag, str(w[key]))]


def print_header(params: str, name: str, seed: str, steps: int, w: dict, lat: dict) -> None:
    heading("設定 header")
    lines = [
        "action mode: velocity",
        "exploration: gSDE",
        "firmware measurement model: ON",
        "mirror augmentation: ON (every transition stored with its mirror)",
        f"obs staleness DR: {lat['obs_staleness_min_ms']:g}–{lat['obs_staleness_max_ms']:g} ms (measured rig value 15.6 ms)",
        *[f"{key}: {w[key]:g}" for _, key, _, _ in REWARD_WEIGHTS],
        f"rig sysid: {params}",
        f"control rate: {CONTROL_FREQ} Hz, max accel: {MAX_ACCEL} rad/s²",
        "stage 2 delay: [0, 1] ticks + lag tau [0, 20] ms",
        f"stage 3 delay: [{lat['stage3_delay_ticks']}, {lat['stage3_delay_ticks']}] ticks + "
        f"lag tau [{lat['stage3_lag_min_ms']:g}, {lat['stage3_lag_max_ms']:g}] ms",
        "action_smooth_window: 4 (firmware boxcar on the action)",
        f"steps per stage: {steps:,}",
        f"run: {name}_stage1..3　seed: {seed}　device: cpu",
    ]
    for ln in lines:
        print("  " + ln)


def main() -> int:
    banner("06 模擬訓練（約 25–60 分鐘，看電腦速度；不需要機台）")
    params = need_sysid()
    info("筆電接上電源、不要闔上蓋子，睡眠會讓訓練中斷。")
    info("訓練中畫面會一直捲動英文統計表，那張表不用看；每 30 秒會印一行中文進度與預估剩餘時間。")
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

    # 專題任務：從一支已經練好的模型接著練第 3 階段（例如換一組延遲設定），不用三個階段從頭來。
    base = None
    ts = [t for t in teachers() if t.parent.name != f"{name}_stage3"]
    if start == 1 and ts and ask_yes("要從現有的模型接著練、只跑第 3 階段嗎？（專題任務用；不用就直接按 Enter）",
                                     default=False):
        base = choose("從哪一支模型接著練：", ts, [label(t) for t in ts])
        start = 3

    steps = ask_number("每階段步數", STEPS_PER_STAGE, 1000)
    prev = base.parent if base else (RUNS / f"{name}_stage{start - 1}" if start > 1 else None)
    w = ask_reward(prev)
    lat = ask_latency(None if base else prev)
    stages = dict(STAGES)
    stages[3] = dict(lag=(f"{lat['stage3_lag_min_ms'] / 1000:g}", f"{lat['stage3_lag_max_ms'] / 1000:g}"),
                     delay=(str(lat['stage3_delay_ticks']),) * 2)
    print_header(params, name, seed, steps, w, lat)
    if not check_reward(w):
        return 1
    for stage in (1, 2, 3):
        if stage < start:
            continue
        run_dir = RUNS / f"{name}_stage{stage}"
        heading(f"Stage {stage}" + (" (no DR)" if stage == 1 else
                f" (delay {stages[stage]['delay']} ticks, lag tau {stages[stage]['lag']} s)"))
        args = ["train_sac.py", "--total-steps", str(steps), "--device", "cpu",
                "--control-freq", str(CONTROL_FREQ), "--max-accel-rad-s2", str(MAX_ACCEL),
                *common_args(params, lat), *reward_args(w), "--run-name", run_dir.name, "--seed", seed]
        if stage > 1:
            cfg = stages[stage]
            args += ["--domain-randomization",
                     "--dr-action-lag-tau-min", cfg["lag"][0], "--dr-action-lag-tau-max", cfg["lag"][1],
                     "--dr-delay-min", cfg["delay"][0], "--dr-delay-max", cfg["delay"][1],
                     "--resume", rel(base) if base else f"runs/{name}_stage{stage - 1}/best_model.zip"]
        with StageProgress(run_dir, stage, 3, steps):
            code, _ = run_policy_script(args)
        if code != 0:
            fail(f"Stage {stage} 沒有完成（代碼 {code}）。再執行 06_train_teacher、輸入同一個名稱就能接續。")
            return code
        mark_done(run_dir)
        save_reward_copy(run_dir)
        (run_dir / SETTINGS).write_text(json.dumps({"steps": steps, **lat}, indent=2, ensure_ascii=False) + "\n",
                                        encoding="utf-8")
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

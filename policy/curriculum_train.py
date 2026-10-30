"""三階段課程訓練：作者 curriculum_train.sh 的 Python 版（Windows 沒有 bash）。

用法（在 policy/ 裡）：
    uv run python curriculum_train.py v1 --params-path sysid_params.json
    uv run python curriculum_train.py v1 --params-path sysid_params.json --start-stage 2   # 中斷後接續
    uv run python curriculum_train.py v2 --params-path sysid_params.json --seed 1

產出 runs/<名稱>_stage1..3/，最後的教師是 runs/<名稱>_stage3/best_model.zip。

預設值就是作者驗證過的標準配方（velocity 模式、50 Hz、±3.5 rad/s、150 rad/s²、K=4、gSDE、
靜止獎勵 5、韌體量測模型、4-tap 動作平滑、鏡像增強、觀測延遲 DR 到 20 ms），跟 bash 版一樣。
跟 bash 版的差別：
- --params-path 必填。bash 版沒給時會默默用作者機台的 sysid_params_rig1.json。
- --device 預設 cpu（bash 版預設 cuda）。作者也是在 MacBook 上用 CPU 訓練。
- 只開放課程會用到的旋鈕；要改其他設定（reward、DR 範圍）就直接呼叫 train_sac.py。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 第 2、3 階段的傳輸延遲 DR：(整數 tick 延遲下限, 上限, 一階延遲 τ 下限 s, 上限 s)
STAGE_DR = {
    2: ("0", "1", "0.000", "0.020"),
    3: ("1", "1", "0.000", "0.015"),
}


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)  # 跟子程序的輸出照順序出現
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", help="run 名稱前綴，例如 v1")
    p.add_argument("--params-path", required=True, help="你的機台的 sysid 檔，例如 sysid_params.json")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--start-stage", type=int, choices=(1, 2, 3), default=1,
                   help="從第幾階段開始；2 或 3 會接續前一階段的 best_model.zip")
    p.add_argument("--steps-per-stage", type=int, default=100_000)
    p.add_argument("--device", default="cpu")
    p.add_argument("--eval-freq", type=int, default=10_000, help="每幾步評估一次並更新 best_model.zip")
    p.add_argument("--control-freq", type=int, default=50)
    p.add_argument("--max-accel-rad-s2", type=float, default=150)
    p.add_argument("--net-arch", default=None, help="例如 128,128（作者用來快速探索，正式訓練用預設）")
    p.add_argument("--no-mirror-augment", action="store_true", help="關掉鏡像增強（只做對照實驗用）")
    a = p.parse_args()

    if not (HERE / a.params_path).exists() and not Path(a.params_path).exists():
        sys.exit(f"找不到 {a.params_path}。先做 Step 0（sysid_wizard.py）產生它。")

    common = [
        "--action-mode", "velocity",
        "--max-velocity-rad-s", "3.5",
        "--use-sde",
        "--obs-history-len", "4",
        "--firmware-obs-model",
        "--no-mirror-augment" if a.no_mirror_augment else "--mirror-augment",
        "--action-smooth-window", "4",
        "--dr-obs-staleness-max", "0.020",
        "--params-path", a.params_path,
        "--reward-stillness-bonus-weight", "5",
    ]
    if a.net_arch:
        common += ["--net-arch", a.net_arch]

    print("Curriculum config:")
    print("  action mode: velocity")
    print("  exploration: gSDE")
    print("  firmware measurement model: ON")
    print("  mirror augmentation: " + ("OFF (asymmetric baseline)" if a.no_mirror_augment
                                       else "ON (every transition stored with its mirror)"))
    print("  obs staleness DR: up to 0.02 s (measured rig value 0.0156)")
    print("  reward_stillness_bonus_weight: 5")
    print(f"  rig sysid: {a.params_path}")
    print(f"  control rate: {a.control_freq} Hz, max accel: {a.max_accel_rad_s2:g} rad/s²")
    for s, (d0, d1, t0, t1) in STAGE_DR.items():
        print(f"  stage {s} delay: [{d0}, {d1}] ticks + lag tau [{float(t0) * 1000:.0f}, {float(t1) * 1000:.0f}] ms")
    print("  action_smooth_window: 4 (firmware boxcar on the action)")
    if a.net_arch:
        print(f"  net_arch: {a.net_arch} (actor/critic hidden sizes)")
    print()

    for stage in (1, 2, 3):
        run = f"{a.name}_stage{stage}"
        if stage < a.start_stage:
            print(f"=== Stage {stage} skipped (--start-stage {a.start_stage}) ===")
            continue
        args = [sys.executable, "-u", "train_sac.py",
                "--total-steps", str(a.steps_per_stage), "--device", a.device, "--eval-freq", str(a.eval_freq),
                "--control-freq", str(a.control_freq), "--max-accel-rad-s2", str(a.max_accel_rad_s2)]
        if stage == 1:
            print("=== Stage 1 (no DR) ===")
        else:
            d0, d1, t0, t1 = STAGE_DR[stage]
            print(f"=== Stage {stage} (delay [{d0}, {d1}] ticks, lag tau [{t0}, {t1}] s) ===")
            args += ["--domain-randomization",
                     "--dr-action-lag-tau-min", t0, "--dr-action-lag-tau-max", t1,
                     "--dr-delay-min", d0, "--dr-delay-max", d1,
                     "--resume", f"runs/{a.name}_stage{stage - 1}/best_model.zip"]
        args += [*common, "--run-name", run, "--seed", str(a.seed)]
        code = subprocess.call(args, cwd=HERE)
        if code != 0:
            print(f"\nStage {stage} 沒有完成（代碼 {code}）。接續：加上 --start-stage {stage} 再跑一次。")
            return code

    print(f"=== Curriculum complete. Final policy: runs/{a.name}_stage3/best_model.zip ===")
    print(f"Deploy/fine-tune at the same control rate AND action mode: "
          f"--control-freq {a.control_freq} --action-mode velocity")
    return 0


if __name__ == "__main__":
    sys.exit(main())

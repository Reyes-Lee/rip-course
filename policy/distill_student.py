"""把微調好的教師蒸餾成要燒進 Nano 的小學生：作者 distill_student.sh 的 Python 版（Windows 沒有 bash）。

用法（在 policy/ 裡）：
    uv run python distill_student.py ft3              # 教師是 runs/ft3/best_model.zip
    uv run python distill_student.py ft3 --seed 1     # 換 SEED 再蒸餾一次

1/3 行為克隆（distill.py）→ 2/3 DAgger（dagger_distill.py，部署時的傳輸條件）→ 3/3 學生在模擬裡的分數。
run 裡有 replay_buffer.pkl（實機微調過）就自動帶 --buffer。資料夾名稱跟作者一樣：
runs/<run>/distill_h16_aug/、runs/<run>/distill_h16_dagger_dev/student.pt。
跟 bash 版的差別：SEED 不是 0 時資料夾名稱加 _s<SEED>，不會蓋掉之前的學生。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(args: list[str]) -> None:
    code = subprocess.call([sys.executable, *args], cwd=HERE)
    if code != 0:
        sys.exit(code)


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)  # 跟子程序的輸出照順序出現
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run", help="runs/ 底下的資料夾名稱，例如 ft3")
    p.add_argument("--hidden", type=int, default=16, help="學生寬度（16 是能塞進 Nano 50 Hz 的大小）")
    p.add_argument("--transport", choices=("device", "tethered"), default="device",
                   help="學生要在哪裡跑：device＝燒進 Nano 獨立執行，tethered＝接著筆電")
    p.add_argument("--bc-epochs", type=int, default=800)
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--steps-per-round", type=int, default=40_000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--params-path", default=None, help="不給就沿用教師 config.json 裡的 sysid 檔（通常就是你要的）")
    p.add_argument("--force", action="store_true", help="行為克隆已經做過也重做")
    a = p.parse_args()

    run_dir = Path("runs") / a.run
    teacher = run_dir / "best_model.zip"
    if not (HERE / teacher).exists():
        sys.exit(f"no teacher at {teacher}\n(pass the run directory name, e.g. 'ft3' or 'v1_stage3')")

    sfx = "" if a.seed == 0 else f"_s{a.seed}"
    t_sfx = "dev" if a.transport == "device" else "teth"
    bc_dir = run_dir / f"distill_h{a.hidden}_aug{sfx}"
    dagger_dir = run_dir / f"distill_h{a.hidden}_dagger_{t_sfx}{sfx}"
    student = dagger_dir / "student.pt"
    params = ["--params-path", a.params_path] if a.params_path else []

    buf = run_dir / "replay_buffer.pkl"
    buffer_args = ["--buffer", str(buf)] if (HERE / buf).exists() else []
    print(f"Distilling {a.run} (h{a.hidden}, {a.transport} transport, "
          + ("real-rig buffer + sim rollouts)" if buffer_args else "sim rollouts only — no replay buffer)"))

    print(f"=== 1/3 behaviour cloning -> {bc_dir} ===")
    if (HERE / bc_dir / "student.pt").exists() and not a.force:
        print("  exists, skipping (--force to redo)")
    else:
        run(["distill.py", "--teacher", str(teacher), *buffer_args, "--out-dir", str(bc_dir),
             "--hidden", str(a.hidden), "--epochs", str(a.bc_epochs), "--seed", str(a.seed), *params,
             *(["--force"] if a.force else [])])

    print(f"=== 2/3 DAgger at the {a.transport} transport -> {dagger_dir} ===")
    run(["dagger_distill.py", "--teacher", str(teacher), "--bc-dir", str(bc_dir), "--out-dir", str(dagger_dir),
         "--transport", a.transport, "--rounds", str(a.rounds), "--steps-per-round", str(a.steps_per_round),
         "--seed", str(a.seed), *params])

    print("=== 3/3 scoring the student in sim ===")
    run(["analyze_sim.py", str(student), "--transport", a.transport, *params])

    print(f"""
Judge the gate against the TEACHER's, not an absolute bar — sim under-predicts
smooth students on the rig, most of all when the teacher was rig-fine-tuned:
    python analyze_sim.py {teacher.as_posix()}

To flash this student:
    python export_weights.py --student {student.as_posix()} \\
        --header ../firmware/RLControl/policy_weights_student.h \\
        --source-name {a.run}/{dagger_dir.name}
    then upload firmware/RLControl with the Arduino IDE.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())

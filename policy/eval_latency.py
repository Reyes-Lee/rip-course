"""Score a policy in the on-device sim with extra observation latency injected.

The off-rig counterpart to the latency ladder on the rig (RLControl's 'L'
serial command, or a `latency_profile.h`): the policy reads a sample that is
`extra` ms older than usual, so the
sample->command age becomes the measured 15.6 ms plus `extra`. With
`--jitter-ms J` every control tick draws its own extra delay uniformly from
[extra, extra + J] in whole ms, like the firmware (which then reads the
sample whose timestamp is closest to that age).
`--profile` instead reads a `latency_profile.h` and replays its stages
against time since engage, exactly as the firmware does.

Each episode starts hanging and runs --episode-s seconds; the score is the
longest continuous balanced stretch (|θ| ≤ 15° AND |θ̇| ≤ 4 rad/s), the
same gate `analyze_onboard.py` uses on the rig.

Usage:
    python eval_latency.py runs/ft2/distill_h16_dagger_dev/student.pt --ladder
    python eval_latency.py runs/ft2/distill_h16_dagger_dev/student.pt --levels 0 20 35 40 45
    python eval_latency.py runs/<run>_stage3/best_model.zip
    python eval_latency.py runs/<run>/distill_h16_dagger_dev/student.pt \\
        --extra-ms 0 10 20 30 40 --jitter-ms 0 20
    python eval_latency.py <policy> --profile ../firmware/RLControl/latency_profile.h
"""

from __future__ import annotations

import argparse
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

import balance_metrics
from analyze_sim import _load_policy
from dagger_distill import TRANSPORTS, make_env
from run_config import find_run_config

DEVICE_STALENESS_S = TRANSPORTS["device"][1][2]  # measured on the rig: 15.6 ms
MAX_EXTRA_MS = 70                                # RLControl.ino cap (MAX_INJECT_MS)


def read_profile(path: Path) -> list[tuple[float, float, float]]:
    """The {start_s, extra_ms, jitter_ms} stages of a latency_profile.h."""
    text = re.sub(r"//.*", "", path.read_text(encoding="utf-8"))
    m = re.search(r"#define\s+LATENCY_STAGES\s+(\{.*\})\s*$", text, re.M)
    if m is None:
        raise SystemExit(f"{path}: no LATENCY_STAGES line")
    stages = [tuple(float(v) for v in t) for t in
              re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}", m.group(1))]
    if not stages or stages[0][0] != 0:
        raise SystemExit(f"{path}: the first stage must start at 0 s")
    return stages


def run_condition(policy: str, stages: list[tuple[float, float, float]],
                  episodes: int, episode_s: float, seed: int) -> list[float]:
    cfg = find_run_config(Path(policy))
    predict, _ = _load_policy(Path(policy), "cpu")
    hz = float(cfg.get("control_freq_hz", 50.0))
    # Firmware units: whole ms, extra + jitter capped like the sketch.
    steps = [(start, int(extra), int(jit)) for start, extra, jit in stages]
    worst = min(MAX_EXTRA_MS, max(d + j for _, d, j in steps))
    env = make_env(cfg, dr=False, transport="device", episode_length_s=episode_s,
                   obs_staleness_s=DEVICE_STALENESS_S + worst / 1000)
    rng = np.random.default_rng(seed)
    streaks = []
    for ep in range(episodes):
        obs, _ = env.reset(seed=seed + ep)
        motor, phi, action = [], [], []
        done = False
        tick = 0
        while not done:
            now_s = tick / hz
            _, d, j = [s for s in steps if s[0] <= now_s][-1]
            d = min(MAX_EXTRA_MS, d + (int(rng.integers(0, j + 1)) if j else 0))
            env._obs_staleness_s = DEVICE_STALENESS_S + d / 1000
            tick += 1
            a, _ = predict(obs, deterministic=True)
            obs, _, term, trunc, info = env.step(a)
            motor.append(float(info["motor_pos"]))
            phi.append(float(info["phi"]))
            action.append(float(np.asarray(a).reshape(-1)[0]))
            done = term or trunc
        m = balance_metrics.score(phi=phi, motor_pos=motor, action=action, hz=hz)
        streaks.append(m.longest_streak_s)
    return streaks


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("policy", help="SAC .zip or distilled .pt")
    p.add_argument("--extra-ms", type=float, nargs="+", default=None,
                   help="extra latency grid in ms (default 0 10 20 30 40; not with --ladder/--levels)")
    p.add_argument("--jitter-ms", type=float, nargs="+", default=[0])
    p.add_argument("--profile", type=Path, default=None,
                   help="replay a latency_profile.h instead of the grid")
    p.add_argument("--episodes", type=int, default=10)
    p.add_argument("--episode-s", type=float, default=None,
                   help="episode length (default 30 s, also with --ladder)")
    p.add_argument("--ladder", action="store_true",
                   help="延遲階梯的 14 階（+0、+10、+15、+20、+25、+30、+35、+37、+40、+42、+45、+47、+50、+55 ms，"
                        "和 latency_ladder.py 同一組）全部測，印出每一階的通過率；"
                        "每回合 30 秒，最長連續平衡 >= --hold-s 算這一回合通過")
    p.add_argument("--levels", type=int, nargs="+", default=None,
                   help="照專題規則選的 5 階（例如 0 20 35 40 45），由低到高判，"
                        "某一階沒過就停，印出「依你選的 5 階最高到哪一階」（隱含 --ladder）")
    p.add_argument("--hold-s", type=float, default=10.0)
    p.add_argument("--pass-frac", type=float, default=0.8,
                   help="--ladder：一階要有多少比例的回合通過才算這一階通過")
    p.add_argument("--seed", type=int, default=100)
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args(argv if argv is not None else sys.argv[1:])
    if args.episode_s is None:
        args.episode_s = 30.0
    if args.levels is not None:
        args.ladder = True
    if args.ladder:
        if args.extra_ms is not None:
            raise SystemExit("--ladder／--levels 會自己決定要測的延遲，不能再給 --extra-ms")
        if args.profile is not None:
            raise SystemExit("--ladder／--levels 不能和 --profile 一起用")
        from latency_ladder import DEFAULT_LEVELS, check_levels
        picked = check_levels(args.levels, 5) if args.levels is not None else None
        args.extra_ms = [float(x) for x in (picked or DEFAULT_LEVELS)]
    elif args.extra_ms is None:
        args.extra_ms = [0.0, 10.0, 20.0, 30.0, 40.0]
    over = [(e, j) for j in args.jitter_ms for e in args.extra_ms if e + j > MAX_EXTRA_MS]
    if over and args.profile is None:
        raise SystemExit(f"額外延遲 + 抖動不能超過 {MAX_EXTRA_MS} ms（RLControl 的上限）："
                         + "、".join(f"+{e:g} 加抖動 {j:g}" for e, j in over))

    if args.profile is not None:
        stages = read_profile(args.profile)
        conds = [(args.profile.name, stages)]
    else:
        conds = [(f"{e:5.0f}ms {j:5.0f}ms", [(0.0, e, j)])
                 for j in args.jitter_ms for e in args.extra_ms]
    # Split episodes across workers so a single profile still runs in parallel.
    chunks = [(i, min(args.episodes, i + max(1, args.episodes // args.workers)))
              for i in range(0, args.episodes, max(1, args.episodes // args.workers))]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = [[pool.submit(run_condition, args.policy, st, b - a,
                             args.episode_s, args.seed + a) for a, b in chunks]
                for _, st in conds]
        results = [sum((f.result() for f in fl), []) for fl in futs]

    print(f"\n{args.policy}")
    print(f"  {args.episodes} episodes x {args.episode_s:.0f} s from hanging; "
          f"base sample->command age {DEVICE_STALENESS_S * 1000:.1f} ms")
    if args.profile is not None:
        print(f"  profile stages (start s, extra ms, jitter ms): {conds[0][1]}")
    print(f"  {'extra   jitter' if args.profile is None else 'condition':<16}"
          f" longest streak (s): median  min   "
          f"episodes >= {args.hold_s:g} s")
    for (name, _), s in zip(conds, results):
        s = np.asarray(s)
        good = int(np.sum(s >= args.hold_s))
        print(f"  {name:<16} {np.median(s):26.1f} {s.min():5.1f}   {good}/{len(s)}")
    if args.ladder:
        for j in args.jitter_ms:
            best, stopped, ok = None, False, []
            for (name, st), s in zip(conds, results):
                if st[0][2] != j:
                    continue
                if np.mean(np.asarray(s) >= args.hold_s) >= args.pass_frac:
                    ok.append(int(st[0][1]))
                    if not stopped:
                        best = int(st[0][1])
                else:
                    stopped = True
            head = (f"  模擬的延遲階梯（抖動 {j:g} ms，一階要 {args.pass_frac:.0%} 回合連續平衡 >= {args.hold_s:g} s）：")
            if args.levels is not None:
                print(head + f"依你選的 5 階（由低到高，某一階沒過就停），最高 "
                      f"{'沒有（第一階就沒過）' if best is None else f'+{best} ms'}")
            else:
                print(head + f"通過的階：{'、'.join(f'+{x}' for x in ok) or '沒有'}。"
                      "demo 要選 5 階、由低到高測，可以用 --levels 模擬你們選的組合")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

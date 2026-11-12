"""07_finetune：實機非同步微調（作者的 finetune_async.py），每執行一次跑一段。

第一次（ft1）：從你選的教師開始。之後（ft2、ft3…）：從最新一段接續，帶上它的 replay buffer。
回合數、每回合秒數、接續用哪個模型等設定都會在畫面上問，直接按 Enter 是作者的預設值。
reward 權重預設沿用起點模型 config.json 裡的值（也就是 Step 1 訓練時用的），也可以在這裡改。
每一段實際用的設定存在 runs/ftN/07_settings.json。
"""
from __future__ import annotations

import csv
import json
import time

from _common import (RUNS, ask_number, ask_yes, banner, check_reward, choose, fail, finish, finetune_runs, get_port,
                     heading, info, label, mark_done, need_sysid, ok, rel, run_policy_script, same_reward_as,
                     save_reward_copy, teachers, wait_enter, warn)
from _direction import require_or_exit

# 作者的預設值（直接按 Enter 就用這些）
FIRST_EPISODES = 50
NEXT_EPISODES = 30
EPISODE_LENGTH_S = 6.0
LEARNING_RATE = 1e-4
GRADIENT_STEPS = 4
EVAL_EVERY = 5
# 實機微調能改的 reward 權重：(finetune_async.py 的選項, config.json 的欄位, 畫面上的名稱)
REWARD_WEIGHTS = [
    ("--reward-alive-offset", "reward_alive_offset", "存活偏移"),
    ("--reward-upright-alive-weight", "reward_upright_alive_weight", "接住的直立獎勵"),
    ("--reward-stillness-bonus-weight", "reward_stillness_bonus_weight", "靜止獎勵"),
    ("--reward-motor-pos-weight", "reward_motor_pos_weight", "手臂角度² 懲罰"),
    ("--reward-motor-vel-weight", "reward_motor_vel_weight", "手臂角速度² 懲罰"),
    ("--reward-action-rate-weight", "reward_action_rate_weight", "動作變化² 懲罰"),
]


def best_eval_episode(run_dir, eval_every: int):
    """從 timing.csv 找出 best_model 來自哪一個評估回合（回合編號從 1 起算）與它的分數。"""
    try:
        rows = list(csv.DictReader((run_dir / "timing.csv").open(encoding="utf-8")))
    except OSError:
        return None
    evals = [(int(r["episode"]) + 1, float(r["cumulative_reward"])) for r in rows
             if (int(r["episode"]) + 1) % eval_every == 0]
    # finetune_async 只在分數「超過」之前最高分時才存，所以同分取最早的那個。
    return max(evals, key=lambda e: (e[1], -e[0])) if evals else None


def main() -> int:
    banner("07 實機微調", "firmware/LowLevelServer", needs_rig=True)
    params = need_sysid()
    done = finetune_runs()
    n_next = (int(done[-1].name[2:]) + 1) if done else 1
    run_dir = RUNS / f"ft{n_next}"

    if run_dir.exists():
        # 上次這一段沒跑完（Ctrl+C 或當掉）：改名保留，這一段重跑。
        keep = run_dir.with_name(f"{run_dir.name}_incomplete_{time.strftime('%Y%m%d_%H%M%S')}")
        run_dir.rename(keep)
        warn(f"上次的 {run_dir.name} 沒有跑完，已改名為 {keep.name} 保留，這一段重跑。")

    if not done:
        ts = teachers()
        if not ts:
            fail("找不到完成的教師。請先做 Step 1：執行 06_train_teacher。")
            return 1
        start = choose("選要微調的教師（Step 1 檢查點你判斷最好的那一支）：", ts, [label(t) for t in ts])
        buffer = None
        n_default = FIRST_EPISODES
    else:
        prev = done[-1]
        starts = [prev / "best_model.zip"] + ([prev / "last.zip"] if (prev / "last.zip").exists() else [])
        start = choose(f"從 {prev.name} 的哪個模型接續：", starts,
                       ["best_model.zip（評估回合分數最高的那個時間點）",
                        "last.zip（這一段最後一回合結束時）"][:len(starts)], default=0)
        buffer = prev / "replay_buffer.pkl"
        n_default = NEXT_EPISODES

    heading("這一段的設定（直接按 Enter 用 [ ] 裡的預設值）")
    episodes = ask_number("回合數", n_default, 1)
    length = ask_number("每回合秒數", EPISODE_LENGTH_S, 2.0, 60.0)
    lr, grad_steps, eval_every = LEARNING_RATE, GRADIENT_STEPS, EVAL_EVERY
    if ask_yes("要改進階設定（學習率、每次更新的梯度步數、評估間隔）嗎？", default=False):
        lr = ask_number("學習率", LEARNING_RATE, 1e-6, 1e-2)
        grad_steps = ask_number("每次更新的梯度步數", GRADIENT_STEPS, 1, 32)
        eval_every = ask_number("每幾回合做一次評估回合", EVAL_EVERY, 1, episodes)

    try:
        cfg = json.loads((start.parent / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    if not cfg:
        warn(f"找不到 {label(start.parent)}/config.json，下面的 reward 權重是 finetune_async 的預設值。")
    defaults = {"reward_motor_pos_weight": 0.5, "reward_motor_vel_weight": 0.005}  # finetune_async 沒有 config 時的值
    reward = {key: float(cfg.get(key) if cfg.get(key) is not None else defaults.get(key, 0.0))
              for _, key, _ in REWARD_WEIGHTS}
    info(f"reward 權重（沿用 {label(start.parent / 'config.json')}）：" +
         "、".join(f"{lab} {reward[key]:g}" for _, key, lab in REWARD_WEIGHTS))
    if cfg.get("reward_motor_jerk_weight"):
        warn(f"起點模型訓練時用了手臂角速度變化² 懲罰 {cfg['reward_motor_jerk_weight']:g}，實機微調不支援這一項，會當成 0。")
    reward_changed = ask_yes("要改這一段的 reward 權重嗎？", default=False)
    if reward_changed:
        for _, key, lab in REWARD_WEIGHTS:
            reward[key] = ask_number(lab, reward[key], 0.0)

    args = ["finetune_async.py", "--policy", rel(start), "--episodes", str(episodes),
            "--episode-length-s", str(length), "--learning-rate", str(lr),
            "--gradient-steps", str(grad_steps), "--eval-every", str(eval_every)]
    if reward_changed:
        # 跟起點模型 config.json 不同時，finetune_async 預設會停下來，要加這個選項才會照新的權重跑。
        args += [a for flag, key, _ in REWARD_WEIGHTS for a in (flag, str(reward[key]))]
        args += ["--ignore-config-mismatch"]
    if buffer:
        args += ["--resume-buffer", rel(buffer)]
        heading(f"接續段 {run_dir.name}：從 {label(start)} 接續（帶上 {prev.name} 的 replay buffer），{episodes} 回合")
    else:
        heading(f"第一段 ft1：從 {label(start)} 開始，{episodes} 回合")

    same = same_reward_as(start.parent)
    if same is None:
        info(f"{label(start.parent)} 沒有存 reward_used.py，無法比對 policy/reward.py 有沒有改過。")
    elif not same:
        warn(f"policy/reward.py 跟 {label(start.parent)}/reward_used.py（起點模型訓練時的版本）不同，這一段會用現在的 reward.py。")
    if not check_reward({**cfg, **reward}):
        return 1

    port = get_port()
    lo, hi = episodes * (length + 5) / 60, episodes * (length + 15) / 60
    info(f"每回合 {length:g} 秒；回合之間馬達斷電，最多等 15 秒讓擺錘停下來。這一段約 {lo:.0f}–{hi:.0f} 分鐘。")
    info("前幾個回合要聽馬達：嘶嘶或磨擦聲代表失步，立刻按 Ctrl + C 停止。")
    wait_enter("擺錘靜止垂下、手臂周圍淨空後按 Enter")
    # 每一段開始前都確認方向沒變（AS5600 的 DIR 腳沒接時方向可能改變），最多浪費一段。
    require_or_exit(port, quick_check=True)
    code, out = run_policy_script([*args, "--port", port, "--run-name", run_dir.name, "--params-path", params],
                                  capture=True)
    if code != 0 or not (run_dir / "best_model.zip").exists() or not (run_dir / "replay_buffer.pkl").exists():
        fail(f"{run_dir.name} 沒有完成（代碼 {code}）。處理好問題後再執行 07_finetune，會重跑這一段。")
        return code or 1
    mark_done(run_dir)
    save_reward_copy(run_dir)
    settings = {"start_model": rel(start), "resume_buffer": rel(buffer) if buffer else None,
                "episodes": episodes, "episode_length_s": length, "learning_rate": lr,
                "gradient_steps": grad_steps, "eval_every": eval_every, "reward_changed": reward_changed,
                **reward}
    (run_dir / "07_settings.json").write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8")
    ok(f"已存：runs/{run_dir.name}/best_model.zip")
    best = best_eval_episode(run_dir, eval_every)
    if best:
        info(f"best_model.zip 是第 {best[0]} 回合（評估回合）結束時的模型，評估分數 {best[1]:.0f}；"
             f"last.zip 是第 {episodes} 回合結束時的模型。")
    # 每 10 回合的 replay buffer 快照每份約 80 MB，下一段只用最後的 replay_buffer.pkl。
    snaps = sorted(run_dir.glob("replay_buffer_ep*.pkl"))
    if snaps:
        freed = sum(p.stat().st_size for p in snaps) / 1e6
        for p in snaps:
            p.unlink()
        info(f"已刪除 {len(snaps)} 份中途的 replay buffer 快照（約 {freed:.0f} MB），保留最後的 replay_buffer.pkl。")
    info("每回合那一行的 violations= 持續大於 0 時，先關掉其他程式（尤其是同步、備份或訓練）。")
    info("這一段存了 best_model.zip、last.zip，以及每 10 回合的 checkpoint_epNNN.zip，08_test_policy 都可以選來測。")
    info("下一步：執行 08_test_policy 測試，再決定要不要加一段。")
    return 0


if __name__ == "__main__":
    finish(main())

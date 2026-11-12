"""開跑前檢查 policy/reward.py 的 compute_reward()：會不會出錯、回傳的是不是有限的數字。

只檢查「工具會不會因為 reward 壞掉」，不判斷 reward 好不好。由 06、07 在 policy/ 目錄執行：
    python _reward_check.py '<權重 JSON>'
權重 JSON 的欄位是 config.json 的 reward_* 名稱。通過回傳 0，失敗印出出錯的輸入並回傳 1。

檢查的輸入涵蓋模擬與實機會遇到的情況，包括實機特有的：算 reward 時「上一步的動作」等於
這一步的動作、「上一步的手臂角速度」一律是 0，以及感測器的速度尖峰。
"""
from __future__ import annotations

import itertools
import json
import math
import os
import random
import sys
import traceback

sys.path.insert(0, os.getcwd())  # policy/，才 import 得到 reward.py

# config.json 欄位 → RewardWeights 欄位
FIELDS = {
    "reward_alive_offset": "k_alive_offset",
    "reward_upright_alive_weight": "k_upright_alive",
    "reward_stillness_bonus_weight": "k_stillness_bonus",
    "reward_motor_pos_weight": "k_motor_pos",
    "reward_motor_vel_weight": "k_motor_vel",
    "reward_motor_jerk_weight": "k_motor_jerk",
    "reward_action_rate_weight": "k_action_rate",
}

THETA = [0.0, 0.1, -0.1, 0.2618, 1.0, -1.0, math.pi / 2, math.pi, -math.pi]
PEN_VEL = [0.0, 2.0, -2.0, 10.0, -10.0, 40.0, -40.0]
MOTOR_POS = [0.0, 1.0, -1.0, math.radians(125), -math.radians(125), math.radians(135), -math.radians(135)]
MOTOR_VEL = [0.0, 3.5, -3.5, 15.0, -15.0]
ACTION = [0.0, 1.0, -1.0]
PREV_MOTOR_VEL = [0.0, 15.0, -15.0]


def cases():
    for th, pv, mp, mv, a, pa, pmv in itertools.product(
            THETA, PEN_VEL, MOTOR_POS, MOTOR_VEL, ACTION, ACTION, PREV_MOTOR_VEL):
        yield dict(theta=th, pen_vel=pv, motor_pos=mp, motor_vel=mv, action=a, prev_action=pa, prev_motor_vel=pmv)
    rng = random.Random(0)
    for _ in range(20000):
        a = rng.uniform(-1, 1)
        yield dict(theta=rng.uniform(-math.pi, math.pi), pen_vel=rng.uniform(-60, 60),
                   motor_pos=rng.uniform(-2.4, 2.4), motor_vel=rng.uniform(-20, 20),
                   action=a, prev_action=a if rng.random() < 0.5 else rng.uniform(-1, 1),
                   prev_motor_vel=0.0 if rng.random() < 0.5 else rng.uniform(-20, 20))


def main() -> int:
    try:
        from reward import RewardWeights, compute_reward
    except Exception:
        traceback.print_exc()
        print("REWARD_CHECK_FAIL policy/reward.py 載入失敗（上面是錯誤訊息）")
        return 1
    given = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    try:
        weights = RewardWeights(**{FIELDS[k]: float(v) for k, v in given.items() if k in FIELDS})
    except Exception:
        traceback.print_exc()
        print("REWARD_CHECK_FAIL 用工具的權重建立 RewardWeights 失敗（上面是錯誤訊息）")
        return 1
    n = 0
    for c in cases():
        n += 1
        try:
            r = compute_reward(**c, weights=weights)
            ok = math.isfinite(float(r))
        except Exception:
            traceback.print_exc()
            print(f"REWARD_CHECK_FAIL compute_reward 出錯，輸入：{c}")
            return 1
        if not ok:
            print(f"REWARD_CHECK_FAIL compute_reward 回傳 {r!r}（不是有限的數字），輸入：{c}")
            return 1
    print(f"REWARD_CHECK_OK compute_reward 用 {n} 組輸入都回傳有限的數字")
    return 0


if __name__ == "__main__":
    sys.exit(main())

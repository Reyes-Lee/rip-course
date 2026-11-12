"""08_test_policy：接線（LowLevelServer）測一支策略，印誠實指標（作者的 run_policy.py）。

清單裡除了每一段的 best_model.zip，也有 last.zip 與每 10 回合的 checkpoint_epNNN.zip。
測試秒數會在畫面上問，直接按 Enter 是作者的 30 秒。
"""
from __future__ import annotations

from _common import (RECORDINGS, ask_number, banner, choose, fail, finetune_runs, finish, get_port, info, label,
                     rel, run_policy_script, students, teachers, wait_enter)
from _direction import require_or_exit

DURATION_S = 30


def finetune_models(run_dir):
    """一段微調存下的所有模型：best_model、每 10 回合的 checkpoint、last。"""
    ckpts = sorted(run_dir.glob("checkpoint_ep*.zip"))
    return [run_dir / "best_model.zip", *ckpts] + ([run_dir / "last.zip"] if (run_dir / "last.zip").exists() else [])


def log_path(pol):
    """recordings/<名稱>.npz；同名的檔案已經存在就加 _2、_3…，不蓋掉之前的測試。"""
    name = label(pol).removesuffix(".zip").removesuffix(".pt").replace("/best_model", "").replace("/", "_")
    log, n = RECORDINGS / f"{name}.npz", 2
    while log.exists():
        log, n = RECORDINGS / f"{name}_{n}.npz", n + 1
    return log


def main() -> int:
    banner("08 接線測試策略", "firmware/LowLevelServer", needs_rig=True)
    # 清單順序：教師 → 微調段（每段的 best、checkpoint、last）→ 學生；預設是最新一段的 best_model。
    fts = finetune_runs()
    items = teachers() + [m for d in fts for m in finetune_models(d)] + students()
    if not items:
        fail("還沒有任何策略。請先做 Step 1 或 Step 2。")
        return 1
    default = items.index(fts[-1] / "best_model.zip") if fts else len(items) - 1
    pol = choose("選要測的策略：", items, [label(p) for p in items], default=default)
    duration = ask_number("測試秒數", DURATION_S, 5, 600)
    RECORDINGS.mkdir(parents=True, exist_ok=True)
    log = log_path(pol)
    port = get_port()
    require_or_exit(port)
    wait_enter(f"擺錘靜止垂下後按 Enter；接下來 {duration:g} 秒不要碰機台")
    code, _ = run_policy_script(["run_policy.py", "--policy", rel(pol), "--port", port,
                                 "--duration-s", str(duration), "--log", rel(log)])
    print()
    info(f"紀錄檔：policy/{rel(log)}")
    info("balanced fraction：|θ| ≤ 15° 且 |θ̇| ≤ 4 rad/s 的時間比例（從開始計時，包含甩上的時間）。")
    info("longest balanced streak：最長連續平衡秒數，最多就是測試秒數減掉甩上花的時間。")
    return code


if __name__ == "__main__":
    finish(main())

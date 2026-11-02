"""06_train_teacher 用：訓練中每 30 秒印一行中文進度。

不改作者的 train_sac.py：直接讀 SB3 寫出的 runs/<名稱>/monitor.monitor.csv
（每一行是一個回合，第 2 欄 l 是回合步數，加總就是目前步數），
預估時間用這台電腦實際的速度算。
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

from _common import color

INTERVAL_S = 30.0
BAR_WIDTH = 20


def _steps(monitor: Path) -> int:
    try:
        lines = monitor.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    total = 0
    for ln in lines[2:]:   # 第 1 行是 #{json}，第 2 行是欄位名稱 r,l,t
        parts = ln.split(",")
        if len(parts) >= 2:
            try:
                total += int(float(parts[1]))
            except ValueError:
                pass
    return total


def _fmt(sec: float) -> str:
    sec = max(0, int(sec))
    return f"{sec // 60}:{sec % 60:02d}"


class StageProgress:
    """with StageProgress(run_dir, stage, n_stages, steps_per_stage): run_policy_script(...)"""

    def __init__(self, run_dir: Path, stage: int, n_stages: int, steps_per_stage: int):
        self.monitor = run_dir / "monitor.monitor.csv"
        self.stage, self.n_stages = stage, n_stages
        self.total = steps_per_stage
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self):
        self.t0 = time.time()
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=1.0)

    def _run(self) -> None:
        while not self._stop.wait(INTERVAL_S):
            n = min(_steps(self.monitor), self.total)
            if n <= 0:
                continue
            frac = n / self.total
            elapsed = time.time() - self.t0
            rate = n / elapsed if elapsed > 0 else 0.0
            left_stage = (self.total - n) / rate if rate > 0 else 0.0
            left_all = left_stage + (self.n_stages - self.stage) * self.total / rate if rate > 0 else 0.0
            overall = ((self.stage - 1) + frac) / self.n_stages
            bar = "█" * int(frac * BAR_WIDTH) + "░" * (BAR_WIDTH - int(frac * BAR_WIDTH))
            print(color(
                f"\n[Stage {self.stage}/{self.n_stages}] {bar} {n:,} / {self.total:,} 步（{frac * 100:.0f}%）"
                f"｜這一階段已 {_fmt(elapsed)}，預估還要 {_fmt(left_stage)}"
                f"｜三階段整體 {overall * 100:.0f}%，預估還要約 {left_all / 60:.0f} 分鐘\n", "cyan"), flush=True)

"""所有工具共用的小工具：路徑、畫面輸出、提問、選檔案、找序列埠、呼叫 policy/ 的腳本。

每個工具都由 `tools/<名稱>.command`（macOS）或 `tools/<名稱>.bat`（Windows）啟動，
兩者只做「切到 repo 根目錄 → uv run --project policy python tools/<名稱>.py」。
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POLICY = REPO / "policy"
RUNS = POLICY / "runs"
RECORDINGS = POLICY / "recordings"
SYSID_JSON = POLICY / "sysid_params.json"   # 你的機台的 sysid 結果（Step 0 產生）
SETTINGS = REPO / "tools" / ".settings.json"
IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# 標記檔：工具在一個階段／一段完整跑完後才寫入，用來判斷要不要接續。
DONE_MARK = ".done"

# Windows 10 以上的終端機要先呼叫一次才會吃 ANSI 色碼。
if IS_WIN:
    os.system("")

_C = {"pink": "95", "yellow": "93", "green": "92", "red": "91", "cyan": "96", "bold": "1", "dim": "2"}


def color(text: str, name: str) -> str:
    return f"\033[{_C[name]}m{text}\033[0m"


def banner(title: str, firmware: str | None = None, *, needs_rig: bool = False) -> None:
    line = "═" * 60
    print(color(line, "pink"))
    print(color(f"  {title}", "bold"))
    if firmware:
        print(color(f"  先用 Arduino IDE 上傳：{firmware}", "yellow"))
        print(color("  並關掉 Arduino IDE 的「序列埠監控」視窗", "yellow"))
    if needs_rig:
        print(color("  需要機台：12 V 接好、Nano 用 USB-C 線接上電腦", "yellow"))
    print(color(line, "pink"))
    print()


def info(msg: str) -> None:
    print(msg)


def ok(msg: str) -> None:
    print(color("✔ ", "green") + msg)


def warn(msg: str) -> None:
    print(color("！ ", "yellow") + msg)


def fail(msg: str) -> None:
    print(color("✘ ", "red") + msg)


def heading(msg: str) -> None:
    print()
    print(color(f"── {msg} ", "cyan") + color("─" * max(4, 50 - len(msg) * 2), "dim"))


def ask(prompt: str, default: str | None = None) -> str:
    """畫面問一個問題。[ ] 裡是預設值，直接按 Enter 就用預設值。"""
    suffix = f" [{default}]" if default not in (None, "") else ""
    try:
        ans = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        ans = ""
    return ans if ans else (default or "")


def ask_yes(prompt: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    try:
        ans = input(f"{prompt} [{d}]: ").strip().lower()
    except EOFError:
        ans = ""
    if not ans:
        return default
    return ans in ("y", "yes", "是", "好")


def wait_enter(prompt: str = "準備好就按 Enter") -> None:
    try:
        input(color(f"→ {prompt}", "yellow"))
    except EOFError:
        pass


def choose(title: str, items: list, labels: list[str] | None = None, default: int | None = None):
    """列出編號清單讓使用者選。直接按 Enter 是預設值（預設是最後一個，也就是最新的）。"""
    if not items:
        return None
    labels = labels or [str(x) for x in items]
    if default is None:
        default = len(items) - 1
    print(title)
    for i, lab in enumerate(labels):
        mark = color(" ← 預設", "dim") if i == default else ""
        print(f"  {i + 1:>2}. {lab}{mark}")
    if len(items) == 1:
        print(color("  （只有一個，直接按 Enter）", "dim"))
    while True:
        ans = ask("輸入編號", str(default + 1))
        if ans.isdigit() and 1 <= int(ans) <= len(items):
            return items[int(ans) - 1]
        warn(f"請輸入 1 到 {len(items)} 的數字")


def finish(code: int = 0) -> None:
    """執行開的視窗結束時會直接關掉，所以最後停一下讓人看結果。"""
    print()
    try:
        input(color("按 Enter 關閉視窗", "dim"))
    except EOFError:
        pass
    sys.exit(code)


# ---------------------------------------------------------------- 設定檔

def load_settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(d: dict) -> None:
    SETTINGS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- 序列埠

CH340_VID = 0x1A86   # Nano 相容板常見的 USB 轉序列晶片
FTDI_VID = 0x0403
ARDUINO_VID = 0x2341


def list_nano_ports():
    from serial.tools import list_ports
    ports = list(list_ports.comports())
    nano = [p for p in ports if p.vid in (CH340_VID, FTDI_VID, ARDUINO_VID)]
    if IS_MAC:
        # macOS 同一個裝置會有 /dev/tty.* 和 /dev/cu.*，要用 cu.*
        nano = [p for p in nano if "/dev/cu." in p.device] or nano
    return nano, ports


def get_port(*, ask_if_many: bool = True) -> str:
    """找 Nano 的序列埠：先用 00_setup 記住的，不在了就重新找。"""
    nano, all_ports = list_nano_ports()
    saved = load_settings().get("port")
    devices = [p.device for p in nano]
    if saved and saved in devices:
        return saved
    if len(nano) == 1:
        return nano[0].device
    if len(nano) > 1 and ask_if_many:
        p = choose("偵測到不只一個 Nano，請選要用的那個：", nano,
                   [f"{p.device}  {p.description}" for p in nano], default=0)
        return p.device
    fail("找不到 Nano 的序列埠。")
    info("  1. 確認 USB-C 線有接好，而且是能傳資料的線（有些線只能充電）")
    info("  2. 關掉 Arduino IDE 的序列埠監控")
    if IS_WIN:
        info("  3. Windows：打開「裝置管理員 → 連接埠」，看不到 CH340 就安裝 CH341SER 驅動")
    if all_ports:
        info("  目前看得到的序列埠：" + "、".join(p.device for p in all_ports))
    finish(1)
    raise SystemExit(1)


# ---------------------------------------------------------------- 呼叫 policy/ 腳本

def mujoco_python() -> str:
    """開 MuJoCo 視窗的 Python：macOS 一定要用 mjpython。"""
    if IS_MAC:
        cand = Path(sys.executable).with_name("mjpython")
        if cand.exists():
            return str(cand)
    return sys.executable


def run_policy_script(args: list[str], *, python: str | None = None, capture: bool = False) -> tuple[int, str]:
    """在 policy/ 目錄執行一支作者的腳本，即時把輸出印到畫面。

    capture=True 時同時回傳完整輸出，讓工具可以從裡面抓數字。
    """
    cmd = [python or sys.executable, "-u", *args]
    print(color("$ " + " ".join(cmd[1:]), "dim"))
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    out: list[str] = []
    proc = subprocess.Popen(cmd, cwd=POLICY, env=env,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.STDOUT if capture else None,
                            text=True, encoding="utf-8", errors="replace", bufsize=1)
    try:
        if capture:
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                out.append(line)
        return proc.wait(), "".join(out)
    except KeyboardInterrupt:
        # Ctrl+C 也會送到子程式；等它自己收尾（例如微調會先存檔、讓馬達斷電）。
        warn("收到 Ctrl + C，等目前的程式收尾…")
        try:
            proc.wait(timeout=60)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            proc.kill()
        return 130, "".join(out)


def rel(p: Path) -> str:
    """policy/ 底下的相對路徑（作者的腳本都在 policy/ 執行）。"""
    try:
        return Path(p).resolve().relative_to(POLICY).as_posix()
    except ValueError:
        return str(p)


def need_sysid() -> str:
    if not SYSID_JSON.exists():
        fail("找不到 policy/sysid_params.json。請先做 Step 0：執行 05_sysid。")
        finish(1)
    return rel(SYSID_JSON)


def mark_done(run_dir: Path) -> None:
    (run_dir / DONE_MARK).write_text(time.strftime("%Y-%m-%d %H:%M:%S") + "\n", encoding="utf-8")


def is_done(run_dir: Path) -> bool:
    return (run_dir / DONE_MARK).exists()


# ---------------------------------------------------------------- 找訓練結果

def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def teachers() -> list[Path]:
    """Step 1 完成的教師（*_stage3/best_model.zip），舊到新。"""
    found = [d / "best_model.zip" for d in RUNS.glob("*_stage3") if is_done(d) and (d / "best_model.zip").exists()]
    return sorted(found, key=_mtime)


def finetune_runs() -> list[Path]:
    """Step 2 完成的微調段（ft1、ft2…），依編號排序。"""
    out = []
    for d in RUNS.glob("ft*"):
        if d.is_dir() and d.name[2:].isdigit() and is_done(d) and (d / "best_model.zip").exists():
            out.append(d)
    return sorted(out, key=lambda d: int(d.name[2:]))


def students() -> list[Path]:
    """Step 3 蒸餾出的學生（student.pt），舊到新。"""
    return sorted(RUNS.glob("*/distill_h*_dagger_*/student.pt"), key=_mtime)


def all_checkpoints() -> list[Path]:
    """所有 best_model.zip，舊到新。"""
    return sorted(RUNS.glob("*/best_model.zip"), key=_mtime)


def label(p: Path) -> str:
    return rel(p).removeprefix("runs/")

"""00_setup：檢查 Python 環境、列出 Nano 序列埠並記住。第一次使用時執行。"""
from __future__ import annotations

import platform
import sys
from pathlib import Path

from _common import (IS_MAC, IS_WIN, REPO, banner, choose, fail, finish, heading, info, list_nano_ports,
                     load_settings, ok, save_settings, warn)


def check_repo_path() -> None:
    """repo 放在雲端同步資料夾或有中文／空格的路徑時提醒（只警告，不中止）。"""
    heading("課程資料夾位置")
    ok(f"{REPO}")
    path = str(REPO)
    synced = "OneDrive" in path or "Mobile Documents" in path
    if IS_MAC:
        # 開了 iCloud「桌面與文件」時，~/Desktop、~/Documents 路徑不變，但會被同步。
        icloud_desktop = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Desktop"
        under = any(REPO.is_relative_to(Path.home() / d) for d in ("Desktop", "Documents"))
        synced = synced or (icloud_desktop.exists() and under)
    if synced:
        warn("這個資料夾會被 iCloud／OneDrive 同步。訓練與微調會寫出很多大檔，背景同步會搶 CPU 和磁碟，")
        warn("可能拖慢 50 Hz 的實機控制。建議照網站「安裝環境」改放到家目錄（macOS）或 C:\\rip-course（Windows）。")
    if IS_WIN and (" " in path or not path.isascii()):
        warn("路徑裡有空格或中文，部分工具可能出錯。建議照網站改放到 C:\\rip-course。")


def main() -> int:
    banner("00 環境設定")
    check_repo_path()

    heading("Python 與套件")
    ok(f"Python {platform.python_version()}（{sys.executable}）")
    bad = False
    for mod in ("numpy", "mujoco", "torch", "stable_baselines3", "gymnasium", "serial", "matplotlib"):
        try:
            m = __import__(mod)
            ok(f"{mod} {getattr(m, '__version__', '')}")
        except Exception as e:  # noqa: BLE001 — 任何載入失敗都要讓學生看到
            fail(f"{mod} 載入失敗：{e}")
            bad = True
    if bad:
        fail("有套件載入失敗。把整個畫面截圖給助教。")
        return 1

    heading("Nano 序列埠")
    nano, all_ports = list_nano_ports()
    settings = load_settings()
    if not nano:
        warn("現在找不到 Nano。之後接上再重新執行 00_setup 也可以；其他工具也會自己找。")
        if all_ports:
            info("  目前看得到的序列埠：" + "、".join(p.device for p in all_ports))
        info("  沒看到就換一條 USB-C 線（有些只能充電，不能傳資料）；Windows 再確認 CH340 驅動。")
    else:
        p = choose("偵測到的 Nano：", nano, [f"{p.device}  {p.description}" for p in nano], default=0)
        settings["port"] = p.device
        save_settings(settings)
        ok(f"已記住序列埠 {p.device}，之後的工具會自動使用。")

    print()
    ok("環境設定完成。")
    return 0


if __name__ == "__main__":
    finish(main())

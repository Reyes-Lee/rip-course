"""00_setup：檢查 Python 環境、列出 Nano 序列埠並記住。第一次使用時執行。"""
from __future__ import annotations

import platform
import sys

from _common import (banner, choose, fail, finish, heading, info, list_nano_ports, load_settings,
                     ok, save_settings, warn)


def main() -> int:
    banner("00 環境設定")

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

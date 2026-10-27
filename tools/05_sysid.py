"""05_sysid：系統識別精靈（作者的 sysid_wizard.py），產生 policy/sysid_params.json。"""
from __future__ import annotations

import json

from _common import (POLICY, SYSID_JSON, banner, choose, fail, finish, get_port, heading, info, ok,
                     rel, run_policy_script, warn)
from _direction import require_or_exit

OMEGA_RANGE = (12.3, 12.6)     # 小振幅自然頻率參考範圍（rad/s）
INERTIA_ERR_MAX = 0.10         # 慣量：量測 vs URDF 預測


def show_checkpoint() -> None:
    if not SYSID_JSON.exists():
        return
    d = json.loads(SYSID_JSON.read_text(encoding="utf-8"))
    pen = d.get("pendulum", {})
    fit = pen.get("fit", {})
    der = pen.get("derived", {})
    heading("檢查點（對照網站 Step 0 的表）")
    w = fit.get("omega_n_small_amp_rad_s")
    ws = fit.get("omega_n_small_amp_rad_s_all_runs", [])
    if w:
        tag = ok if OMEGA_RANGE[0] <= w <= OMEGA_RANGE[1] else warn
        tag(f"小振幅自然頻率 ω_n = {w:.3f} rad/s（週期 {6.2832 / w:.3f} s）；三次："
            + "、".join(f"{x:.3f}" for x in ws) + f"　參考 {OMEGA_RANGE[0]}–{OMEGA_RANGE[1]}")
    im, ip = der.get("inertia_measured_kg_m2"), der.get("inertia_predicted_kg_m2")
    if im and ip:
        err = abs(im - ip) / ip
        (ok if err < INERTIA_ERR_MAX else warn)(
            f"轉動慣量：量測 {im:.3e}、URDF 預測 {ip:.3e}，誤差 {err * 100:.1f}%（參考 < 10%）")
        if err >= INERTIA_ERR_MAX:
            warn("誤差偏大：多半是硬幣位置不對或鬆動，檢查後重新量測。")
    info("另外打開 sysid_runs/ 裡最新資料夾的 freeswing_compare.png 與 motor_sweep.png 對照網站。")


def main() -> int:
    banner("05 系統識別（sysid）", "firmware/LowLevelServer", needs_rig=True)
    mode = choose("要做什麼？", ["new", "refit"],
                  ["新量測（約 15 分鐘，要用機台）", "用已存的錄製重新擬合（不用機台）"], default=0)
    if mode == "refit":
        dirs = sorted(p for p in (POLICY / "sysid_runs").glob("*") if p.is_dir())
        if not dirs:
            fail("還沒有任何錄製。請選「新量測」。")
            return 1
        d = choose("選一次錄製：", dirs, [p.name for p in dirs])
        # 作者的 parser 在最外層也把 --out-json 設成必填，所以子指令前後都要帶。
        out = rel(SYSID_JSON)
        code, _ = run_policy_script(["sysid_wizard.py", "--out-json", out, "fit", "--in-dir", rel(d), "--out-json", out])
    else:
        port = get_port()
        require_or_exit(port)
        info("準備一塊硬紙板或泡棉塊，等一下用來把擺錘墊高。精靈會一步一步提示你。")
        code, _ = run_policy_script(["sysid_wizard.py", "--port", port, "--out-json", rel(SYSID_JSON)])
    if code == 0 and SYSID_JSON.exists():
        ok(f"已寫出 {rel(SYSID_JSON)}")
        show_checkpoint()
    else:
        fail("sysid 沒有完成。照畫面上的錯誤訊息處理，或把畫面截圖給助教。")
    return code


if __name__ == "__main__":
    finish(main())

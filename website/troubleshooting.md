# 疑難排解

遇到問題先照下表由上往下查。先排除硬體與設定問題；reward 與演算法在作者機台上驗證過，不是優先懷疑的對象。不知道從哪裡開始，看[照著做還是失敗時，依序查什麼](theory.md#debug-order)。

| 症狀 | 怎麼處理（照順序） |
| --- | --- |
| 手臂一直往同一個方向飄，最後撞限位 | 先確認桌面是水平、不會晃的，機台四角都著地（[Step 0 開始前](steps/step0-sysid.md#level)）。換了桌子仍然飄就找助教 |
| 接線時會平衡，燒進 Nano 後一直繞圈 | 1. 執行 `11_score_onboard`，第一行頻率不是約 50 Hz 就找助教。2. 確認 4-2 匯出的是 `09_distill` 產生的 `student.pt`（路徑含 `distill_h16_dagger_dev`）。3. 按 RESET 前擺錘要靜止垂下、手臂在正中間 |
| 擺錘會擺但怎麼都甩不上去 | 燒 `LowLevelServer`，執行 `03_check_motor`。FAIL 就找助教檢查 Vref |
| 馬達嘶嘶聲、磨擦聲 | 失步。在工具視窗按 ++ctrl+c++ 停止，燒 `LowLevelServer` 跑 `03_check_motor`，把結果拿給助教。Vref 與韌體加速度由助教調，不要自己轉可變電阻或改 sketch |
| 手臂速度或範圍是預期的一半或兩倍 | 微步接線不對（應為 MS1 接 5V、MS2 接 GND）。拔掉 12 V 後找助教 |
| 編碼器角度亂跳 | 燒 `EncoderCheck`，執行 `02_check_encoder`，照[編碼器測試](prepare/hardware.md#encoder)的 FAIL 處理表調磁鐵 |
| 策略好像「反著推」、完全穩不住，或擺錘只擺到幾十度就甩不上去 | 擺錘角度方向可能跟模擬相反。燒 `LowLevelServer`，執行 `04_check_direction`（見[方向標定](prepare/hardware.md#direction)）。它修正了方向的話，之前的 `runs/ftN` 要丟掉，從教師重新微調；方向本來就對的話找助教 |
| 工具說「還沒做方向標定」或「LowLevelServer 是舊版」 | 照[方向標定](prepare/hardware.md#direction)做一次 `04_check_direction`；說是舊版就先重新上傳 `firmware/LowLevelServer` |
| `07_finetune` 說「方向快速檢查：擺錘方向跟上次標定相反」 | AS5600 的方向變了。執行 `04_check_direction` 重新標定，並告訴助教；這一段之前的微調先保留，讓助教判斷 |
| 工具因 `run_config.check_config` 中止 | 策略與韌體設定不一致。確認 Nano 燒的是工具開頭提醒的那份韌體，重燒後再跑一次；仍然中止就找助教 |
| sysid 自由擺擬合失敗 | 擺得不夠大，或抽出墊塊時有震動。執行 `05_sysid`，選單輸入 `1` 重新量測 |
| 工具說找不到序列埠 | 關掉 Arduino IDE 的序列埠監控；換一條能傳資料的 USB-C 線；Windows 確認 CH340 驅動（[安裝環境](prepare/install.md)） |

## 注意事項 { #notes }

!!! danger "不要自己改程式和韌體常數"

    不要自己改 `firmware/` 裡的常數或 `policy/` 的程式。訓練、微調、部署三處的設定必須一致，工具會自動檢查。

!!! danger "不要轉 TMC2209 的可變電阻"

    TMC2209 設的是 RMS 電流，照抄 DRV8825 的 Vref 會燒馬達。沒有助教同意不要轉可變電阻。

!!! info "比較兩支策略時以實機指標為準"

    模擬分數只當參考。作者的冠軍學生在模擬只有 0.655，實機是 0.996。

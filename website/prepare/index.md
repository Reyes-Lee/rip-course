# 事前準備

開始 Step 0 之前要完成三件事。助教交機前已確認硬體正常，但編碼器磁鐵最容易在搬運或碰撞後跑掉，**每次開工前都先跑一次編碼器測試**。

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **1. 安裝環境**

    ---

    Arduino IDE、Git、uv，下載課程 repo，執行 `00_setup`。

    [:octicons-arrow-right-24: 安裝環境](install.md)

-   :material-wrench:{ .lg .middle } **2. 硬體與上電測試**

    ---

    貼配重硬幣，依序燒 5 個測試韌體，確認編碼器、馬達、serial 都正常，並做一次擺錘方向標定。

    [:octicons-arrow-right-24: 硬體與上電測試](hardware.md)

-   :material-console-line:{ .lg .middle } **3. 工具與指令**

    ---

    事前準備的工具做什麼；Step 0–4 怎麼下指令、檔案放在哪裡。

    [:octicons-arrow-right-24: 工具與指令](tools.md)

</div>

## 開工前檢查清單

- [ ] 機台放在水平、堅固、不會晃的桌面上，四角都著地
- [ ] Nano 用 USB-C 傳輸線接上電腦（要能傳資料的線，只能充電的線電腦會找不到 Nano），再接 12 V；12 V 只接 TMC2209，不接 Nano
- [ ] 插拔或碰過馬達線的話，燒 `LowLevelServer` 跑一次 `03_check_motor`，確認手臂平順
- [ ] Arduino IDE 的序列埠監控視窗已關掉
- [ ] 硬幣沒有鬆動
- [ ] 燒 `EncoderCheck`，跑 `02_check_encoder`，全部 PASS
- [ ] 這台 Nano 做過[方向標定](hardware.md#direction)（`04_check_direction`）。換過 Nano、AS5600 或磁鐵就要重做；沒做過的話 `05`、`07`、`08` 會提醒你

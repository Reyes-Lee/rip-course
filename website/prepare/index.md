# 事前準備

開始 Step 0 之前要完成三件事。助教交機前已確認硬體正常，但編碼器磁鐵最容易在搬運或碰撞後跑掉，**每次開工前都先跑一次編碼器測試**。

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **1. 安裝環境**

    ---

    Arduino IDE、Git、uv，下載課程 repo，執行 `00_setup`。

    [:octicons-arrow-right-24: 安裝環境](install.md)

-   :material-wrench:{ .lg .middle } **2. 硬體與上電測試**

    ---

    貼配重硬幣，依序燒 5 個測試韌體，確認編碼器、馬達、serial 都正常。

    [:octicons-arrow-right-24: 硬體與上電測試](hardware.md)

-   :material-console-line:{ .lg .middle } **3. 認識流程工具**

    ---

    每個工具做什麼、要先燒哪個韌體、在哪一步用。

    [:octicons-arrow-right-24: 工具一覽](tools.md)

</div>

## 開工前檢查清單

- [ ] 機台放在水平、堅固、不會晃的桌面上，四角都著地
- [ ] 12 V 電源接好，Nano 用 USB-C 傳輸線接上電腦（要能傳資料的線，只能充電的線電腦會找不到 Nano）
- [ ] Arduino IDE 的序列埠監控視窗已關掉
- [ ] 硬幣沒有鬆動
- [ ] 燒 `EncoderCheck`，跑 `02_check_encoder`，全部 PASS

# 硬體與上電測試

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 30 分鐘</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
</div>

## 貼上配重硬幣 { #coin }

擺錘大頭（圓盤）那一端要貼一枚新台幣 10 元硬幣當配重，位置對齊作者原本嵌硬幣的地方。作者把英國 2p 硬幣（7.12 g）在列印時封進擺錘裡；我們的擺錘印好時硬幣槽是空的，所以改貼在外側。**10 元硬幣（7.5 g、Ø26.0 × 1.87 mm）只比 2p 重 5%，可以直接用。**

<figure class="rip-figure">
<svg viewBox="0 0 540 340" role="img" aria-label="擺錘正面圖：硬幣貼在擺錘末端的大圓盤上，與圓盤同心，中心距鉸鏈軸心 64 mm，四周各留 3 mm">
  <!-- 擺錘外形取自 3D 模型：鉸鏈圓頭 R9、桿寬 10、末端圓盤 Ø32（圓心距鉸鏈 64 mm）；1 mm = 3.3 px -->
  <!-- 先畫加粗的外框，再蓋上同形狀的填色，只留下外輪廓 -->
  <g style="stroke: var(--md-default-fg-color--light); stroke-width: 3; fill: var(--md-default-fg-color--light)">
    <circle cx="203" cy="50" r="30"/>
    <rect x="186.5" y="50" width="33" height="190"/>
    <circle cx="203" cy="261" r="53"/>
  </g>
  <g style="fill: var(--rip-surface-2)">
    <circle cx="203" cy="50" r="30"/>
    <rect x="186.5" y="50" width="33" height="190"/>
    <circle cx="203" cy="261" r="53"/>
  </g>
  <!-- 鉸鏈軸心 -->
  <circle cx="203" cy="50" r="9" fill="none" class="rip-svg-line" stroke-width="2"/>
  <circle cx="203" cy="50" r="2.5" class="rip-svg-text"/>
  <!-- 硬幣：Ø26 mm，與圓盤同心 -->
  <circle cx="203" cy="261" r="43" class="rip-svg-amber" opacity=".95"/>
  <circle cx="203" cy="261" r="35" fill="none" stroke="#7a4b03" stroke-width="1" opacity=".6"/>
  <text x="203" y="268" text-anchor="middle" font-size="20" font-weight="800" fill="#5a3a02">10</text>
  <!-- 64 mm 標註 -->
  <line x1="120" y1="50" x2="120" y2="261" class="rip-svg-cyan" stroke-width="1.5"/>
  <line x1="112" y1="50" x2="196" y2="50" class="rip-svg-cyan" stroke-width="1" stroke-dasharray="3 3"/>
  <line x1="112" y1="261" x2="196" y2="261" class="rip-svg-cyan" stroke-width="1" stroke-dasharray="3 3"/>
  <polygon points="120,50 115,60 125,60" fill="var(--rip-cyan)"/>
  <polygon points="120,261 115,251 125,251" fill="var(--rip-cyan)"/>
  <text x="104" y="160" text-anchor="end" font-size="15" font-weight="700" class="rip-svg-text">64 mm</text>
  <text x="104" y="178" text-anchor="end" font-size="11" class="rip-svg-muted">鉸鏈軸心 → 硬幣中心</text>
  <!-- 四周 3 mm：硬幣邊到圓盤邊 -->
  <line x1="246" y1="261" x2="256" y2="261" class="rip-svg-cyan" stroke-width="2"/>
  <line x1="256" y1="261" x2="300" y2="282" class="rip-svg-line" stroke-width="1"/>
  <text x="306" y="282" font-size="13" font-weight="700" class="rip-svg-text">四周各留 3 mm</text>
  <text x="306" y="300" font-size="11" class="rip-svg-muted">硬幣邊緣到圓盤邊緣</text>
  <!-- 說明 -->
  <text x="306" y="56" font-size="13" font-weight="700" class="rip-svg-text">鉸鏈端（小圓頭）</text>
  <text x="306" y="74" font-size="11" class="rip-svg-muted">裝在手臂上，不貼硬幣</text>
  <text x="306" y="130" font-size="13" font-weight="700" class="rip-svg-text">貼在外側面</text>
  <text x="306" y="148" font-size="11" class="rip-svg-muted">遠離馬達、沒有凸出軸套的那一面</text>
  <text x="306" y="208" font-size="13" font-weight="700" class="rip-svg-text">大頭圓盤 Ø32 mm</text>
  <text x="306" y="226" font-size="11" class="rip-svg-muted">新台幣 10 元貼在這裡，與圓盤同心</text>
  <text x="306" y="242" font-size="11" class="rip-svg-muted">7.5 g · Ø26.0 × 1.87 mm</text>
</svg>
<figcaption>配重硬幣位置：貼在擺錘大頭（圓盤）那一端</figcaption>
</figure>

!!! tool "操作步驟"

    1. 找到擺錘**大頭（圓盤）那一端**，硬幣就貼在這裡；另一端的小圓頭是裝在手臂上的鉸鏈。
    2. 確認要貼的是**外側面**：遠離馬達、沒有凸出軸套的那一面。
    3. 硬幣放在圓盤正中間，跟圓盤同心：四周到圓盤邊緣都留約 3 mm。這樣硬幣中心就在距鉸鏈軸心 **64 mm** 的地方。
    4. 用薄的強力雙面膠或少量瞬間膠，貼平、貼正。
    5. 用手搖搖看，硬幣不能動。

!!! warning "一定要貼牢"

    擺錘失控旋轉時轉速可能到 35 rad/s，硬幣受到約 8 g 的離心加速度。貼好後就不要再移動；如果必須重貼，要照 [Step 0「檢查點沒過時」](../steps/step0-sysid.md#checkpoint-fail)第 1 點重新量測，之後 Step 1–4 都要重做。

位置誤差 ±1 mm，自然頻率變約 ±0.5%；±3 mm 變約 ±1.6%。這是整台機器裡唯一需要你認真量的尺寸。

## 上電測試 { #power-on }

每個韌體都用 Arduino IDE 開啟 `firmware/<名稱>/<名稱>.ino`，再按「上傳」。照順序做，前一個沒過不要往下。

| 順序 | 燒錄 | 然後 | 通過條件 |
| --- | --- | --- | --- |
| 1 | `TestHeartbeat` | Arduino IDE 選單「工具 → 序列埠監控」，右上角鮑率選 115200；看完關掉這個視窗 | LED 雙閃、持續印心跳計數 |
| 2 | `EncoderCheck` | 執行 `02_check_encoder` | 全部 PASS（見下一節） |
| 3 | `TestMotor` | 看、聽 | 手臂 ±90° 來回，平順的嗡嗡聲，沒有嘶嘶或磨擦聲 |
| 4 | `LowLevelServer` | 執行 `03_check_motor`（見[失步測試](#motor)） | 每級跑完手臂末端還對齊膠帶記號，聲音平順 |
| 5 | `LowLevelServer`（不用重燒） | 執行 `04_check_direction`（見[方向標定](#direction)） | 印出 `PASS`，方向存進 Nano |
| 6 | `TestSerial` | 執行 `01_check_serial` | 來回約 2.5 ms |

!!! warning "工具和 Arduino IDE 不能同時用序列埠"

    執行任何工具前，先關掉 Arduino IDE 的序列埠監控視窗。同一個埠一次只能有一個程式使用。

## 失步測試 { #motor }

步進馬達是開迴路的：失步時韌體的步數計數不會知道，所以要靠「手臂回到原點時還對不對得齊記號」來判斷。工具用的是策略本身的指令路徑（`LowLevelServer` 的加速度指令），最高 150 rad/s²，和策略實際會用到的一樣。

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `LowLevelServer`，關掉序列埠監控。
    2. 用手把手臂轉到正中間（正前方）。
    3. 在底座上貼一小段膠帶，對齊手臂末端，當作原點記號。
    4. 擺錘自然垂下，手臂周圍不要有東西擋到。
    5. 執行 `tools/03_check_motor`，按 Enter 開始。
    6. 加速度依序是 30、60、90、120、150 rad/s²。每一級手臂會在 ±45° 之間來回 4 次，再回到 0°。
    7. 每一級跑完，畫面問兩個問題：
        - `手臂末端還對齊膠帶嗎？`：偏移超過約 1 mm（大約 1°）就輸入 `n`。
        - `剛才的聲音是平順的嗡嗡聲嗎？`：有嘶嘶或磨擦聲就輸入 `n`。
    8. 任何一級回答 `n`，工具會停止測試。

!!! checkpoint "通過條件"

    五級都對齊、聲音都正常，最後印出 `PASS`。FAIL 就把結果拿給助教，檢查 Vref 與韌體加速度設定；不要自己轉可變電阻。

## 編碼器測試：磁場強度與對心 { #encoder }

AS5600 讀的是磁場方向，整套系統對擺錘角度的所有認知都來自它。磁鐵太遠會訊號弱、角度抖；太近會飽和；**沒對準中心時，讀數會隨轉角產生週期性失真**，sysid 與策略都會吃到錯的角度，而且很難從平衡表現看出來。

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `EncoderCheck`，關掉序列埠監控。
    2. 執行 `tools/02_check_encoder`。
    3. **靜態磁場（10 秒）**：畫面提示時，讓擺錘靜止垂下，不要碰。
    4. **用手慢轉**：畫面提示時按 Enter，用手捏著擺錘慢慢轉順時針 3 圈（每圈約 2–3 秒），轉完再按一次 Enter；接著逆時針 3 圈，同樣做一次。
    5. **自由擺（選做）**：畫面問 `要做自由擺測試嗎？[y/N]`，要做就輸入 `y`，把擺錘拉到約 60°，按 Enter 的同時放手，會錄 20 秒。
    6. 每一項印出 PASS/FAIL，並在 `policy/encoder_runs/<時間>/` 存一張圖（角度對時間、磁場強度對角度）。

| 項目 | 檢查什麼 | 通過條件 |
| --- | --- | --- |
| 狀態位元 | MD 偵測到磁鐵、ML 太弱、MH 太強 | MD=1、ML=MH=0 |
| AGC | 自動增益 | 不在 0 或 255 的極端，而且穩定 |
| 無跳點 | 相鄰取樣差 | 不超過 500 LSB（作者韌體用同一門檻擋錯誤讀值） |
| 圈數 | 累積角度 | 約 ±1080°，繞過 0°/360° 時正確接續；兩個方向一正一負（**哪個方向是正不重要**，方向由[方向標定](#direction)處理） |
| 覆蓋 | 一圈分成 64 格（每格 5.6°） | 每一格都有讀到，沒有缺口 |
| 對心 | 一圈內 magnitude 的起伏比例 | ≤ 15%；磁鐵偏心時磁場強度會隨角度變化，起伏越大偏得越多 |
| 自由擺（選做） | 小振幅（< 20°）週期與左右對稱 | 週期 0.49–0.53 s；左右擺幅差 ≤ 10% |

門檻目前是暫定值，助教用正常機台校準後會更新工具。FAIL 時：

| 結果 | 處理 |
| --- | --- |
| ML=1 或 AGC 接近 255 | 磁鐵太遠，靠近晶片（間隙約 1–2 mm） |
| MH=1 或 AGC 接近 0 | 磁鐵太近，拉開一點 |
| 起伏比例太大 | 重新對心：磁鐵中心對準 AS5600 晶片中心 |
| 有跳點 | 檢查 I²C 接線（A4/A5），以及磁鐵是不是徑向充磁 |

調整後重新執行 `02_check_encoder`，直到全部 PASS。

## 方向標定 { #direction }

策略是在模擬裡學的，模擬有固定的正方向。實機的擺錘角度方向由 AS5600 決定：模組的 DIR 腳出廠可能接 GND、接 VCC，也可能沒接，同一批零件做出來的機台方向不一定一樣。**擺錘方向跟模擬相反時，策略推的時機剛好錯半拍，擺錘怎麼都甩不上去**，而且 `02_check_encoder`、`03_check_motor` 都會 PASS，看不出來。

`04_check_direction` 用物理判斷，不需要你分辨順時針或逆時針：手臂突然加速時，垂下的擺錘一定會被往反方向帶。工具讓手臂在正中間小幅抖動，比較「手臂角加速度」和「擺錘角加速度」的正負關係，跟模擬一致就記下來；相反就把方向修正後**存進 Nano 的 EEPROM**，再量一次確認。

!!! tool "操作步驟"

    1. Nano 燒的是 `LowLevelServer`（做完失步測試就不用重燒），關掉序列埠監控，12 V 接好。
    2. 手臂轉到正中間，周圍淨空；擺錘自然垂下、靜止。
    3. 執行 `tools/04_check_direction`，按 Enter。
    4. 手臂會小幅來回抖動約 4 秒（左右各約 10°），這段時間不要碰機台。
    5. 畫面印出相關係數。方向相反時工具會自動修正，再抖動一次確認。

!!! checkpoint "通過條件"

    最後印出 `PASS：擺錘方向 ±1 已存在 Nano 的 EEPROM`。相關係數跟模擬一致時是負的，約 −0.9。紀錄與圖存在 `policy/direction_runs/<時間>/`：`direction.png` 的點應該排成往右下的斜線。

    印出「判讀不出來」：擺錘幾乎沒有跟著手臂反應。檢查 12 V 有沒有接（手臂其實沒動）、擺錘有沒有被卡住，再跑一次 `02_check_encoder`。

- **存在哪裡**：Nano 的 EEPROM。Arduino IDE 重新上傳 `LowLevelServer` 或 `RLControl` **不會**清掉它，不用每次重做。`RLControl` 開機時讀同一個值。
- **什麼時候要重做**：換了 Nano、重新安裝 AS5600 或磁鐵、換了 AS5600 模組。
- **工具會幫你擋**：`05_sysid`、`07_finetune`、`08_test_policy` 開始前會確認 Nano 已經標定，沒有就停止並提示你先跑 `04_check_direction`。`07_finetune` 每一段開始前還會讓手臂抖動約 4 秒，確認方向沒有變；`RLControl` 沒標定就不會啟動馬達。
- **方向被修正過的話**：在錯的方向下做的實機微調（`runs/ftN`）要丟掉，從教師重新微調。sysid 與模擬訓練不受影響。

!!! warning "AS5600 的 DIR 腳不要自己接線"

    方向全部由 `04_check_direction` 處理，DIR 腳**不用接**。有些模組的 DIR 在板上已經用電阻接到 GND，這時再把 DIR 接到 5V 等於把 5V 短路到 GND。

## 我們的硬體與作者的差異 { #diff }

下表是課程 repo 已經處理好的差異，對照作者文件時參考，**不需要你改任何東西**。

| 項目 | 作者 | 我們 | 說明 |
| --- | --- | --- | --- |
| 馬達 | 17HS4023（22 mm 機身） | 17HS3401S（34 mm，額定 1.3 A） | 模擬把步進馬達當成剛性位置致動器，扭力不在模型裡，程式不用改 |
| TMC2209 Vref | 約 0.9 V（0.64 A RMS） | 約 1.0 V（約 0.7 A RMS） | 助教已調好；**Vref 設的是 RMS 不是峰值**，不要照抄 DRV8825 的數字 |
| 微步 | 1/32 | 1/32（MS1 接 5V、MS2 接 GND） | 所有 sketch 的 `MICROSTEPS = 32` |
| Bootloader | 新版 | Old Bootloader | IDE 處理器選 Old Bootloader；flash 上限 30720 bytes |
| 擺錘配重 | 英國 2p 硬幣，列印時嵌入 | 新台幣 10 元，貼在外側 | `model/model.urdf` 已更新 |
| 擺臂 | 列印擺臂 | 同作者的設計列印 | `pendulum_env.py` 的 `ARM_*` 沿用作者值 |
| 底座 | 作者列印外殼 | v5 壓克力三層底座 | 已經調平，放在水平的桌面上即可 |
| AS5600 方向 | DIR 不接，方向由模組決定 | DIR 不接，方向由 `04_check_direction` 存進 EEPROM | 作者的機台方向剛好跟模擬一致；我們的模組不一定，所以每台都要[標定](#direction) |

接線與作者相同：STEP→D9、DIR→D2、ENABLE→D5、AS5600 SDA/SCL→A4/A5，AS5600 只接 VCC、GND、SDA、SCL 四條線（DIR、OUT、GPO 不接）。12 V 供電並聯 100 µF。

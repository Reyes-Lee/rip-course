# 硬體與上電測試

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 30 分鐘</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
</div>

## 貼上配重硬幣 { #coin }

擺錘尖端要貼一枚新台幣 10 元硬幣當配重，位置對齊作者原本嵌硬幣的地方。作者把英國 2p 硬幣（7.12 g）在列印時封進擺錘裡；我們的擺錘印好時硬幣槽是空的，所以改貼在外側。**10 元硬幣（7.5 g、Ø26.0 × 1.87 mm）只比 2p 重 5%，可以直接用。**

<figure class="rip-figure">
<svg viewBox="0 0 520 330" role="img" aria-label="擺錘正面圖：硬幣中心距鉸鏈軸心 64 mm，下緣距底端 3 mm，左右各留 3 mm">
  <!-- 擺錘本體：寬 32 mm、鉸鏈上方 9 mm、下方 80 mm；1 mm = 3.3 px -->
  <rect x="150" y="20" width="106" height="294" rx="10" class="rip-svg-part" stroke-width="1.5"/>
  <!-- 鉸鏈 -->
  <circle cx="203" cy="50" r="9" fill="none" class="rip-svg-line" stroke-width="2"/>
  <circle cx="203" cy="50" r="2.5" class="rip-svg-text"/>
  <!-- 硬幣：Ø26 mm，中心在鉸鏈下方 64 mm -->
  <circle cx="203" cy="261" r="43" class="rip-svg-amber" opacity=".92"/>
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
  <!-- 3 mm 底部 -->
  <line x1="290" y1="304" x2="290" y2="314" class="rip-svg-cyan" stroke-width="1.5"/>
  <line x1="246" y1="304" x2="296" y2="304" class="rip-svg-cyan" stroke-width="1" stroke-dasharray="3 3"/>
  <line x1="256" y1="314" x2="296" y2="314" class="rip-svg-cyan" stroke-width="1" stroke-dasharray="3 3"/>
  <text x="304" y="314" font-size="13" font-weight="700" class="rip-svg-text">下緣距底端 3 mm</text>
  <!-- 3 mm 左右 -->
  <text x="304" y="244" font-size="13" font-weight="700" class="rip-svg-text">左右各留 3 mm</text>
  <line x1="246" y1="261" x2="300" y2="248" class="rip-svg-line" stroke-width="1"/>
  <!-- 說明 -->
  <text x="304" y="60" font-size="13" font-weight="700" class="rip-svg-text">貼在外側面</text>
  <text x="304" y="80" font-size="11" class="rip-svg-muted">遠離馬達、沒有凸出軸套的那一面</text>
  <text x="304" y="120" font-size="13" font-weight="700" class="rip-svg-text">新台幣 10 元</text>
  <text x="304" y="140" font-size="11" class="rip-svg-muted">7.5 g · Ø26.0 × 1.87 mm</text>
  <text x="304" y="180" font-size="13" font-weight="700" class="rip-svg-text">擺錘寬 32 mm</text>
  <text x="304" y="200" font-size="11" class="rip-svg-muted">鉸鏈下方長 80 mm</text>
</svg>
<figcaption>配重硬幣位置（尺寸依作者 pendulum.stl）</figcaption>
</figure>

!!! tool "操作步驟"

    1. 確認要貼的是**外側面**：遠離馬達、沒有凸出軸套的那一面。
    2. 用尺量位置：硬幣下緣距擺錘底端 3 mm，左右各留 3 mm。這樣硬幣中心就在距鉸鏈軸心 **64 mm** 的地方。
    3. 用薄的強力雙面膠或少量瞬間膠，貼平、貼正。
    4. 用手搖搖看，硬幣不能動。

!!! warning "一定要貼牢"

    擺錘失控旋轉時轉速可能到 35 rad/s，硬幣受到約 8 g 的離心加速度。貼好後就不要再移動；如果必須重貼，要照 [Step 0「檢查點沒過時」](../steps/step0-sysid.md#checkpoint-fail)第 1 點重新量測，之後 Step 1–4 都要重做。

位置誤差 ±1 mm，自然頻率變約 ±0.5%；±3 mm 變約 ±1.6%。這是整台機器裡唯一需要你認真量的尺寸。

## 上電測試 { #power-on }

每個韌體都用 Arduino IDE 開啟 `firmware/<名稱>/<名稱>.ino`，再按「上傳」。照順序做，前一個沒過不要往下。

| 順序 | 燒錄 | 然後 | 通過條件 |
| --- | --- | --- | --- |
| 1 | `TestHeartbeat` | Arduino IDE 選單「工具 → 序列埠監控」，右上角鮑率選 115200；看完關掉這個視窗 | LED 雙閃、持續印心跳計數 |
| 2 | `EncoderCheck` | 雙擊 `02_check_encoder` | 全部 PASS（見下一節） |
| 3 | `TestMotor` | 看、聽 | 手臂 ±90° 來回，平順的嗡嗡聲，沒有嘶嘶或磨擦聲 |
| 4 | `LowLevelServer` | 雙擊 `03_check_motor`（見[失步測試](#motor)） | 每級跑完手臂末端還對齊膠帶記號，聲音平順 |
| 5 | `TestSerial` | 雙擊 `01_check_serial` | 來回約 2.5 ms |

!!! warning "工具和 Arduino IDE 不能同時用序列埠"

    執行任何工具前，先關掉 Arduino IDE 的序列埠監控視窗。同一個埠一次只能有一個程式使用。

## 失步測試 { #motor }

步進馬達是開迴路的：失步時韌體的步數計數不會知道，所以要靠「手臂回到原點時還對不對得齊記號」來判斷。工具用的是策略本身的指令路徑（`LowLevelServer` 的加速度指令），最高 150 rad/s²，和策略實際會用到的一樣。

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `LowLevelServer`，關掉序列埠監控。
    2. 用手把手臂轉到正中間（正前方）。
    3. 在底座上貼一小段膠帶，對齊手臂末端，當作原點記號。
    4. 擺錘自然垂下，手臂周圍不要有東西擋到。
    5. 雙擊 `tools/03_check_motor`，按 Enter 開始。
    6. 加速度依序是 30、60、90、120、150 rad/s²。每一級手臂會在 ±45° 之間來回 4 次，再回到 0°。
    7. 每一級跑完，畫面問兩個問題：
        - `手臂末端還對齊膠帶嗎？`：偏移超過約 1 mm（大約 1°）就輸入 `n`。
        - `剛才的聲音是平順的嗡嗡聲嗎？`：有嘶嘶或磨擦聲就輸入 `n`。
    8. 任何一級回答 `n`，工具會停止測試。

!!! checkpoint "通過條件"

    五級都對齊、聲音都正常，最後印出 `PASS`。FAIL 就把結果拿給助教，檢查 Vref 與韌體加速度設定；不要自己轉可變電阻。

## 編碼器測試：磁場強度與對心 { #encoder }

AS5600 讀的是磁場方向，整套系統對擺錘角度的所有認知都來自它。磁鐵太遠會訊號弱、角度抖；太近會飽和；**沒對準中心時，讀數會隨轉角產生週期性失真**，sysid 與策略都會吃到錯的角度，而且很難從平衡表現看出來。助教的機台曾有 19% 的取樣 AGC 飽和，調整磁鐵距離後才歸零。

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `EncoderCheck`，關掉序列埠監控。
    2. 雙擊 `tools/02_check_encoder`。
    3. **靜態磁場（10 秒）**：畫面提示時，讓擺錘靜止垂下，不要碰。
    4. **用手慢轉**：畫面提示時按 Enter，用手捏著擺錘慢慢轉順時針 3 圈（每圈約 2–3 秒），轉完再按一次 Enter；接著逆時針 3 圈，同樣做一次。
    5. **自由擺（選做）**：畫面問 `要做自由擺測試嗎？[y/N]`，要做就輸入 `y`，把擺錘拉到約 60°，按 Enter 的同時放手，會錄 20 秒。
    6. 每一項印出 PASS/FAIL，並在 `policy/encoder_runs/<時間>/` 存一張圖（角度對時間、磁場強度對角度）。

| 項目 | 檢查什麼 | 通過條件 |
| --- | --- | --- |
| 狀態位元 | MD 偵測到磁鐵、ML 太弱、MH 太強 | MD=1、ML=MH=0 |
| AGC | 自動增益 | 不在 0 或 255 的極端，而且穩定 |
| 無跳點 | 相鄰取樣差 | 不超過 500 LSB（作者韌體用同一門檻擋錯誤讀值） |
| 圈數 | 累積角度 | 約 ±1080°，繞過 0°/360° 時正確接續 |
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

調整後重新雙擊 `02_check_encoder`，直到全部 PASS。

## 我們的硬體與作者的差異 { #diff }

下表是課程 repo 已經處理好的差異，對照作者文件時參考，**不需要你改任何東西**。

| 項目 | 作者 | 我們 | 說明 |
| --- | --- | --- | --- |
| 馬達 | 17HS4023（22 mm 機身） | 17HS3401S（34 mm，額定 1.3 A） | 模擬把步進馬達當成剛性位置致動器，扭力不在模型裡，程式不用改 |
| TMC2209 Vref | 約 0.9 V（0.64 A RMS） | 約 1.0 V（約 0.7 A RMS） | 助教已調好；**Vref 設的是 RMS 不是峰值**，不要照抄 DRV8825 的數字 |
| 微步 | 1/32 | 1/32（MS1 接 5V、MS2 接 GND） | 所有 sketch 的 `MICROSTEPS = 32` |
| Bootloader | 新版 | Old Bootloader | IDE 處理器選 Old Bootloader；flash 上限 30720 bytes |
| 擺錘配重 | 英國 2p 硬幣，列印時嵌入 | 新台幣 10 元，貼在外側 | `model/model.urdf` 已更新 |
| 擺臂 | 列印擺臂 | 同作者 STL 列印 | `pendulum_env.py` 的 `ARM_*` 沿用作者值 |
| 底座 | 作者列印外殼 | v5 壓克力三層底座 | 要放在水平桌面，傾斜 < 1°（Step 0 第一步） |

接線與作者相同：STEP→D9、DIR→D2、ENABLE→D5、AS5600 SDA/SCL→A4/A5。12 V 供電並聯 100 µF。

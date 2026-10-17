# Step 0：系統識別

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 15 分鐘</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
  <span class="rip-chip">:material-chip: LowLevelServer</span>
  <span class="rip-chip">:material-file-outline: 產出 sysid_params.json</span>
</div>

這一步把模擬釘在你那台機台上：量出擺錘鉸鏈的黏滯與庫倫摩擦，寫成 `sysid_params.json`。質量、質心、轉動慣量是零件的幾何性質，直接從 URDF 讀，**不在這一步量**。

## 0-1 放在水平桌面並確認傾斜 { #level }

!!! danger "不可略過"

    助教交機前已把底座調平，但那是相對於桌面：桌面本身歪、機台墊在書本或軟墊上，傾斜就回來了。**機台要放在水平、堅固、不會晃的桌面上，四角都著地，量測開始後就不要再移動。** 換桌子或搬動後，重做這一節。

傾斜會讓「真正的直立」隨手臂角度改變。作者的訓練只涵蓋 0–1° 的傾斜，超過就是超出訓練分布。助教的舊機台量到 5–11°，結果手臂會一直往同一個方向飄。

工具用擺錘當鉛錘：擺錘只能在垂直於手臂的平面擺，底座傾斜時，手臂轉到不同角度，擺錘靜止的位置會跟著偏。手臂走 9 個角度量一圈，就能算出傾斜的大小和方向。

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `LowLevelServer`，關掉序列埠監控。
    2. 用手把手臂轉到正中間（正前方），讓擺錘靜止垂下。
    3. 執行 `tools/04_check_level`，按 Enter。Nano 會重開約 2 秒，這段時間不要碰擺錘。
    4. 手臂自動走 9 個角度（−120° 到 +120°，每 30° 一點），每點停 5 秒量擺錘的平均位置。約 1 分鐘，不要碰機台。
    5. 印出傾斜大小。

!!! checkpoint "通過條件：傾斜 < 1°"

    印出 `PASS` 就完成了。

    **FAIL 時**，手臂會自己轉過去**指著比較低的那一側**（低的那一側在機台後方、轉不過去時，畫面會說改成指著高的那一側）：

    1. 先換一張桌子，或確認四角都著地。
    2. 還是 FAIL，就照畫面說的那一側，在那一側的腳下墊紙片或薄墊片。
    3. 按 Enter 讓手臂轉回中間，再執行 `04_check_level` 重測，重複到 **傾斜 < 1°**。
    4. 如果墊了之後傾斜反而變大，代表方向判斷相反，請告訴助教。

    畫面也會印「擬合殘差」。殘差超過 0.8° 代表量測時機台被碰到或桌面在晃，請重測。

## 0-2 擺錘配重與幾何：要量什麼？ { #geometry }

結論：**不用秤手臂、也不用秤擺錘；要確認的是硬幣貼在正確位置而且貼牢，然後讓 sysid 的自由擺去驗證。**

<div class="grid cards" markdown>

-   :material-arm-flex:{ .lg .middle } **手臂質量不影響模型**

    ---

    模擬裡手臂由步進馬達以剛性位置控制驅動，它的質量不進入擺錘的運動方程式，只影響馬達會不會失步，而這在上電測試（`03_check_motor`）已驗過。手臂要對的是長度，由 STL 決定，列印不會改變。

-   :material-printer-3d:{ .lg .middle } **列印質量差異幾乎不影響**

    ---

    模擬真正需要的是 m·d/I（決定自然頻率）與摩擦。列印密度從 0.6 到 1.24 g/cm³，自然頻率只在 12.41–12.51 rad/s 之間（±0.4%），因為 7.5 g 的硬幣佔了一半以上的質量。

-   :material-target:{ .lg .middle } **真正會影響的是硬幣位置**

    ---

    硬幣沿擺杆偏 3 mm，自然頻率就變約 1.6%，是列印差異的 4 倍。照[貼上配重硬幣](../prepare/hardware.md#coin)的方式貼，誤差控制在 ±1 mm。

-   :material-check-decagram:{ .lg .middle } **怎麼檢查**

    ---

    用手搖搖看硬幣不會鬆動；sysid 後小振幅自然頻率應在 12.3–12.6 rad/s（週期約 0.50–0.51 s），慣量誤差 < 10%。選做：秤擺錘總重（含硬幣），預期約 14–15 g。

</div>

## 0-3 跑 sysid 精靈 { #wizard }

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `LowLevelServer`（與微調時同一份韌體，量測與部署不會對不上），關掉序列埠監控。
    2. 準備一塊硬紙板或泡棉塊。
    3. 執行 `tools/05_sysid`。
    4. 選單出現時輸入 `1`（新量測），或直接按 Enter。
    5. 照畫面依序做下面四件事。

精靈會帶你做：

1. **標定垂下位置**：擺錘靜止垂下 3 秒，取中位數當 0。
2. **自由擺動 × 3**：手壓住手臂，用塊子把擺錘墊高，再從垂直於擺動平面的方向抽出。每次錄 10 秒。
3. **馬達 ±90° 掃描**：手臂走 0 → +90° → 0 → −90° → 0。目視確認峰值約垂直，明顯不足就是失步。
4. **擬合與畫圖**：寫出 json，並在 `sysid_runs/<時間>/` 產生 `freeswing_compare.png` 與 `motor_sweep.png`。

精靈的掃描只用到約 40 rad/s²，策略則會用到 150 rad/s²；高加速度下不失步已在上電測試用 `03_check_motor` 驗過。

??? cmd "背後執行的指令"

    ```bash
    cd policy
    uv run python sysid_wizard.py --port <PORT> --out-json sysid_params.json
    ```

## 檢查點 { #checkpoint }

!!! checkpoint "全部符合才進 Step 1"

    | 項目 | 通過條件 | 助教機台參考值 |
    | --- | --- | --- |
    | `freeswing_compare.png` | 模擬與實測的振幅包絡線幾乎重疊 | — |
    | 小振幅自然頻率 ω~n~ | 三次量測很接近 | 12.38 rad/s（週期 0.507 s） |
    | 轉動慣量：量測 vs URDF 預測 | 誤差 < 10% | 誤差 0.9% |
    | `motor_sweep.png` | 實際位置追得上指令，峰值約 ±90° | — |
    | 馬達聲音 | 平順，不嘶嘶不磨 | — |

### 檢查點沒過時 { #checkpoint-fail }

<ol class="rip-ol">
<li><b>只有「自由擺擬合」不好</b>（包絡線不重疊、三次 ω<sub>n</sub> 差很多）：再執行 <code>tools/05_sysid</code>，選單輸入 <code>1</code>（新量測），整套重做一次，約 15 分鐘。</li>
<li><b>想用同一份錄製重新擬合</b>（例如助教更新了擬合程式）：執行 <code>tools/05_sysid</code>，選單輸入 <code>2</code>（用已存的錄製重新擬合），再從列出的 <code>sysid_runs/&lt;時間&gt;</code> 裡選一個，不用碰機台。</li>
<li><b>慣量誤差超過 10%</b>：先檢查硬幣位置與是否鬆動（<a href="../../prepare/hardware/#coin">貼上配重硬幣</a>），修好後照第 1 點重量。仍然超過就找助教。</li>
</ol>

??? cmd "第 2 點背後執行的指令"

    ```bash
    cd policy
    uv run python sysid_wizard.py fit --in-dir sysid_runs/<時間> --out-json sysid_params.json
    ```

!!! warning "機構改過就要重量"

    換軸承、重裝擺臂或擺錘、重貼硬幣，都要照第 1 點重量，而且後面的 Step 1–4 都要重做。

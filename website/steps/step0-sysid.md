# Step 0：系統識別

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 15 分鐘</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
  <span class="rip-chip">:material-chip: LowLevelServer</span>
  <span class="rip-chip">:material-file-outline: 產出 sysid_params.json</span>
</div>

這一步讓模擬對上你的機台：量出擺錘鉸鏈的黏滯與庫倫摩擦，寫成 `sysid_params.json`。質量、質心、轉動慣量是零件的幾何性質，直接從 URDF 讀，**不在這一步量**。

!!! todo "這一步要做的事"

    1. [跑 sysid 精靈](#wizard)：燒 `LowLevelServer`，執行 `05_sysid`，照畫面做完四個階段。
    2. [對照檢查點](#checkpoint)：看兩張圖和工具印出的數字，全部符合才進 Step 1。
    3. （需要時）[檢查點沒過時](#checkpoint-fail)：重新量測或重新擬合。

    開始前先確認[機台放在水平的桌面上](#level)。標題前標「說明」的段落是原理說明，讀懂就好，不用操作。

<span id="level"></span>

!!! info "開始前：機台放在水平的桌面上"

    機台交給你之前已經調平，不需要另外測量。你只要確認桌面水平、堅固、不會晃，機台四角都著地，量測開始後不要再移動機台。桌面不平就換一張桌子。

## 1. 跑 sysid 精靈 { #wizard .rip-do }

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `LowLevelServer`（和微調用的是同一份韌體，量測條件才會一致），關掉序列埠監控。
    2. 準備一塊硬紙板或泡棉塊。
    3. 執行 `tools/05_sysid`。
    4. 選單出現時輸入 `1`（新量測），或直接按 Enter。
    5. 照畫面依序做完下面四個階段。

!!! tool "精靈的四個階段（照畫面提示做）"

    1. **標定垂下位置**：**先不要放墊塊**，讓擺錘自然垂到最低點、完全靜止，再按 Enter。精靈錄 3 秒，取中位數當 0。墊塊是下一步自由擺時才用。標定位置跟擺錘停下的位置差超過 10°，擬合時工具會提醒你（擬合結果不受影響）。
    2. **自由擺動 × 3**：手壓住手臂，用墊塊把擺錘墊高，再從垂直於擺動平面的方向抽出。每次錄 10 秒。
    3. **馬達 ±90° 掃描**：手臂走 0 → +90° → 0 → −90° → 0。**12 V 要接著**。目視確認手臂真的轉到左右約 90°（跟底座垂直）再回到正中間，明顯轉不到就是失步。
    4. **擬合與畫圖**：寫出 json，並在 `sysid_runs/<時間>/` 產生 `freeswing_compare.png` 與 `motor_sweep.png`。

精靈的掃描只用到約 40 rad/s²，策略則會用到 150 rad/s²；高加速度下不失步已在上電測試用 `03_check_motor` 驗過。

??? cmd "背後執行的指令"

    ```bash
    cd policy
    uv run python sysid_wizard.py --port <PORT> --out-json sysid_params.json
    ```

## 2. 對照檢查點 { #checkpoint .rip-do }

!!! checkpoint "全部符合才進 Step 1"

    | 項目 | 通過條件 |
    | --- | --- |
    | `freeswing_compare.png` | 模擬與實測的振幅包絡線幾乎重疊 |
    | 小振幅自然頻率 ω~n~ | 工具採用的那次（三次的中位數，寫進 `sysid_params.json`）在 12.3–12.6 rad/s（週期約 0.50–0.51 s），而且三次的最大與最小相差 < 3%（約 0.4 rad/s）。只有一次偏掉、另外兩次彼此接近又都在範圍內也算通過：工具用中位數，偏掉的那次不影響結果，多半是放手時碰到或有震動 |
    | 轉動慣量：量測 vs URDF 預測 | 誤差 < 10% |
    | 馬達掃描（**目視**） | 手臂真的轉到左右約 90° 再回到正中間。`motor_sweep.png` 的藍線是韌體的步數計數，12 V 沒接、手臂沒動也會畫得很漂亮，所以不能只看圖 |
    | 馬達聲音 | 平順，沒有嘶嘶聲或摩擦聲 |

### 兩張圖怎麼看 { #plots .rip-learn }

<figure class="rip-figure" markdown>
![freeswing_compare.png 的正常範例：上圖實測與模擬都是衰減的正弦波，下圖兩條峰值線靠近](../assets/img/step0-freeswing-compare.png)
<figcaption><code>freeswing_compare.png</code> 正常的樣子</figcaption>
</figure>

- **上圖**：藍色（實測）和橘色（模擬）都是衰減的正弦波，y 軸大約在 ±1 rad 內。一開始的相位可能差一點（放手時手的干擾），不影響。
- **下圖**：兩條峰值線是往下的斜線，彼此靠近。
- **標題的 Δ**：第一個是週期差，應在約 ±5% 內；第二個是衰減差，±20% 內都算正常。
- **壞掉的樣子**：y 軸到幾百、幾千 rad，或下圖是空的。這是工具的問題，不是你的量測，找助教。

<figure class="rip-figure" markdown>
![motor_sweep.png 的範例：藍線落後橘色虛線約 0.5 秒，最後到達 ±90° 並回到 0°](../assets/img/step0-motor-sweep.png)
<figcaption><code>motor_sweep.png</code>：藍線（韌體計數）落後目標約 0.5 秒是正常的</figcaption>
</figure>

- 藍線會落後橘色虛線約 0.5 秒才到位，這是正常的（精靈只用約 30–40 rad/s²）。
- 要看藍線最後有沒有到 ±90° 的細黑線、回到 0°。
- **這張圖不能證明手臂真的動了**（見上面檢查點的「目視」那一列）。

## 3. （需要時）檢查點沒過時 { #checkpoint-fail .rip-do }

!!! tool "依情況處理"

    1. **只有「自由擺擬合」不好**（包絡線不重疊，或三次 ω~n~ 相差 ≥ 3% 而且不只一次偏掉）：再執行 `tools/05_sysid`，選單輸入 `1`（新量測），整套重做一次，約 15 分鐘。
    2. **想用同一份錄製重新擬合**（例如助教更新了擬合程式）：執行 `tools/05_sysid`，選單輸入 `2`（用已存的錄製重新擬合），再從列出的 `sysid_runs/<時間>` 裡選一個，不用碰機台。
    3. **慣量誤差超過 10%**：先檢查硬幣位置與是否鬆動（[貼上配重硬幣](../prepare/hardware.md#coin)），修好後照第 1 點重新量測。仍然超過就找助教。

??? cmd "第 2 點背後執行的指令"

    ```bash
    cd policy
    uv run python sysid_wizard.py fit --in-dir sysid_runs/<時間> --out-json sysid_params.json
    ```

!!! warning "機構改過就要重新量測"

    換軸承、重裝擺臂或擺錘、重貼硬幣，都要照第 1 點重新量測，而且後面的 Step 1–4 都要重做。

## 擺錘配重與幾何：為什麼只看硬幣 { #geometry .rip-learn }

擺錘的質量、質心、轉動慣量不在這一步量，模擬直接用 URDF 的值。和這些量有關、你唯一要確認的是**硬幣**：貼在正確位置、貼牢。貼得對不對，由 sysid 的自由擺來驗證（檢查點的「慣量誤差」）。

<div class="grid cards" markdown>

-   :material-target:{ .lg .middle } **硬幣位置**

    ---

    硬幣要貼在擺錘大頭圓盤的正中間（見[貼上配重硬幣](../prepare/hardware.md#coin)）。偏離中心太多，模擬會跟實機對不上。

-   :material-check-decagram:{ .lg .middle } **怎麼檢查**

    ---

    用手搖搖看硬幣不會鬆動；sysid 後小振幅自然頻率應在 12.3–12.6 rad/s（週期約 0.50–0.51 s），慣量誤差 < 10%。選做：秤擺錘總重（含硬幣），預期約 14–15 g。

</div>

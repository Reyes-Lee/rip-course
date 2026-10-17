# Step 1：在模擬中訓練教師策略

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 筆電 CPU 約 25 分鐘</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台</span>
  <span class="rip-chip">:material-file-outline: 產出 v1_stage3/best_model.zip</span>
</div>

執行 `06_train_teacher` 就會跑完三階段課程，產出一支 256×256 的 SAC 教師策略。

## 操作步驟 { #run }

!!! tool "第一次訓練"

    1. 確認 Step 0 已經產生 `policy/sysid_params.json`。
    2. 筆電接上電源、不要闔上蓋子（睡眠會讓訓練中斷）。
    3. 執行 `tools/06_train_teacher`。
    4. 畫面問 `run 名稱 [v1]:`，第一次直接按 Enter。
    5. 畫面問 `SEED [0]:`，直接按 Enter。
    6. 工具印出設定 header 並自動核對（見[檢查點](#checkpoint)），然後開始訓練。畫面會持續印出進度，約 25 分鐘。
    7. 訓練完工具自動跑檢查點並印出數字（見[檢查點](#checkpoint)）。工具不替你判斷，由你對照參考門檻決定下一步。

!!! tip "中途中斷了（關掉視窗、筆電睡眠）"

    再執行 `tools/06_train_teacher`，`run 名稱` 輸入**同一個名稱**（例如 `v1`）。工具會顯示 `已完成第 N 階段，從第 N+1 階段接續？[Y/n]`，按 Enter，已完成的階段不會重跑。

??? cmd "背後執行的指令"

    `06_train_teacher` 是作者 `curriculum_train.sh` 的 Python 版（Windows 不能直接跑 bash），參數照原腳本的預設值。等同於：

    ```bash
    cd policy
    DEVICE=cpu PARAMS_PATH=sysid_params.json bash curriculum_train.sh v1
    ```

    實際上是依序跑三次 `train_sac.py`，例如第 1 階段：

    ```bash
    uv run python train_sac.py --total-steps 100000 --device cpu \
        --control-freq 50 --max-accel-rad-s2 150 --action-mode velocity \
        --max-velocity-rad-s 3.5 --use-sde --obs-history-len 4 \
        --firmware-obs-model --mirror-augment --action-smooth-window 4 \
        --dr-obs-staleness-max 0.020 --params-path sysid_params.json \
        --reward-stillness-bonus-weight 5 --run-name v1_stage1 --seed 0
    ```

    第 2、3 階段再加上 `--domain-randomization`、延遲範圍，並用 `--resume` 接續前一階段的 `best_model.zip`。工具固定用 CPU 訓練：訓練的瓶頸是梯度更新，GPU 幫不上忙。

## 模擬訓練在做什麼 { #what }

這一步是用 reward 在 MuJoCo 裡訓練出一個 policy。四個角色：

<div class="grid cards" markdown>

-   :material-brain:{ .lg .middle } **Policy**

    ---

    一個 256×256 的神經網路。輸入是最近 4 幀的觀測，輸出是手臂的速度指令。這是要**學出來**的東西。

-   :material-scoreboard:{ .lg .middle } **Reward**

    ---

    每一步的評分規則，定義「**要做什麼**」：擺錘越直立、越安靜、手臂越置中、出力越小，分數越高。

-   :material-refresh:{ .lg .middle } **SAC**

    ---

    強化學習演算法。讓 policy 在模擬裡反覆嘗試（3 階段共 30 萬步），調整權重讓長期累積的 reward 最大，也就是學會「**怎麼做**」。

-   :material-dice-multiple:{ .lg .middle } **Domain randomization**

    ---

    每回合隨機改摩擦、質量、延遲等參數，逼 policy 學到不依賴單一模型的控制方式，搬到實機才不會垮。

</div>

!!! question "為什麼不用改 reward？"

    reward 描述的是任務（甩上、站直、站穩），不是硬體。它用的是物理量（rad、rad/s）與正規化的動作（−1 到 1），換馬達、換配重都不影響它。作者在開發時反覆調過 reward，現在的預設值就是他最後驗證的版本，他自己跑這一步也是直接用。每台機台真正不同的是**動態**，這由 Step 0 的 sysid 與 Step 2 的實機微調處理。

## 參數怎麼送進 MuJoCo { #params }

全部自動，不用改任何檔案。`06_train_teacher` 會自動帶上你的 `sysid_params.json`；每次建立模擬時，`pendulum_env.py` 的 `build_mjcf()` 會用下表的來源組出 MuJoCo 模型。

| 參數 | 來源 | 誰負責 |
| --- | --- | --- |
| 擺錘鉸鏈的黏滯與庫倫摩擦 | `sysid_params.json` | Step 0 量測，自動帶入 |
| 擺錘質量、質心、轉動慣量 | `model/model.urdf`（已更新為 10 元外貼） | 助教已改好 |
| 手臂長度與質量 | `pendulum_env.py` 常數（作者值） | 不用改 |
| 動作延遲、觀測延遲 | 三階段課程的 DR 範圍（作者實測） | 不用改 |
| 控制頻率、速度與加速度上限 | `train_sac.py` 預設值，與韌體一致 | 不用改 |

!!! warning "sysid 只把摩擦送進模擬"

    質量與慣量用的是 URDF。硬幣貼歪不會被 sysid 自動修正，只會在 [Step 0 檢查點](step0-sysid.md#checkpoint)的「慣量誤差」看出來，所以那一項要認真看。

## 三個階段在做什麼 { #stages }

| 階段 | 動作延遲 | 延遲濾波 τ | Domain randomization | 目的 |
| --- | --- | --- | --- | --- |
| 1 學技能 | 0 | 0 | 關 | 先學會甩上與平衡 |
| 2 緩坡 | 0–1 拍 | 0–20 ms | 開 | 引入傳輸延遲 |
| 3 集中 | 1 拍 | 0–15 ms | 開 | 集中在實測延遲（約 20–35 ms） |

每階段 10 萬步，從前一階段的 `best_model.zip` 接續。第 2 階段起同時隨機化：擺錘質量與質心 ±10%、擺錘摩擦 ×0.5–2、馬達加速度上限 110–190 rad/s²、控制週期 ±5% 抖動、觀測延遲 2–20 ms、底座傾斜 0–1°、編碼器量化與雜訊。

## 策略看到什麼、輸出什麼 { #obs }

觀測
:   每幀 6 個數 `[手臂角, sin θ, cos θ, 手臂角速度, 擺錘角速度, 上一個動作]`，堆疊最近 4 幀共 24 維。θ = 0 是直立。用 sin/cos 是為了避開 ±π 的數值跳躍。

動作
:   a ∈ [−1, 1]，代表手臂速度設定值 a × 3.5 rad/s。韌體用飽和 P 律換成加速度指令，上限 150 rad/s²，再對最近 4 個動作取平均。

回合
:   8 秒；25% 的回合從接近直立開始，其餘從垂下開始。

手臂角度限制
:   策略的指令最多到 ±125°；手臂碰到 ±135° 就當成撞到硬限位，扣 5 分並結束回合。實機韌體有對應的保護（見 [Step 4](step4-deploy.md#flash)）。

## Reward（標準配方） { #reward }

$$
\begin{aligned}
r \;=\;& \underbrace{15}_{\text{存活偏移}} \;+\; \underbrace{5\cdot\mathbb{1}\!\left[\,|\theta|\le 15^\circ,\ |\dot\theta|\le 2\,\right]}_{\text{接住的直立}} \;+\; \underbrace{5\, e^{-\theta^2/0.3^2}\, e^{-\dot\alpha^2/1^2}}_{\text{靜止獎勵}} \\[6pt]
&-\; \underbrace{\left(\theta^2 + 0.001\,\dot\theta^2 + 0.5\,\alpha^2 + 0.005\,\dot\alpha^2 + 0.2\,a^2\right)}_{\text{Quanser 式二次成本}}
\end{aligned}
$$

α 是手臂角（rad）。括號內是 Quanser 式的二次成本；前面三項各有用途：

- **15（存活偏移）**：讓每步 reward 為正。若全是負的，「快點撞牆結束回合」反而划算。
- **5·𝟙[…]（接住的直立）**：只有「角度小且速度慢」才拿得到，快速甩過直立不算，防止策略一直繞圈刷分。
- **靜止獎勵**：擺錘直立且手臂不動時最大，把策略從「用力平衡」推向「安靜平衡」。

作者網站「The transition contract」頁的 reward 是舊版，以程式 `policy/reward.py` 與 `train_sac.py` 的預設值為準。

## 在 MuJoCo 視窗看訓練成果 { #mujoco }

訓練完就可以在 MuJoCo 視窗看策略在模擬裡怎麼動。這是作者自己看訓練成果的方式。

!!! tool "操作步驟"

    1. 執行 `tools/12_view_policy`。
    2. 清單列出 `runs/` 裡所有的 `best_model.zip`，輸入要看的那一支的編號；直接按 Enter 是最新的那一支。
    3. MuJoCo 視窗打開，策略從垂下開始跑 30 秒，結束後視窗自動關閉。想再看一次就重新執行。

<div class="grid cards" markdown>

-   :material-eye:{ .lg .middle } **要看什麼**

    ---

    從垂下開始，幾次擺動內甩上、接住不衝過頭；平衡時擺錘幾乎不動，手臂留在中間附近。

-   :material-compare:{ .lg .middle } **比較階段**

    ---

    執行兩次：第一次選 `v1_stage1/best_model.zip`，第二次選 `v1_stage3/best_model.zip`，看加入延遲與 DR 後動作有什麼不同。

-   :material-mouse:{ .lg .middle } **操作**

    ---

    左鍵拖曳旋轉視角、滾輪縮放。點兩下擺錘選取後，按住 ++ctrl++ 用右鍵拖曳可以推它，看策略怎麼救回來。

-   :material-alert-circle-outline:{ .lg .middle } **別被騙了**

    ---

    模擬裡很穩不代表實機很穩，實機表現以 Step 2 的誠實指標為準。

</div>

??? cmd "背後執行的指令"

    Windows 用 `python`，macOS 用 `mjpython`，工具會自動選。

    ```bash
    cd policy
    uv run mjpython train_sac.py --eval runs/v1_stage3/best_model.zip \
        --params-path sysid_params.json
    ```

## 檢查點 { #checkpoint }

`06_train_teacher` 訓練結束時會自動跑下面三項並印出結果；除了設定 header 不符會中止，其餘只印數字，不替你判斷。之後想對任何一支策略重跑，執行 `tools/13_check_sim`，從清單選那支策略即可。

!!! checkpoint "參考門檻（作者的建議，由你判斷）"

    | 項目 | 工具做什麼 | 參考門檻 |
    | --- | --- | --- |
    | 設定 header | 訓練開始時核對 4 行設定 | `mirror augmentation: ON`、`obs staleness DR: up to 0.02 s`、`rig sysid: sysid_params.json`、`control rate: 50 Hz, max accel: 150` 全部符合；不符工具會中止，請找助教 |
    | 對稱性 | 從垂下的狀態開始，看策略能不能自己甩上 | 從垂下的狀態能自己甩上（工具印出 `從垂下自己甩上：是／否`） |
    | 敏感度關卡 | 在模擬裡各跑 20 回合：開著與關掉韌體量測模型 | 關掉後的 balanced fraction ≥ 0.7 |

敏感度關卡在問：策略學到的是控制本身，還是模擬量測的統計特徵？作者的校準：關掉後 ≥ 0.7 的策略部署全部成功，≤ 0.3 的四支全部失敗；兩者之間作者沒有資料。我們的建議：

| 關掉後的分數 | 建議 | 下一步 |
| --- | --- | --- |
| ≥ 0.7 | :material-check-circle:{ style="color: var(--rip-green)" } 多半可行 | 進 Step 2 |
| 0.3–0.7 | :material-alert:{ style="color: var(--rip-amber)" } 不確定 | 可以進 Step 2，但建議同時照下面的方法再訓練一支，後續用分數高的 |
| < 0.3，或不能自己甩上 | :material-close-circle:{ style="color: var(--rip-red)" } 多半會失敗 | 照下面換 SEED 重訓 |

### 決定重訓時：換一個 SEED { #reseed }

SEED 是亂數種子，決定網路初始權重與探索過程；同一套配方換一個 SEED，結果就可能不同。不需要機台。

!!! tool "操作步驟"

    1. 執行 `tools/06_train_teacher`。
    2. `run 名稱 [v1]:` 輸入 `v2`。**不要沿用 v1**，否則工具會把它當成接續舊的那一支。
    3. `SEED [0]:` 輸入 `1`。
    4. 約 25 分鐘後看新的檢查點數字，和前一支比較。
    5. 還是不理想，再用 `v3`、SEED `2`。連續三支都低於 0.3 就找助教，通常是 Step 0 的問題。
    6. Step 2 選教師時，選你判斷最好的那一支（例如 `v2_stage3`）。

??? cmd "檢查點背後執行的指令"

    ```bash
    cd policy
    uv run python analyze_symmetry.py runs/v1_stage3/best_model.zip
    uv run python analyze_sim.py runs/v1_stage3/best_model.zip --episodes 20
    uv run python analyze_sim.py runs/v1_stage3/best_model.zip --episodes 20 --no-firmware-obs-model
    ```

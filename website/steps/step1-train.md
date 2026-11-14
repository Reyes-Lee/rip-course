# Step 1：在模擬中訓練教師策略

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 筆電 CPU 約 25–60 分鐘</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台</span>
  <span class="rip-chip">:material-file-outline: 產出 v1_stage3/best_model.zip</span>
</div>

執行 `06_train_teacher` 會依序跑完三個訓練階段，產出一支 256×256 的 SAC 教師策略。

!!! todo "這一步要做的事"

    1. [訓練教師策略](#run)：執行 `06_train_teacher`，等三個階段跑完。要改 reward 的話，訓練前先看[選做：修改 reward](#edit-reward)。
    2. [看檢查點](#checkpoint)：對照工具印出的數字，決定直接進 Step 2 還是重訓。
    3. （選做）[在 MuJoCo 視窗看訓練成果](#mujoco)。
    4. （需要時）[換一個 SEED 重訓](#reseed)。

    標題前標「說明」的段落是原理說明，讀懂就好，不用操作。

## 1. 訓練教師策略 { #run .rip-do }

!!! tool "第一次訓練"

    1. 確認 Step 0 已經產生 `policy/sysid_params.json`。
    2. 筆電接上電源，訓練期間不要讓電腦進入睡眠，睡眠會中斷訓練。
    3. 執行 `tools/06_train_teacher`。
    4. 畫面問 `run 名稱 [v1]:`，第一次直接按 Enter。
    5. 畫面問 `SEED [0]:`，直接按 Enter。
    6. 畫面問 `每階段步數 [100000]:` 和 `要改 reward 權重嗎？ [y/N]:`，直接按 Enter 是作者的設定（見[三個階段](#stages)與[修改 reward](#edit-reward)）。
    7. 工具印出設定 header（用眼睛確認，見[檢查點](#checkpoint)），然後開始訓練。畫面會一直捲動英文統計表，那張表不用看；每 30 秒會印一行中文進度，例如 `[Stage 1/3] ████████░░ 45,600 / 100,000 步（46%）｜……預估還要約 43 分鐘`。總時間取決於電腦速度，作者的電腦約 25 分鐘，Apple M1 約 50 分鐘。印出 `Stage 3 完成` 和檢查點結果，才算跑完。
    8. 訓練結束後，工具接著跑檢查點並印出數字（見[檢查點](#checkpoint)）。請對照參考門檻，自行判斷下一步。

!!! tip "中途中斷了（關掉視窗、筆電睡眠）"

    再執行 `tools/06_train_teacher`，`run 名稱` 輸入**同一個名稱**（例如 `v1`）。工具會顯示 `已完成第 N 階段，從第 N+1 階段接續？[Y/n]`，按 Enter 後，已完成的階段不會重跑。**中斷時正在跑的那個階段會從頭再跑一次**（最多約 20 分鐘）。

??? cmd "背後執行的指令"

    `06_train_teacher` 是作者 repo 裡 [`curriculum_train.sh`](https://github.com/ferrolho/rotary-inverted-pendulum/blob/main/policy/curriculum_train.sh) 的 Python 版（Windows 不能直接跑 bash，課程 repo 沒有附這支 `.sh`），參數照原腳本的預設值。

    實際上是依序跑三次 `train_sac.py`，例如第 1 階段：

    ```bash
    uv run python train_sac.py --total-steps 100000 --device cpu \
        --control-freq 50 --max-accel-rad-s2 150 --action-mode velocity \
        --max-velocity-rad-s 3.5 --use-sde --obs-history-len 4 \
        --firmware-obs-model --mirror-augment --action-smooth-window 4 \
        --dr-obs-staleness-max 0.020 --params-path sysid_params.json \
        --reward-alive-offset 15.0 --reward-upright-alive-weight 5.0 \
        --reward-stillness-bonus-weight 5.0 --reward-motor-pos-weight 0.5 \
        --reward-motor-vel-weight 0.005 --reward-motor-jerk-weight 0.0 \
        --reward-action-rate-weight 0.0 --run-name v1_stage1 --seed 0
    ```

    第 2、3 階段再加上 `--domain-randomization`、延遲範圍，並用 `--resume` 接續前一階段的 `best_model.zip`。工具固定用 CPU 訓練：訓練的瓶頸是梯度更新，GPU 幫不上忙。

## 2. 看檢查點 { #checkpoint .rip-do }

`06_train_teacher` 訓練結束時會接著跑下面三項並印出結果；結果只列出數字，可以對照下面的參考門檻自行判斷。之後想對任何一支策略重跑，執行 `tools/13_check_sim`，從清單選那支策略即可。

!!! checkpoint "參考門檻（作者的建議，由你判斷）"

    | 項目 | 工具做什麼 | 參考門檻 |
    | --- | --- | --- |
    | 設定 header | 訓練開始時用眼睛確認這 4 行（其他行是步數、reward 權重等你選的設定） | `mirror augmentation: ON`、`obs staleness DR: up to 0.02 s`、`rig sysid: sysid_params.json`、`control rate: 50 Hz, max accel: 150` 全部符合；不符就按 ++ctrl+c++ 停止，找助教 |
    | 對稱性 | 從垂下的狀態開始，看策略能不能自己甩上 | 從垂下的狀態能自己甩上（工具印出 `從垂下自己甩上：是／否`） |
    | 敏感度關卡 | 在模擬裡各跑 20 回合：開著與關掉韌體量測模型 | 關掉後的 balanced fraction ≥ 0.7 |

敏感度關卡在問：策略學到的是控制本身，還是模擬量測的統計特徵？作者的校準：關掉後 ≥ 0.7 的策略部署全部成功，≤ 0.3 的四支全部失敗；兩者之間作者沒有資料。要直接進 Step 2，還是先換 SEED 重訓，由你判斷。

??? cmd "檢查點背後執行的指令"

    ```bash
    cd policy
    uv run python analyze_symmetry.py runs/v1_stage3/best_model.zip
    uv run python analyze_sim.py runs/v1_stage3/best_model.zip --episodes 20
    uv run python analyze_sim.py runs/v1_stage3/best_model.zip --episodes 20 --no-firmware-obs-model
    ```

## 3. （選做）在 MuJoCo 視窗看訓練成果 { #mujoco .rip-do }

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

    Windows 用 `python`，macOS 用 `mjpython`，工具會依系統選擇。

    ```bash
    cd policy
    uv run mjpython train_sac.py --eval runs/v1_stage3/best_model.zip \
        --params-path sysid_params.json
    ```

## 4. （需要時）換一個 SEED 重訓 { #reseed .rip-do }

SEED 是亂數種子，決定網路初始權重與探索過程；同一套配方換一個 SEED，結果就可能不同。不需要機台。

!!! tool "操作步驟"

    1. 執行 `tools/06_train_teacher`。
    2. `run 名稱 [v1]:` 輸入 `v2`。**不要沿用 v1**，否則工具會把它當成接續舊的那一支。
    3. `SEED [0]:` 輸入 `1`。
    4. 跑完（約 25–60 分鐘）後看新的檢查點數字，和前一支比較。
    5. 還是不理想，再用 `v3`、SEED `2`，以此類推。連續好幾支都很低，問題通常不在 SEED：回去對照 [Step 0 檢查點](step0-sysid.md#checkpoint)，確認模型對上機台；改過 reward 的話，也要檢查你的修改。
    6. Step 2 選教師時，選你判斷最好的那一支（例如 `v2_stage3`）。

!!! warning "訓練和實機微調不要同時跑"

    `06_train_teacher` 會吃滿 CPU，`07_finetune` 要在同一台筆電上維持 50 Hz 控制。兩個同時跑會拖慢控制迴路，微調資料就不可靠。要多訓練幾支，趁不用機台的時間（例如晚上）一支接一支跑，**選好教師再開始 Step 2**。

    已經用某一支開始微調後，才發現另一支 SEED 分數比較高：只要現在的微調在 [Step 2 的接線測試](step2-finetune.md#test)還在進步，就繼續用原本那支，不用換；如果接線測試的 balanced fraction 一直 < 0.4，再換新的教師從 ft1 重跑。

## 模擬訓練在做什麼 { #what .rip-learn }

這一步在 MuJoCo 裡依照 reward 訓練出一個 policy，過程中有四個角色：

<div class="grid cards" markdown>

-   :material-brain:{ .lg .middle } **Policy**

    ---

    一個 256×256 的神經網路。輸入是最近 4 幀的觀測，輸出是手臂的速度指令。這是要**學出來**的東西。

-   :material-scoreboard:{ .lg .middle } **Reward**

    ---

    每一步的評分規則，定義「**要做什麼**」：擺錘越直立、越安靜、手臂越置中、出力越小，分數越高。

-   :material-refresh:{ .lg .middle } **SAC**

    ---

    強化學習演算法。讓 policy 在模擬裡反覆嘗試（3 階段共 30 萬步），調整網路權重，讓長期累積的 reward 最大，也就是學會「**怎麼做**」。

-   :material-dice-multiple:{ .lg .middle } **Domain randomization**

    ---

    每回合隨機改摩擦、質量、延遲等參數，逼 policy 學會不依賴單一模型的控制方式，換到實機上才不會失效。

</div>

!!! note "作者的 reward 是 baseline"

    reward 描述的是任務（甩上、站直、站穩），用的是物理量（rad、rad/s）與正規化的動作（−1 到 1）。作者在開發時反覆調過 reward，[下面的公式](#reward)是他最後驗證過的版本，他自己跑這一步時也直接使用，本專題把它當成 baseline。每台機台不同的**動態**由 Step 0 的 sysid 與 Step 2 的實機微調處理；reward 要不要改、怎麼改，由你決定，改的位置見[修改 reward](#edit-reward)。

## 參數怎麼送進 MuJoCo { #params .rip-learn }

`06_train_teacher` 會把你的 `sysid_params.json` 傳給訓練程式（指令裡的 `--params-path`）。每次建立模擬時，`pendulum_env.py` 的 `build_mjcf()` 依下表的來源組出 MuJoCo 模型；想知道某個參數實際用了多少，就到表上的位置去看。

| 參數 | 來源 | 數值從哪裡來 |
| --- | --- | --- |
| 擺錘鉸鏈的黏滯與庫倫摩擦 | `sysid_params.json` | 你在 Step 0 量的 |
| 擺錘質量、質心、轉動慣量 | `model/model.urdf` | 由擺錘和硬幣的幾何算出 |
| 手臂長度與質量 | `pendulum_env.py` 常數 | 作者機台的值，擺臂相同 |
| 動作延遲、觀測延遲 | 三個訓練階段的 DR 範圍 | 作者實測 |
| 控制頻率、速度與加速度上限 | `train_sac.py` 預設值 | 作者配方，必須和韌體一致 |

!!! warning "sysid 只把摩擦送進模擬"

    質量與慣量用的是 URDF。硬幣貼歪，sysid 不會修正，只會在 [Step 0 檢查點](step0-sysid.md#checkpoint)的「慣量誤差」看出來，所以那一項要認真看。

## 三個階段在做什麼 { #stages .rip-learn }

| 階段 | 動作延遲 | 延遲濾波 τ | Domain randomization | 目的 |
| --- | --- | --- | --- | --- |
| 1 學會動作 | 0 | 0 | 關 | 先學會甩上與平衡 |
| 2 逐步加入延遲 | 0–1 拍 | 0–20 ms | 開 | 開始加入傳輸延遲 |
| 3 貼近實機延遲 | 1 拍 | 0–15 ms | 開 | 集中在實測的延遲範圍（約 20–35 ms） |

每階段預設 10 萬步（`06_train_teacher` 會問 `每階段步數`，三個階段用同一個值，訓練時間大約和步數成正比），從前一階段的 `best_model.zip` 接續。第 2 階段起同時隨機化：擺錘質量與質心 ±10%、擺錘摩擦 ×0.5–2、馬達加速度上限 110–190 rad/s²、控制週期 ±5% 抖動、觀測延遲 2–20 ms、底座傾斜 0–1°、編碼器量化與雜訊。

## 策略看到什麼、輸出什麼 { #obs .rip-learn }

觀測
:   每幀 6 個數 `[手臂角, sin θ, cos θ, 手臂角速度, 擺錘角速度, 上一個動作]`，堆疊最近 4 幀共 24 維。θ = 0 是直立。用 sin/cos 是為了避開 ±π 的數值跳躍。

動作
:   a ∈ [−1, 1]，代表手臂的目標速度 a × 3.5 rad/s。韌體先對最近 4 個動作取平均，再用比例控制換成加速度指令，加速度上限 150 rad/s²。

回合
:   8 秒；25% 的回合從接近直立開始，其餘從垂下開始。

手臂角度限制
:   策略的指令最多到 ±125°；手臂碰到 ±135° 就當成撞到硬限位，扣 5 分並結束回合。實機韌體有對應的保護（見 [Step 4](step4-deploy.md#flash)）。

## Reward（作者的版本） { #reward .rip-learn }

$$
\begin{aligned}
r \;=\;& \underbrace{15}_{\text{存活偏移}} \;+\; \underbrace{5\cdot\mathbb{1}\!\left[\,|\theta|\le 15^\circ,\ |\dot\theta|\le 2\,\right]}_{\text{接住的直立}} \;+\; \underbrace{5\, e^{-\theta^2/0.3^2}\, e^{-\dot\alpha^2/1^2}}_{\text{靜止獎勵}} \\[6pt]
&-\; \underbrace{\left(\theta^2 + 0.001\,\dot\theta^2 + 0.5\,\alpha^2 + 0.005\,\dot\alpha^2 + 0.2\,a^2\right)}_{\text{Quanser 式二次成本}}
\end{aligned}
$$

α 是手臂角（rad）。括號內是 Quanser 式的二次成本；前面三項各有用途：

- **15（存活偏移）**：讓每一步的 reward 都是正的。如果每一步都是負的，策略會發現「趕快撞到限位、結束回合」反而划算。
- **5·𝟙[…]（接住的直立）**：只有「角度小且速度慢」才拿得到，快速甩過直立不算，避免策略靠一直繞圈來刷分。
- **靜止獎勵**：擺錘直立且手臂不動時最大，把策略從「用力平衡」推向「安靜平衡」。

作者網站「The transition contract」頁的 reward 是舊版，以程式 `policy/reward.py` 與 `train_sac.py` 的預設值為準。

## 選做：修改 reward { #edit-reward .rip-do }

reward 有三種改法：

1. **用工具改權重**：最常調的 7 個權重，`06_train_teacher` 會問，不用碰程式。
2. **改工具沒問到的係數**：公式裡其他現有的係數，要直接改檔案裡的數字。
3. **改寫公式**：改每一項怎麼算、加新的項，或整個重寫 `compute_reward()`。

### 用工具改權重

`06_train_teacher` 問 `要改 reward 權重嗎？` 時輸入 `y`，會逐項問下表的值（`[ ]` 裡是作者的值）。

| 工具上的名稱 | 在 reward 裡的位置 | 作者的值 | `train_sac.py` 選項 |
| --- | --- | --- | --- |
| 存活偏移 | 每步加上的常數（公式裡的 15） | 15 | `--reward-alive-offset` |
| 接住的直立獎勵 | \|θ\| ≤ 15° 且 \|θ̇\| ≤ 2 rad/s 時加上的值（公式裡的第一個 5） | 5 | `--reward-upright-alive-weight` |
| 靜止獎勵 | 靜止獎勵前面的係數（公式裡的第二個 5） | 5 | `--reward-stillness-bonus-weight` |
| 手臂角度² 懲罰 | α² 的係數 | 0.5 | `--reward-motor-pos-weight` |
| 手臂角速度² 懲罰 | α̇² 的係數 | 0.005 | `--reward-motor-vel-weight` |
| 手臂角速度變化² 懲罰 | 額外一項：係數 ×（這一步 α̇ − 上一步 α̇）²，作者的值是 0（關閉），所以不在上面的公式裡 | 0 | `--reward-motor-jerk-weight` |
| 動作變化² 懲罰 | 額外一項：係數 ×（這一步 a − 上一步 a）²，作者的值是 0（關閉） | 0 | `--reward-action-rate-weight` |

### 改工具沒問到的係數

`06_train_teacher` 只問上表 7 個權重。公式裡還有下面這些係數，工具不會問，要改的話得直接改檔案裡的數字：

| 要改的東西 | 作者的值 | 位置 |
| --- | --- | --- |
| θ² 的係數 | 1（寫死在公式裡） | `policy/reward.py` 的 `compute_reward()` |
| θ̇² 的係數 | 0.001 | `policy/pendulum_env.py`（模擬）和 `policy/real_env.py`（實機微調）的 `reward_pen_vel_weight` 預設值，兩個檔案都要改 |
| a² 的係數 | 0.2 | 同上，`reward_action_weight` |
| 靜止獎勵的寬度 0.3 rad、1 rad/s | 0.3、1.0 | 同上，`reward_stillness_sigma_theta_rad`、`reward_stillness_sigma_motor_vel_rad_s` |
| 接住的直立的條件 15°、2 rad/s | 0.2618 rad、2.0 | `policy/reward.py` 的 `RewardWeights`：`alive_theta_band`、`alive_pen_vel_limit` |

### 改寫公式

要改每一項怎麼算、加新的項，就要改 `policy/reward.py` 的 `compute_reward()`，模擬訓練和實機微調都呼叫這一個函式。也可以整個重寫，工具照樣能用，只要守住它的介面：

- 輸入固定是這 8 個（都是 keyword 參數）：`theta`（擺錘角，0 是直立，範圍 −π 到 π）、`pen_vel`（擺錘角速度）、`motor_pos`（手臂角）、`motor_vel`（手臂角速度）、`action`（這一步的動作，−1 到 1）、`prev_action`（上一步的動作）、`prev_motor_vel`（上一步的手臂角速度）、`weights`（`RewardWeights`，工具問的權重在這裡面；用不到可以不管）。單位都是 rad、rad/s。
- 回傳一個數字，代表這一步的 reward。
- 要用其他資訊（例如回合進行到第幾步），就要連 `pendulum_env.py` 和 `real_env.py` 呼叫 `compute_reward()` 的地方一起改。
- 手臂撞到 ±135° 硬限位時的 −5 和結束回合，是在兩個環境檔裡另外處理的，不在 `compute_reward()` 裡。
- 改壞了要還原成作者的版本：在 `rip-course` 資料夾執行 `git checkout policy/reward.py`。

**工具的配套**：

- **開跑前檢查**：`06_train_teacher` 和 `07_finetune` 開始前，會用約 8 萬組輸入呼叫 `compute_reward()`，涵蓋垂下、直立、快速轉圈、手臂到極限，以及下面說的實機特有輸入。出錯或回傳的不是有限數字（例如 `nan`、`inf`），工具會印出出錯的那組輸入並停止，不會開始訓練或動到機台。這個檢查只確認 reward 不會讓工具出錯；reward 設計得好不好，要看訓練結果。
- **保存副本**：每個階段、每一段微調結束後，工具把當時的 `policy/reward.py` 複製一份存成結果資料夾裡的 `reward_used.py`。`07_finetune` 開始時會比對現在的 `reward.py` 和起點模型的 `reward_used.py`，不同就印出提醒。

改了 reward 之後會連帶影響的地方：

- **記錄與沿用**：工具問的 7 個權重會寫進每個階段的 `runs/<名稱>_stageN/config.json`。從中斷處接續第 2、3 階段時，工具沿用前一階段 `config.json` 的權重。Step 2 的 `07_finetune` 會讀起點模型的 `config.json`，沿用同一組權重（見 [Step 2](step2-finetune.md#options)）。
- **改程式的部分不會寫進 `config.json`**：每次執行時用的是當時檔案裡的程式，當時的版本存在 `reward_used.py`。Step 1 訓練完再改程式，Step 2 微調時用的就是改過的版本，而這個版本沒有在模擬裡跑過。
- **replay buffer 裡新舊 reward 會混在一起**：buffer 存的是收集當時算好的 reward，不會重算。Step 2 每一段都會帶上前一段的 buffer，所以兩段之間改了 reward，buffer 裡就會同時有新舊兩種 reward。
- **鏡像資料增強假設 reward 左右對稱**：訓練和微調預設會把每筆資料存一份左右鏡像（擺錘角、手臂角、速度和動作全部變號），而且直接沿用同一個 reward。reward 不對稱時，鏡像那一筆的 reward 就不是它真正會拿到的值。
- **實機和模擬算 reward 的輸入不完全一樣**：
    - 模擬用 MuJoCo 的真實狀態；實機用感測器量到的值，速度會有雜訊和尖峰。
    - 實機算 reward 時，`prev_action` 已經被更新成這一步的動作，所以 `action − prev_action` 一律是 0；`prev_motor_vel` 一律是 0。作者的「動作變化²」「手臂角速度變化²」兩項在實機上因此都是 0。
- **實機微調少一項**：`real_env.py` 沒有「手臂角速度變化²」這一項，在 Step 2 一律是 0。
- **best_model 的挑法跟著變**：Step 1 每個階段的 `best_model.zip` 和 Step 2 的 `best_model.zip`，都是用 reward 總和挑的。改了 reward，「分數最高」指的就是新 reward 下的最高分，不同 reward 的分數不能直接比。
- **誠實指標不受影響**：balanced fraction、最長連續平衡、擺錘標準差等指標，不用 reward 計算，改 reward 前後可以直接比。

# Step 1：在模擬中訓練教師策略

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 筆電 CPU 約 25–60 分鐘</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台</span>
  <span class="rip-chip">:material-file-outline: 產出 v1_stage3/best_model.zip</span>
</div>

用 `curriculum_train.py` 跑完三階段課程，產出一支 256×256 的 SAC 教師策略。輸入是 Step 0 的 `sysid_params.json`，輸出是 `runs/v1_stage3/best_model.zip`。

## 操作步驟 { #run }

!!! tool "第一次訓練"

    1. 確認 Step 0 已經產生 `policy/sysid_params.json`。
    2. 筆電接上電源、不要闔上蓋子（睡眠會讓訓練中斷）。
    3. 在 `policy/` 裡執行：

        ```bash
        uv run python curriculum_train.py v1 --params-path sysid_params.json
        ```

        `v1` 是你取的名稱，會產生 `runs/v1_stage1/`、`v1_stage2/`、`v1_stage3/`。`--params-path` 告訴模擬要用哪一台機台的摩擦，**一定要指定你自己的檔**。

    4. 一開始會印出 `Curriculum config:` 設定 header，用眼睛確認（見[檢查點](#checkpoint)），然後開始訓練。
    5. 畫面會一直捲動 Stable-Baselines3 的英文統計表，`total_timesteps` 是目前步數，每階段 100,000 步。總時間看電腦速度，作者的機器約 25 分鐘、Apple M1 約 50 分鐘。
    6. 看到 `=== Curriculum complete. Final policy: runs/v1_stage3/best_model.zip ===` 才算跑完。接著自己跑[檢查點](#checkpoint)。

!!! tip "中途中斷了（關掉視窗、筆電睡眠）"

    看 `runs/` 裡哪幾個階段有 `best_model.zip`，從下一個階段接續，例如第 1 階段完成了：

    ```bash
    uv run python curriculum_train.py v1 --params-path sysid_params.json --start-stage 2
    ```

    第 2、3 階段會從前一階段的 `best_model.zip` 接續。**中斷時正在跑的那個階段要從頭再跑**（最多約 20 分鐘）。

??? cmd "curriculum_train.py 在做什麼"

    它是作者 `curriculum_train.sh` 的 Python 版（Windows 不能直接跑 bash），預設值跟原腳本一樣，只是 `--params-path` 必填、預設用 CPU。實際上是依序跑三次 `train_sac.py`，例如第 1 階段：

    ```bash
    uv run python train_sac.py --total-steps 100000 --device cpu \
        --control-freq 50 --max-accel-rad-s2 150 --action-mode velocity \
        --max-velocity-rad-s 3.5 --use-sde --obs-history-len 4 \
        --firmware-obs-model --mirror-augment --action-smooth-window 4 \
        --dr-obs-staleness-max 0.020 --params-path sysid_params.json \
        --reward-stillness-bonus-weight 5 --run-name v1_stage1 --seed 0
    ```

    第 2、3 階段再加上 `--domain-randomization`、延遲範圍，並用 `--resume` 接續前一階段的 `best_model.zip`。打開 `curriculum_train.py` 就看得到每個參數。用 CPU 是因為訓練的瓶頸是梯度更新，GPU 幫不上忙。

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

你用 `--params-path` 指定的 `sysid_params.json` 會記在 `runs/v1_stage1/config.json` 裡，之後的階段、蒸餾、模擬檢查都從這裡讀，不用每一步重新指定。每次建立模擬時，`pendulum_env.py` 的 `build_mjcf()` 會用下表的來源組出 MuJoCo 模型。

| 參數 | 來源 | 誰負責 |
| --- | --- | --- |
| 擺錘鉸鏈的黏滯與庫倫摩擦 | `sysid_params.json` | Step 0 量測，訓練時用 `--params-path` 指定 |
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

    1. 在 `policy/` 裡執行（macOS 用 `mjpython`，Windows 用 `python`）：

        ```bash
        uv run mjpython train_sac.py --eval runs/v1_stage3/best_model.zip
        ```

    2. MuJoCo 視窗打開，策略從垂下開始跑。看完關掉視窗。
    3. 設定（動作模式、控制頻率、sysid 檔）會從那支策略的 `config.json` 讀，不用重打。

<div class="grid cards" markdown>

-   :material-eye:{ .lg .middle } **要看什麼**

    ---

    從垂下開始，幾次擺動內甩上、接住不衝過頭；平衡時擺錘幾乎不動，手臂留在中間附近。

-   :material-compare:{ .lg .middle } **比較階段**

    ---

    把路徑換成 `runs/v1_stage1/best_model.zip` 再看一次，比較加入延遲與 DR 前後動作有什麼不同。

-   :material-mouse:{ .lg .middle } **操作**

    ---

    左鍵拖曳旋轉視角、滾輪縮放。點兩下擺錘選取後，按住 ++ctrl++ 用右鍵拖曳可以推它，看策略怎麼救回來。

-   :material-alert-circle-outline:{ .lg .middle } **別被騙了**

    ---

    模擬裡很穩不代表實機很穩，實機表現以 Step 2 的誠實指標為準。

</div>

## 檢查點 { #checkpoint }

訓練完自己跑下面三項。對任何一支策略都可以跑（之後 Step 2、3 也會用到），把路徑換掉就好：

```bash
uv run python analyze_symmetry.py runs/v1_stage3/best_model.zip
uv run python analyze_sim.py runs/v1_stage3/best_model.zip --episodes 20
uv run python analyze_sim.py runs/v1_stage3/best_model.zip --episodes 20 --no-firmware-obs-model
```

!!! checkpoint "參考門檻（作者的建議，由你判斷）"

    | 項目 | 看哪裡 | 參考門檻 |
    | --- | --- | --- |
    | 設定 header | 訓練開始時 `Curriculum config:` 底下的 4 行 | `mirror augmentation: ON`、`obs staleness DR: up to 0.02 s`、`rig sysid: sysid_params.json`、`control rate: 50 Hz, max accel: 150` 全部符合；不符就按 ++ctrl+c++ 停止，找助教 |
    | 對稱性 | `analyze_symmetry.py` 最後 `Self-start from the exact engage state` 那段 | 印出 `time to upright: … s`（能自己甩上）；`never reached upright` 就是不能 |
    | 敏感度關卡 | 兩次 `analyze_sim.py` 的 `balanced fraction:`（開著、關掉韌體量測模型） | 關掉後的 balanced fraction ≥ 0.7 |

敏感度關卡在問：策略學到的是控制本身，還是模擬量測的統計特徵？作者的校準：關掉後 ≥ 0.7 的策略部署全部成功，≤ 0.3 的四支全部失敗；兩者之間作者沒有資料。我們的建議：

| 關掉後的分數 | 建議 | 下一步 |
| --- | --- | --- |
| ≥ 0.7 | :material-check-circle:{ style="color: var(--rip-green)" } 多半可行 | 進 Step 2 |
| 0.3–0.7 | :material-alert:{ style="color: var(--rip-amber)" } 不確定 | 進 Step 2 **之前**，先照下面換一個 SEED 再訓練一支（不需要機台），兩支比較後用「關掉後」分數高的那支進 Step 2 |
| < 0.3，或不能自己甩上 | :material-close-circle:{ style="color: var(--rip-red)" } 多半會失敗 | 照下面換 SEED 重訓 |

### 決定重訓時：換一個 SEED { #reseed }

SEED 是亂數種子，決定網路初始權重與探索過程；同一套配方換一個 SEED，結果就可能不同。不需要機台。

!!! tool "操作步驟"

    1. 換一個名稱和 SEED：

        ```bash
        uv run python curriculum_train.py v2 --params-path sysid_params.json --seed 1
        ```

        **名稱不要沿用 v1**，不然會覆蓋掉舊的那一支。
    2. 跑完（約 25–60 分鐘）後對 `runs/v2_stage3/best_model.zip` 跑檢查點，和前一支比較。
    3. 還是不理想，再用 `v3`、SEED `2`。連續三支都低於 0.3 就找助教，通常是 Step 0 的問題。
    4. Step 2 選教師時，用你判斷最好的那一支（例如 `runs/v2_stage3/best_model.zip`）。

!!! warning "訓練和實機微調不要同時跑"

    訓練會吃滿 CPU，實機微調（`finetune_async.py`）要在同一台筆電上維持 50 Hz 控制。兩個同時跑會拖慢控制迴路，微調資料就不可靠。要多訓練幾支，趁不用機台的時間（例如晚上）一支接一支跑，**選好教師再開始 Step 2**。

    已經用某一支開始微調後，才發現另一支 SEED 分數比較高：只要現在的微調在 [Step 2 的 30 秒測試](step2-finetune.md#test)還在進步，就繼續用原本那支，不用換；如果 30 秒測試的 balanced fraction 一直 < 0.4，再換新的教師從 ft1 重跑。

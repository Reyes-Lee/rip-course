# Step 2：在實機上微調

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 30 回合約 6–11 分鐘，段數自己決定</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
  <span class="rip-chip">:material-chip: LowLevelServer</span>
  <span class="rip-chip">:material-file-outline: 產出 ftN/best_model.zip</span>
</div>

模擬訓練出來的策略，第一次上實機時通常平衡得不好。這一步用真實回合繼續跑 SAC，把模擬沒涵蓋到的動態（傳動細節、實際延遲分布、步進馬達行為）直接學進去。每段跑幾個回合、總共跑幾段，由你根據每一段的測試結果決定。

!!! todo "這一步要做的事"

    1. [燒錄 LowLevelServer](#flash)。
    2. [跑一段微調](#finetune)：執行 `07_finetune`。
    3. [接線測試](#test)：執行 `08_test_policy`，看結果決定要不要回到第 2 項再加一段。
    4. [進 Step 3 前：回歸測試](#regression)：決定不再微調之後做一次。

    標題前標「說明」的段落是原理說明，讀懂就好，不用操作。

!!! info "為什麼要微調"

    只在模擬裡訓練的策略，上實機通常甩得上去，但平衡不穩。微調是讓策略適應你這台機台。效果會因機台和每次訓練而不同，**段數多不保證比較穩**；要不要再加一段，看每一段 `08_test_policy` 的結果決定。

## 1. 燒錄 LowLevelServer { #flash .rip-do }

!!! tool "操作步驟"

    1. 用 Arduino IDE 上傳 `firmware/LowLevelServer`。
    2. 關掉序列埠監控。

這個模式下筆電透過 USB serial（2 Mbaud）讀狀態、送動作，Nano 只當低階伺服器。

## 2. 跑一段微調 { #finetune .rip-do }

!!! tool "第一次（ft1）"

    1. 確認 Nano 燒的是 `LowLevelServer`，Arduino IDE 的序列埠監控已關掉。
    2. 擺錘靜止垂下，機台旁邊不要有東西擋到手臂。
    3. 執行 `tools/07_finetune`。
    4. 畫面列出 `runs/` 裡所有教師（`*_stage3/best_model.zip`），輸入 [Step 1 檢查點](step1-train.md#checkpoint)通過的那一支的編號；只有一支就直接按 Enter。
    5. 畫面問這一段的設定（回合數、每回合秒數、要不要改進階設定），接著印出沿用的 reward 權重並問要不要改。每個設定的意思見 [07 會問的設定](#options)；直接按 Enter 是作者的預設值（50 回合、每回合 6 秒）。
    6. 工具開始跑，畫面會顯示目前第幾回合。結束時印出 `已存：runs/ft1/best_model.zip`，以及 best_model 來自第幾回合。
    7. 接著做 [3. 接線測試](#test)。

!!! tool "之後每一段（ft2、ft3…）"

    1. 再執行 `tools/07_finetune`。
    2. 工具從最新一段接續，帶上那一段的 replay buffer。畫面先問從那一段的 `best_model.zip` 還是 `last.zip` 接續（差別見 [best_model 和 last 是怎麼來的](#best-model)），直接按 Enter 是作者的 `best_model.zip`。
    3. 接著問這一段的設定和 reward 權重，直接按 Enter 是作者的預設值（30 回合、每回合 6 秒、reward 沿用上一段）。
    4. 跑完一樣接著做 [3. 接線測試](#test)。

    控制頻率、動作模式、平滑窗口都從 checkpoint 的 `config.json` 繼承，工具不會問。每一段實際用的設定存在 `runs/ftN/07_settings.json`。

!!! warning "前幾個回合要聽馬達"

    平順的嗡嗡聲正常；**嘶嘶或磨擦聲代表失步**。立刻在工具視窗按 ++ctrl+c++ 停止（這一段不會存檔），照[疑難排解](../troubleshooting.md)的「馬達嘶嘶聲」處理，再重新執行 `07_finetune`，它會重跑這一段。

- 每一段開始前，工具會先讓手臂在正中間小幅抖動約 4 秒，確認擺錘方向跟[方向標定](../prepare/hardware.md#direction)一致；不一致就停止，不會白跑一段。
- 每回合預設 6 秒；回合之間馬達斷電，最多等 15 秒讓擺錘自己停下來（停得快就提早開始）。用預設值時每回合約 11–21 秒：30 回合約 6–11 分鐘，50 回合約 9–18 分鐘。工具開始前會依你選的設定印出這一段的預估時間。
- 每回合會印一行 `steps=… mean_dt=…ms max_overrun=…ms violations=…`。`mean_dt` 應約 20 ms；`violations` 持續大於 0 代表控制週期被拖慢，先關掉其他程式（同步、備份、訓練）。
- 每段結束時工具會印出 `best_model.zip` 是第幾回合的模型，並刪掉中途的 replay buffer 快照（每份約 80 MB），只留下一段要用的 `replay_buffer.pkl`。
- 開始前工具會檢查 `policy/reward.py`（見 [Step 1 修改 reward](step1-train.md#edit-reward)）：`compute_reward()` 出錯或回傳非有限數字就停止，不會動到機台。也會比對現在的 `reward.py` 和起點模型的 `reward_used.py`，不同就印出提醒。結束後這一段用的 `reward.py` 存成 `runs/ftN/reward_used.py`。
- 控制迴路與 SAC 梯度更新跑在不同執行緒，所以訓練進行中，控制頻率仍然維持 50 Hz。
- Mirror augmentation 預設開啟，每筆真實資料同時存一份鏡像。

??? cmd "背後執行的指令"

    ```bash
    cd policy

    # 第一段（作者的預設值）
    uv run python finetune_async.py \
        --policy runs/v1_stage3/best_model.zip \
        --port <PORT> --episodes 50 --episode-length-s 6 \
        --learning-rate 0.0001 --gradient-steps 4 --eval-every 5 --run-name ft1

    # 接續段：帶上上一段的 replay buffer（--policy 可以換成 runs/ft1/last.zip）
    uv run python finetune_async.py \
        --policy runs/ft1/best_model.zip \
        --resume-buffer runs/ft1/replay_buffer.pkl \
        --port <PORT> --episodes 30 --episode-length-s 6 \
        --learning-rate 0.0001 --gradient-steps 4 --eval-every 5 --run-name ft2
    ```

    改 reward 權重時，工具會再加上 `--reward-alive-offset`、`--reward-motor-pos-weight` 等 6 個選項和 `--ignore-config-mismatch`。`finetune_async.py` 還有其他選項（例如 `--reset-settle-s`、`--deterministic`），工具沒有問，要用就自己在 `policy/` 執行指令，`uv run python finetune_async.py --help` 會列出全部。

## 3. 接線測試教師 { #test .rip-do }

!!! tool "每跑完一段微調就測一次"

    1. Nano 仍然是 `LowLevelServer`。等擺錘靜止垂下。
    2. 執行 `tools/08_test_policy`。
    3. 清單的預設是最新一段微調的 `best_model.zip`（例如 `ft2/best_model.zip`），直接按 Enter。同一段的 `checkpoint_epNNN.zip`、`last.zip` 也在清單裡。
    4. `測試秒數 [30]:` 直接按 Enter 是作者的 30 秒，也可以輸入其他秒數（5–600）。
    5. 策略會從垂下開始甩上，一直跑到測試秒數結束。不要碰機台。
    6. 結束時印出誠實指標，紀錄檔存在 `policy/recordings/ft2.npz`。同一個模型再測一次會存成 `ft2_2.npz`、`ft2_3.npz`…，不會蓋掉之前的紀錄。

??? cmd "背後執行的指令"

    ```bash
    cd policy
    uv run python run_policy.py \
        --policy runs/ft2/best_model.zip \
        --port <PORT> --duration-s 30 --log recordings/ft2.npz
    ```

測試秒數和指標的關係：

- balanced fraction 從按下開始的那一刻算起，包含甩上的時間。
- `longest balanced streak`（最長連續平衡）最多就是「測試秒數 − 甩上花的時間」。例如 30 秒的測試裡，擺錘第 7 秒才進入平衡、一直撐到結束，最長連續平衡最多只有約 23 秒：這個數字被測試長度限制住，看不出測試結束之後還能撐多久。
- 作者的[獨立執行參考值](step4-deploy.md#score)是用 300 秒量的。

看結束時印出的 **balanced fraction**：「|θ| ≤ 15° 且 |θ̇| ≤ 4 rad/s」的時間比例（作者在 2026-07 從 2 rad/s 放寬到 4 rad/s：平衡得好的策略也會有約 5 Hz 的小抖動，2 rad/s 會低估）。`verdict` 是 `NO SWING-UP` 代表擺錘從沒擺過水平、根本沒甩上去，先跑 `04_check_direction`；`SPINNING` 才是甩上去但一直繞圈接不住。這個定義故意不用策略自己的觀測，因為「是否直立」的檢查可以被一直繞圈騙過。

作者的建議如下，由你判斷：

| balanced fraction | 下一步 |
| --- | --- |
| ≥ 0.85 | :material-check-circle:{ style="color: var(--rip-green)" } 教師夠穩了。可以進 Step 3，也可以再加一段微調看看 |
| 0.4–0.85 | :material-trending-up:{ style="color: var(--rip-amber)" } 還在進步。再執行一次 `07_finetune`（從最新一段接續，預設 30 回合），然後再跑 `08_test_policy` |
| < 0.4 | :material-close-circle:{ style="color: var(--rip-red)" } 先停止微調，依序檢查硬體：燒 `LowLevelServer` 跑 `04_check_direction`（方向被修正的話，丟掉 `runs/ftN` 從教師重跑）；燒 `EncoderCheck` 跑 `02_check_encoder`；確認桌面水平、機台沒有被移動。都正常就燒 `LowLevelServer` 重跑 `05_sysid`，對照 [Step 0 檢查點](step0-sysid.md#checkpoint)。仍然沒問題就找助教，帶著 `policy/recordings/` 裡最新的 `.npz` |

## 4. 進 Step 3 前：回歸測試 { #regression .rip-do }

!!! tool "進 Step 3 前做一次（不需要機台）"

    1. 執行 `tools/13_check_sim`。
    2. 清單選最後一段微調（例如 `ft3/best_model.zip`）。
    3. 參考門檻與 [Step 1 檢查點](step1-train.md#checkpoint)相同：關掉韌體量測模型後的 balanced fraction ≥ 0.7 就進 Step 3。
    4. 如果掉到 0.7 以下，代表最後幾段微調讓策略變脆弱。對前一段（例如 `ft2`）再跑一次，用通過的那一段進 Step 3，並告訴助教。
    5. **教師在 Step 1 就落在 0.3–0.7 的情況**（例如教師本身只有 0.37）：每一段都可能到不了 0.7，這時門檻改成「不比教師自己的分數低超過 0.1」。用符合的段裡 [接線測試](#test) balanced fraction 最高的那段進 Step 3。每一段都比教師低超過 0.1，就用接線測試最好的那段進 Step 3，並把每段的分數一起給助教。

    實機的接線測試才是主要依據；回歸測試是用來抓「微調讓策略在模擬裡明顯變差」的情況。

## 07 會問的設定 { #options .rip-learn }

| 設定 | 預設 | 它改變什麼 |
| --- | --- | --- |
| 回合數 | ft1 50，之後 30 | 這一段在實機上跑幾個回合。每個回合的資料都會進 replay buffer，網路在回合進行中持續用 buffer 裡的資料更新。時間大約和回合數成正比 |
| 每回合秒數 | 6 | 每個回合從擺錘垂下開始，跑滿這個秒數就結束。回合內扣掉甩上的時間，剩下的才是平衡中的資料，所以這個值決定真實資料裡有多長的連續平衡片段。模擬訓練（Step 1）的回合是 8 秒，而且 25% 的回合從接近直立開始；實機微調的回合一律從垂下開始。評估回合的分數是整個回合 reward 的總和，所以改了秒數之後，分數不能和其他秒數的段直接比 |
| 從哪個模型接續（ft2 起） | `best_model.zip` | 這一段的網路從哪一組權重開始。兩者的差別見[下一節](#best-model)。replay buffer 一律帶上上一段的完整 buffer，跟這個選擇無關 |
| 學習率（進階） | 0.0001 | 每次梯度更新的步幅。模擬訓練用 0.0003。作者在 `finetune_async.py --help` 裡說明微調刻意調低的原因：真實資料很少時，用全速的梯度更新，是把模擬訓練好的策略弄壞的典型原因 |
| 每次更新的梯度步數（進階） | 4 | 學習執行緒每輪做幾次梯度更新。越多代表每筆真實資料被用得越多次，電腦的負擔也越重。控制迴路在另一個執行緒，不受影響；但電腦太忙時，每回合那一行的 `violations=` 會大於 0 |
| 每幾回合做一次評估回合（進階） | 5 | 評估回合用不隨機（deterministic）的動作跑，用來挑 `best_model.zip`。評估回合的資料一樣會進 buffer 和訓練，但它沒有探索用的隨機性 |
| reward 權重 | 沿用起點模型的 `config.json` | 工具先印出起點模型訓練時用的 6 個權重（[Step 1 修改 reward](step1-train.md#edit-reward) 那 7 個去掉實機不支援的「手臂角速度變化²」）。選擇要改時，工具會加上 `--ignore-config-mismatch`，因為 `finetune_async.py` 預設在權重和起點模型不同時停下來。這一段用的權重會寫進 `runs/ftN/config.json`，下一段再沿用。replay buffer 裡已經存的資料，reward 是收集當時的權重算的，不會重算；改了權重之後，buffer 裡新舊兩種 reward 會混在一起 |

## best_model 和 last 是怎麼來的 { #best-model .rip-learn }

每一段微調結束後，`runs/ftN/` 裡會有好幾個模型檔，都是同一個網路在不同時間點的權重：

| 檔案 | 是哪個時間點 |
| --- | --- |
| `best_model.zip` | 這一段裡**評估回合分數最高**的那個評估回合結束時 |
| `checkpoint_ep010.zip`、`checkpoint_ep020.zip`… | 每 10 回合結束時 |
| `last.zip` | 這一段最後一回合結束時 |

- 網路在整段裡持續用 replay buffer 的全部資料更新，所以每個時間點的權重都學過「到那時為止」的所有資料。`best_model.zip` 不是只用某一個回合訓練出來的，而是**從這些時間點裡挑出一個**。
- 挑的依據只有評估回合的分數：每回合 reward 的總和。用預設值時，一段裡有 10 個評估回合，每個只跑 6 秒、從垂下開始，所以分數包含甩上的過程，量不到 6 秒以後的平衡。每一段重新開始比，不會跟前一段的分數比。
- 舉例：ft1 跑 50 回合、每 5 回合做一次評估，共 10 個評估回合。如果分數最高的是第 3 個評估回合（第 15 回合），`best_model.zip` 就是第 15 回合結束時的模型，第 16–50 回合的更新不包含在裡面。工具結束時印出的「best_model.zip 是第幾回合」就是這個資訊。
- 下一段從哪個檔接續，就是從那一組權重繼續訓練。作者在 `finetune_async.py` 開頭的使用說明裡，接續的範例用的是 `last.zip`；課程工具的預設則是 `best_model.zip`。
- `08_test_policy` 的清單裡，每一段的 `best_model.zip`、各個 `checkpoint_epNNN.zip`、`last.zip` 都可以選來測。

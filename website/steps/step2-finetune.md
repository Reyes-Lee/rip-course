# Step 2：在實機上微調

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 每段 30 回合約 6 分鐘，共 2–4 段</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
  <span class="rip-chip">:material-chip: LowLevelServer</span>
  <span class="rip-chip">:material-file-outline: 產出 ftN/best_model.zip</span>
</div>

模擬訓練的策略第一次上實機不會平衡得好。這一步用 30–90 個真實回合繼續跑 SAC，把模擬沒涵蓋到的動態（傳動細節、實際延遲分布、步進馬達行為）直接學進去。

!!! danger "這是整個流程最不能省的一步"

    作者微調後，平衡時擺錘角度標準差降到 1.2–1.9°；微調越多段越穩，見下方「要微調多久」。

## 2-1 燒錄 LowLevelServer { #flash }

用 Arduino IDE 上傳 `firmware/LowLevelServer`，關掉序列埠監控。這個模式下筆電透過 USB serial（2 Mbaud）讀狀態、送動作，Nano 只當低階伺服器。

## 2-2 跑非同步微調 { #finetune }

!!! tool "第一次（ft1，50 回合）"

    1. 確認 Nano 燒的是 `LowLevelServer`，Arduino IDE 的序列埠監控已關掉。
    2. 擺錘靜止垂下，機台旁邊不要有東西擋到手臂。
    3. 執行 `tools/07_finetune`。
    4. 畫面列出 `runs/` 裡所有教師（`*_stage3/best_model.zip`），輸入 [Step 1 檢查點](step1-train.md#checkpoint)通過的那一支的編號；只有一支就直接按 Enter。
    5. 工具開始跑，畫面會顯示目前第幾回合。結束時印出 `已存：runs/ft1/best_model.zip`。
    6. 接著做 [2-3 測試](#test)。

!!! tool "之後每一段（ft2、ft3…，各 30 回合）"

    1. 再執行 `tools/07_finetune` 就好。
    2. 工具會自動從最新一段接續（帶上上一段的 replay buffer），不用選。
    3. 跑完一樣接著做 [2-3 測試](#test)。

    控制頻率、動作模式、reward、平滑窗口都從 checkpoint 的 `config.json` 繼承。

!!! warning "前幾個回合要聽馬達"

    平順的嗡嗡聲正常；**嘶嘶或磨擦聲代表失步**。立刻在工具視窗按 ++ctrl+c++ 停止（這一段不會存檔），照[疑難排解](../troubleshooting.md)的「馬達嘶嘶聲」處理，再重新執行 `07_finetune`，它會重跑這一段。

- 每一段開始前，工具會先讓手臂在正中間小幅抖動約 4 秒，確認擺錘方向跟[方向標定](../prepare/hardware.md#direction)一致；不一致就停止，不會白跑一段。
- 每回合 6 秒；回合之間馬達斷電 15 秒，讓擺錘自己停下來。
- 控制迴路與 SAC 梯度更新跑在不同執行緒，所以訓練中控制頻率仍嚴格是 50 Hz。
- Mirror augmentation 預設開啟，每筆真實資料同時存一份鏡像。

??? cmd "背後執行的指令"

    ```bash
    cd policy

    # 第一段：50 回合
    uv run python finetune_async.py \
        --policy runs/v1_stage3/best_model.zip \
        --port <PORT> --episodes 50 --run-name ft1

    # 接續段：帶上上一段的 replay buffer
    uv run python finetune_async.py \
        --policy runs/ft1/best_model.zip \
        --resume-buffer runs/ft1/replay_buffer.pkl \
        --port <PORT> --episodes 30 --run-name ft2
    ```

## 2-3 用 30 秒測試教師 { #test }

!!! tool "每跑完一段微調就測一次"

    1. Nano 仍然是 `LowLevelServer`。等擺錘靜止垂下。
    2. 執行 `tools/08_test_policy`。
    3. 清單的預設是最新一段微調（例如 `ft2/best_model.zip`），直接按 Enter。
    4. 策略會從垂下開始甩上、平衡 30 秒。不要碰機台。
    5. 結束時印出誠實指標，紀錄檔存在 `policy/recordings/ft2.npz`。照下表決定下一步。

??? cmd "背後執行的指令"

    ```bash
    cd policy
    uv run python run_policy.py \
        --policy runs/ft2/best_model.zip \
        --port <PORT> --duration-s 30 --log recordings/ft2.npz
    ```

看結束時印出的 **balanced fraction**：「|θ| ≤ 15° 且 |θ̇| ≤ 2 rad/s」的時間比例。這個定義故意不用策略自己的觀測，因為「是否直立」的檢查可以被一直繞圈騙過。

作者的建議如下，由你判斷：

| balanced fraction | 下一步 |
| --- | --- |
| ≥ 0.85 | :material-check-circle:{ style="color: var(--rip-green)" } 教師夠穩了。仍照[下一節](#how-long)決定要不要再加一段，然後進 Step 3 |
| 0.4–0.85 | :material-trending-up:{ style="color: var(--rip-amber)" } 還在進步。再執行一次 `07_finetune`（自動加一段 30 回合），然後再跑 `08_test_policy` |
| < 0.4 | :material-close-circle:{ style="color: var(--rip-red)" } 先停止微調，依序檢查硬體：燒 `LowLevelServer` 跑 `04_check_direction`（方向被修正的話，丟掉 `runs/ftN` 從教師重跑）；燒 `EncoderCheck` 跑 `02_check_encoder`；確認桌面水平、機台沒有被移動。都正常就燒 `LowLevelServer` 重跑 `05_sysid`，對照 [Step 0 檢查點](step0-sysid.md#checkpoint)。仍然沒問題就找助教，帶著 `policy/recordings/` 裡最新的 `.npz` |

## 要微調多久？比 eval 曲線看起來的更久 { #how-long }

作者的量測：eval reward 很早就持平，實機平衡品質卻還在明顯變好。

| 驅動板／微調回合 | 擺錘標準差 | 手臂速度 RMS（rad/s） | \|動作\| 平均 | balanced |
| --- | --- | --- | --- | --- |
| DRV8825／30 | 6.74° | 2.98 | 0.623 | 0.972 |
| DRV8825／60 | 3.23° | 1.43 | 0.313 | 1.000 |
| DRV8825／90 | 1.83° | 0.86 | 0.275 | 1.000 |
| TMC2209／30 | 1.62° | 0.76 | 0.236 | 0.993 |
| TMC2209／60 | 1.23° | 0.58 | 0.177 | 1.000 |

!!! checkpoint "什麼時候停（建議）"

    每加一段就跑一次 `08_test_policy`，把 balanced fraction 與擺錘標準差記下來。只要其中一個還在變好，就再加一段；**連續兩段都沒有變好才停**。

    就算工具印出 `best_model 未更新` 也要照這個規則加，因為 Step 3 的蒸餾會用到 replay buffer 裡所有的真實狀態。

### 停止後：回歸測試 { #regression }

!!! tool "進 Step 3 前做一次（不需要機台）"

    1. 執行 `tools/13_check_sim`。
    2. 清單選最後一段微調（例如 `ft3/best_model.zip`）。
    3. 參考門檻與 [Step 1 檢查點](step1-train.md#checkpoint)相同：關掉韌體量測模型後的 balanced fraction ≥ 0.7 就進 Step 3。
    4. 如果掉到 0.7 以下，代表最後幾段微調讓策略變脆弱。對前一段（例如 `ft2`）再跑一次，用通過的那一段進 Step 3，並告訴助教。

# Step 2：在實機上微調

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 每段 30 回合約 6–11 分鐘，段數自己決定</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
  <span class="rip-chip">:material-chip: LowLevelServer</span>
  <span class="rip-chip">:material-file-outline: 產出 ftN/best_model.zip</span>
</div>

模擬訓練的策略第一次上實機不會平衡得好。這一步用 30–90 個真實回合繼續跑 SAC，把模擬沒涵蓋到的動態（傳動細節、實際延遲分布、步進馬達行為）直接學進去。

!!! danger "這是整個流程最不能省的一步"

    作者微調後，平衡時擺錘角度標準差降到 1.2–1.9°；微調越多段越穩，見下方「要微調多久」。

## 2-1 燒錄 LowLevelServer { #flash }

用 Arduino IDE 上傳 `firmware/LowLevelServer`，關掉序列埠監控。這個模式下筆電透過 USB serial（2 Mbaud）讀狀態、送動作，Nano 只當低階伺服器。這塊 Nano 要做過[方向標定](../prepare/hardware.md#direction)：沒標定的 `LowLevelServer` 會照 AS5600 原本的方向跑，**不會提醒你**。

## 2-2 微調之前：先直接上機，看 sim2real gap { #zero-shot }

先不微調，把 Step 1 的教師直接放到實機上跑 30 秒，看看模擬裡學到的東西搬到實機會變成什麼樣子。

!!! tool "零樣本測試"

    1. 擺錘靜止垂下，機台旁邊不要有東西擋到手臂。
    2. 在 `policy/` 裡執行（`<PORT>` 見[工具與指令](../prepare/tools.md#cli)）：

        ```bash
        uv run python run_policy.py --policy runs/v1_stage3/best_model.zip \
            --port <PORT> --duration-s 30 --log recordings/v1_stage3_zeroshot.npz
        ```

    3. 結束時印出的 `Honest balance` 那一行記下來（balanced fraction 的定義見 [2-4](#test)）。
    4. 把同一段紀錄丟回模擬重播：實機每一步送出的動作，原封不動在模擬裡再跑一次，比較兩邊的手臂與擺錘軌跡。

        ```bash
        uv run python sim_vs_real.py recordings/v1_stage3_zeroshot.npz \
            --params-path sysid_params.json --out recordings/v1_stage3_zeroshot_cmp.png
        ```

    5. 打開 `v1_stage3_zeroshot_cmp.png`。上圖是手臂、中圖是擺錘：藍色實機、紅色模擬。

??? question "怎麼看 sim_vs_real 的結果"

    - 擺錘是混沌系統，開迴路重播一定會越來越分開，所以只看**前 1–3 秒**：畫面會印 `first 1s / 2s / 3s` 的 rmse。
    - 手臂差很多、擺錘差不多：步進馬達沒有照指令走（失步、延遲）。
    - 手臂差不多、擺錘的擺幅或週期不同：擺錘的模型（摩擦、慣量）不準，回 Step 0 檢查。
    - 手臂往右推時，實機和模擬的擺錘往**相反**方向反應：擺錘角度的正負號反了，做[方向標定](../prepare/hardware.md#direction)。
    - `motor cross-corr lag` 是實機比模擬慢幾步，對照 Step 1 訓練時的延遲 DR 範圍（20–35 ms）。

    `--action-lag-tau`、`--firmware-model` 可以加進模擬重播，看哪一個讓兩邊比較接近。

## 2-3 跑非同步微調 { #finetune }

!!! tool "第一段（ft1）"

    1. Nano 是 `LowLevelServer`，序列埠監控已關掉；擺錘靜止垂下。
    2. 從你選的教師開始，跑 50 回合：

        ```bash
        uv run python finetune_async.py --policy runs/v1_stage3/best_model.zip \
            --port <PORT> --episodes 50 --run-name ft1 --params-path sysid_params.json
        ```

    3. 跑完後 `runs/ft1/` 裡有 `best_model.zip`（微調後的教師）和 `replay_buffer.pkl`（這一段所有的真實資料）。
    4. 接著做 [2-4 測試](#test)。

!!! tool "之後每一段"

    從上一段的 `best_model.zip` 接續，並用 `--resume-buffer` 把上一段的真實資料帶過來（不帶的話，之前的回合就白跑了）。例如第二段：

    ```bash
    uv run python finetune_async.py --policy runs/ft1/best_model.zip \
        --resume-buffer runs/ft1/replay_buffer.pkl \
        --port <PORT> --episodes 30 --run-name ft2 --params-path sysid_params.json
    ```

    第三段就把 `ft1` 換成 `ft2`、`--run-name` 換成 `ft3`，依此類推。每段跑完一樣做 [2-4 測試](#test)。

    控制頻率、動作模式、reward、平滑窗口都從 checkpoint 的 `config.json` 繼承，不用重打。`--params-path` 在微調時只是記錄用（實機就是被控體），Step 3 蒸餾會讀它。

!!! warning "前幾個回合要聽馬達"

    平順的嗡嗡聲正常；**嘶嘶或磨擦聲代表失步**。立刻按 ++ctrl+c++ 停止，照[疑難排解](../troubleshooting.md)的「馬達嘶嘶聲」處理，再用同一個 `--run-name` 重跑這一段。

- 每回合 6 秒；回合之間馬達斷電，最多等 15 秒讓擺錘自己停下來（停得快就提早開始）。所以每回合約 11–21 秒：30 回合約 6–11 分鐘，50 回合約 9–18 分鐘。
- 每回合會印一行 `steps=… mean_dt=…ms max_overrun=…ms violations=…`。`mean_dt` 應約 20 ms；`violations` 持續大於 0 代表控制週期被拖慢，先關掉其他程式（同步、備份、訓練）。
- 每 5 回合會做一次評估，分數變好才印 `new best deterministic eval (…) → best_model.zip`。
- `runs/ftN/` 裡每 10 回合存一份 `replay_buffer_ep010.pkl`…（每份約 80 MB），下一段只需要最後的 `replay_buffer.pkl`，硬碟不夠可以刪掉快照。
- 控制迴路與 SAC 梯度更新跑在不同執行緒，所以訓練中控制頻率仍嚴格是 50 Hz。
- Mirror augmentation 預設開啟，每筆真實資料同時存一份鏡像。

## 2-4 用 30 秒測試教師 { #test }

!!! tool "每跑完一段微調就測一次"

    1. Nano 仍然是 `LowLevelServer`。等擺錘靜止垂下。
    2. 測剛跑完的那一段，例如 `ft2`：

        ```bash
        uv run python run_policy.py --policy runs/ft2/best_model.zip \
            --port <PORT> --duration-s 30 --log recordings/ft2.npz
        ```

    3. 策略會從垂下開始甩上、平衡 30 秒。不要碰機台。
    4. 結束時印出誠實指標，紀錄檔存在 `policy/recordings/ft2.npz`。

看結束時印出的 **balanced fraction**：「|θ| ≤ 15° 且 |θ̇| ≤ 4 rad/s」的時間比例（作者在 2026-07 從 2 rad/s 放寬到 4 rad/s：平衡得好的策略也會有約 5 Hz 的小抖動，2 rad/s 會低估）。`verdict` 是 `NO SWING-UP` 代表擺錘從沒擺過水平、根本沒甩上去，先檢查[方向標定](../prepare/hardware.md#direction)；`SPINNING` 才是甩上去但一直繞圈接不住。這個定義故意不用策略自己的觀測，因為「是否直立」的檢查可以被一直繞圈騙過。

作者的建議：

| balanced fraction | 下一步 |
| --- | --- |
| ≥ 0.85 | :material-check-circle:{ style="color: var(--rip-green)" } 教師夠穩，可以進 Step 3。要不要再加一段，看[下一節](#how-long) |
| 0.4–0.85 | :material-trending-up:{ style="color: var(--rip-amber)" } 通常再加一段還會進步 |
| < 0.4 | :material-close-circle:{ style="color: var(--rip-red)" } 先停止微調，找原因再繼續：重做 sysid、用 `sim_vs_real.py` 重播這段紀錄（見 [2-2](#zero-shot)）、檢查傳輸延遲的假設。硬體方面：`02_check_encoder`、`04_check_direction`、桌面水平。都查過還是不行就找助教，帶著 `policy/recordings/` 裡最新的 `.npz` |

## 要微調多久？比 eval 曲線看起來的更久 { #how-long }

**要跑幾段由你決定。** 作者的量測：eval reward 很早就持平，實機平衡品質卻還在明顯變好。

| 驅動板／微調回合 | 擺錘標準差 | 手臂速度 RMS（rad/s） | \|動作\| 平均 | balanced |
| --- | --- | --- | --- | --- |
| DRV8825／30 | 6.74° | 2.98 | 0.623 | 0.972 |
| DRV8825／60 | 3.23° | 1.43 | 0.313 | 1.000 |
| DRV8825／90 | 1.83° | 0.86 | 0.275 | 1.000 |
| TMC2209／30 | 1.62° | 0.76 | 0.236 | 0.993 |
| TMC2209／60 | 1.23° | 0.58 | 0.177 | 1.000 |

作者的經驗：

- 判斷一段有沒有用，看實機測試，不看 eval reward。測試越來越「平靜」（擺錘標準差、手臂速度、動作大小變小）就值得再加。
- `best_model` 不再更新之後，繼續加段還是有用：Step 3 蒸餾時，教師會對 replay buffer 裡**所有**的真實狀態重新標動作，所以多跑的回合會變成學生看過的狀態。
- 記錄每一段的數字（balanced fraction、擺錘標準差、手臂速度），自己決定什麼時候停，並說得出理由。

## 停止後：回歸檢查 { #regression }

!!! tool "進 Step 3 前做一次（不需要機台）"

    對最後一段微調再跑一次 Step 1 的敏感度關卡，例如 `ft3`：

    ```bash
    uv run python analyze_sim.py runs/ft3/best_model.zip --episodes 20
    uv run python analyze_sim.py runs/ft3/best_model.zip --episodes 20 --no-firmware-obs-model
    ```

    作者量過的每一條線，微調都沒有讓「關掉後」的分數掉下來，所以這只是便宜的保險。如果關掉後明顯比教師在 [Step 1](step1-train.md#checkpoint) 時低很多，代表這幾段微調讓策略去依賴量測的統計特徵，蒸餾它會浪費時間：改用前一段，並告訴助教。

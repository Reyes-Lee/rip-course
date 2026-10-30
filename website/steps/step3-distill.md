# Step 3：蒸餾成小網路

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 3 分鐘</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台（選做的接線測試要）</span>
  <span class="rip-chip">:material-file-outline: 產出 distill_h16_dagger_dev/student.pt</span>
</div>

256×256 的教師塞不進 Nano。這一步用「模仿學習」把它壓成 16 個隱藏神經元的學生網路。

## 操作步驟 { #run }

!!! tool "蒸餾"

    1. 選要蒸餾的那一段微調（通常是最後一段，例如 `ft3`）。在 `policy/` 裡執行：

        ```bash
        uv run python distill_student.py ft3
        ```

    2. 約 3 分鐘，依序做 1/3 行為克隆、2/3 DAgger、3/3 學生在模擬裡的分數。`runs/ft3/replay_buffer.pkl` 存在就會自動拿來用。
    3. 學生存在 `runs/ft3/distill_h16_dagger_dev/student.pt`。
    4. 結束時它會提醒你拿教師的分數來比，照著跑一次（見[檢查點](#checkpoint)）：

        ```bash
        uv run python analyze_sim.py runs/ft3/best_model.zip
        ```

??? cmd "distill_student.py 在做什麼"

    它是作者 `distill_student.sh` 的 Python 版（Windows 不能直接跑 bash），預設值一樣。等同於：

    ```bash
    uv run python distill.py --teacher runs/ft3/best_model.zip \
        --buffer runs/ft3/replay_buffer.pkl --out-dir runs/ft3/distill_h16_aug \
        --hidden 16 --epochs 800 --seed 0
    uv run python dagger_distill.py --teacher runs/ft3/best_model.zip \
        --bc-dir runs/ft3/distill_h16_aug --out-dir runs/ft3/distill_h16_dagger_dev \
        --transport device --rounds 5 --steps-per-round 40000 --seed 0
    uv run python analyze_sim.py runs/ft3/distill_h16_dagger_dev/student.pt --transport device
    ```

    `--seed` 不是 0 時，資料夾名稱會多一個後綴，例如 `distill_h16_dagger_dev_s1`。

## 它在做什麼 { #what }

<div class="rip-flow" markdown>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">教師 256×256<small>Step 2 微調完的 best_model.zip</small></div>
  <div class="rip-flow__edge" markdown="span">對 replay buffer 的每個狀態標動作<span>BC</span></div>
  <div class="rip-flow__node" markdown="span">學生 H=16（第 0 輪）<small>只模仿過教師看過的狀態</small></div>
  <div class="rip-flow__edge rip-flow__edge--loop" markdown="span">學生自己開 → 收集走到的狀態 → 請教師標動作 → 重新訓練，重複數輪<span>DAgger</span></div>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">DAgger 學生<small>student.pt</small></div>
</div>

1. **行為克隆（BC）**：用教師對 replay buffer 裡每個狀態的動作當標籤，做監督式學習。
2. **DAgger**：讓學生自己開，收集學生會走到的狀態，再請教師標籤、重新訓練。rollout 在「Nano 獨立執行」的傳輸條件下進行（`--transport device`）。

??? question "為什麼只做 BC 不夠？"

    倒單擺在直立附近是不穩定的，學生一點點誤差就會走到教師沒示範過的狀態（covariate shift）。作者實測 BC 學生的閉迴路分數只有 0.12。

??? question "為什麼不直接用 RL 訓練小網路？"

    作者試過兩次，小網路在模擬與接線微調都很好，一旦獨立執行就只剩約 0.24。RL 容易學出利用特定時序的銳利控制器，傳輸條件一變就壞；蒸餾學生輕微的欠擬合反而像降低增益，換來強健性。

??? question "為什麼是 16 個神經元？"

    Nano 沒有浮點運算單元，每次乘加約 19 µs。H=16 約 12 ms，放得進 50 Hz 的 20 ms 週期；H=32 要 35–40 ms，迴路會掉到 25 Hz，平衡策略會變成繞圈。

## 檢查點 { #checkpoint }

下面兩項由你判斷。敏感度關卡跟 Step 1 一樣跑兩次 `analyze_sim.py`，路徑換成學生、加上 `--transport device`：

```bash
uv run python analyze_sim.py runs/ft3/distill_h16_dagger_dev/student.pt --transport device --episodes 20
uv run python analyze_sim.py runs/ft3/distill_h16_dagger_dev/student.pt --transport device --episodes 20 --no-firmware-obs-model
```

!!! checkpoint "參考門檻（由你判斷）"

    | 項目 | 參考門檻 |
    | --- | --- |
    | DAgger gate | DAgger 每一輪印的 `gate`（最後 `best gate`）接近教師自己的 `balanced fraction`（上面第 4 步）。作者沒有給數字，只說「大約到教師的 gate 或更好就是好的」 |
    | 敏感度關卡 | 同 Step 1：關掉韌體量測模型後的 balanced fraction ≥ 0.7 |

DAgger gate 要跟教師比、不跟絕對門檻比，是因為模擬會系統性低估實機微調過的策略：作者的冠軍在模擬 gate 只有 0.655，實機是 0.996。

!!! tool "判斷要重做時"

    1. 同一段微調換一個 SEED：`uv run python distill_student.py ft3 --seed 1`。
    2. 換兩個 SEED 都明顯低於教師就找助教。

## （選做）燒進 Nano 前先接線測學生 { #tethered }

!!! tool "接線測試學生"

    1. Nano 燒 `LowLevelServer`，等擺錘靜止垂下。
    2. 用 Step 2 的 `run_policy.py`，策略換成學生：

        ```bash
        uv run python run_policy.py --policy runs/ft3/distill_h16_dagger_dev/student.pt \
            --port <PORT> --duration-s 30 --log recordings/ft3_student.npz
        ```

    3. 學生是為獨立執行最佳化的，接線分數略低於教師是正常的。

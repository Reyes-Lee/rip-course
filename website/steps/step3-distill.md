# Step 3：蒸餾成小網路

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 3 分鐘</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台（選做的接線測試要）</span>
  <span class="rip-chip">:material-file-outline: 產出 distill_h16_dagger_dev/student.pt</span>
</div>

256×256 的教師網路太大，放不進 Nano。這一步用「模仿學習」把它縮小成只有 16 個隱藏神經元的學生網路。

!!! todo "這一步要做的事"

    1. [蒸餾](#run)：執行 `09_distill`。
    2. [看檢查點](#checkpoint)：學生和教師的分數接近嗎？需要時換 SEED 重做。
    3. （選做）[燒進 Nano 前先接線測學生](#tethered)。

    標題前標「說明」的段落是原理說明，讀懂就好，不用操作。

## 1. 蒸餾 { #run .rip-do }

!!! tool "蒸餾"

    1. 執行 `tools/09_distill`。
    2. 清單的預設是最後一段微調（例如 `ft3`），直接按 Enter。如果 [Step 2 的回歸測試](step2-finetune.md#regression)改用了前一段，就輸入那一段的編號。
    3. `SEED [0]:` 直接按 Enter。
    4. 接著問教師用那一段的 `best_model.zip` 還是 `last.zip`（差別見 [Step 2](step2-finetune.md#best-model)），以及要不要改進階設定。直接按 Enter 是作者的預設值（`best_model.zip`、不改）。
    5. 約 3 分鐘後，工具印出結果表（見[檢查點](#checkpoint)）。學生存在 `runs/ftN/distill_h16_dagger_dev/student.pt`。

??? cmd "背後執行的指令"

    `09_distill` 是作者 repo 裡 [`distill_student.sh`](https://github.com/ferrolho/rotary-inverted-pendulum/blob/main/policy/distill_student.sh) 的 Python 版（課程 repo 沒有附這支 `.sh`），以 `ft3` 為例等同於：

    ```bash
    cd policy
    uv run python distill.py --teacher runs/ft3/best_model.zip \
        --buffer runs/ft3/replay_buffer.pkl --out-dir runs/ft3/distill_h16_aug \
        --hidden 16 --epochs 800 --seed 0
    uv run python dagger_distill.py --teacher runs/ft3/best_model.zip \
        --bc-dir runs/ft3/distill_h16_aug --out-dir runs/ft3/distill_h16_dagger_dev \
        --transport device --rounds 5 --steps-per-round 40000 --seed 0
    uv run python analyze_sim.py runs/ft3/distill_h16_dagger_dev/student.pt --transport device
    uv run python analyze_sim.py runs/ft3/best_model.zip
    ```

    設定不是預設值時，資料夾名稱會多一個後綴，不同設定的結果不會互相覆蓋：

    | 設定 | 預設 | 後綴例子 |
    | --- | --- | --- |
    | 教師模型 | `best_model.zip` | `last.zip` → `_last` |
    | SEED | 0 | 1 → `_s1` |
    | 行為克隆 epoch 數（進階） | 800 | 400 → `_e400` |
    | DAgger 輪數 × 每輪步數（進階） | 5 × 40000 | 3 × 40000 → `_r3x40000`（只加在 DAgger 的資料夾） |

    - 教師模型：蒸餾時當「老師」的那組權重，學生學的是它在每個狀態輸出的動作。資料集裡的真實狀態一律來自那一段的 `replay_buffer.pkl`，跟選哪個教師模型無關。
    - SEED：決定網路初始權重和資料打亂的順序。同樣設定換 SEED，結果會有差異。
    - 行為克隆 epoch 數：學生把整個資料集看過幾遍。
    - DAgger 輪數：每一輪讓學生自己在模擬裡跑，把它走到的狀態交給教師標上動作、加進資料集再訓練。每輪結束都會用模擬分數（gate）檢查，只保留分數最好的那一輪；0 輪就是只用行為克隆的結果。每輪步數是每輪讓學生跑幾步來收集新狀態。

## 2. 看檢查點 { #checkpoint .rip-do }

`09_distill` 結束時會印出下面兩項的數字，由你判斷；之後要重跑敏感度關卡，可以執行 `tools/13_check_sim` 選 `student.pt`。

!!! checkpoint "參考門檻（由你判斷）"

    | 項目 | 參考門檻 |
    | --- | --- |
    | DAgger gate | 學生的 gate 接近教師自己的 gate（工具並排印出兩個數字）。作者沒有給數字，我們建議相差 0.05 以內 |
    | 敏感度關卡 | 同 Step 1：關掉韌體量測模型後的 balanced fraction ≥ 0.7 |

DAgger gate 要跟教師比、不跟絕對門檻比，是因為模擬會系統性低估實機微調過的策略：作者的冠軍在模擬 gate 只有 0.655，實機是 0.996。

!!! tool "判斷要重做時"

    1. 再執行 `tools/09_distill`。
    2. 選同一段微調。
    3. `SEED [0]:` 輸入 `1`。
    4. 換了幾個 SEED 都明顯低於教師，可以在 `09_distill` 的進階設定增加行為克隆 epoch 數或 DAgger 輪數，或回 Step 2 改用另一段微調當教師。

## 3. （選做）燒進 Nano 前先接線測學生 { #tethered .rip-do }

!!! tool "接線測試學生"

    1. Nano 燒 `LowLevelServer`，等擺錘靜止垂下。
    2. 執行 `tools/08_test_policy`。
    3. 清單輸入 `ftN/distill_h16_dagger_dev/student.pt` 那一個的編號。
    4. `測試秒數 [30]:` 直接按 Enter，或輸入想測的秒數。學生是針對獨立執行最佳化的，接線分數略低於教師是正常的。

## 它在做什麼 { #what .rip-learn }

<div class="rip-flow" markdown>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">教師 256×256<small>Step 2 微調完的 best_model.zip</small></div>
  <div class="rip-flow__edge" markdown="span">對 replay buffer 的每個狀態標動作<span>BC</span></div>
  <div class="rip-flow__node" markdown="span">學生 H=16（第 0 輪）<small>只模仿過教師看過的狀態</small></div>
  <div class="rip-flow__edge rip-flow__edge--loop" markdown="span">學生自己控制 → 收集走到的狀態 → 請教師標動作 → 重新訓練，重複數輪<span>DAgger</span></div>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">DAgger 學生<small>student.pt</small></div>
</div>

1. **行為克隆（BC）**：用教師對 replay buffer 裡每個狀態的動作當標籤，做監督式學習。
2. **DAgger**：讓學生自己控制擺錘，收集學生會走到的狀態，再請教師標上動作、重新訓練。rollout 在「Nano 獨立執行」的傳輸條件下進行（`--transport device`）。

??? question "為什麼只做 BC 不夠？"

    倒單擺在直立附近是不穩定的，學生只要有一點點誤差，就會走到教師沒示範過的狀態（covariate shift）。作者實測 BC 學生的閉迴路分數只有 0.12。

??? question "為什麼不直接用 RL 訓練小網路？"

    作者試過兩次：小網路在模擬和接線微調時都表現很好，但一換成獨立執行就只剩約 0.24。RL 容易學出依賴特定時序、反應很激進的控制器，傳輸條件一變就失效；蒸餾出來的學生有輕微的欠擬合，效果反而像把增益調低，換來強健性。

??? question "為什麼是 16 個神經元？"

    Nano 沒有浮點運算單元，每次乘加約 19 µs。H=16 約 12 ms，放得進 50 Hz 的 20 ms 週期；H=32 要 35–40 ms，迴路會掉到 25 Hz，原本會平衡的策略會變成一直繞圈。

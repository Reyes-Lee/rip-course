# Step 3：蒸餾成小網路

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 3 分鐘</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台（選做的接線測試要）</span>
  <span class="rip-chip">:material-file-outline: 產出 distill_h16_dagger_dev/student.pt</span>
</div>

256×256 的教師塞不進 Nano。這一步用「模仿學習」把它壓成 16 個隱藏神經元的學生網路。

## 操作步驟 { #run }

!!! tool "蒸餾"

    1. 雙擊 `tools/09_distill`。
    2. 清單的預設是最後一段微調（例如 `<組別>_ft3`），直接按 Enter。如果 [Step 2 的回歸測試](step2-finetune.md#regression)改用了前一段，就輸入那一段的編號。
    3. `SEED [0]:` 直接按 Enter。
    4. 約 3 分鐘後，工具印出結果表（見[檢查點](#checkpoint)）。學生存在 `runs/<組別>_ftN/distill_h16_dagger_dev/student.pt`。

??? cmd "背後執行的指令"

    ```bash
    cd policy
    ./distill_student.sh <組別>_ft3
    ```

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

`09_distill` 結束時會印出下面兩項的數字，由你判斷；之後要重跑敏感度關卡，可以雙擊 `tools/13_check_sim` 選 `student.pt`。

!!! checkpoint "參考門檻（由你判斷）"

    | 項目 | 參考門檻 |
    | --- | --- |
    | DAgger gate | 學生的 gate 接近教師自己的 gate（工具並排印出兩個數字）。作者沒有給數字，我們建議相差 0.05 以內 |
    | 敏感度關卡 | 同 Step 1：關掉韌體量測模型後的 balanced fraction ≥ 0.7 |

DAgger gate 要跟教師比、不跟絕對門檻比，是因為模擬會系統性低估實機微調過的策略：作者的冠軍在模擬 gate 只有 0.655，實機是 0.996。

!!! tool "判斷要重做時"

    1. 再雙擊 `tools/09_distill`。
    2. 選同一段微調。
    3. `SEED [0]:` 輸入 `1`。
    4. 換兩個 SEED 都明顯低於教師就找助教。

## （選做）燒進 Nano 前先接線測學生 { #tethered }

!!! tool "接線測試學生"

    1. Nano 燒 `LowLevelServer`，等擺錘靜止垂下。
    2. 雙擊 `tools/08_test_policy`。
    3. 清單輸入 `<組別>_ftN/distill_h16_dagger_dev/student.pt` 那一個的編號。
    4. 跑 30 秒。學生是為獨立執行最佳化的，接線分數略低於教師是正常的。

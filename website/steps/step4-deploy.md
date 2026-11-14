# Step 4：燒錄與獨立執行評分

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 5 分鐘</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
  <span class="rip-chip">:material-chip: RLControl</span>
  <span class="rip-chip">:material-file-outline: 產出 policy_weights_student.h</span>
</div>

把學生權重匯出成 C 標頭檔（存在 PROGMEM），燒進 `RLControl.ino`，由 Nano 自己算動作、甩上、平衡。

!!! todo "這一步要做的事"

    1. [匯出與燒錄](#flash)：執行 `10_export_weights`，再用 Arduino IDE 上傳 `RLControl`。
    2. [用誠實指標評分](#score)：執行 `11_score_onboard`。
    3. （需要時）[獨立執行比接線測試差時](#gap)：依序嘗試。

    標題前標「說明」的段落是原理說明，讀懂就好，不用操作。

## 1. 匯出與燒錄 { #flash .rip-do }

!!! tool "操作步驟"

    1. 執行 `tools/10_export_weights`。清單預設是最新的學生，直接按 Enter。工具核對[下面的 sketch 常數](#constants)，全部 OK 才匯出到 `firmware/RLControl/policy_weights_student.h`。
    2. 用 Arduino IDE 開 `firmware/RLControl/RLControl.ino`，按「上傳」。sketch 載入的是第 1 步匯出的 `policy_weights_student.h`；repo 不附任何權重，還沒匯出就上傳，編譯會停在 `No policy weights yet` 的錯誤。
    3. 看 IDE 下方的編譯訊息：「草稿碼使用了 N 位元組」的 N 必須 ≤ 30720（Nano 的上限）。超過會上傳失敗：照預設的 H=16 不會超過；你改大了 H 的話，要改小再重新蒸餾。
    4. 上傳完 Nano 會自動重開。前 1 秒 LED 恆亮，這時擺錘要**靜止垂下**（這個姿勢會被當成編碼器零點），之後它會自己甩上、平衡。如果馬達完全不動，打開序列埠監控（500000）看有沒有 `[DIR] not calibrated`：這塊 Nano 沒做過[方向標定](../prepare/hardware.md#direction)，改燒 `LowLevelServer` 跑 `04_check_direction`，再重新上傳 `RLControl`。

??? cmd "第 1 步背後執行的指令"

    ```bash
    cd policy
    uv run python export_weights.py \
        --student runs/ft3/distill_h16_dagger_dev/student.pt \
        --header  ../firmware/RLControl/policy_weights_student.h \
        --source-name ft3/distill_h16_dagger_dev
    ```

!!! warning "手臂轉太遠會自動斷電"

    `RLControl` 有兩層保護：手臂超過 ±125° 就不再往外加速；超過 ±132° 就讓馬達斷電、停止控制。

    **要重新開始**：用手把手臂轉回正中間，等擺錘靜止垂下，按 Nano 上的 RESET 鍵。

### `RLControl.ino` 固定了什麼 { #fixed .rip-learn }

`RLControl.ino` 是課程版，**不修改**。燒進 Nano 時，你能換的只有權重檔 `policy_weights_student.h`。所以從 Step 1 訓練到 Step 3 蒸餾，下面這些設定都要維持課程的值，策略才能在這份 sketch 上正確執行：

| 固定的東西 | 課程的值 | 為什麼 |
| --- | --- | --- |
| 網路結構 | 24 → H → H → 1，隱藏層 ReLU、輸出 tanh，float32 | sketch 的前向計算照這個結構寫。H 由 `.h` 決定 |
| 觀測 | 最近 4 幀，每幀 `[手臂角, sin θ, cos θ, 手臂角速度, 擺錘角速度, 上一個動作]`；速度用 8 ms 視窗的差分估計 | 跟 `LowLevelServer` 同一套算法，微調時策略看到的就是這些數字 |
| 控制頻率 | 50 Hz | 訓練、微調、部署三處必須一樣 |
| 動作 | 速度指令，上限 3.5 rad/s；加速度上限 150 rad/s²；對最近 4 個動作取平均 | 150 rad/s² 是 `03_check_motor` 驗過不會失步的範圍 |
| 手臂保護 | 超過 ±125° 不再往外加速，超過 ±132° 斷電 | 保護機台 |
| 接線、微步、方向標定、開機抓零點 | 見[硬體與上電測試](../prepare/hardware.md) | 硬體設定 |

能變的是 `.h` 裡的權重和隱藏層大小 H，也就是 Step 1–3 怎麼訓練、怎麼蒸餾，包括 reward 和蒸餾方法。H 越大推論越慢：H=16 約 12 ms，超過 20 ms 的控制週期，頻率就會往下掉。所以換 H 之後要看 `11_score_onboard` 第一行的頻率是不是約 50 Hz，以及 Arduino IDE 編譯訊息裡的大小是不是 ≤ 30720 bytes。

### 工具核對的 sketch 常數 { #constants .rip-learn }

標頭檔只有權重，控制迴路的設定寫在 sketch 裡，兩邊必須一致。`10_export_weights` 匯出前會讀 `firmware/RLControl/RLControl.ino` 與策略的 `config.json`，印出下表逐項比對。repo 的預設值是對齊的；有一項不一致，工具就會停止匯出。這代表你的策略用了和課程版 sketch 不同的設定；sketch 不能改，要回頭用一致的設定重新訓練。

| `RLControl.ino` 常數 | 必須等於 | 預設值 |
| --- | --- | --- |
| `CONTROL_FREQUENCY_HZ` | `config.json` 的 `control_freq_hz` | 50 |
| `ACTION_SMOOTH_WINDOW` | `action_smooth_window` | 4 |
| `OBS_FRAMES` | `obs_history_len` | 4 |
| `MAX_VELOCITY_RAD_S` | `max_velocity_rad_s` | 3.5 |
| `MICROSTEPS` | 驅動板接線 | 32 |

## 2. 用誠實指標評分 { #score .rip-do }

!!! tool "操作步驟"

    1. Nano 燒的是 `RLControl`（[第 1 節](#flash)），Arduino IDE 的序列埠監控已關掉。這時策略可能已經在甩，不用先停它。
    2. 執行 `tools/11_score_onboard`。`評分秒數 [60]:` 直接按 Enter 是作者的 60 秒，也可以輸入其他秒數（5–600；作者的參考值是用 300 秒量的）。工具打開 serial 時 Nano 會重開，接著工具讓馬達斷電，印出「馬達已斷電」。
    3. 用手把手臂轉回正中間，等擺錘**完全靜止垂下**，按 Enter。Nano 在這一刻抓零點並開始甩。
    4. 之後在「評分秒數 + 5 秒」內不要碰機台（前 5 秒是甩上去的時間，不計分；預設約 65 秒）。結束時印出結果，紀錄檔存在 `policy/recordings/onboard_<時間>.npz`。照下面的順序看。

!!! warning "為什麼要先斷電、等你按 Enter"

    `RLControl` 開機 1 秒後，會把「當下」的擺錘角度當成垂下的零點。打開 serial 會讓 Nano 重開；如果策略原本在平衡，重開時擺錘還在甩，零點就會抓錯，之後手臂會一直轉、分數完全不準。所以工具改成重開後先讓馬達斷電，等擺錘靜止再送指令重新抓零點。

??? cmd "背後執行的指令"

    ```bash
    cd policy
    uv run python analyze_onboard.py --port <PORT> --duration-s 60 --rearm \
        --log recordings/onboard_<時間>.npz
    ```

!!! checkpoint "照這個順序看結果"

    1. **先看第一行的頻率，必須約 50 Hz。** 如果不是，代表推論超時、迴路變慢，後面的數字評的是壞掉的部署，不是策略。找助教。
    2. **再看 sample→command 延遲**（平均、p95、最大）。作者實測 15.6 ms，訓練涵蓋 2–20 ms。超出這個範圍是模擬沒有涵蓋到的問題，不是策略本身的問題。
    3. **最後看** balanced fraction、最長連續平衡、擺錘標準差、手臂偏移。

| 作者的參考值 | 冠軍 | 獨立重跑 |
| --- | --- | --- |
| balanced fraction | 1.000（300 s） | 0.980 |
| 最長連續平衡 | 299.6 s | 265 s |
| 擺錘標準差 | 1.90° | — |

「獨立重跑」是作者在配方定案後，用預設設定從頭重跑整套流程一次的結果（重新訓練教師、重新實機微調、蒸餾、燒錄）。照流程做，結果應該在這附近。

## 3. （需要時）獨立執行比接線測試差時 { #gap .rip-do }

同一個學生在 Nano 上獨立執行，分數通常會比 Step 3 的接線測試低一些。網路是同一個，差別在於由誰計算、指令多久之後才生效：

| | 接線（`08_test_policy`） | 獨立執行（`RLControl`） |
| --- | --- | --- |
| 誰讀感測器、估速度 | Nano | Nano |
| 誰算神經網路 | 電腦 | Nano（約 12 ms） |
| 指令延遲 | 經過 USB，約晚一個控制週期 | 沒有 USB 往返，sample→command 約 16 ms |

DAgger 用 `--transport device` 就是為了讓學生適應獨立執行的時序。頻率約 50 Hz、延遲在範圍內，但 balanced fraction 明顯低於參考值（例如手臂大幅來回、一直倒下又接回）時，照這個順序試：

!!! tool "依序嘗試"

    1. 再跑一次 `11_score_onboard`，確認不是單次運氣不好。
    2. 回到 [Step 3](step3-distill.md#checkpoint) 用 `SEED 1` 重新蒸餾，再匯出、燒錄、評分。`09_distill` 印出的 DAgger gate 如果和第 0 輪一樣，代表 DAgger 沒有改善，換 SEED 最值得一試。
    3. 回 [Step 2](step2-finetune.md#finetune) 再加一段微調，用 `08_test_policy` 確認教師有變好，再重新蒸餾。
    4. 都試過仍然遠低於參考值，回頭檢查前面每一步的選擇（教師、微調段數、蒸餾設定），照[依序查什麼](../theory.md#debug-order)往前找原因。

# Step 4：燒錄與獨立執行評分

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 5 分鐘</span>
  <span class="rip-chip rip-chip--amber">:material-robot-industrial: 需要機台</span>
  <span class="rip-chip">:material-chip: RLControl</span>
  <span class="rip-chip">:material-file-outline: 產出 policy_weights_student.h</span>
</div>

把學生權重匯出成 C 標頭檔（存在 PROGMEM），燒進 `RLControl.ino`，拔掉筆電也能自己甩上、平衡。

## 4-1 sketch 常數與策略一致 { #constants }

標頭檔只帶權重，迴路形狀寫在 sketch 裡，兩邊必須一致。**你不用自己核對**：`10_export_weights` 匯出前會自動讀 `firmware/RLControl/RLControl.ino` 與策略的 `config.json`，印出下表並逐項標 OK。課程 repo 的預設值已對齊，正常不會不一致；如果有一項不一致，工具會停止匯出，請找助教，不要自己改 sketch。

| `RLControl.ino` 常數 | 必須等於 | 預設值 |
| --- | --- | --- |
| `CONTROL_FREQUENCY_HZ` | `config.json` 的 `control_freq_hz` | 50 |
| `ACTION_SMOOTH_WINDOW` | `action_smooth_window` | 4 |
| `OBS_FRAMES` | `obs_history_len` | 4 |
| `MAX_VELOCITY_RAD_S` | `max_velocity_rad_s` | 3.5 |
| `MICROSTEPS` | 驅動板接線 | 32 |

## 4-2 匯出與燒錄 { #flash }

!!! tool "操作步驟"

    1. 雙擊 `tools/10_export_weights`。清單預設是最新的學生，直接按 Enter。工具核對 4-1 的表，全部 OK 才匯出到 `firmware/RLControl/policy_weights_student.h`。
    2. 用 Arduino IDE 開 `firmware/RLControl/RLControl.ino`，按「上傳」。sketch 預設就載入 `policy_weights_student.h`，不用改任何一行。
    3. 看 IDE 下方的編譯訊息：「草稿碼使用了 N 位元組」的 N 必須 ≤ 30720（Old Bootloader 的上限）。超過會上傳失敗，找助教。
    4. 上傳完 Nano 會自動重開。前 1 秒 LED 恆亮，這時擺錘要**靜止垂下**（這個姿勢會被當成編碼器零點），之後它會自己甩上、平衡。

??? cmd "第 1 步背後執行的指令"

    ```bash
    cd policy
    uv run python export_weights.py \
        --student runs/<組別>_ft3/distill_h16_dagger_dev/student.pt \
        --header  ../firmware/RLControl/policy_weights_student.h \
        --source-name <組別>_ft3/distill_h16_dagger_dev
    ```

!!! warning "手臂轉太遠會自動斷電"

    `RLControl` 有兩層保護：手臂超過 ±125° 就不再往外加速；超過 ±132° 就讓馬達斷電、停止控制。

    **要重新開始**：用手把手臂轉回正中間，等擺錘靜止垂下，按 Nano 上的 RESET 鍵。

## 4-3 用誠實指標評分 { #score }

!!! tool "操作步驟"

    1. Nano 燒的是 `RLControl`（4-2），Arduino IDE 的序列埠監控已關掉。
    2. 用手把手臂轉回正中間，等擺錘靜止垂下。工具打開 serial 時會讓 Nano 重開並重新標定零點。
    3. 雙擊 `tools/11_score_onboard`。
    4. 60 秒內不要碰機台。結束時印出結果，紀錄檔存在 `policy/recordings/onboard_<組別>.npz`。照下面的順序看。

??? cmd "背後執行的指令"

    ```bash
    cd policy
    uv run python analyze_onboard.py --port <PORT> --duration-s 60 \
        --log recordings/onboard_<組別>.npz
    ```

!!! checkpoint "照這個順序看結果"

    1. **先看第一行的頻率，必須約 50 Hz。** 如果不是，代表推論超時、迴路變慢，後面的數字評的是壞掉的部署，不是策略。找助教。
    2. **再看 sample→command 延遲**（平均、p95、最大）。作者實測 15.6 ms，訓練涵蓋 2–20 ms。超出這個範圍是模型問題，不是策略問題。
    3. **最後看** balanced fraction、最長連續平衡、擺錘標準差、手臂偏移。

| 作者的參考值 | 冠軍 | 獨立重跑 |
| --- | --- | --- |
| balanced fraction | 1.000（300 s） | 0.980 |
| 最長連續平衡 | 299.6 s | 265 s |
| 擺錘標準差 | 1.90° | — |

「獨立重跑」是作者在配方定案後，用預設設定從頭重跑整套流程一次的結果（重新訓練教師、重新實機微調、蒸餾、燒錄）。照流程做，應該落在這個附近。

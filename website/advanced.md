# 進階任務：延遲

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--amber">:material-timer-sand: 進階</span>
  <span class="rip-chip">:material-chip: RLControl ＋ 延遲階梯</span>
  <span class="rip-chip">:material-file-outline: 繳交兩份 policy_weights_student.h</span>
</div>

照五個步驟做，Nano 會自己甩上、平衡。但它只在**一種**延遲下練過：Nano 從讀取感測器到送出馬達指令大約 16 ms，策略在模擬裡也只見過差不多的值。真實系統的延遲會變，例如換一顆比較慢的 MCU、感測器改走通訊匯流排、或是同時要做別的事。

進階任務有兩項：**延遲階梯**和**甩上競速**，第 3 週 demo。

!!! warning "這一頁的規定是草稿"

    配分另外公告。規則可能調整，只會往對學生有利的方向調整。

這一頁只寫進階任務特有的規定。沒寫到的（兩條硬規定、器材使用、教師格式），照[專題規則](rules.md)。

## 配分 { #grading }

延遲階梯、甩上競速和分析報告的配分另外公告。

## 延遲的定義 { #latency }

**延遲**是策略用的那一筆感測資料，從 Nano 讀到它，到依照它送出馬達指令，中間經過的時間（遙測裡的 `sample→command`）。

| | |
| --- | --- |
| 原本 | 約 16 ms（實測 15.6 ms）。Nano 讀到擺錘和手臂的位置、算出速度、跑完網路、送出指令，本來就要這麼久 |
| +X ms | 策略改讀 X ms 以前的那一筆資料，位置和速度一起變舊。總延遲變成約 16 + X ms |
| 不變 | 控制週期（每 20 ms 一拍）、馬達、感測器本身都不變，只有策略看到的資料變舊 |

意思是：**策略看到的是擺錘 X ms 以前的樣子**，但指令作用在現在的擺錘上。擺錘在直立附近會自己越倒越快，根據舊資料出力，修正就會慢半拍；延遲越長，越容易修過頭或修不夠，最後倒下。例如 +70 時，策略看到的是約 86 ms 以前的狀態，超過 4 拍以前。實作細節見[延遲怎麼加進去](#mechanism)。

## 任務一：延遲階梯 { #task }

助教把課程版 `firmware/RLControl/RLControl.ino` 加上繳交的延遲階梯策略燒進 Nano，執行 `11_score_onboard`，選「延遲階梯」。

| | 規則 |
| --- | --- |
| 階 | +0、+10、+15、+20 … 每 5 ms 一階，最高 +70 ms。延遲加在原本約 16 ms 的上面 |
| 每一階 | 重新甩上。engage 後 **40 秒內連續平衡滿 20 秒**就通過，進下一階 |
| 平衡 | \|θ\| ≤ 15° 且 \|θ̇\| ≤ 4 rad/s |
| 順序 | 從 +0 開始，由低往高，不能跳階 |
| 重試 | 每一階沒過可以重試 1 次，還是沒過就停 |
| 策略 | 全程同一支，中間不能換權重 |
| 成績 | **最後通過的那一階** |

## 任務二：甩上競速 { #swingup }

另外繳交一支甩上策略，可以和延遲階梯同一支。規定和延遲階梯的策略相同：課程版 `RLControl.ino`、同樣的學生網路、標籤來自 RL 教師。助教燒進 Nano 後執行 `11_score_onboard`，選「甩上計時」。

| | 規則 |
| --- | --- |
| 延遲 | 不加（+0） |
| 次數 | 甩 3 次，每次從手臂在正中間、擺錘靜止垂下開始 |
| 每一次 | engage 後 20 秒內要**站穩**（連續平衡滿 10 秒）才算數 |
| 甩上時間 | engage 到「站穩的那一段」開始的秒數 |
| 成績 | 3 次的**中位數**。沒算數的那一次當成無限大，3 次裡有 2 次沒站穩就沒有成績 |
| 排名 | 依成績排名，差距在 0.2 秒以內算同一名次 |

## 分析報告 { #report }

demo 之後繳交事後的分析報告，內容與評分方式另外公告。

## 可以改什麼、不能改什麼 { #scope }

| 可以 | 不可以 |
| --- | --- |
| 訓練流程的任何部分：模擬環境、domain randomization、reward、RL 演算法、微調、蒸餾 | Nano 上的網路用 RL 教師以外的東西當標籤（LQR、PID、手動示範） |
| 改 `LowLevelServer`、`finetune_async.py` 和各個訓練腳本 | 改硬體（Vref、微步、配重等），見[專題規則](rules.md#scope) |
| 用[可以調的地方](#knobs)列出的任何設定，或自己加新的 | |
| 在自己的機台上做實機微調，次數不限 | |
| 甩上競速用另一支策略 | |

## 繳交 { #submit }

demo 前繳交，demo 時用的就是繳交的檔案，當天不能換。只交下面這些：

```text
ladder/
  policy_weights_student.h   # 延遲階梯的策略（Nano 上的網路）
  teacher.zip                # 蒸餾出這支網路的 RL 教師
  config.json                # 和 teacher.zip 同一個 runs/ 資料夾裡的那份
swingup/
  policy_weights_student.h   # 甩上競速的策略
  teacher.zip
  config.json
```

| 檔案 | 從哪裡拿 |
| --- | --- |
| `policy_weights_student.h` | `10_export_weights` 輸出的 `firmware/RLControl/policy_weights_student.h` |
| `teacher.zip` | `09_distill` 用來蒸餾的那支教師，例如 `policy/runs/ft2/last.zip`，改名成 `teacher.zip`。不是用 Stable-Baselines3 的話，改交 `teacher_act.py`（格式見[專題規則](rules.md#submit)），並附上訓練這支教師的程式 |
| `config.json` | 上面那支教師所在的資料夾裡的 `config.json` |

甩上策略和延遲階梯同一支的話，`swingup/` 只放一個寫著「同 ladder」的文字檔。

## Demo（第 3 週） { #demo }

1. 用自己的機台。助教先確認硬體照交付狀態。
2. 助教把課程版 `RLControl.ino` 加上 `ladder/policy_weights_student.h` 燒進 Nano，`11_score_onboard` 選「延遲階梯」，從 +0 開始。每一階由組員把手臂轉回正中間、等擺錘靜止，助教按 Enter。
3. 換成 `swingup/policy_weights_student.h` 重新燒錄，`11_score_onboard` 選「甩上計時」，甩 3 次。

**硬體出問題時**：遙測顯示是硬體的問題（擺錘角度讀值卡住、馬達失步、接線鬆脫），由助教判斷，那一次不算，排除後重測。策略自己倒下不算硬體問題。

## 延遲怎麼加進去 { #mechanism }

Nano 大約每 2 ms 讀一次擺錘和手臂的位置（推論時會稍微拉長到 2–3 ms），連同時間戳，存在一個環狀緩衝區裡。每一拍（20 ms）策略原本讀最新的那一筆，速度用最近 8 ms 的差分。加延遲就是讓它改讀比較舊的一筆：位置和速度一起變舊，就像整個量測晚到一樣。Nano 依時間戳挑最接近的那一筆，所以實際延遲和設定差約 ±1 ms。馬達的保護和遙測不受影響，`11_score_onboard` 量到的還是真實的擺錘角度，印出的 `sample→command` 會包含加進去的延遲。

延遲有兩種設定方式：

| 方式 | 用在哪裡 |
| --- | --- |
| `11_score_onboard` 的延遲階梯 | 用序列埠指令直接設定每一階的延遲，不用重新上傳。demo 和平常練習都用這個 |
| `firmware/RLControl/latency_profile.h` | 想測「每拍抖動」或「平衡途中延遲改變」時用，要重新上傳 |

`latency_profile.h` 的格式：每一段 `{start_s, extra_ms, jitter_ms}`，`start_s` 是 engage 後第幾秒開始用這一段，`extra_ms` 是每一拍固定多退的毫秒數，`jitter_ms` 是每一拍再隨機多退 0 到這麼多毫秒。`extra_ms + jitter_ms` 最多 70。開機時序列埠會印 `[boot] latency profile = <名稱>`。

## 在自己的機台上練習 { #practice }

!!! tool "用延遲階梯測自己的策略"

    1. 照 [Step 4](steps/step4-deploy.md#flash) 用 Arduino IDE 上傳 `RLControl`（要用這個 repo 裡最新的版本，舊版沒有設定延遲的指令）。
    2. 執行 `11_score_onboard`，選「延遲階梯」。練習時可以從比較高的階開始，省時間；但那樣的結果不是正式成績。
    3. 每一階畫面會請你把手臂轉回正中間、擺錘靜止垂下再按 Enter。
    4. 每一次的遙測和結果存在 `policy/recordings/ladder_<時間>/`。
    5. 甩上策略選「甩上計時」，結果存在 `policy/recordings/swingup_<時間>/`。

!!! warning "不要只看上傳後它自己甩的樣子"

    demo 是用 11 量的，兩者的表現可能不一樣。練習也用 11 量。

如果改過 `latency_profile.h`，練習完改回 `{ {0, 0, 0} }`，不然一般任務的分數也會被拖累。延遲階梯不受這個檔案影響。

## 在模擬裡先測 { #sim }

每一輪實機測試都要燒錄、擺好、一階一階等。先在模擬裡篩掉明顯不行的策略會快很多：

!!! tool "用 `eval_latency.py` 掃延遲"

    ```bash
    cd policy
    # 模擬的延遲階梯：和實機同一組階，每階 10 回合 × 40 秒
    uv run python eval_latency.py runs/<名稱>/distill_h16_dagger_dev/student.pt --ladder
    # 自己選要掃的延遲和抖動
    uv run python eval_latency.py <教師或學生> --extra-ms 0 10 20 30 40 --jitter-ms 0 10
    # 重播一份 latency_profile.h
    uv run python eval_latency.py <教師或學生> \
        --profile ../firmware/RLControl/latency_profile.h --episode-s 60
    ```

    教師（`.zip`）和學生（`.pt`）都可以測。`--ladder` 最後一行是「模擬裡最高通過到哪一階」（一階要 80% 的回合連續平衡滿 20 秒）。

模擬的基準是在 Nano 上量到的 15.6 ms，延遲加在這上面。模擬分數高不代表實機一定行，但模擬就撐不住的，實機通常也撐不住。

## 可以調的地方 { #knobs }

一般任務的流程每一步都有預設值，那些值是為約 16 ms 的延遲挑的。下面列出每一步和延遲有關、工具裡就能改的設定。要改哪些、改成多少，由你們自己決定。每個工具在畫面上問「要改延遲設定嗎？」時回答 `y` 才會問這些；一般任務直接按 Enter，行為和以前一樣。

| 步驟 | 工具 | 可以改的設定 | 預設 |
| --- | --- | --- | --- |
| Step 1 模擬訓練教師 | `06_train_teacher` | 觀測延遲的範圍（每回合在上下限之間抽一個）；第 3 階段的動作延遲（幾拍）和動作 lag 時間常數範圍 | 2–20 ms；1 拍；0–15 ms |
| Step 1 | `06_train_teacher` | 「從現有的教師接著練、只跑第 3 階段」：換一組設定時不用三個階段從頭練 | 不用 |
| Step 2 實機微調 | `firmware/LowLevelServer/finetune_latency.h` ＋ `07_finetune` | 每回合在 `FT_LATENCY_MIN_MS`–`FT_LATENCY_MAX_MS` 之間抽一個延遲，加在原本的延遲上面。改完要重新上傳 `LowLevelServer`；07 會印出這個設定並存進 `07_settings.json` | 0–0 ms（不加） |
| Step 2 | `07_finetune` | 「從教師重新開始一條新的微調」：換了教師時用，不接續舊的 replay buffer | 不用 |
| Step 3 蒸餾 | `09_distill` | DAgger 練習時的觀測延遲範圍；選學生時用哪些延遲評分（可以給好幾個，取平均） | 2–10 ms；15.6 ms |
| 模擬裡測 | `eval_latency.py` | 見[上一節](#sim) | — |
| 實機上測 | `11_score_onboard` 的延遲階梯 | 見[練習](#practice) | — |

每一輪「訓練 → 微調 → 蒸餾 → 實測」大約要 1.5–2 小時，三週能跑的輪數有限。建議每一輪只改少數幾個設定，並且記下改了什麼、模擬和實機各量到多少，之後的分析報告會用到這些紀錄。

!!! warning "Step 2 微調完記得 `finetune_latency.h`"

    `08_test_policy` 也是走 `LowLevelServer`，所以也會帶著這個延遲。想看沒有延遲的表現，就把它改回 `0`、`0` 再上傳一次。

想更深入也可以直接改程式：`policy/pendulum_env.py`（`obs_staleness_s` 的說明）、`policy/train_sac.py --help`、`policy/dagger_distill.py --help`、[sim2real 理論](theory.md)。

能改和不能改的範圍見[上面](#scope)。

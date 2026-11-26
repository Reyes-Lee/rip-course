# 專題任務

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--amber">:material-timer-sand: 專題任務</span>
  <span class="rip-chip">:material-chip: RLControl ＋ 延遲階梯</span>
  <span class="rip-chip">:material-file-outline: 每項任務一份 policy_weights_student.h（同一支可以共用）</span>
</div>

**[五個步驟](steps/index.md)是我們提供的 baseline。** 每一步的做法和工具都準備好了，照著跑完，你們就會有一支在 Nano 上、不加延遲時能甩上並平衡的策略。這是專題的起點，跑不出來或中途遇到問題，直接問助教。

不過這支 baseline 只在**一種**延遲下練過：Nano 從讀取感測器到送出馬達指令大約 16 ms，策略在模擬裡也只見過差不多的值。真實系統的延遲會變，例如換一顆比較慢的 MCU、感測器改走通訊匯流排、或是同時要做別的事。

專題任務有兩項，第 3 週 demo，之後繳交分析報告（期限見[專題規則](rules.md)）：

- **任務一　延遲階梯：在延遲下平衡**。自己選 5 階延遲，由低到高測，量策略在多長的延遲下還能甩上並連續平衡 10 秒。
- **任務二　甩上到平衡計時**。不加延遲，量從擺錘垂下到甩上去、在直立處站穩花了幾秒。

這一頁是專題要做的事：任務、繳交、demo，以及練習和訓練用的工具。整個專題共通的規定（兩條硬規定與要交的證明、其他可以改的、器材使用）在[專題規則](rules.md)。

延遲階梯、甩上到平衡計時和分析報告的配分另外公告。

## 延遲的定義 { #latency }

**延遲**是策略用的那一筆感測資料，從 Nano 讀到它，到依照它送出馬達指令，中間經過的時間（遙測裡的 `sample→command`）。

| | |
| --- | --- |
| 原本 | 約 16 ms（實測 15.6 ms）。Nano 讀到擺錘和手臂的位置、算出速度、跑完網路、送出指令，本來就要這麼久 |
| +X ms | 策略改讀 X ms 以前的那一筆資料，位置和速度一起變舊。總延遲變成約 16 + X ms |
| 不變 | 控制週期（每 20 ms 一拍）、馬達、感測器本身都不變，只有策略看到的資料變舊 |

意思是：**策略看到的是擺錘 X ms 以前的樣子**，但指令作用在現在的擺錘上。擺錘在直立附近會自己越倒越快，根據舊資料出力，修正就會慢半拍；延遲越長，越容易修過頭或修不夠，最後倒下。例如最高的 +55，策略看到的是約 71 ms 以前的狀態，超過 3 拍以前。實作細節見[延遲怎麼加進去](#mechanism)。

## 任務一：延遲階梯（在延遲下平衡） { #task }

量策略**在延遲下還能不能平衡**：從階梯裡自己選 5 階，由低到高測，每一階都要甩上並且連續平衡滿 10 秒，看策略能撐到哪一階。

demo 時助教用 `11_score_onboard` 的「延遲階梯」量，流程見 [Demo](#demo)。

| | 規則 |
| --- | --- |
| 階 | 共 14 階：+0、+10、+15、+20、+25、+30、+35、+37、+40、+42、+45、+47、+50、+55（沒有 +5；+35 以後分得比較細）。延遲加在原本約 16 ms 的上面 |
| 每一階 | 重新甩上。從 engage（按 Enter 後 Nano 開始控制馬達）起，**30 秒內連續平衡滿 10 秒**就通過，進下一階。這 10 秒要在 30 秒內數完，所以最晚約第 20 秒就要接住 |
| 平衡 | 擺錘離直立 15° 以內（\|θ\| ≤ 15°），而且擺錘角速度 \|θ̇\| ≤ 4 rad/s |
| 選階 | 從上面的階裡**選剛好 5 階**，不一定要連續，例如 +0、+20、+35、+40、+45。demo 時告訴助教 |
| 順序 | 選的 5 階由低到高測，某一階重試後還是沒過就停，後面的不測 |
| 重試 | 每一階沒過可以重試 1 次，還是沒過就停 |
| 策略 | 全程同一支，中間不能換權重 |
| 成績 | **最後通過的那一階**。選的第一階就沒過，就沒有成績 |

**5 階怎麼選**：第一階選太高，可能一階都過不了；5 階都選低的，最高也只到選的第 5 階，例如選 +0 到 +25，最多就是 +25。中間可以跳過有把握的階，把階數留給接近極限的地方，例如 +0、+20、+35、+40、+45。先用 11 在自己的機台上[練習](#practice)再決定。

## 任務二：甩上到平衡計時 { #swingup }

量策略**從擺錘靜止垂下，到甩上去、在直立處站穩，花了幾秒**。不加延遲，越快越好。

另外繳交一支策略，可以和延遲階梯同一支，一樣要守住[兩條硬規定](rules.md#hard-rules)。助教燒進 Nano 後執行 `11_score_onboard`，選「甩上到平衡計時」。

| | 規則 |
| --- | --- |
| 延遲 | 不加（+0） |
| 次數 | 甩 3 次，每次從手臂在正中間、擺錘靜止垂下開始 |
| 每一次 | engage 後 20 秒內要**站穩**（連續平衡滿 10 秒）才算數。這 10 秒要在 20 秒內數完，所以最晚約第 10 秒就要接住 |
| 計時 | 從 engage 到擺錘進入平衡的秒數。算的是「之後連續平衡滿 10 秒」的那一次進入平衡；甩上去又掉下來的不算，要等到真正站穩的那一次 |
| 成績 | 3 次的**中位數**。沒算數的那一次當成無限大，3 次裡有 2 次沒站穩就沒有成績 |
| 排名 | 秒數越少，名次越前面。差距在 0.2 秒以內算同一名次 |

## 三週怎麼安排（建議） { #plan }

1. 先量起點：用[模擬的延遲階梯](#sim)和 11 的延遲階梯（[練習](#practice)），看照五個步驟做出來、蒸餾後的模型能到哪一階。
2. 用 06 的延遲設定（或「從現有的模型接著練、只跑第 3 階段」）和 09 的 DAgger 延遲條件重練，見[可以調的地方](#knobs)。需要時在 Step 2 用 `finetune_latency.h` 加延遲微調。
3. 每一輪「訓練 → 微調 → 蒸餾 → 實測」約 1.5–2 小時：先在模擬裡篩，再上機確認。記下每一輪改了什麼、模擬和實機各量到多少，報告會用到。
4. demo 前用 11 練幾種 5 階的組合，決定要選哪 5 階；也量一下甩上到平衡計時，決定兩項任務要不要用同一支策略。

## 分析報告 { #report }

期限見[專題規則](rules.md)，評分方式另外公告。報告寫你們實際做了什麼、為什麼這樣做、結果怎麼解釋，不用重複五個步驟。內容包含：

| | 要寫什麼 |
| --- | --- |
| 分工 | 每位組員負責什麼，例如誰負責延遲階梯的策略、誰負責甩上到平衡計時的策略、誰做實機微調和量測。分工要和後面寫的工作對得起來 |
| 訓練策略與方法 | 兩支策略各自怎麼訓練：從五個步驟的預設流程改了哪些地方（例如 reward、domain randomization 的延遲範圍、實機微調時加的延遲、蒸餾的資料），為什麼這樣改。附上關鍵設定（`config.json` 裡的值） |
| 嘗試與比較 | 試過哪些做法，哪些有效、哪些沒效，用數據比較，例如同一支策略在模擬（[`eval_latency.py`](#sim)）和實機上各撐到哪一階 |
| 結果分析 | demo 的成績。延遲階梯在哪一階倒下，從遙測看是怎麼倒的；甩上的速度和站穩的機率怎麼取捨 |
| 檢討 | 再多一點時間會試什麼，為什麼 |

## 繳交 { #submit }

demo 前繳交，繳交方式另外公告。demo 時用的就是繳交的檔案，當天不能換。只交下面這些：

```text
ladder/
  policy_weights_student.h   # 延遲階梯的策略（Nano 上的網路）
  teacher.zip                # 蒸餾前的模型（你們用 RL 訓練的）
  config.json                # 和 teacher.zip 同一個 runs/ 資料夾裡的那份
swingup/
  policy_weights_student.h   # 甩上到平衡計時的策略
  teacher.zip
  config.json
```

| 檔案 | 從哪裡拿 |
| --- | --- |
| `policy_weights_student.h` | `10_export_weights` 輸出的 `firmware/RLControl/policy_weights_student.h` |
| `teacher.zip` | 蒸餾前的模型，也就是 `09_distill` 用來蒸餾的那個檔：09 選的那一段微調裡的 `best_model.zip`（預設；當時選了 `last.zip` 就交它），例如 `policy/runs/ft2/best_model.zip`，改名成 `teacher.zip`。不是用 Stable-Baselines3 的話，改交 `teacher_act.py`（格式見[專題規則](rules.md#teacher)），並附上訓練這個模型的程式 |
| `config.json` | 上面那個蒸餾前的模型所在的資料夾裡的 `config.json` |

`policy_weights_student.h` 是要燒進 Nano 的權重（[規定一](rules.md#hard-rules)）；`teacher.zip` 和 `config.json` 用來確認它是用 RL 訓練出來的（[規定二](rules.md#hard-rules)）。甩上策略和延遲階梯同一支的話，`swingup/` 只放一個文字檔 `SAME_AS_LADDER.txt`（內容寫「同 ladder」）。

## Demo（第 3 週） { #demo }

1. 用自己的機台。助教先確認硬體照交付狀態。
2. 助教把課程版 `RLControl.ino` 加上 `ladder/policy_weights_student.h` 燒進 Nano，`11_score_onboard` 選「延遲階梯」，輸入組員選的 5 階。每一階由組員把手臂轉回正中間、等擺錘靜止，助教按 Enter。
3. 換成 `swingup/policy_weights_student.h` 重新燒錄，`11_score_onboard` 選「甩上到平衡計時」，甩 3 次。
4. 助教會請組員說明訓練過程，例如改了哪些地方、為什麼。

**硬體出問題時**：遙測顯示是硬體的問題（擺錘角度讀值卡住、馬達失步、接線鬆脫），由助教判斷，那一次不算，排除後重測。策略自己倒下不算硬體問題。

## 延遲怎麼加進去 { #mechanism }

Nano 大約每 2 ms 讀一次擺錘和手臂的位置（推論時會稍微拉長到 2–3 ms），連同時間戳，存在一個環狀緩衝區裡。每一拍（20 ms）策略原本讀最新的那一筆，速度用最近 8 ms 的差分。加延遲就是讓它改讀比較舊的一筆：位置和速度一起變舊，就像整個量測晚到一樣。Nano 依時間戳挑最接近的那一筆，所以實際延遲和設定差約 ±1 ms。馬達的保護和遙測不受影響，`11_score_onboard` 量到的還是真實的擺錘角度，印出的 `sample→command` 會包含加進去的延遲。

延遲有兩種設定方式：

| 方式 | 用在哪裡 |
| --- | --- |
| `11_score_onboard` 的延遲階梯 | 用序列埠指令直接設定每一階的延遲，不用重新上傳。demo 和平常練習都用這個 |
| `firmware/RLControl/latency_profile.h` | 不透過 11、讓上傳後的 `RLControl` 自己帶著延遲時用，要重新上傳 |

`latency_profile.h` 的格式是 `{ {0, extra_ms, jitter_ms} }`，只能寫一段：`extra_ms` 是每一拍固定多退的毫秒數，`jitter_ms` 是每一拍再隨機多退 0 到這麼多毫秒，`extra_ms + jitter_ms` 最多 70。寫錯（兩段以上、第一個數不是 0、超過 70）編譯時會直接報錯。開機時序列埠會印 `[boot] latency profile = <名稱>`。

## 在自己的機台上練習 { #practice }

!!! tool "用延遲階梯測自己的策略"

    1. 照 [Step 4](steps/step4-deploy.md#flash) 用 Arduino IDE 上傳 `RLControl`（要用這個 repo 裡最新的版本，舊版沒有設定延遲的指令）。
    2. 執行 `11_score_onboard`，選「延遲階梯」。和 demo 一樣要選 5 階，練習時可以每次選不同的組合。
    3. 每一階畫面會請你把手臂轉回正中間、擺錘靜止垂下再按 Enter。
    4. 每一次的遙測和結果存在 `policy/recordings/ladder_<時間>/`。
    5. 甩上策略選「甩上到平衡計時」，結果存在 `policy/recordings/swingup_<時間>/`。

!!! warning "不要只看上傳後它自己甩的樣子"

    demo 是用 11 量的，兩者的表現可能不一樣。練習也用 11 量。

如果改過 `latency_profile.h`，練習完改回 `{ {0, 0, 0} }`，不然一般評分的分數也會被拖累。延遲階梯和甩上到平衡計時都不受這個檔案影響（11 會用序列埠指令設定延遲）。

## 在模擬裡先測 { #sim }

每一輪實機測試都要燒錄、擺好、一階一階等。先在模擬裡篩掉明顯不行的策略會快很多：

!!! tool "用 `eval_latency.py` 在模擬裡跑延遲階梯"

    打開終端機，進到 repo 的 `policy` 資料夾再執行（選你的系統）。下面以 `ft2` 蒸餾後的模型為例，路徑換成你自己的：

    === ":material-apple: macOS"

        ```bash
        cd ~/rip-course/policy
        uv run python eval_latency.py runs/ft2/distill_h16_dagger_dev/student.pt --ladder --levels 0 20 35 40 45
        ```

    === ":material-microsoft-windows: Windows"

        ```powershell
        cd C:\rip-course\policy
        uv run python eval_latency.py runs\ft2\distill_h16_dagger_dev\student.pt --ladder --levels 0 20 35 40 45
        ```

    - `--levels` 換成你想試的 5 階，規則和實機一樣：由低到高，某一階沒過就停。模擬裡每階跑 10 回合 × 30 秒，一階要 80% 的回合連續平衡滿 10 秒才算通過。最後一行會寫「依你選的 5 階（由低到高，某一階沒過就停），最高 +X ms」。
    - 只寫 `--ladder`、不加 `--levels`，會把 14 階都跑一次，印出每一階有幾個回合連續平衡滿 10 秒，方便決定要選哪 5 階。
    - 蒸餾前的模型（`.zip`，例如 `runs/ft2/best_model.zip`）和蒸餾後的模型（`.pt`）都可以測。

??? cmd "其他用法：自己選延遲和抖動、重播 latency_profile.h"

    一樣在 `policy` 資料夾執行（Windows 的路徑分隔可以用 `/` 或 `\`）：

    ```bash
    uv run python eval_latency.py runs/ft2/distill_h16_dagger_dev/student.pt --extra-ms 0 10 20 30 40 --jitter-ms 0 10
    uv run python eval_latency.py runs/ft2/distill_h16_dagger_dev/student.pt --profile ../firmware/RLControl/latency_profile.h --episode-s 60
    ```

模擬的基準是在 Nano 上量到的 15.6 ms，延遲加在這上面。模擬和實機會差，而且方向不一定：助教測過的策略裡，有的模擬比實機悲觀約 5 ms（模擬 +25 全倒，實機一次就過），有的比實機樂觀 5–10 ms。模擬適合用來比較同一支策略在不同延遲下的表現、篩掉差很多的版本，最後能到哪一階要在實機上量。

## 可以調的地方 { #knobs }

五個步驟的每一步都有預設值，那些值是為約 16 ms 的延遲挑的。下面列出每一步和延遲有關、工具裡就能改的設定。要改哪些、改成多少，由你們自己決定。不改就直接按 Enter，行為和預設一樣：

- `06_train_teacher` 問 `要改延遲設定嗎？` 時回答 `y`。
- `09_distill` 問 `要改 DAgger 的延遲條件嗎？` 時回答 `y`。
- `07_finetune` 不問：改 `firmware/LowLevelServer/finetune_latency.h`，重新上傳 `LowLevelServer`。

!!! info "模擬裡有三種延遲"

    | 設定 | 模擬的是什麼 | 在哪裡改 |
    | --- | --- | --- |
    | 觀測延遲 | 策略看到的感測資料變舊，也就是 Nano 上的 `sample→command`。**延遲階梯的 +X 加的就是這一種** | 06、09 |
    | 動作延遲（拍） | 指令晚幾拍才生效，主要模擬接線時指令經過 USB | 06 的第 3 階段 |
    | 動作 lag 時間常數 τ | 指令生效時不是一下子到位，而是以時間常數 τ 慢慢跟上 | 06 的第 3 階段 |

    要練延遲階梯，主要調的是觀測延遲；動作延遲和 lag 是 Step 1 原本就有的設定，見 [Step 1 的三個階段](steps/step1-train.md#stages)。

!!! warning "延遲有兩種寫法：總延遲和加上去的延遲"

    | 寫法 | 意思 | 用在哪裡 |
    | --- | --- | --- |
    | **總延遲** | 包含原本約 16 ms | `06_train_teacher` 的觀測延遲範圍、`09_distill` 的練習範圍和評分延遲 |
    | **加上去的延遲** | 加在原本約 16 ms 上面 | `finetune_latency.h`、延遲階梯的 +X、`eval_latency.py` 的 `--extra-ms`、`latency_profile.h` |

    例如要讓策略練到實機的 +55，06 和 09 的上限要設到約 71 ms（16 + 55），`finetune_latency.h` 則是寫 55。06 預設的 2–20 ms 只涵蓋到大約 +4。`finetune_latency.h` 是加在接線測試原本的延遲上，接線和獨立執行原本的延遲不完全一樣，所以寫 55 是讓蒸餾前的模型在微調時見過那個範圍，不等於完全重現實機的 +55。

    所有範圍都是**每回合在上下限之間均勻抽一個**；上下限設成一樣就是固定延遲。

| 步驟 | 工具 | 可以改的設定 | 預設 |
| --- | --- | --- | --- |
| Step 1 模擬訓練 | `06_train_teacher` | 觀測延遲的範圍（總延遲，最多 100 ms）；第 3 階段的動作延遲（幾拍）和動作 lag 時間常數範圍 | 2–20 ms；1 拍；0–15 ms |
| Step 1 | `06_train_teacher` | 「從現有的模型接著練、只跑第 3 階段」：換一組設定時不用三個階段從頭練 | 不用 |
| Step 2 實機微調 | `firmware/LowLevelServer/finetune_latency.h` ＋ `07_finetune` | 每回合在 `FT_LATENCY_MIN_MS`–`FT_LATENCY_MAX_MS` 之間抽一個延遲，加在原本的延遲上面。改完要重新上傳 `LowLevelServer`；07 會印出這個設定並存進 `07_settings.json`。上限最多 70 ms，涵蓋延遲階梯的最高階 +55 | 0–0 ms（不加） |
| Step 2 | `07_finetune` | 「從 Step 1 的模型重新開始一條新的微調」：換了 Step 1 的模型時用，不接續舊的 replay buffer | 不用 |
| Step 3 蒸餾 | `09_distill` | DAgger 練習時的觀測延遲範圍（總延遲，最多 100 ms）；選蒸餾後的模型時用哪些延遲評分（總延遲）（可以給好幾個，取平均） | 2–10 ms；15.6 ms |
| 模擬裡測 | `eval_latency.py` | 見[上一節](#sim) | — |
| 實機上測 | `11_score_onboard` 的延遲階梯 | 見[練習](#practice) | — |

每一輪「訓練 → 微調 → 蒸餾 → 實測」大約要 1.5–2 小時，三週能跑的輪數有限。建議每一輪只改少數幾個設定，並且記下改了什麼、模擬和實機各量到多少，之後的分析報告會用到這些紀錄。

!!! warning "Step 2 微調完記得改回 `finetune_latency.h`"

    所有走 `LowLevelServer` 的工具（`03_check_motor`、`04_check_direction`、`05_sysid`、`07_finetune`、`08_test_policy`）都會帶著這個延遲。微調完要做其他測試、或想看沒有延遲的表現，就把它改回 `0`、`0` 再上傳一次。

想更深入也可以直接改程式：`policy/pendulum_env.py`（`obs_staleness_s` 的說明）、`policy/train_sac.py --help`、`policy/dagger_distill.py --help`、[sim2real 理論](theory.md)。

能改和不能改的範圍見[專題規則](rules.md#scope)。

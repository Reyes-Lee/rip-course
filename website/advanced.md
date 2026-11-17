# 進階任務：延遲

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--amber">:material-timer-sand: 進階</span>
  <span class="rip-chip">:material-chip: RLControl ＋ latency_profile.h</span>
  <span class="rip-chip">:material-file-outline: 繳交 policy_weights_student.h</span>
</div>

照五個步驟做，Nano 會自己甩上、平衡。但它只在**一種**延遲下練過：Nano 從讀取感測器到送出馬達指令大約 16 ms，策略在模擬裡也只見過差不多的值。真實系統的延遲會變，例如換一顆比較慢的 MCU、感測器改走通訊匯流排、或是同時要做別的事。

進階任務要你們的策略在**比較舊的資料**下仍然能甩上、平衡。

## 任務 { #task }

demo 時助教燒進 Nano 的是：

- 課程版 `firmware/RLControl/RLControl.ino`
- 你們繳交的 `policy_weights_student.h`
- **助教自己的 `latency_profile.h`（不公開）**

`latency_profile.h` 決定 Nano 每一拍讀到的資料要比最新的舊多少。助教的版本會落在下面公開的範圍內，所有組用同一份。

!!! info "公開範圍"

    - 額外延遲 `extra_ms`：0–40 ms
    - 每拍抖動 `jitter_ms`：0–20 ms
    - 任何時候 `extra_ms + jitter_ms` ≤ 40 ms
    - 一次 60 秒的評分最多分 4 段，每段至少 10 秒，延遲會在平衡途中改變
    - 第一段從 engage 開始，所以甩上的時候也有延遲

評分方式另外公告；量測工具和一般任務一樣是 `11_score_onboard`（最長連續平衡、平衡比例）。

## 延遲怎麼加進去 { #mechanism }

Nano 每 2 ms 讀一次擺錘和手臂的位置，存在一個環狀緩衝區裡。每一拍（20 ms）策略原本讀最新的那一筆，速度用最近 8 ms 的差分。`latency_profile.h` 讓它改讀比較舊的一筆：

| 設定 | 意思 |
| --- | --- |
| `extra_ms` | 每一拍都往回多退這麼多毫秒 |
| `jitter_ms` | 每一拍再隨機多退 0 到這麼多毫秒，每拍各抽一次 |
| `start_s` | 從 engage（開始甩）後第幾秒開始用這一段；可以分好幾段，延遲會在平衡途中改變 |

都以 2 ms 為單位，`extra_ms + jitter_ms` 最多 44 ms。位置和速度一起變舊，就像整個量測晚到一樣。馬達的保護（±125°、±132°）和遙測不受影響，`11_score_onboard` 量到的還是真實的擺錘角度。

開機時序列埠會印出 `[boot] latency profile = <名稱>`，可以確認燒進去的是哪一份。

## 在自己的機台上練習 { #practice }

!!! tool "用練習用的延遲燒 Nano"

    1. 打開 `firmware/RLControl/latency_profile.h`，照檔案裡的說明改 `LATENCY_STAGES`，例如 `#define LATENCY_STAGES { {0, 20, 10} }` 是「固定多 20 ms，每拍再隨機多 0–10 ms」。`LATENCY_PROFILE_NAME` 改成好認的名字。
    2. 照 [Step 4](steps/step4-deploy.md#flash) 用 Arduino IDE 上傳 `RLControl`。
    3. 執行 `11_score_onboard`。結果裡的 `sample->command latency` 會包含你加的延遲。
    4. 練習完把 `latency_profile.h` 改回 `{ {0, 0, 0} }`，不然一般任務的分數也會被拖累。

!!! warning "繳交時 `latency_profile.h` 不用交"

    demo 用的是助教的版本。你們的 `latency_profile.h` 改成什麼都不影響 demo。

## 在模擬裡先測 { #sim }

每一輪實機測試都要燒錄、擺好、等 65 秒。先在模擬裡篩掉明顯不行的策略會快很多：

!!! tool "用 `eval_latency.py` 掃延遲"

    ```bash
    cd policy
    # 掃一排固定延遲，加上兩種抖動
    uv run python eval_latency.py runs/<名稱>/distill_h16_dagger_dev/student.pt \
        --extra-ms 0 10 20 30 40 --jitter-ms 0 20
    # 直接重播一份 latency_profile.h（和 Nano 用同一份檔案）
    uv run python eval_latency.py <教師或學生> \
        --profile ../firmware/RLControl/latency_profile.h --episode-s 60
    ```

    教師（`.zip`）和學生（`.pt`）都可以測。每個條件從垂下開始跑 10 回合，印出最長連續平衡的中位數、最差的一回合，以及幾回合撐過「回合長度減 10 秒」。

模擬的基準是在 Nano 上量到的 15.6 ms（取樣到送出指令），`extra_ms` 加在這上面。模擬分數高不代表實機一定行，但模擬就撐不住的，實機通常也撐不住。

## 從哪裡下手 { #where }

一般任務的流程每一步都有預設值，那些值是為 16 ms 左右的延遲挑的。要撐過更大的延遲，你們得自己找出流程裡哪些地方假設了延遲、各自要改成什麼。可以先讀：

- [sim2real 理論](theory.md)：domain randomization 在做什麼。
- `policy/pendulum_env.py` 裡 `obs_staleness_s` 的說明，以及 `policy/train_sac.py --help` 裡和延遲有關的選項。
- 每一步用的是什麼「傳輸條件」：Step 2 的實機微調走 `LowLevelServer`，Step 3 的 DAgger 用 `--transport device`。它們看到的延遲跟 demo 時一樣嗎？

`RLControl.ino` 不能改，其他都可以，包括 `LowLevelServer`、`run_policy.py`、`finetune_async.py` 和各個訓練腳本。改了什麼都要寫進 `changes.diff`，demo 時說明為什麼這樣改。

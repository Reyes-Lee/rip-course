---
title: 首頁
hide:
  - navigation
  - toc
---

# RL 旋轉倒單擺 Sim2Real

<div class="rip-hero" markdown>

<div markdown>

<span class="rip-hero__eyebrow">AI 概論 · 課程專題</span>

<h1><span class="rip-hero__big">SIM2REAL</span><span class="rip-hero__zh">旋轉倒單擺</span></h1>

<p class="rip-hero__tag">TRAIN IN SIM · BALANCE FOR REAL</p>

<p class="rip-hero__lead">用強化學習在 MuJoCo 裡訓練一支策略，搬到真實機台上微調，最後壓成 16 個神經元的小網路，燒進 Arduino Nano 獨立執行。</p>

<div class="rip-hero__actions" markdown>
[開始準備 :material-arrow-right:](prepare/index.md){ .md-button .md-button--primary }
[看五個步驟](steps/index.md){ .md-button }
</div>

</div>

<div class="rip-player" aria-label="範例玩家卡：五個關卡的進度">
  <div class="rip-player__top">
    <div class="rip-player__avatar">?</div>
    <div><div class="rip-player__name">你的機台</div><div class="rip-player__rank">FRESH RECRUIT</div></div>
  </div>
  <div class="rip-player__bar"><i></i></div>
  <div class="rip-player__xp"><span>STAGE 0 / 5</span><span>NEXT：系統識別</span></div>
  <div class="rip-player__next">先做事前準備 <b>READY?</b></div>
  <div class="rip-player__loadout">CURRENT LOADOUT<br><span>17HS3401S</span><span>TMC2209</span><span>AS5600</span><span>Nano</span><span>10 元硬幣</span></div>
  <div class="rip-sticker">50 Hz!</div>
</div>

</div>

<div class="rip-marquee" aria-hidden="true"><div class="rip-marquee__track"><span>SYSTEM ID</span><span>TRAIN IN SIM</span><span>FINE-TUNE ON THE RIG</span><span>DISTILL TO 16 NEURONS</span><span>FLASH THE NANO</span><span>BALANCE 300 S</span><span>SYSTEM ID</span><span>TRAIN IN SIM</span><span>FINE-TUNE ON THE RIG</span><span>DISTILL TO 16 NEURONS</span><span>FLASH THE NANO</span><span>BALANCE 300 S</span></div></div>

<div class="rip-stats">
  <div class="rip-stat"><b>1.000</b><span>作者冠軍：300 秒內 balanced fraction</span></div>
  <div class="rip-stat"><b>1.90°</b><span>平衡時擺錘角度標準差</span></div>
  <div class="rip-stat"><b>16</b><span>燒進 Nano 的學生網路神經元數</span></div>
  <div class="rip-stat"><b>50 Hz</b><span>訓練、微調、部署共用的控制頻率</span></div>
</div>

## 五個步驟

每一步都有檢查點，**沒過不要往下走**。每一步的產出檔就是下一步的輸入。

<ul class="rip-steps">
  <li><a class="rip-step" href="steps/step0-sysid/"><span class="rip-step__n">STEP 0 · 實機 15 分</span><span class="rip-step__t">系統識別</span><span class="rip-step__d">量擺錘鉸鏈的摩擦，把模擬釘在你的機台上。</span><span class="rip-step__out">sysid_params.json</span></a></li>
  <li><a class="rip-step" href="steps/step1-train/"><span class="rip-step__n">STEP 1 · CPU 25 分</span><span class="rip-step__t">模擬訓練教師</span><span class="rip-step__d">三階段 domain randomization，訓練 256×256 的 SAC 策略。</span><span class="rip-step__out">v1_stage3/best_model.zip</span></a></li>
  <li><a class="rip-step" href="steps/step2-finetune/"><span class="rip-step__n">STEP 2 · 實機 10–25 分</span><span class="rip-step__t">實機微調</span><span class="rip-step__d">用 30–90 個真實回合，學會模擬沒涵蓋的動態。</span><span class="rip-step__out">ftN/best_model.zip</span></a></li>
  <li><a class="rip-step" href="steps/step3-distill/"><span class="rip-step__n">STEP 3 · CPU 3 分</span><span class="rip-step__t">蒸餾學生</span><span class="rip-step__d">行為克隆＋DAgger，壓成 16 個神經元的小網路。</span><span class="rip-step__out">distill_h16_dagger_dev/student.pt</span></a></li>
  <li><a class="rip-step" href="steps/step4-deploy/"><span class="rip-step__n">STEP 4 · 實機 5 分</span><span class="rip-step__t">燒錄與評分</span><span class="rip-step__d">燒進 Nano，拔掉電腦也能自己甩上、平衡。</span><span class="rip-step__out">policy_weights_student.h</span></a></li>
</ul>

只想用筆電接線控制的話，做到 Step 2 就是一個完整的控制器；Step 3–4 是為了拔掉電腦。

## 你會用到的東西

<div class="grid cards" markdown>

-   :material-engine:{ .lg .middle } **17HS3401S + TMC2209**

    ---

    步進馬達轉動手臂，以「速度指令」換成加速度驅動，不是位置指令。

-   :material-magnet:{ .lg .middle } **AS5600 磁性編碼器**

    ---

    量擺錘角度，12-bit（4096 格／圈），I²C。整套系統對角度的認知都來自它。

-   :material-chip:{ .lg .middle } **Arduino Nano**

    ---

    ATmega328P、2 KB RAM、沒有浮點運算單元。最後策略就跑在它上面。

-   :material-circle-multiple:{ .lg .middle } **10 元硬幣配重**

    ---

    貼在擺錘外側、距鉸鏈 64 mm。整台機器唯一需要你認真量的尺寸。

</div>

## 三個原則

!!! tip "做這個專題時記住"

    - **一次只處理一個問題。** 同時換兩樣東西，壞了就不知道是誰。
    - **訓練、微調、部署的設定必須一致。** 控制頻率、動作尺度、堆疊幀數、平滑窗口三處要一樣；工具會自動檢查，不一致就中止，不要繞過它。
    - **用實機的誠實指標判斷好壞。** 模擬分不出策略優劣：作者的冠軍學生在模擬只有 0.655，實機是 0.996。

## 來源

整套流程與程式來自作者 ferrolho 的開源專案 [rotary-inverted-pendulum](https://github.com/ferrolho/rotary-inverted-pendulum)（[文件網站](https://ferrolho.github.io/rotary-inverted-pendulum/)，MIT License）。課程只改了硬體相關的常數，並加上一組雙擊就能執行的測試與流程工具。作者的 reward、domain randomization、超參數是本專題的**標準配方**，照作者的實際做法直接沿用。

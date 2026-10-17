---
hide:
  - toc
---

# 五個步驟

每一步都有檢查點，**沒過不要往下走**。每一步的產出檔就是下一步的輸入；Step 2 可以重複多段，直到實機測試不再變好。

<ul class="rip-steps">
  <li><a class="rip-step" href="step0-sysid/"><span class="rip-step__n">STEP 0 · 實機 15 分</span><span class="rip-step__t">系統識別</span><span class="rip-step__d">量擺錘鉸鏈的摩擦，把模擬釘在你的機台上。</span><span class="rip-step__out">sysid_params_&lt;組別&gt;.json</span></a></li>
  <li><a class="rip-step" href="step1-train/"><span class="rip-step__n">STEP 1 · CPU 25 分</span><span class="rip-step__t">模擬訓練教師</span><span class="rip-step__d">三階段 domain randomization，訓練 256×256 的 SAC 策略。</span><span class="rip-step__out">&lt;組別&gt;_v1_stage3/best_model.zip</span></a></li>
  <li><a class="rip-step" href="step2-finetune/"><span class="rip-step__n">STEP 2 · 實機 10–25 分</span><span class="rip-step__t">實機微調</span><span class="rip-step__d">用 30–90 個真實回合，學會模擬沒涵蓋的動態。</span><span class="rip-step__out">&lt;組別&gt;_ftN/best_model.zip</span></a></li>
  <li><a class="rip-step" href="step3-distill/"><span class="rip-step__n">STEP 3 · CPU 3 分</span><span class="rip-step__t">蒸餾學生</span><span class="rip-step__d">行為克隆＋DAgger，壓成 16 個神經元的小網路。</span><span class="rip-step__out">distill_h16_dagger_dev/student.pt</span></a></li>
  <li><a class="rip-step" href="step4-deploy/"><span class="rip-step__n">STEP 4 · 實機 5 分</span><span class="rip-step__t">燒錄與評分</span><span class="rip-step__d">燒進 Nano，拔掉電腦也能自己甩上、平衡。</span><span class="rip-step__out">policy_weights_student.h</span></a></li>
</ul>

## 檔案怎麼一路傳下去

<div class="rip-flow" markdown>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">:material-robot-industrial: 你的機台</div>
  <div class="rip-flow__edge" markdown="span"><code>05_sysid</code><span>Step 0</span></div>
  <div class="rip-flow__node" markdown="span"><code>sysid_params_&lt;組別&gt;.json</code><small>擺錘鉸鏈的摩擦</small></div>
  <div class="rip-flow__edge" markdown="span"><code>06_train_teacher</code><span>Step 1</span></div>
  <div class="rip-flow__node" markdown="span"><code>&lt;組別&gt;_v1_stage3/best_model.zip</code><small>256×256 教師（模擬）</small></div>
  <div class="rip-flow__edge rip-flow__edge--loop" markdown="span"><code>07_finetune</code> × N 段，每段後 <code>08_test_policy</code><span>Step 2</span></div>
  <div class="rip-flow__node" markdown="span"><code>&lt;組別&gt;_ftN/best_model.zip</code><small>微調後的教師 ＋ replay buffer</small></div>
  <div class="rip-flow__edge" markdown="span"><code>09_distill</code><span>Step 3</span></div>
  <div class="rip-flow__node" markdown="span"><code>distill_h16_dagger_dev/student.pt</code><small>16 個神經元的學生</small></div>
  <div class="rip-flow__edge" markdown="span"><code>10_export_weights</code> → Arduino IDE 上傳<span>Step 4</span></div>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">:material-chip: Nano 獨立執行<small><code>11_score_onboard</code> 評分</small></div>
</div>

每個方框是一個檔案，方框之間是產生它的工具。Step 2 會重複好幾段，每段跑完都用 `08_test_policy` 接線測一次。

## 每一步要不要機台、要燒什麼

| 步驟 | 要不要機台 | Nano 要燒的韌體 | 用到的工具 |
| --- | --- | --- | --- |
| [Step 0](step0-sysid.md) | 要 | `LevelCheck` → `LowLevelServer` | `04_check_level`、`05_sysid` |
| [Step 1](step1-train.md) | 不用 | — | `06_train_teacher`、`12_view_policy`、`13_check_sim` |
| [Step 2](step2-finetune.md) | 要 | `LowLevelServer` | `07_finetune`、`08_test_policy`、`13_check_sim` |
| [Step 3](step3-distill.md) | 不用（選做的接線測試要） | 選做：`LowLevelServer` | `09_distill`、`08_test_policy` |
| [Step 4](step4-deploy.md) | 要 | `RLControl` | `10_export_weights`、`11_score_onboard` |

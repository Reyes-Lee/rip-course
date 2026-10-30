---
hide:
  - toc
---

# 五個步驟

每一步都有檢查點，**沒過不要往下走**。每一步的產出檔就是下一步的輸入；Step 2 可以重複多段，直到實機測試不再變好。

<ul class="rip-steps">
  <li><a class="rip-step" href="step0-sysid/"><span class="rip-step__n">STEP 0 · 實機 15 分</span><span class="rip-step__t">系統識別</span><span class="rip-step__d">量擺錘鉸鏈的摩擦，把模擬釘在你的機台上。</span><span class="rip-step__out">sysid_params.json</span></a></li>
  <li><a class="rip-step" href="step1-train/"><span class="rip-step__n">STEP 1 · CPU 25–60 分</span><span class="rip-step__t">模擬訓練教師</span><span class="rip-step__d">三階段 domain randomization，訓練 256×256 的 SAC 策略。</span><span class="rip-step__out">v1_stage3/best_model.zip</span></a></li>
  <li><a class="rip-step" href="step2-finetune/"><span class="rip-step__n">STEP 2 · 實機 15–50 分</span><span class="rip-step__t">實機微調</span><span class="rip-step__d">用 30–90 個真實回合，學會模擬沒涵蓋的動態。</span><span class="rip-step__out">ftN/best_model.zip</span></a></li>
  <li><a class="rip-step" href="step3-distill/"><span class="rip-step__n">STEP 3 · CPU 3 分</span><span class="rip-step__t">蒸餾學生</span><span class="rip-step__d">行為克隆＋DAgger，壓成 16 個神經元的小網路。</span><span class="rip-step__out">distill_h16_dagger_dev/student.pt</span></a></li>
  <li><a class="rip-step" href="step4-deploy/"><span class="rip-step__n">STEP 4 · 實機 5 分</span><span class="rip-step__t">燒錄與評分</span><span class="rip-step__d">燒進 Nano，拔掉電腦也能自己甩上、平衡。</span><span class="rip-step__out">policy_weights_student.h</span></a></li>
</ul>

## 檔案怎麼一路傳下去

<div class="rip-flow" markdown>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">:material-robot-industrial: 你的機台</div>
  <div class="rip-flow__edge" markdown="span"><code>sysid_wizard.py</code><span>Step 0</span></div>
  <div class="rip-flow__node" markdown="span"><code>sysid_params.json</code><small>擺錘鉸鏈的摩擦</small></div>
  <div class="rip-flow__edge" markdown="span"><code>curriculum_train.py</code><span>Step 1</span></div>
  <div class="rip-flow__node" markdown="span"><code>v1_stage3/best_model.zip</code><small>256×256 教師（模擬）</small></div>
  <div class="rip-flow__edge rip-flow__edge--loop" markdown="span"><code>finetune_async.py</code> × N 段，每段後 <code>run_policy.py</code><span>Step 2</span></div>
  <div class="rip-flow__node" markdown="span"><code>ftN/best_model.zip</code><small>微調後的教師 ＋ replay buffer</small></div>
  <div class="rip-flow__edge" markdown="span"><code>distill_student.py</code><span>Step 3</span></div>
  <div class="rip-flow__node" markdown="span"><code>distill_h16_dagger_dev/student.pt</code><small>16 個神經元的學生</small></div>
  <div class="rip-flow__edge" markdown="span"><code>export_weights.py</code> → Arduino IDE 上傳<span>Step 4</span></div>
  <div class="rip-flow__node rip-flow__node--rig" markdown="span">:material-chip: Nano 獨立執行<small><code>analyze_onboard.py</code> 評分</small></div>
</div>

每個方框是一個檔案，方框之間是產生它的指令（都在 `policy/` 裡執行，見[工具與指令](../prepare/tools.md#cli)）。**每一步的輸出檔，就是下一步指令裡要你填的路徑。** Step 2 會重複好幾段，每段跑完都用 `run_policy.py` 接線測一次。

## 每一步要不要機台、要燒什麼

| 步驟 | 要不要機台 | Nano 要燒的韌體 | 用到的指令 |
| --- | --- | --- | --- |
| [Step 0](step0-sysid.md) | 要 | `LowLevelServer` | `sysid_wizard.py` |
| [Step 1](step1-train.md) | 不用 | — | `curriculum_train.py`、`train_sac.py --eval`、`analyze_symmetry.py`、`analyze_sim.py` |
| [Step 2](step2-finetune.md) | 要 | `LowLevelServer` | `run_policy.py`、`sim_vs_real.py`、`finetune_async.py`、`analyze_sim.py` |
| [Step 3](step3-distill.md) | 不用（選做的接線測試要） | 選做：`LowLevelServer` | `distill_student.py`、`analyze_sim.py`、選做 `run_policy.py` |
| [Step 4](step4-deploy.md) | 要 | `RLControl` | `export_weights.py`、`analyze_onboard.py` |

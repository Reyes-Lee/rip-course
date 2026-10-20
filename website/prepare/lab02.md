# Lab02 環境預習

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 一堂課</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台</span>
  <span class="rip-chip">:material-notebook-outline: Jupyter notebook</span>
</div>

專題開始前的 Lab02 只做一件事：把電腦的開發環境裝好。notebook 裡每個套件的小範例，都是從這個網站和課程 repo 實際用到的程式或數字縮小來的；每一段都附連結，連回網站對應的地方。

[:material-download: 下載 Lab02 notebook](https://github.com/Reyes-Lee/rip-course/raw/main/labs/Lab02_environment_setup.ipynb){ .md-button .md-button--primary }
[在 GitHub 上看](https://github.com/Reyes-Lee/rip-course/blob/main/labs/Lab02_environment_setup.ipynb){ .md-button }

## 每個練習在專題裡的哪裡

| Lab02 段落 | 套件 | 練習內容 | 專題裡在哪裡用到 |
| --- | --- | --- | --- |
| Part 2 開頭 | NumPy | 用擺錘的質量、質心、慣量算自然頻率 12.46 rad/s | [Step 1 參數怎麼送進 MuJoCo](../steps/step1-train.md#params)、`model/model.urdf` |
| 2-1 | NumPy | 角度包到 ±π；組出 6 個數 × 4 幀 = 24 維的觀測 | [Step 1 策略看到什麼](../steps/step1-train.md#obs)、`policy/pendulum_env.py` |
| 2-1 | NumPy | 把 0–4095 的編碼器讀數累積成圈數 | [編碼器測試](hardware.md#encoder)、`02_check_encoder` |
| 2-2 | Matplotlib | 畫一段自由擺的角度曲線 | [Step 0 檢查點](../steps/step0-sysid.md#checkpoint)的 `freeswing_compare.png` |
| 2-3 | SciPy | 用 `curve_fit` 擬合自由擺，求 ω<sub>n</sub> 並對照 12.3–12.6 rad/s | [Step 0 sysid 精靈](../steps/step0-sysid.md#wizard)、`policy/sysid_core.py` |
| 2-4 | PyTorch | 建 24 → 16 → 16 → 1 的學生網路；689 個參數、2756 bytes；估算 Nano 推論時間 | [Step 3 蒸餾](../steps/step3-distill.md#what)、[Step 4 匯出](../steps/step4-deploy.md#flash)、`policy/distill.py` |
| 2-5 | Gymnasium | 迷你版倒單擺環境：同樣的 24 維觀測、動作與 reward 公式，跑一次 `reset()`／`step()` | [Step 1 模擬訓練在做什麼](../steps/step1-train.md#what)、[Reward](../steps/step1-train.md#reward)、`policy/reward.py` |
| 2-6 | Stable-Baselines3、TensorBoard | 用課程設定（256×256、gSDE）建 SAC，訓練 400 步並寫出 TensorBoard 紀錄 | [Step 1](../steps/step1-train.md#what)、[Step 2 微調](../steps/step2-finetune.md#finetune)、`policy/train_sac.py` |
| 2-7 | PySerial | 用 CH340 晶片找 Nano 的序列埠；組出 `LowLevelServer` 的指令與 20 bytes 的狀態封包 | [工具一覽](tools.md)、[Step 2 LowLevelServer](../steps/step2-finetune.md#flash)、`policy/lowlevel_client.py` |
| 2-8 | Trimesh | 算 10 元硬幣的慣量，驗證「硬幣偏 3 mm，ω<sub>n</sub> 變約 1.6%」 | [貼上配重硬幣](hardware.md#coin)、[Step 0 配重與幾何](../steps/step0-sysid.md#geometry) |
| Part 3 | Arduino IDE | 安裝 AVR Boards 與 FastAccelStepper、AccelStepper、AS5600 | [安裝環境](install.md)、`firmware/` |
| Part 4 | MuJoCo | 骨牌場景：從 XML 字串建模型、`mj_step`、離線渲染、互動視窗 | [Step 1 參數怎麼送進 MuJoCo](../steps/step1-train.md#params)、[MuJoCo 視窗](../steps/step1-train.md#mujoco)、`12_view_policy` |

!!! info "Lab02 的環境和專題的環境是分開的"

    Lab02 在 `~/pendulum`（Windows：`C:\pendulum`）建一個自己的 `.venv`，用來練習。專題開始後，課程工具會用 uv 在課程 repo 裡另外建環境，套件清單相同，不用再手動安裝；Lab02 的資料夾之後可以刪掉。

# 工具與指令

事前準備（安裝、上電測試）用**點兩下的工具**；Step 0–4 的訓練流程用**自己下指令**，跟作者的做法一樣。每一步會產生哪個檔案、下一步要把哪個檔案餵進去，都要你自己接起來。

## 事前準備的工具（點兩下）

macOS 在 Finder 打開 `tools/<名稱>.command`，Windows 在檔案總管打開 `tools\<名稱>.bat`。每個工具開頭會提醒你該燒哪個韌體，結束時印出結果與檔案位置。

| 工具 | 先燒的韌體 | 做什麼 | 用在 |
| --- | --- | --- | --- |
| `00_setup` | — | 環境、列出 Nano 的序列埠 | [第一次](install.md#setup) |
| `01_check_serial` | TestSerial | 量 serial 來回延遲 | [上電測試](hardware.md#power-on) |
| `02_check_encoder` | EncoderCheck | 磁場強度、對心、轉圈連續性，逐項 PASS/FAIL | [上電測試、每次開工](hardware.md#encoder) |
| `03_check_motor` | LowLevelServer | 加速度逐級升到 150 rad/s²，檢查失步 | [上電測試](hardware.md#power-on) |
| `04_check_direction` | LowLevelServer | 擺錘方向跟模擬一致，結果存進 Nano 的 EEPROM | [上電測試、換零件後](hardware.md#direction) |

!!! warning "點兩下後只看到 `no such file or directory` 或 `[程序完成]`"

    正常打開時，第一行是工具名稱，接著提醒要燒哪個韌體。只看到 `no such file or directory` 或 `[程序完成]`，代表**工具沒有執行**，`[程序完成]` 不代表成功。常見於裝了 oh-my-zsh、powerlevel10k 或 conda 的 macOS（終端機啟動較慢，吃掉了路徑的第一個字）。先回 Finder 再點兩下一次；還是一樣就打開終端機，等提示字元出現後輸入 `bash `（後面有空格），把 `.command` 檔拖進視窗，按 Enter。

## Step 0–4：自己下指令 { #cli }

### 開一個終端機，進到 `policy/`

所有指令都在 `policy/` 資料夾裡執行，前面加 `uv run`（uv 會自動用課程的 Python 環境）。

=== ":material-apple: macOS"

    打開「終端機」：

    ```bash
    cd ~/rip-course/policy
    uv run python train_sac.py --help
    ```

    **會打開 MuJoCo 視窗的指令**（`--eval`）要用 `mjpython`，不是 `python`：`uv run mjpython train_sac.py --eval …`。

=== ":material-microsoft-windows: Windows"

    打開 PowerShell：

    ```powershell
    cd C:\rip-course\policy
    uv run python train_sac.py --help
    ```

    網站上的指令用 `\` 換行，那是 macOS／Linux 的寫法。在 PowerShell 裡請**整行打在同一行**（或把行尾的 `\` 換成 `` ` ``）。路徑裡的 `/` 在 Windows 也可以用。

每個腳本都可以加 `--help` 看所有參數。

### `<PORT>`：Nano 的序列埠

指令裡寫 `<PORT>` 的地方，換成你的 Nano 的序列埠：`00_setup` 最後會印出來，Arduino IDE 的「工具 → 連接埠」也看得到。

- macOS：`/dev/cu.usbserial-xxxx` 或 `/dev/cu.wchusbserial-xxxx`
- Windows：`COM3`、`COM4`…

序列埠同一時間只能給一個程式用：**跑指令前先關掉 Arduino IDE 的序列埠監控**。

### 檔案會放在哪裡 { #files }

指令產生的檔案都在 `policy/` 底下，**不會進 git**，`git pull` 不會蓋掉。名稱是你自己在指令裡取的，下表是網站範例用的名稱：

```text
policy/
├── sysid_params.json            Step 0：你的機台的摩擦參數（之後訓練時要指定它）
├── sysid_runs/<時間>/            Step 0：原始錄製與兩張檢查圖
├── runs/
│   ├── v1_stage1/ … v1_stage3/  Step 1：三階段教師，最後用 v1_stage3/best_model.zip
│   ├── ft1/  ft2/ …             Step 2：每段微調的 best_model.zip 與 replay_buffer.pkl
│   └── ft3/distill_h16_dagger_dev/student.pt   Step 3：蒸餾出的學生
└── recordings/                  Step 2–4：實機測試的紀錄（.npz）
```

每個 `runs/<名稱>/` 裡有 `best_model.zip`（訓練中評估分數最高的版本）和 `last.zip`（最後一步的版本）。**一律用 `best_model.zip`**。`config.json` 記錄了這支策略的設定，下游的腳本會從它讀控制頻率、動作模式和 sysid 檔。

### 中途停止

在終端機按 ++ctrl+c++（macOS 也是 Ctrl，不是 Command）。

### 作者的其他工具

`policy/` 裡還有作者用來分析的腳本，網站的步驟沒有全部用到，進階任務可能會用上。用途見作者網站的 [Python tooling](https://ferrolho.github.io/rotary-inverted-pendulum/reference/python/)，例如：

| 腳本 | 做什麼 |
| --- | --- |
| `sim_vs_real.py` | 把實機紀錄的動作丟回模擬重播，比較兩邊的軌跡（[Step 2](../steps/step2-finetune.md#zero-shot) 會用） |
| `analyze_sim.py --kick-amp` | 在模擬裡推擺錘，測擾動恢復；`disturbance.py` 說明每個指標的意義 |
| `eval_dr_sensitivity.py` | 看策略對各個隨機化參數有多敏感 |
| `fft_deploy.py` | 實機紀錄的頻譜，查震動 |

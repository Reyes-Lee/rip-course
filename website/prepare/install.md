# 安裝環境

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 30 分鐘（多半在等下載）</span>
  <span class="rip-chip">:material-laptop: macOS／Windows</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台</span>
</div>

兩個系統的流程完全一樣，只有安裝方式不同。每個工具都有 macOS 的 `.command` 與 Windows 的 `.bat` 兩個入口檔，執行後呼叫同一支 Python 腳本。下面每個區塊都可以切換 macOS／Windows，選一次之後整個網站都會記住。

## 1. 安裝軟體

=== ":material-apple: macOS"

    | 項目 | 怎麼裝 |
    | --- | --- |
    | Arduino IDE | 到 [arduino.cc](https://www.arduino.cc/en/software) 下載 macOS 版，拖進「應用程式」 |
    | Git | 打開「終端機」，執行 `xcode-select --install`，照視窗指示安裝 |
    | USB 驅動（CH340） | 系統內建，通常不用裝 |
    | uv | 在終端機執行下面這行 |

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    裝完 uv **要關掉終端機再重開**，`uv` 指令才會生效。

=== ":material-microsoft-windows: Windows"

    | 項目 | 怎麼裝 |
    | --- | --- |
    | Arduino IDE | 到 [arduino.cc](https://www.arduino.cc/en/software) 下載 Windows 版安裝 |
    | Git | 安裝 [Git for Windows](https://git-scm.com/download/win)，選項都用預設 |
    | USB 驅動（CH340） | Nano 插上後，打開「裝置管理員 → 連接埠」。看不到 `USB-SERIAL CH340 (COMx)` 時，安裝 WCH 的 CH341SER 驅動（助教會附連結） |
    | uv | 打開 PowerShell，執行下面這行 |

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

    裝完 uv **要關掉 PowerShell 再重開**，`uv` 指令才會生效。

## 2. 設定 Arduino IDE

1. 打開 Arduino IDE，Nano 用 USB-C 傳輸線接上電腦。
2. 選單「工具 → 開發板」選 **Arduino Nano**。
3. 「工具 → 處理器」選 **ATmega328P (Old Bootloader)**。選錯會上傳逾時，看起來像線壞了。
4. 「工具 → 連接埠」選 Nano 對應的那個。
5. 「工具 → 管理程式庫」，搜尋並安裝三個程式庫：**AS5600**（作者 Rob Tillaart）、**FastAccelStepper**、**AccelStepper**（`TestMotor` 用）。

## 3. 取得課程檔案 { #get-files }

所有檔案（程式、韌體、模型、流程工具）都放在助教的 GitHub：[Reyes-Lee/rip-course](https://github.com/Reyes-Lee/rip-course)。用 `git clone` 下載一份到自己的電腦，之後助教更新時用 `git pull` 拿新版。

=== ":material-apple: macOS"

    放在家目錄，**不要放在有 iCloud 同步的「桌面」或「文件」**。打開「終端機」，執行：

    ```bash
    cd ~
    git clone https://github.com/Reyes-Lee/rip-course.git
    ```

    完成後會多出 `~/rip-course` 資料夾。在 Finder 按 ++cmd+shift+g++，輸入 `~/rip-course` 就能打開。

=== ":material-microsoft-windows: Windows"

    路徑**不要有中文或空格**，建議放在 `C:\rip-course`。打開 PowerShell，執行：

    ```powershell
    cd C:\
    git clone https://github.com/Reyes-Lee/rip-course.git
    ```

    完成後會多出 `C:\rip-course` 資料夾。

??? info "不想用 git：下載 ZIP"

    在 [GitHub 頁面](https://github.com/Reyes-Lee/rip-course)按綠色的「Code → Download ZIP」，解壓到上面建議的位置，資料夾改名成 `rip-course`。

    - macOS 解壓後要在終端機多跑一行，工具才能執行：`chmod +x ~/rip-course/tools/*.command`
    - 缺點：之後助教更新時，要重新下載 ZIP，並把舊資料夾裡的 `policy/runs/`、`policy/sysid_params.json` 搬到新資料夾。用 git 就不用。

### 助教更新檔案時 { #update }

助教在課堂或公告說「有更新」時，照下面做。你自己產生的檔案（訓練結果、sysid、紀錄檔）不在 repo 裡，**更新不會蓋掉它們**。

=== ":material-apple: macOS"

    ```bash
    cd ~/rip-course
    git pull
    ```

=== ":material-microsoft-windows: Windows"

    ```powershell
    cd C:\rip-course
    git pull
    ```

看到 `Already up to date.` 代表已經是最新版。如果出現 `error: Your local changes ... would be overwritten`，代表你改過 repo 裡的檔案；把整段訊息截圖給助教，不要自己刪檔案。

## 4. 執行 `00_setup` { #setup }

!!! tool "操作步驟"

    1. 打開 repo 裡的 `tools` 資料夾，執行 `00_setup`（macOS 點 `00_setup.command`，Windows 點 `00_setup.bat`）。
    2. 第一次執行會被系統擋下來時：
        - macOS：在檔案上按右鍵 →「打開」→ 再按「打開」。
        - Windows：SmartScreen 跳出時按「其他資訊 → 仍要執行」。
    3. uv 會自動下載 Python 3.13、PyTorch、MuJoCo 等套件。第一次要幾分鐘到十幾分鐘，畫面會持續跑進度。
    4. 畫面列出偵測到的 Nano 序列埠；只有一個就直接按 Enter，有多個就輸入編號。

!!! checkpoint "通過條件"

    `00_setup` 最後印出這四樣東西：

    - `Python 3.13.x`
    - `mujoco` 的版本
    - `torch` 的版本
    - 你的 Nano 序列埠（macOS 是 `/dev/cu.usbserial-xxxx` 或 `/dev/cu.wchusbserial-xxxx`，Windows 是 `COM3`、`COM4`…）

    **沒看到序列埠**：先換一條 USB-C 線（有些線只能充電，不能傳資料），Windows 再確認 CH340 驅動，然後重新執行 `00_setup`。

## 課程 repo 的結構

```text
rip-course/
├── firmware/        用 Arduino IDE 開啟、上傳
│   ├── TestHeartbeat/  TestMotor/  TestSerial/   作者的上電測試
│   ├── EncoderCheck/      磁場強度與對心測試（課程新增）
│   ├── LowLevelServer/    接線模式：失步測試、sysid、微調、測試都用它
│   └── RLControl/         獨立執行的策略
├── policy/          Python：模擬、訓練、sysid、蒸餾（來自作者）
├── model/
│   └── model.urdf         擺錘質量與慣量（已更新為 10 元硬幣配重）
└── tools/           流程工具，每個工具都是同名的三個檔
    ├── 00_setup.command   00_setup.bat   00_setup.py
    └── …
```

你執行工具後產生的檔案都在 `policy/` 底下，不會進 repo：

| 檔案 | 哪一步產生 |
| --- | --- |
| `policy/sysid_params.json` | Step 0 |
| `policy/runs/v1_stage1…3/` | Step 1 |
| `policy/runs/ft1/`、`ft2/`… | Step 2 |
| `policy/runs/ftN/distill_h16_dagger_dev/student.pt` | Step 3 |
| `policy/recordings/*.npz` | Step 2–4 的測試紀錄 |

# 安裝環境

<div class="rip-meta" markdown>
  <span class="rip-chip rip-chip--cyan">:material-clock-outline: 約 30 分鐘（多半在等下載）</span>
  <span class="rip-chip">:material-laptop: macOS／Windows</span>
  <span class="rip-chip">:material-robot-off-outline: 不需要機台</span>
</div>

兩個系統的流程完全一樣，只有安裝方式不同。每個工具都有 macOS 的 `.command` 與 Windows 的 `.bat` 兩個入口檔，雙擊後呼叫同一支 Python 腳本。下面每個區塊都可以切換 macOS／Windows，選一次之後整個網站都會記住。

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

1. 打開 Arduino IDE，Nano 用 USB 接上電腦。
2. 選單「工具 → 開發板」選 **Arduino Nano**。
3. 「工具 → 處理器」選 **ATmega328P (Old Bootloader)**。選錯會上傳逾時，看起來像線壞了。
4. 「工具 → 連接埠」選 Nano 對應的那個。
5. 「工具 → 管理程式庫」，搜尋並安裝 **AS5600**（作者 Rob Tillaart）與 **FastAccelStepper**。

## 3. 下載課程 repo

=== ":material-apple: macOS"

    放在家目錄，**不要放在有 iCloud 同步的「桌面」或「文件」**。在終端機執行：

    ```bash
    cd ~
    git clone https://github.com/Reyes-Lee/rip-course.git rip-course
    ```

    也可以在 GitHub 頁面按「Code → Download ZIP」解壓到 `~/rip-course`，但之後要在終端機多跑一行，讓工具可以雙擊：

    ```bash
    chmod +x ~/rip-course/tools/*.command
    ```

=== ":material-microsoft-windows: Windows"

    路徑**不要有中文或空格**，建議 `C:\rip-course`。在 PowerShell 執行：

    ```powershell
    cd C:\
    git clone https://github.com/Reyes-Lee/rip-course.git rip-course
    ```

    也可以在 GitHub 頁面按「Code → Download ZIP」，解壓到 `C:\rip-course`。

## 4. 雙擊 `00_setup` { #setup }

!!! tool "操作步驟"

    1. 打開 repo 裡的 `tools` 資料夾，雙擊 `00_setup`（macOS 點 `00_setup.command`，Windows 點 `00_setup.bat`）。
    2. 第一次執行會被系統擋下來時：
        - macOS：在檔案上按右鍵 →「打開」→ 再按「打開」。
        - Windows：SmartScreen 跳出時按「其他資訊 → 仍要執行」。
    3. uv 會自動下載 Python 3.13、PyTorch、MuJoCo 等套件。第一次要幾分鐘到十幾分鐘，畫面會持續跑進度。
    4. 畫面問 `組別名稱:` 時，輸入助教給的組別代號（例如 `g3`），按 Enter。之後所有工具都會用這個名稱命名檔案。
    5. 畫面列出偵測到的 Nano 序列埠；只有一個就直接按 Enter，有多個就輸入編號。

!!! checkpoint "通過條件"

    `00_setup` 最後印出這四樣東西：

    - `Python 3.13.x`
    - `mujoco` 的版本
    - `torch` 的版本
    - 你的 Nano 序列埠（macOS 是 `/dev/cu.usbserial-xxxx` 或 `/dev/cu.wchusbserial-xxxx`，Windows 是 `COM3`、`COM4`…）

    **沒看到序列埠**：先換一條 USB 線（有些線只能充電），Windows 再確認 CH340 驅動，然後重新雙擊 `00_setup`。

## 課程 repo 的結構

```text
rip-course/
├── firmware/        用 Arduino IDE 開啟、上傳
│   ├── TestHeartbeat/  TestMotor/  TestSerial/
│   ├── EncoderCheck/      磁場強度與對心測試
│   ├── MotorStepCheck/    高加速度失步測試
│   ├── LevelCheck/        底座傾斜測量
│   ├── LowLevelServer/    接線模式（sysid、微調、測試）
│   └── RLControl/         獨立執行的策略
├── policy/          Python：模擬、訓練、sysid、蒸餾（來自作者）
├── model/
│   ├── model.urdf         已更新為 10 元硬幣配重
│   └── meshes/            作者的 STL（不修改）
└── tools/           雙擊工具，每個工具都是同名的三個檔
    ├── 00_setup.command   00_setup.bat   00_setup.py
    └── …
```

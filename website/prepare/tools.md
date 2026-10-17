# 工具一覽

Nano 用 USB-C 線接上電腦、燒好對應的韌體，再執行工具，就會由 Python 直接控制機台。執行方式：macOS 在 Finder 打開 `tools/<名稱>.command`，Windows 在檔案總管打開 `tools\<名稱>.bat`（兩者都是點兩下）。每個工具開頭會提醒你該燒哪個韌體，結束時印出結果與檔案位置。

| 工具 | 先燒的韌體 | 做什麼 | 用在 |
| --- | --- | --- | --- |
| `00_setup` | — | 環境、序列埠 | [第一次](install.md#setup) |
| `01_check_serial` | TestSerial | 量 serial 來回延遲 | [上電測試](hardware.md#power-on) |
| `02_check_encoder` | EncoderCheck | 磁場強度、對心、轉圈連續性，逐項 PASS/FAIL | [上電測試、每次開工](hardware.md#encoder) |
| `03_check_motor` | LowLevelServer | 加速度逐級升到 150 rad/s²，檢查失步 | [上電測試](hardware.md#power-on) |
| `05_sysid` | LowLevelServer | 系統識別精靈 | [Step 0](../steps/step0-sysid.md) |
| `06_train_teacher` | — | 三階段模擬訓練＋印出檢查點數字 | [Step 1](../steps/step1-train.md) |
| `07_finetune` | LowLevelServer | 實機微調，自動接續上一段 | [Step 2](../steps/step2-finetune.md) |
| `08_test_policy` | LowLevelServer | 接線測試 30 秒，印誠實指標 | [Step 2–3](../steps/step2-finetune.md) |
| `09_distill` | — | BC＋DAgger＋敏感度關卡 | [Step 3](../steps/step3-distill.md) |
| `10_export_weights` | — | 核對 sketch 常數，匯出 `policy_weights_student.h` | [Step 4](../steps/step4-deploy.md) |
| `11_score_onboard` | RLControl | 獨立執行 60 秒評分 | [Step 4](../steps/step4-deploy.md) |
| `12_view_policy` | — | 在 MuJoCo 視窗播放策略 30 秒 | [Step 1–2](../steps/step1-train.md#mujoco) |
| `13_check_sim` | — | 對稱性＋敏感度關卡，印出數字 | [Step 1–3](../steps/step1-train.md#checkpoint) |

## 所有工具共通的操作方式

<div class="grid cards" markdown>

-   :material-format-list-numbered:{ .lg .middle } **選檔案：輸入編號**

    ---

    需要選檔案的工具（例如要測哪一支策略）會列出編號清單，輸入編號按 Enter。**直接按 Enter 就是預設值，預設一律是最新的那一個。**

-   :material-keyboard-return:{ .lg .middle } **回答問題：`[ ]` 是預設值**

    ---

    例如畫面問 `run 名稱 [g3_v1]:`，直接按 Enter 就是用 `g3_v1`。

-   :material-stop-circle-outline:{ .lg .middle } **中途停止：++ctrl+c++**

    ---

    在工具的視窗裡按 ++ctrl+c++。macOS 也是 Ctrl，不是 Command。

-   :material-console:{ .lg .middle } **「背後執行的指令」不用自己打**

    ---

    每一步列出的指令只是讓你知道工具在做什麼。所有動作都寫成「執行哪個工具 → 畫面問什麼 → 輸入什麼 → 看到什麼算通過」。

</div>

!!! warning "工具和 Arduino IDE 不能同時用序列埠"

    執行工具前先關掉 Arduino IDE 的序列埠監控視窗。工具會自動找 Nano 的序列埠，接了不只一個裝置時會請你選。

所有工具都一律使用 `best_model.zip`（訓練中評估分數最高的版本），不會用同一個資料夾裡的 `last.zip`（最後一步的版本，不一定最好），你不用選。

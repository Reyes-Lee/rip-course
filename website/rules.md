# 專題規則

這一頁是期末專題的規定：繳交什麼、demo 怎麼進行、器材的使用規定。評分項目與 demo 日期會另外公告。

!!! info "截止時間"

    **2026-12-16（三）23:59**（台灣時間）。網站最上方有倒數。

## 兩條硬規定 { #hard-rules }

<div class="grid cards" markdown>

-   :material-chip:{ .lg .middle } **最後的模型在 Nano 上跑**

    ---

    demo 時由助教把你們繳交的程式碼燒進 Nano。筆電會接著，負責供電和記錄分數，甩上、平衡的動作全部由 Nano 上的網路計算。在筆電上算動作的控制器（例如 `08_test_policy`）不算。

-   :material-brain:{ .lg .middle } **一定要用 RL**

    ---

    燒進 Nano 的網路，必須來自你們自己用強化學習訓練的策略。

</div>

## 可以改什麼、不能改什麼 { #scope }

網站的五個步驟是**建議做法**，你們不一定要用課程工具或作者的程式。

| 可以自由決定 | 不能改 |
| --- | --- |
| reward 的權重與公式 | 課程版 `firmware/RLControl/RLControl.ino` |
| RL 演算法與函式庫（不一定要 SAC 或 SB3） | 韌體接口：網路結構 24 → H → H → 1、觀測（最近 4 幀）、50 Hz、速度上限 3.5 rad/s、加速度上限 150 rad/s²、動作平滑 4 拍，見 [Step 4「`RLControl.ino` 固定了什麼」](steps/step4-deploy.md#fixed) |
| 訓練步數、SEED、微調回合數與段數 | 硬體：Vref、微步、接線、編碼器、配重照交付狀態，不加感測器或機構輔助 |
| 蒸餾方法、隱藏層大小 H（要守住約 50 Hz 與 30720 bytes） | |
| 直接用 RL 訓練小網路、不蒸餾（這時教師就是它本身） | |

**不允許**：Nano 上的網路用 RL 教師以外的東西當標籤，例如 LQR、PID、手動示範。

## 繳交 { #submit }

繳交方式另外公告。demo 用的就是你們繳交的檔案，**demo 當天不能換檔**。

| 繳交內容 | 說明 |
| --- | --- |
| Nano 用的權重檔 | `firmware/RLControl/policy_weights_student.h` |
| 教師與訓練紀錄 | 照課程流程的話，交 `policy/runs/` 裡 Step 1 的每個階段（`<名稱>_stage1`～`stage3`）和 Step 2 的每一段（`ft1`、`ft2`…）整個資料夾，包含 `best_model.zip`、`config.json`、`reward_used.py` 和訓練過程的紀錄。`replay_buffer.pkl`、`checkpoints/`、`checkpoint_ep*.zip` 檔案很大，不用交 |
| 程式碼 | 在 `rip-course` 資料夾執行 `git diff > changes.diff`，交 `changes.diff`，加上你們新增的檔案 |

**教師的格式**：RL 演算法和函式庫不限，但交出來的教師必須能在課程 repo 的 Python 環境（`policy/`，有 PyTorch、numpy、Stable-Baselines3）裡直接執行：

- 用 Stable-Baselines3（照課程流程就是）：交 `.zip`。
- 用其他方法：另外交一支只用上面這些套件的 `teacher_act.py`，提供 `act(obs) -> action`。`obs` 是 24 個數（觀測的格式見 [Step 1](steps/step1-train.md#obs)），`action` 在 −1 到 1 之間。

助教會用同一批模擬狀態，比對 Nano 上的網路和你們的教師輸出的動作，確認 Nano 網路是從這支教師來的。

## Demo { #demo }

1. 用你們自己的機台。
2. 助教用課程版 `RLControl.ino` 加上你們繳交的 `policy_weights_student.h`，燒進 Nano。
3. 手臂轉回正中間、擺錘靜止垂下，按 RESET 開始；助教用 `11_score_onboard` 記錄。
4. 助教會請組員說明訓練過程，例如改了哪些地方、為什麼。

要做的任務與評分方式會另外公告。

## 器材使用規定 { #equipment }

1. **領取時現場測試**：助教和你們一起做編碼器（`02_check_encoder`）、馬達（`03_check_motor`）、方向（`04_check_direction`）三項測試，並清點零件、拍照。有問題當場更換。測試完雙方在點交單上簽名，之後以點交單為準。
2. **之後的損壞**：正常使用下的損壞，每組每一種零件可以免費更換一次。需要更換時直接找助教，換新時請交回壞掉的零件，交不出來就視為遺失。
3. **不算正常使用的情況**：違反網站上明確寫出的注意事項（例如 12 V 接著時插拔馬達線、轉 TMC2209 的 Vref 可變電阻、12 V 接到 Nano、AS5600 的 DIR 腳接 5V）、摔落、自行改裝硬體。這些損壞不免費更換。是否屬於正常使用，由助教和老師判斷，你們可以說明情況。
4. **遺失**不免費補。
5. **繳回**：繳回日期另外公告。損壞或遺失、而且不屬於正常使用的零件，全組依價格表照價賠償。價格表另外公告。
6. 課程發放 12 V 電源供應器與軸承；USB-C 傳輸線（要能傳資料）和 10 元硬幣請自備。杜邦線、膠帶、螺絲等消耗品不在此規則內。

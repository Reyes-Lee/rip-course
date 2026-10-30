<div align="center">

# RL 旋轉倒單擺 Sim2Real

**AI 概論課程專題**：用強化學習在 MuJoCo 裡訓練策略，搬到真實的旋轉倒單擺上微調，<br>
最後蒸餾成 16 個神經元的小網路，燒進 Arduino Nano 獨立執行。

### 📖 [打開教學網站](https://reyes-lee.github.io/rip-course/)

</div>

> [!IMPORTANT]
> 所有步驟、指令、檢查點都在**教學網站**上。這份 README 只說明怎麼下載。

## 下載

macOS（放在家目錄，不要放在有 iCloud 同步的「桌面」或「文件」）：

```bash
cd ~
git clone https://github.com/Reyes-Lee/rip-course.git
```

Windows（路徑不要有中文或空格）：

```powershell
cd C:\
git clone https://github.com/Reyes-Lee/rip-course.git
```

下載後照網站的[安裝環境](https://reyes-lee.github.io/rip-course/prepare/install/)，執行 `tools/00_setup` 開始。

助教更新檔案後，在 `rip-course` 資料夾執行 `git pull` 就能拿到新版。你自己產生的訓練結果、sysid 檔都不在 repo 裡，更新不會蓋掉。

## 流程

```mermaid
flowchart LR
    S0[Step 0<br/>系統識別] --> S1[Step 1<br/>模擬訓練]
    S1 --> S2[Step 2<br/>實機微調]
    S2 --> S3[Step 3<br/>蒸餾]
    S3 --> S4[Step 4<br/>燒錄與評分]
```

## 資料夾

| 資料夾 | 內容 |
| --- | --- |
| `firmware/` | Arduino sketch，用 Arduino IDE 開啟、上傳 |
| `policy/` | Python：模擬、訓練、sysid、蒸餾 |
| `model/` | 機台模型參數（URDF） |
| `tools/` | 事前準備的硬體測試工具（macOS `.command`、Windows `.bat`） |
| `website/` | 教學網站原始檔 |

## 來源與授權

整套流程與程式來自 Henrique Ferrolho 的 [rotary-inverted-pendulum](https://github.com/ferrolho/rotary-inverted-pendulum)（MIT License）。課程版只改了硬體相關的常數，加上硬體測試工具，並把 `curriculum_train.sh`、`distill_student.sh` 改寫成 Python。

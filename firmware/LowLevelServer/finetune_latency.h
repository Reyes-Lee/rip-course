// 實機微調（07_finetune）時要不要加延遲。專題任務用；一般流程維持 0、0。
//
// 每次 ENGAGE（也就是每一回合開始）在 [FT_LATENCY_MIN_MS, FT_LATENCY_MAX_MS]
// 之間均勻抽一個整數毫秒，這一回合的 GET_STATE 都回傳比最新樣本舊這麼多的那一筆
// （位置、速度、時間戳一起變舊；依時間戳挑最接近的樣本，誤差約 ±1 ms）。
// 這個延遲是「加在原本的延遲上面」，跟 RLControl 的 latency_profile.h 一樣。
//
// 範圍：0 ≤ MIN ≤ MAX ≤ 70（和 RLControl 序列埠指令的上限一樣，涵蓋延遲階梯的最高階 +55）。改完要重新上傳 LowLevelServer；
// 07_finetune 會讀這個檔案，把設定印出來並存進 runs/ftN/07_settings.json。
// 微調完要回到一般流程時，記得改回 0、0 再上傳：所有走 LowLevelServer、會 engage 的工具
// （03_check_motor、04_check_direction、05_sysid 的馬達掃描、07、08_test_policy）都會帶著這個延遲。
#define FT_LATENCY_MIN_MS 0
#define FT_LATENCY_MAX_MS 0

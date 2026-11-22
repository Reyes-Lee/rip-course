// 實機微調（07_finetune）時要不要加延遲。專題任務用；一般流程維持 0、0。
//
// 每次 ENGAGE（也就是每一回合開始）在 [FT_LATENCY_MIN_MS, FT_LATENCY_MAX_MS]
// 之間均勻抽一個整數毫秒，這一回合的 GET_STATE 都回傳比最新樣本舊這麼多的那一筆
// （位置、速度、時間戳一起變舊；依時間戳挑最接近的樣本，誤差約 ±1 ms）。
// 這個延遲是「加在原本的延遲上面」，跟 RLControl 的 latency_profile.h 一樣。
//
// 範圍：0 ≤ MIN ≤ MAX ≤ 70（和延遲階梯的最高階一樣）。改完要重新上傳 LowLevelServer；
// 07_finetune 會讀這個檔案，把設定印出來並存進 runs/ftN/07_settings.json。
// 微調完要回到一般流程（08 測試、04 檢查方向）時，可以不用改回來，
// 但要記得：08_test_policy 也會帶著這個延遲。
#define FT_LATENCY_MIN_MS 0
#define FT_LATENCY_MAX_MS 0

// 延遲注入設定（專題任務用）。課程預設：不注入，RLControl 的行為和以前完全一樣。
//
// 練習時改這個檔再上傳 RLControl，就能在自己的機台上模擬「Nano 讀到的資料比較舊」。
// 格式 { {start_s, extra_ms, jitter_ms} }，只能寫一段：
//   start_s   固定寫 0（從 engage 開始就用這個延遲）
//   extra_ms  每一拍都額外延遲的毫秒數
//   jitter_ms 每一拍再隨機多延遲 0..jitter_ms 毫秒
// 單位是毫秒。Nano 依樣本的時間戳挑最接近的一筆（取樣間隔實際約 2–3 ms，所以誤差約 ±1 ms）。
// extra_ms + jitter_ms 最多 70（和序列埠指令的上限一樣）。
// 寫兩段以上、start_s 不是 0、或超過 70，編譯時會直接報錯：多段的表會佔用 Nano 的 SRAM，
// 讓堆疊不夠用。
//
// 延遲階梯和甩上到平衡計時（11_score_onboard 的選項 2、3）都用序列埠指令直接設定延遲，不看這個檔案。
//
// 例：固定多 20 ms，再加上每拍 0–10 ms 的抖動
//   #define LATENCY_STAGES { {0, 20, 10} }
//
// demo 用課程版（不注入），延遲由 11_score_onboard 用序列埠指令設定。開機時序列埠會印出 LATENCY_PROFILE_NAME。

#define LATENCY_PROFILE_NAME "none"
#define LATENCY_STAGES { {0, 0, 0} }

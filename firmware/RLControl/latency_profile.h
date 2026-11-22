// 延遲注入設定（進階任務用）。課程預設：不注入，RLControl 的行為和以前完全一樣。
//
// 練習時改這個檔再上傳 RLControl，就能在自己的機台上模擬「Nano 讀到的資料比較舊」。
// 每一段 {start_s, extra_ms, jitter_ms}：
//   start_s   從 engage（開始甩）後第幾秒開始用這一段，第一段必須是 0
//   extra_ms  每一拍都額外延遲的毫秒數
//   jitter_ms 每一拍再隨機多延遲 0..jitter_ms 毫秒
// 單位是毫秒。Nano 依樣本的時間戳挑最接近的一筆（取樣間隔實際約 2–3 ms，所以誤差約 ±1 ms），
// extra_ms + jitter_ms 最多 70（超過的部分會被截掉）。
//
// 延遲階梯（11_score_onboard 的選項 2）會用序列埠指令直接設定延遲，不看這個檔案。
//
// 例：固定多 20 ms，再加上每拍 0–10 ms 的抖動
//   #define LATENCY_STAGES { {0, 20, 10} }
// 例：前 20 秒不延遲，之後多 30 ms
//   #define LATENCY_STAGES { {0, 0, 0}, {20, 30, 0} }
//
// demo 時助教會換成自己的版本（不公開）；開機時序列埠會印出 LATENCY_PROFILE_NAME。

#define LATENCY_PROFILE_NAME "none"
#define LATENCY_STAGES { {0, 0, 0} }

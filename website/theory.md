# 為什麼這樣設計：sim2real 的理論

模擬和真實機台的動態永遠不會完全一樣，這個差距叫 **reality gap**。五個步驟各自處理它的一部分，而且順序有意義：先修硬體、再量測、再用隨機化涵蓋剩餘誤差、最後在實機上學掉模型完全沒有的部分。

| 落差來源 | 對策 | 在流程哪裡 | 文獻 |
| --- | --- | --- | --- |
| 物理參數不準（摩擦、慣量） | 系統識別：讓模擬的「平均」等於你的機台 | Step 0 | Ljung, *System Identification* (1999) |
| 量不準、會飄的參數 | Domain randomization：對一個機台分布訓練，真實機台只是其中一個樣本 | Step 1 | [Tobin et al. 2017](https://arxiv.org/abs/1703.06907)、[Peng et al. 2018](https://arxiv.org/abs/1710.06537) |
| 延遲、致動器、感測器特性 | 明確建模：動作延遲佇列、韌體量測模型（量化、有限差分速度、觀測延遲） | Step 1 | [Tan et al. 2018](https://arxiv.org/abs/1804.10332)、[Hwangbo et al. 2019](https://arxiv.org/abs/1901.08652) |
| 模型完全沒有的動態 | 實機微調：用真實的 (s, a, r, s′) 繼續訓練 | Step 2 | [Zhao et al. 2020（綜述）](https://arxiv.org/abs/2009.13303) |
| 部署硬體算不動大網路 | 策略蒸餾 + DAgger | Step 3 | [Rusu et al. 2016](https://arxiv.org/abs/1511.06295)、[Ross et al. 2011](https://arxiv.org/abs/1011.0686) |

## 照著做還是失敗時，依序查什麼 { #debug-order }

照流程做的成功機率很高，但不是保證。作者在配方定案後，用預設設定從頭重跑整套流程一次（重新訓練教師、重新實機微調、蒸餾、燒錄），燒進 Nano 的學生得到 balanced 0.980、最長連續平衡 265 秒；冠軍是 1.000、299 秒。差異來自每次實機微調收到的資料不同。

失敗時照 sim2real 的邏輯，**從最便宜、最常見的原因往後查**：

<ol class="rip-ol">
<li><b>硬體與設定</b>（最常見）：編碼器、接線、微步、燒錯韌體。照<a href="../troubleshooting/">疑難排解</a>表的症狀處理，不用重訓。</li>
<li><b>模型沒對上機台</b>（Step 0）：傾斜超過 1°、慣量誤差超過 10%（多半是硬幣位置）、自由擺包絡線不重疊。照 <a href="../steps/step0-sysid/#checkpoint-fail">Step 0「檢查點沒過時」</a>處理，重量後 Step 1–4 重做。</li>
<li><b>策略本身不穩健</b>（Step 1）：敏感度關卡沒過。照 <a href="../steps/step1-train/#reseed">Step 1「換一個 SEED 重訓」</a>。</li>
<li><b>模型沒有的動態</b>（Step 2）：接線測試有進步但還不穩。再雙擊 <code>07_finetune</code> 加段，照 <a href="../steps/step2-finetune/#how-long">Step 2「什麼時候停」</a>的規則。這是最有效的一招。</li>
<li><b>蒸餾或部署</b>（Step 3–4）：教師接線很穩、燒進 Nano 後不穩。照 <a href="../steps/step3-distill/#tethered">Step 3 的選做步驟</a>用 <code>08_test_policy</code> 接線測學生，再看 <code>11_score_onboard</code> 第一行的頻率是否約 50 Hz。</li>
</ol>

!!! warning "這五層都排除了，才輪到 reward 與 DR 範圍"

    到這一步請找助教討論，不要自己改。

## 幾個設計選擇的理由 { #choices }

SAC（[Haarnoja et al. 2018](https://arxiv.org/abs/1801.01290)）
:   Off-policy，可以重複使用 replay buffer 裡的資料。模擬訓練完直接把真實資料加進同一個 buffer，實機時間才夠用。最大熵目標也讓策略對擾動更強健。

gSDE 平滑探索（[Raffin et al. 2021](https://arxiv.org/abs/2005.05719)）
:   每步獨立的高斯雜訊會讓馬達爆抖；狀態相關的平滑雜訊對硬體更友善。

4 幀堆疊加上一個動作
:   有延遲時系統是部分可觀測的（POMDP），策略必須知道「還在路上的指令」才能正確推論狀態；歷史也讓它能自己濾掉速度量化雜訊。

鏡像增強
:   機台左右對稱，(s, a, r, s′) 的鏡像也是完全合法的資料。不加的話 SAC 會隨機偏好一個方向，作者觀察到手臂持續偏斜。

速度模式動作 + 4-tap 平滑
:   動作與擺錘之間少一個積分器；平滑恰好抵消控制頻率 1/2 與 1/4 的抖動。

## 從助教踩過的坑學到的事 { #lessons }

!!! quote "Reward 應該描述「任務是什麼」，而不是拿來補償模型誤差"

    助教在舊機台（5–11° 傾斜、沒做實機微調）上試過 5 次 reward 修改，3 次實機退步；其中一版模擬平衡 30–55 秒、比前一版更好，實機卻從 14 秒掉到 1.5 秒。模擬不夠準時調 reward，等於在對一個錯的系統最佳化。

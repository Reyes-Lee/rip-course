/*
 * PickupCheck — 領取器材當天的快速檢查（約 1 分鐘，不需要裝 Python 環境）
 *
 * 助教發放前先把這份燒進每一塊 Nano。學生領到後接上 USB 與 12 V，Nano 會自己依序測：
 *   1. 編碼器靜態（2 秒）：AS5600 讀得到、偵測到磁鐵、磁場不太強也不太弱、AGC 穩定
 *   2. 手轉擺錘：往同一個方向慢慢轉 2 圈，檢查沒有跳點、一圈每一格都讀得到、磁鐵對心
 *   3. 馬達：手臂在 ±45° 之間來回（約 50 與 150 rad/s²），再回到正中間。
 *      手臂真的有動，垂下的擺錘一定會被帶著擺；編碼器看不到擺動就是 12 V、馬達線或驅動板有問題。
 *      失步要靠眼睛：最後手臂末端要對齊開始前貼的膠帶記號。
 *
 * 結果：LED 恆亮 = 全部通過；LED 閃 N 下、停一下、重複 = 第 N 項沒過（看最前面的那一項）：
 *   1 下  讀不到 AS5600（接線：SDA→A4、SCL→A5、5V、GND）
 *   2 下  磁鐵：沒偵測到、太弱、太強，或 AGC 不穩（磁鐵間隙、有沒有黏牢）
 *   3 下  手轉：45 秒內沒轉滿 2 圈、有跳點，或有角度讀不到
 *   4 下  磁鐵沒對心（轉一圈磁場強度起伏太大）
 *   5 下  馬達：手臂動了但擺錘沒被帶動（12 V、馬達線、TMC2209）
 * 詳細數字印在序列埠監控（115200），填點交單用。按 RESET 或重開序列埠監控就重測一次。
 *
 * 門檻跟 tools/_lib/02_check_encoder.py 相同。完整測試（02、03、04）之後回家照網站做。
 * 需要 Arduino IDE 程式庫：AS5600（Rob Tillaart）、FastAccelStepper。
 */
#include <AS5600.h>
#include <FastAccelStepper.h>
#include <Wire.h>

// 接線與作者相同
const int DIR_PIN = 2;
const int STEP_PIN = 9;     // FastAccelStepper 在 ATmega328 上一定要用 D9（Timer1 OC1A）
const int ENABLE_PIN = 5;

const long SERIAL_BAUD_RATE = 115200;
const unsigned long SAMPLE_PERIOD_US = 4000;  // 250 Hz

const int MICROSTEPS = 32;  // TMC2209：MS1→5V、MS2→GND
const long STEPS_PER_REV = 200L * MICROSTEPS;
const float STEPS_PER_RAD = (float)STEPS_PER_REV / (2.0f * (float)PI);
const float LSB_PER_DEG = 4096.0f / 360.0f;

// ---- 門檻（同 02_check_encoder）--------------------------------------------
const uint8_t ST_MD = 0x20, ST_ML = 0x10, ST_MH = 0x08;
const float BAD_FRAC_MAX = 0.01f;     // 狀態不對或 AGC 飽和（0／255）的取樣比例上限
const int AGC_RANGE_MAX = 12;         // 靜態時 AGC 最大值 − 最小值
const int JUMP_LSB = 500;             // 相鄰取樣差超過這個值 = 跳點
const float MAG_RIPPLE_MAX = 0.15f;   // 轉動時 magnitude 的 (最大−最小)/平均
const float TURN_RANGE_DEG = 700.0f;  // 累積角度的最大−最小（約 2 圈 = 720°）
const unsigned long TURN_TIMEOUT_MS = 45000;
const float SWING_MIN_DEG = 5.0f;     // 馬達動作時擺錘至少要擺這麼多
// ---------------------------------------------------------------------------

// 馬達動作：±45°，先 50 rad/s²（跟 LowLevelServer 的位置指令一樣）再 150 rad/s²（策略會用到的上限）
const float MOVE_DEG = 45.0f;
const float ACCEL_SLOW_RAD_S2 = 50.0f;
const float ACCEL_FAST_RAD_S2 = 150.0f;
const uint32_t MOTOR_MIN_STEP_US =   // 最高 5 rad/s
    (uint32_t)(1.0e6f * 2.0f * (float)PI / (5.0f * (float)STEPS_PER_REV));

enum Fail { F_NONE = 0, F_NO_CHIP = 1, F_MAGNET = 2, F_TURN = 3, F_OFFCENTER = 4, F_MOTOR = 5 };

AS5600 as5600;
FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

unsigned long next_us = 0;
uint8_t first_fail = F_NONE;
bool chip_ok = false;

// 擺錘累積角度（處理 0/4095 的換圈）
uint16_t last_raw = 0;
long pen_lsb = 0;
uint16_t jumps = 0;

void fail(uint8_t code)
{
    if (first_fail == F_NONE) first_fail = code;
}

void waitTick()
{
    while ((long)(micros() - next_us) < 0) {}
    next_us += SAMPLE_PERIOD_US;
}

uint16_t readPendulum()
{
    uint16_t raw = as5600.rawAngle();
    int d = (int)raw - (int)last_raw;
    if (d > 2048) d -= 4096;
    if (d < -2048) d += 4096;
    if (abs(d) > JUMP_LSB) jumps++;
    else pen_lsb += d;
    last_raw = raw;
    return raw;
}

void blinkFor(unsigned long ms, unsigned long period_ms)
{
    digitalWrite(LED_BUILTIN, ((ms / (period_ms / 2)) % 2) ? HIGH : LOW);
}

void printPassFail(bool ok)
{
    Serial.println(ok ? F("  → PASS") : F("  → FAIL"));
}

// ---- 1. 編碼器靜態 -----------------------------------------------------------
void testStatic()
{
    Serial.println(F("\n[1/3] 編碼器靜態（2 秒）：擺錘自然垂下，不要碰"));
    digitalWrite(LED_BUILTIN, HIGH);
    chip_ok = as5600.isConnected();
    if (!chip_ok)
    {
        Serial.println(F("  讀不到 AS5600：檢查 SDA→A4、SCL→A5、5V、GND"));
        printPassFail(false);
        fail(F_NO_CHIP);
        return;
    }
    const int N = 500;
    int bad_status = 0, agc_sat = 0;
    int agc_min = 255, agc_max = 0;
    long agc_sum = 0, mag_sum = 0;
    next_us = micros();
    for (int i = 0; i < N; i++)
    {
        waitTick();
        uint8_t st = as5600.readStatus();
        int agc = as5600.readAGC();
        mag_sum += as5600.readMagnitude();
        if (!(st & ST_MD) || (st & (ST_ML | ST_MH))) bad_status++;
        if (agc == 0 || agc == 255) agc_sat++;
        agc_min = min(agc_min, agc);
        agc_max = max(agc_max, agc);
        agc_sum += agc;
    }
    uint8_t st = as5600.readStatus();
    Serial.print(F("  偵測到磁鐵 MD="));  Serial.print((st & ST_MD) ? 1 : 0);
    Serial.print(F("  太弱 ML="));        Serial.print((st & ST_ML) ? 1 : 0);
    Serial.print(F("  太強 MH="));        Serial.println((st & ST_MH) ? 1 : 0);
    Serial.print(F("  AGC 平均 "));       Serial.print(agc_sum / N);
    Serial.print(F("（範圍 "));           Serial.print(agc_min);
    Serial.print(F("–"));                 Serial.print(agc_max);
    Serial.print(F("）  磁場強度 "));     Serial.println(mag_sum / N);

    bool ok = true;
    if (bad_status > N * BAD_FRAC_MAX)
    {
        ok = false;
        if (st & ST_ML) Serial.println(F("  磁場太弱：磁鐵離晶片太遠，間隙應約 1–2 mm"));
        else if (st & ST_MH) Serial.println(F("  磁場太強：磁鐵離晶片太近"));
        else Serial.println(F("  沒偵測到磁鐵：檢查擺錘裡的磁鐵還在、有對準晶片"));
    }
    if (agc_sat > N * BAD_FRAC_MAX || agc_max - agc_min > AGC_RANGE_MAX)
    {
        ok = false;
        Serial.println(F("  AGC 碰到極限或不穩：檢查磁鐵間隙與 AS5600 是否固定牢"));
    }
    printPassFail(ok);
    if (!ok) fail(F_MAGNET);
}

// ---- 2. 手轉擺錘 -------------------------------------------------------------
void testTurn()
{
    Serial.println(F("\n[2/3] 手轉：用手捏著擺錘，往同一個方向慢慢轉 2 圈（每圈約 2–3 秒）"));
    Serial.println(F("      LED 慢閃 = 等你轉；45 秒內沒轉完算 FAIL"));
    if (!chip_ok)
    {
        Serial.println(F("  跳過（讀不到 AS5600）"));
        fail(F_TURN);
        return;
    }
    uint32_t cover_lo = 0, cover_hi = 0;   // 一圈分 64 格
    uint16_t mag_min = 4095, mag_max = 0;
    long mag_sum = 0, n = 0;
    last_raw = as5600.rawAngle();
    pen_lsb = 0;
    jumps = 0;
    long cum_min = 0, cum_max = 0;
    const long need_lsb = (long)(TURN_RANGE_DEG * LSB_PER_DEG);
    unsigned long t0 = millis();
    next_us = micros();
    while (true)
    {
        waitTick();
        uint16_t raw = readPendulum();
        cum_min = min(cum_min, pen_lsb);
        cum_max = max(cum_max, pen_lsb);
        uint8_t bin = raw >> 6;
        if (bin < 32) cover_lo |= (1UL << bin); else cover_hi |= (1UL << (bin - 32));
        if (cum_max - cum_min > 20)   // 開始轉了才算磁場起伏
        {
            uint16_t mag = as5600.readMagnitude();
            mag_min = min(mag_min, mag);
            mag_max = max(mag_max, mag);
            mag_sum += mag;
            n++;
        }
        unsigned long el = millis() - t0;
        blinkFor(el, 1000);
        if (cum_max - cum_min >= need_lsb) break;
        if (el > TURN_TIMEOUT_MS) break;
    }
    float turned = (cum_max - cum_min) / LSB_PER_DEG;
    int covered = __builtin_popcountl(cover_lo) + __builtin_popcountl(cover_hi);
    float ripple = n ? (float)(mag_max - mag_min) / ((float)mag_sum / n) : 0.0f;
    Serial.print(F("  轉了 "));          Serial.print(turned, 0);
    Serial.print(F("°  跳點 "));         Serial.print(jumps);
    Serial.print(F(" 次  讀到的格數 ")); Serial.print(covered);
    Serial.println(F("/64"));
    Serial.print(F("  對心起伏 "));      Serial.print(ripple * 100.0f, 1);
    Serial.println(F("%（門檻 15%）"));

    bool turn_ok = turned >= TURN_RANGE_DEG && jumps == 0 && covered == 64;
    if (turned < TURN_RANGE_DEG) Serial.println(F("  沒轉滿 2 圈：按 RESET 重測"));
    if (jumps) Serial.println(F("  有跳點：磁鐵偏心或鬆動、AS5600 接線接觸不良"));
    if (covered < 64 && turned >= TURN_RANGE_DEG) Serial.println(F("  有角度讀不到：磁鐵偏心或間隙太大"));
    bool center_ok = ripple <= MAG_RIPPLE_MAX;
    if (!center_ok) Serial.println(F("  磁鐵沒對心：磁鐵中心要對準晶片中心"));
    printPassFail(turn_ok && center_ok);
    if (!turn_ok) fail(F_TURN);
    if (!center_ok) fail(F_OFFCENTER);
}

// ---- 3. 馬達 -----------------------------------------------------------------
float swing_max_deg = 0;
long hang_lsb = 0;

void moveAndWatch(float deg, float accel_rad_s2)
{
    stepper->setAcceleration((int32_t)(accel_rad_s2 * STEPS_PER_RAD));
    stepper->moveTo(lroundf(deg * (float)PI / 180.0f * STEPS_PER_RAD));
    next_us = micros();
    while (stepper->isRunning())
    {
        waitTick();
        if (chip_ok)
        {
            readPendulum();
            swing_max_deg = max(swing_max_deg, abs(pen_lsb - hang_lsb) / LSB_PER_DEG);
        }
    }
    // 停 0.4 秒再動下一段，避免一直推到共振
    for (int i = 0; i < 100; i++)
    {
        waitTick();
        if (chip_ok)
        {
            readPendulum();
            swing_max_deg = max(swing_max_deg, abs(pen_lsb - hang_lsb) / LSB_PER_DEG);
        }
    }
}

void testMotor()
{
    Serial.println(F("\n[3/3] 馬達：放開擺錘、讓它停下來；手臂要在正中間、對齊膠帶記號"));
    Serial.println(F("      LED 快閃 = 等擺錘停下，停下 3 秒後手臂開始動"));
    // 等擺錘停下：1.5 秒內變化 < 2°（最多等 20 秒）
    if (chip_ok)
    {
        last_raw = as5600.rawAngle();
        pen_lsb = 0;
        long win_min = 0, win_max = 0;
        unsigned long win_t0 = millis(), t0 = millis();
        next_us = micros();
        while (millis() - t0 < 20000)
        {
            waitTick();
            readPendulum();
            win_min = min(win_min, pen_lsb);
            win_max = max(win_max, pen_lsb);
            blinkFor(millis() - t0, 200);
            if (win_max - win_min > (long)(2.0f * LSB_PER_DEG))
            {
                win_min = win_max = pen_lsb;
                win_t0 = millis();
            }
            else if (millis() - win_t0 > 1500) break;
        }
    }
    unsigned long t0 = millis();
    while (millis() - t0 < 3000) blinkFor(millis() - t0, 200);
    digitalWrite(LED_BUILTIN, HIGH);

    if (chip_ok)
    {
        last_raw = as5600.rawAngle();
        pen_lsb = 0;
        hang_lsb = 0;
    }
    swing_max_deg = 0;
    stepper->setCurrentPosition(0);
    stepper->enableOutputs();
    delay(100);
    Serial.println(F("  50 rad/s²：+45° → −45°"));
    moveAndWatch(+MOVE_DEG, ACCEL_SLOW_RAD_S2);
    moveAndWatch(-MOVE_DEG, ACCEL_SLOW_RAD_S2);
    Serial.println(F("  150 rad/s²：+45° → −45° → +45° → −45°"));
    for (int i = 0; i < 2; i++)
    {
        moveAndWatch(+MOVE_DEG, ACCEL_FAST_RAD_S2);
        moveAndWatch(-MOVE_DEG, ACCEL_FAST_RAD_S2);
    }
    Serial.println(F("  回到正中間"));
    moveAndWatch(0, ACCEL_SLOW_RAD_S2);
    delay(300);
    stepper->disableOutputs();

    if (!chip_ok)
    {
        Serial.println(F("  讀不到編碼器，無法自動確認手臂有沒有動；用眼睛看"));
        return;
    }
    Serial.print(F("  擺錘被帶動的最大擺幅 "));
    Serial.print(swing_max_deg, 0);
    Serial.println(F("°"));
    bool ok = swing_max_deg >= SWING_MIN_DEG;
    if (!ok) Serial.println(F("  擺錘幾乎沒動 = 手臂其實沒轉：檢查 12 V、馬達線接頭、TMC2209"));
    printPassFail(ok);
    if (!ok) fail(F_MOTOR);
    Serial.println(F("  另外用眼睛確認：手臂末端回到膠帶記號（偏 > 1 mm 是失步）、聲音是平順的嗡嗡聲"));
}

void setup()
{
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);
    pinMode(ENABLE_PIN, OUTPUT);
    digitalWrite(ENABLE_PIN, HIGH);  // 先停用驅動（active-low）

    Serial.begin(SERIAL_BAUD_RATE);
    Wire.begin();
    Wire.setClock(400000);
    as5600.begin();

    engine.init();
    stepper = engine.stepperConnectToPin(STEP_PIN);
    if (stepper)
    {
        stepper->setDirectionPin(DIR_PIN);
        stepper->setEnablePin(ENABLE_PIN);   // FastAccelStepper 預設 active-low
        stepper->setAutoEnable(false);
        stepper->setSpeedInUs(MOTOR_MIN_STEP_US);
        stepper->disableOutputs();
    }

    Serial.println(F("#PickupCheck v1"));
    Serial.println(F("領取器材快速檢查：編碼器 → 手轉擺錘 → 馬達，約 1 分鐘。12 V 要接著。"));
    delay(1000);

    testStatic();
    testTurn();
    if (stepper) testMotor();
    else Serial.println(F("\n[3/3] 馬達：FastAccelStepper 初始化失敗（STEP 一定要接 D9）"));

    Serial.println(F("\n================ 結果 ================"));
    if (first_fail == F_NONE)
    {
        Serial.println(F("全部 PASS（LED 恆亮）。手臂有對齊膠帶、聲音平順就可以簽點交單。"));
    }
    else
    {
        Serial.print(F("FAIL：LED 閃 "));
        Serial.print(first_fail);
        Serial.println(F(" 下 = 上面第一個 FAIL 的項目。修好後按 RESET 重測。"));
    }
}

void loop()
{
    if (first_fail == F_NONE)
    {
        digitalWrite(LED_BUILTIN, HIGH);
        return;
    }
    for (uint8_t i = 0; i < first_fail; i++)
    {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(250);
        digitalWrite(LED_BUILTIN, LOW);
        delay(250);
    }
    delay(1500);
}

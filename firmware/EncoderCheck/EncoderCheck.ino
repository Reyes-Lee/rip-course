/*
 * EncoderCheck — 課程用的 AS5600 編碼器測試（搭配 tools/02_check_encoder）
 *
 * 以作者的 TestEncoder.ino 為基礎。差別：除了角度，也讀 AS5600 的狀態位元、
 * AGC（自動增益）與 MAGNITUDE（磁場強度），用來檢查磁鐵距離與對心。
 *
 * 每 4 ms（250 Hz）輸出一行 CSV：
 *     t_us,raw,status,agc,magnitude
 *   raw       0–4095，12-bit 角度
 *   status    STATUS 暫存器：bit5 MD（偵測到磁鐵）、bit4 ML（太弱）、bit3 MH（太強）
 *   agc       0–255（5 V 供電時）；磁場越弱數字越大
 *   magnitude 0–4095，CORDIC 算出的磁場強度
 * 開機時先印一行 "#EncoderCheck v1"，工具用它確認燒對了韌體。
 *
 * 馬達驅動保持停用（ENABLE 拉高），不會發熱。
 * 需要 Arduino IDE 程式庫：AS5600（Rob Tillaart）。
 */
#include <AS5600.h>
#include <Wire.h>

const long SERIAL_BAUD_RATE = 500000;
const long I2C_CLOCK_HZ = 400000;
const unsigned long SAMPLE_PERIOD_US = 4000;  // 250 Hz

// 接線與作者相同
const int DIR_PIN = 2;
const int STEP_PIN = 9;
const int ENABLE_PIN = 5;

AS5600 as5600;
unsigned long last_us = 0;

void setup()
{
    pinMode(ENABLE_PIN, OUTPUT);
    digitalWrite(ENABLE_PIN, HIGH);  // HIGH = 停用驅動（active-low）
    pinMode(DIR_PIN, OUTPUT);
    pinMode(STEP_PIN, OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);

    Serial.begin(SERIAL_BAUD_RATE);
    Wire.begin();
    Wire.setClock(I2C_CLOCK_HZ);
    as5600.begin();

    Serial.println("#EncoderCheck v1");
    if (!as5600.isConnected())
    {
        // 讀不到晶片也照常輸出，讓工具判斷（status 會是 0）
        Serial.println("#AS5600 not connected (check SDA=A4, SCL=A5, 5V, GND)");
    }
    last_us = micros();
}

void loop()
{
    unsigned long now = micros();
    if ((unsigned long)(now - last_us) < SAMPLE_PERIOD_US) return;
    last_us += SAMPLE_PERIOD_US;

    uint16_t raw = as5600.rawAngle();
    uint8_t status = as5600.readStatus();
    uint8_t agc = as5600.readAGC();
    uint16_t mag = as5600.readMagnitude();

    Serial.print(now);
    Serial.print(',');
    Serial.print(raw);
    Serial.print(',');
    Serial.print(status);
    Serial.print(',');
    Serial.print(agc);
    Serial.print(',');
    Serial.println(mag);

    // 有偵測到磁鐵時 LED 亮
    digitalWrite(LED_BUILTIN, (status & 0x20) ? HIGH : LOW);
}

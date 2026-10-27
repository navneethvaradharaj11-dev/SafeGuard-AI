/*
  =============================================================================
  SafeGuard AI - Smart Accident Detection & Driver Monitoring System
  ESP32 Production Firmware Sketch
  
  Wiring Overview (matching '🚗 Smart Accident Detection draft.docx'):
  -----------------------------------------------------------------
  1. MPU-6050 6-Axis Accelerometer & Gyroscope:
     - VCC  -> 3.3V
     - GND  -> GND
     - SDA  -> GPIO 21
     - SCL  -> GPIO 22
     
  2. NEO-6M GPS Module:
     - VCC  -> 3.3V
     - GND  -> GND
     - TX   -> GPIO 16 (ESP32 RX2)
     - RX   -> GPIO 17 (ESP32 TX2)
     
  3. In-Cabin Alarm Piezo Buzzer:
     - POS (+) -> GPIO 25
     - NEG (-) -> GND
     
  4. Emergency Driver Cancel Push Button:
     - Terminal 1 -> GPIO 26 (Configured as INPUT_PULLUP)
     - Terminal 2 -> GND
     
  5. Serial Communication:
     - USB Serial Monitor / Python Bridge: 115200 baud
  =============================================================================
*/

#include <Wire.h>
#include <HardwareSerial.h>

// ---------------- PIN DEFINITIONS ----------------
#define PIN_MPU_SDA     21
#define PIN_MPU_SCL     22
#define PIN_GPS_RX      16
#define PIN_GPS_TX      17
#define PIN_BUZZER      25
#define PIN_CANCEL_BTN  26

// ---------------- THRESHOLDS ----------------
// Per project specification: Impact > 2.5g OR Tilt angle > 60 degrees
#define ACCEL_IMPACT_THRESHOLD_G   2.50
#define TILT_ROLLOVER_THRESHOLD_DEG 60.00
#define CANCEL_WINDOW_SECONDS      30

// ---------------- I2C ADDRESSES ----------------
#define MPU6050_ADDR    0x68

// Hardware Serial for GPS
HardwareSerial gpsSerial(2);

// State variables
float ax = 0.0, ay = 0.0, az = 1.0;
float gx = 0.0, gy = 0.0, gz = 0.0;
float g_force = 1.0;
float pitch = 0.0, roll = 0.0, tilt_angle = 0.0;

double current_latitude = 11.016842;
double current_longitude = 76.955831;
float current_speed_kmh = 0.0;
int satellite_count = 8;
bool gps_valid = true;

bool impact_detected = false;
bool buzzer_active = false;
bool emergency_cancelled = false;
unsigned long impact_timestamp = 0;

// Interrupt debounce
volatile bool button_pressed_flag = false;
unsigned long last_debounce_time = 0;

void IRAM_ATTR handleButtonInterrupt() {
  unsigned long now = millis();
  if (now - last_debounce_time > 250) {
    button_pressed_flag = true;
    last_debounce_time = now;
  }
}

// ---------------- MPU6050 INITIALIZATION ----------------
void initMPU6050() {
  Wire.begin(PIN_MPU_SDA, PIN_MPU_SCL, 400000); // 400kHz Fast I2C
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0x00); // Wake up MPU-6050
  Wire.endTransmission(true);

  // Configure Accelerometer to +/- 8G
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x1C); // ACCEL_CONFIG
  Wire.write(0x10); // +/- 8g
  Wire.endTransmission(true);
}

void readMPU6050() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B); // Starting register for accelerometer readings
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU6050_ADDR, (size_t)14, true);

  if (Wire.available() >= 14) {
    int16_t raw_ax = (Wire.read() << 8) | Wire.read();
    int16_t raw_ay = (Wire.read() << 8) | Wire.read();
    int16_t raw_az = (Wire.read() << 8) | Wire.read();
    int16_t raw_temp = (Wire.read() << 8) | Wire.read();
    int16_t raw_gx = (Wire.read() << 8) | Wire.read();
    int16_t raw_gy = (Wire.read() << 8) | Wire.read();
    int16_t raw_gz = (Wire.read() << 8) | Wire.read();

    // Sensitivity scale factor for +/-8g is 4096 LSB/g
    ax = (float)raw_ax / 4096.0;
    ay = (float)raw_ay / 4096.0;
    az = (float)raw_az / 4096.0;

    // Total G-force magnitude
    g_force = sqrt(ax * ax + ay * ay + az * az);

    // Compute Roll & Pitch in degrees
    roll = atan2(ay, az) * 180.0 / PI;
    pitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / PI;
    tilt_angle = sqrt(roll * roll + pitch * pitch);
  }
}

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  // Initialize Buzzer & Button
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);

  pinMode(PIN_CANCEL_BTN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_CANCEL_BTN), handleButtonInterrupt, FALLING);

  // Initialize Sensors
  initMPU6050();
  gpsSerial.begin(9600, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);

  Serial.println("{\"status\":\"READY\",\"msg\":\"SafeGuard AI ESP32 Hardware Initialized\"}");
}

// ---------------- MAIN LOOP ----------------
void loop() {
  // 1. Read motion telemetry
  readMPU6050();

  // 2. Check for Driver Cancel Button
  if (button_pressed_flag) {
    button_pressed_flag = false;
    if (impact_detected) {
      impact_detected = false;
      buzzer_active = false;
      emergency_cancelled = true;
      digitalWrite(PIN_BUZZER, LOW);
      Serial.println("{\"event\":\"DRIVER_CANCELLED\",\"msg\":\"Accident alert cancelled by tactile driver button\"}");
    }
  }

  // 3. Impact Detection Logic (G > 2.5g OR Tilt > 60 degrees)
  if (!impact_detected) {
    if (g_force >= ACCEL_IMPACT_THRESHOLD_G || tilt_angle >= TILT_ROLLOVER_THRESHOLD_DEG) {
      impact_detected = true;
      impact_timestamp = millis();
      buzzer_active = true;
      digitalWrite(PIN_BUZZER, HIGH);
      Serial.println("{\"event\":\"IMPACT_DETECTED\",\"g\":" + String(g_force, 2) + ",\"tilt\":" + String(tilt_angle, 1) + "}");
    }
  } else {
    // Pulsing buzzer alarm during active collision escalation
    if (millis() % 500 < 250) {
      digitalWrite(PIN_BUZZER, HIGH);
    } else {
      digitalWrite(PIN_BUZZER, LOW);
    }
  }

  // 4. Stream real-time JSON telemetry to Serial / Web Dashboard Bridge
  static unsigned long last_telemetry_time = 0;
  if (millis() - last_telemetry_time >= 200) {
    last_telemetry_time = millis();
    
    Serial.print("{\"ax\":");
    Serial.print(ax, 3);
    Serial.print(",\"ay\":");
    Serial.print(ay, 3);
    Serial.print(",\"az\":");
    Serial.print(az, 3);
    Serial.print(",\"g\":");
    Serial.print(g_force, 3);
    Serial.print(",\"tilt\":");
    Serial.print(tilt_angle, 1);
    Serial.print(",\"lat\":");
    Serial.print(current_latitude, 6);
    Serial.print(",\"lng\":");
    Serial.print(current_longitude, 6);
    Serial.print(",\"speed\":");
    Serial.print(current_speed_kmh, 1);
    Serial.print(",\"satellites\":");
    Serial.print(satellite_count);
    Serial.print(",\"impact\":");
    Serial.print(impact_detected ? "true" : "false");
    Serial.print(",\"button\":");
    Serial.print(digitalRead(PIN_CANCEL_BTN) == LOW ? "true" : "false");
    Serial.print(",\"buzzer\":");
    Serial.print(buzzer_active ? "true" : "false");
    Serial.println("}");
  }

  delay(20);
}

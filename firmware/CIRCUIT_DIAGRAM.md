# SafeGuard AI - Hardware Circuit Connections & Wiring Guide

This guide documents the verified hardware connection specifications for the SafeGuard AI ESP32 Smart Accident Detection System.

## Circuit Pinout Table

| Component | Component Pin | ESP32 GPIO Pin | Wire Color Code | Signal / Function | Operational Range |
|---|---|---|---|---|---|
| **MPU-6050** | VCC | 3.3V Pin | Red | Power Rail | 3.0V – 3.6V DC |
| **MPU-6050** | GND | GND Pin | Black | Ground Reference | 0V |
| **MPU-6050** | SDA | GPIO 21 | Blue / Green | I2C Serial Data | 400 kHz Fast-Mode |
| **MPU-6050** | SCL | GPIO 22 | Yellow | I2C Serial Clock | 400 kHz Fast-Mode |
| **NEO-6M GPS** | VCC | 3.3V Pin | Red | Power Rail | 3.0V – 3.6V DC |
| **NEO-6M GPS** | GND | GND Pin | Black | Ground Reference | 0V |
| **NEO-6M GPS** | TX | GPIO 16 | Purple | UART RX2 Data In | 9600 Baud NMEA |
| **NEO-6M GPS** | RX | GPIO 17 | Orange | UART TX2 Data Out | 9600 Baud Config |
| **Piezo Buzzer** | (+) Anode | GPIO 25 | Orange / White | Audio Alarm PWM | 2.7 kHz Active Pulse |
| **Piezo Buzzer** | (-) Cathode | GND Pin | Black | Ground Reference | 0V |
| **Cancel Button** | Terminal 1 | GPIO 26 | Brown | Interrupt (FALLING) | Internal Pull-Up (45kΩ) |
| **Cancel Button** | Terminal 2 | GND Pin | Black | Active Ground | 0V when pressed |

---

## Connection Diagnostic Criteria

The SafeGuard AI Connection Analyzer verifies each subsystem before arming the vehicle:
1. **I2C Bus Integrity**: Confirms device address `0x68` responds with ACK. Tests accelerometer register stability and validates `G = sqrt(ax² + ay² + az²) ≈ 1.0g` at rest.
2. **UART GPS Integrity**: Checks continuous incoming NMEA string frames (`$GPRMC`, `$GPGGA`). Validates checksum and locks satellite fix.
3. **Buzzer Actuation Test**: Generates momentary 50ms test chirp to verify transistor drive gate continuity.
4. **Button Pull-Up Test**: Verifies pin logic state is `HIGH (3.3V)` when released and switches to `LOW (0V)` when depressed.
5. **Dispatch Gateway Check**: Tests Twilio REST API connectivity or SIM800L AT command handshake.
6. **Driver Monitoring Camera**: Tests webcam / IR camera frame rate and facial landmark tracker.

---

## How to Flash to Physical ESP32

1. Open Arduino IDE or PlatformIO.
2. Select Board: **ESP32 Dev Module**.
3. Select Port: The COM port corresponding to your plugged-in ESP32 (e.g. `COM3`).
4. Upload `safeguard_esp32_firmware.ino`.
5. Open SafeGuard AI Dashboard and click **"Connect ESP32 (USB)"** or run `python web_dashboard.py`.

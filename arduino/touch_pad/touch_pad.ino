// Capacitive rest-pad sensor for the push task.
// Arduino Nano (ATmega328P). Output D2 drives Dev1/ai2: HIGH (5 V) while the pad is touched.
// Wiring and calibration: README.md in this folder.

#include <CapacitiveSensor.h>

// Pins
const uint8_t PIN_SEND = 4;     // 1 MOhm from D4 to D6
const uint8_t PIN_PAD = 6;      // pad lead
const uint8_t PIN_POT = A0;     // pot wiper; outer legs to GND and 5V
const uint8_t PIN_OUT = 2;      // to ai2 (SCB-68A terminal 65)
const uint8_t PIN_LED = LED_BUILTIN;

// Sensing
const uint8_t N_SAMPLES = 20;          // samples per capacitiveSensorRaw() call
const uint8_t AVG_LEN = 4;             // moving-average length
const uint16_t TARE_READINGS = 64;
const unsigned long CS_TIMEOUT_MS = 10; // keeps the loop responsive if the pad is shorted

// Sensitivity: the pot sets the ON threshold (in raw counts above baseline) on an
// exponential scale between these limits. Clockwise = more sensitive (lower threshold).
const float THR_MIN = 20.0;
const float THR_MAX = 5000.0;
const float OFF_FRACTION = 0.7;        // OFF threshold = 0.7 x ON (hysteresis)
const uint8_t DEBOUNCE_ON = 3;
const uint8_t DEBOUNCE_OFF = 3;

// Baseline tracking (only while released)
const float DRIFT_ALPHA = 0.0005;      // slow upward/downward drift
const float DROP_ALPHA = 0.05;         // fast follow when the reading falls below baseline

// Pot smoothing and serial output
const unsigned long POT_INTERVAL_MS = 20;
const float POT_ALPHA = 0.2;
const unsigned long PRINT_INTERVAL_MS = 20;
const unsigned long FAULT_BLINK_MS = 50;

CapacitiveSensor cs(PIN_SEND, PIN_PAD);

long avgBuf[AVG_LEN];
uint8_t avgIdx = 0;
long avgSum = 0;

float baseline = 0;
float potFiltered = 0;
float onThr = THR_MAX;
float offThr = THR_MAX * OFF_FRACTION;

bool touched = false;
bool fault = false;
uint8_t aboveCount = 0;
uint8_t belowCount = 0;
bool printing = true;

unsigned long lastPot = 0;
unsigned long lastPrint = 0;
unsigned long lastBlink = 0;
bool blinkState = false;

long readRaw() {
  return cs.capacitiveSensorRaw(N_SAMPLES);
}

void setOutput(bool on) {
  digitalWrite(PIN_OUT, on ? HIGH : LOW);
  digitalWrite(PIN_LED, on ? HIGH : LOW);
}

void updateThresholds() {
  potFiltered += POT_ALPHA * (analogRead(PIN_POT) - potFiltered);
  float sens = potFiltered / 1023.0;
  onThr = THR_MAX * pow(THR_MIN / THR_MAX, sens);
  offThr = onThr * OFF_FRACTION;
}

void resetAverage(long value) {
  for (uint8_t i = 0; i < AVG_LEN; i++) avgBuf[i] = value;
  avgSum = value * AVG_LEN;
  avgIdx = 0;
}

long pushAverage(long value) {
  avgSum += value - avgBuf[avgIdx];
  avgBuf[avgIdx] = value;
  avgIdx = (avgIdx + 1) % AVG_LEN;
  return avgSum / AVG_LEN;
}

// The pad must be untouched during tare.
void tare() {
  setOutput(false);
  digitalWrite(PIN_LED, HIGH);
  long sum = 0;
  uint16_t n = 0;
  unsigned long start = millis();
  while (n < TARE_READINGS && millis() - start < 5000) {
    long raw = readRaw();
    if (raw >= 0) {
      sum += raw;
      n++;
    }
  }
  digitalWrite(PIN_LED, LOW);
  fault = (n == 0);
  baseline = fault ? 0 : (float)sum / n;
  resetAverage((long)baseline);
  touched = false;
  aboveCount = 0;
  belowCount = 0;
}

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 't' || c == 'T') {
      tare();
      Serial.println(F("# tared"));
    } else if (c == 'p' || c == 'P') {
      printing = !printing;
    }
  }
}

void setup() {
  pinMode(PIN_OUT, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  setOutput(false);
  Serial.begin(115200);
  cs.set_CS_AutocaL_Millis(0xFFFFFFFF);
  cs.set_CS_Timeout_Millis(CS_TIMEOUT_MS);
  potFiltered = analogRead(PIN_POT);
  updateThresholds();
  tare();
  Serial.println(F("# touch_pad ready: send t to re-tare, p to toggle printing"));
}

void loop() {
  unsigned long now = millis();
  handleSerial();

  if (now - lastPot >= POT_INTERVAL_MS) {
    lastPot = now;
    updateThresholds();
  }

  long raw = readRaw();
  if (raw < 0) {
    fault = true;
    touched = false;
    aboveCount = 0;
    belowCount = 0;
    digitalWrite(PIN_OUT, LOW);
    if (now - lastBlink >= FAULT_BLINK_MS) {
      lastBlink = now;
      blinkState = !blinkState;
      digitalWrite(PIN_LED, blinkState ? HIGH : LOW);
    }
    if (printing && now - lastPrint >= PRINT_INTERVAL_MS) {
      lastPrint = now;
      Serial.println(F("# fault: pad timeout (shorted or disconnected)"));
    }
    return;
  }
  if (fault) {
    fault = false;
    resetAverage(raw);
  }

  long avg = pushAverage(raw);
  float delta = avg - baseline;

  if (!touched) {
    if (delta > onThr) {
      belowCount = 0;
      if (++aboveCount >= DEBOUNCE_ON) {
        touched = true;
        aboveCount = 0;
      }
    } else {
      aboveCount = 0;
      float alpha = (delta < 0) ? DROP_ALPHA : DRIFT_ALPHA;
      baseline += alpha * delta;
    }
  } else {
    if (delta < offThr) {
      if (++belowCount >= DEBOUNCE_OFF) {
        touched = false;
        belowCount = 0;
      }
    } else {
      belowCount = 0;
    }
  }
  setOutput(touched);

  if (printing && now - lastPrint >= PRINT_INTERVAL_MS) {
    lastPrint = now;
    Serial.print(F("raw:"));
    Serial.print(avg);
    Serial.print(F(",baseline:"));
    Serial.print((long)baseline);
    Serial.print(F(",delta:"));
    Serial.print((long)delta);
    Serial.print(F(",on_thr:"));
    Serial.print((long)onThr);
    Serial.print(F(",off_thr:"));
    Serial.print((long)offThr);
    Serial.print(F(",state:"));
    Serial.println(touched ? (long)onThr : 0L);
  }
}

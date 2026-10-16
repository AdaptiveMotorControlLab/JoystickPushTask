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
const uint16_t TARE_READINGS = 64;
const unsigned long CS_TIMEOUT_MS = 10; // keeps the loop responsive if the pad is shorted

// Mains rejection: a mouse on the pad picks up 50 Hz hum. Readings are averaged over exactly
// one mains period (two half-windows of DECISION_US), so the hum cancels; a new touch decision
// is made every half-window. Set DECISION_US to 8333 on 60 Hz mains.
const unsigned long DECISION_US = 10000;
const unsigned long DECISION_MS = DECISION_US / 1000;

// Sensitivity: the pot sets the ON threshold (in raw counts above baseline) on an
// exponential scale between these limits. Clockwise = more sensitive (lower threshold).
const float THR_MIN = 20.0;
const float THR_MAX = 5000.0;
const float OFF_FRACTION = 0.5;        // OFF threshold = 0.5 x ON (hysteresis)
const unsigned long TOUCH_HOLD_MS = 20;   // above ON for this long before D2 goes HIGH
const unsigned long RELEASE_HOLD_MS = 40; // below OFF for this long before D2 goes LOW

// Baseline tracking (only while released), per decision step
const float DRIFT_ALPHA = 0.0025;      // slow upward/downward drift (~4 s)
const float DROP_ALPHA = 0.22;         // fast follow when the reading falls below baseline (~40 ms)

// Pot smoothing and serial output
const unsigned long POT_INTERVAL_MS = 20;
const float POT_ALPHA = 0.2;
const unsigned long PRINT_INTERVAL_MS = 20;
const unsigned long FAULT_BLINK_MS = 50;

CapacitiveSensor cs(PIN_SEND, PIN_PAD);

struct HalfWindow {
  long sum;
  uint16_t n;
  long lo;
  long hi;
};

HalfWindow cur;
HalfWindow prev;
unsigned long halfStartUs = 0;

float baseline = 0;
float potFiltered = 0;
float onThr = THR_MAX;
float offThr = THR_MAX * OFF_FRACTION;

bool touched = false;
bool fault = false;
bool pending = false;          // switch condition currently met, waiting for the hold time
unsigned long pendingSince = 0;
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

void clearHalf(HalfWindow &h) {
  h.sum = 0;
  h.n = 0;
  h.lo = 2147483647L;
  h.hi = 0;
}

void addReading(HalfWindow &h, long raw) {
  h.sum += raw;
  h.n++;
  if (raw < h.lo) h.lo = raw;
  if (raw > h.hi) h.hi = raw;
}

void resetWindow() {
  clearHalf(cur);
  clearHalf(prev);
  halfStartUs = micros();
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
  resetWindow();
  touched = false;
  pending = false;
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

void decide(unsigned long now, long avg, long ripple) {
  float delta = avg - baseline;
  bool wantSwitch = touched ? (delta < offThr) : (delta > onThr);

  if (wantSwitch) {
    if (!pending) {
      pending = true;
      pendingSince = now;
    }
    if (now - pendingSince >= (touched ? RELEASE_HOLD_MS : TOUCH_HOLD_MS)) {
      touched = !touched;
      pending = false;
    }
  } else {
    pending = false;
  }

  if (!touched && delta <= onThr) {
    float alpha = (delta < 0) ? DROP_ALPHA : DRIFT_ALPHA;
    baseline += alpha * delta;
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
    Serial.print(F(",ripple:"));
    Serial.print(ripple);
    Serial.print(F(",on_thr:"));
    Serial.print((long)onThr);
    Serial.print(F(",off_thr:"));
    Serial.print((long)offThr);
    Serial.print(F(",state:"));
    Serial.println(touched ? (long)onThr : 0L);
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
    pending = false;
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
    resetWindow();
  }

  addReading(cur, raw);

  unsigned long nowUs = micros();
  if (nowUs - halfStartUs < DECISION_US) return;
  halfStartUs += DECISION_US;
  if (nowUs - halfStartUs >= DECISION_US) halfStartUs = nowUs;  // fell behind (serial, tare)

  long sum = prev.sum + cur.sum;
  uint16_t n = prev.n + cur.n;
  long lo = min(prev.lo, cur.lo);
  long hi = max(prev.hi, cur.hi);
  prev = cur;
  clearHalf(cur);

  decide(millis(), sum / n, hi - lo);
}

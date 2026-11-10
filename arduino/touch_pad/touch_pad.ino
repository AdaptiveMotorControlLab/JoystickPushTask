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
// one mains period (N_BINS bins of BIN_US), so the hum cancels; the window slides by one bin,
// so a new touch decision is made every BIN_US. Set MAINS_PERIOD_US to 16667 on 60 Hz mains.
const unsigned long MAINS_PERIOD_US = 20000;
const uint8_t N_BINS = 10;
const unsigned long BIN_US = MAINS_PERIOD_US / N_BINS;

// Sensitivity: the pot sets the ON threshold (in raw counts above baseline) on an
// exponential scale between these limits. Clockwise = more sensitive (lower threshold).
const float THR_MIN = 20.0;
const float THR_MAX = 5000.0;
const float OFF_FRACTION = 0.5;        // OFF threshold = 0.5 x ON (hysteresis)
const unsigned long TOUCH_HOLD_MS = 20;   // above ON for this long before D2 goes HIGH
const unsigned long RELEASE_HOLD_MS = 4;  // below OFF for this long before D2 goes LOW

// Baseline tracking (only while released), one step every BASELINE_STEP_MS
const unsigned long BASELINE_STEP_MS = 10;
const float DRIFT_ALPHA = 0.0025;      // slow upward/downward drift (~4 s)
const float DROP_ALPHA = 0.22;         // fast follow when the reading falls below baseline (~40 ms)

// Pot smoothing and serial output
const unsigned long POT_INTERVAL_MS = 20;
const float POT_ALPHA = 0.2;
const unsigned long PRINT_INTERVAL_MS = 20;
const unsigned long FAULT_BLINK_MS = 50;

CapacitiveSensor cs(PIN_SEND, PIN_PAD);

// Readings last ~0.5-10 ms (longer while touched), so each one is weighted by its duration
// and split across the bins it overlaps; the window then covers exactly one mains period.
struct Bin {
  long sum;          // raw x microseconds
  unsigned long us;  // microseconds covered by readings
  long lo;
  long hi;
};

// One spare slot: the open bin, which is not part of the decision window.
Bin bins[N_BINS + 1];
uint8_t openBin = 0;
unsigned long binStartUs = 0;

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
unsigned long lastBaseline = 0;
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

void clearBin(Bin &b) {
  b.sum = 0;
  b.us = 0;
  b.lo = 2147483647L;
  b.hi = 0;
}

void addReading(Bin &b, long raw, unsigned long us) {
  b.sum += raw * (long)us;
  b.us += us;
  if (raw < b.lo) b.lo = raw;
  if (raw > b.hi) b.hi = raw;
}

void resetWindow() {
  for (uint8_t i = 0; i <= N_BINS; i++) clearBin(bins[i]);
  openBin = 0;
  binStartUs = micros();
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

  if (now - lastBaseline >= BASELINE_STEP_MS) {
    lastBaseline = now;
    if (!touched && delta <= onThr) {
      float alpha = (delta < 0) ? DROP_ALPHA : DRIFT_ALPHA;
      baseline += alpha * delta;
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

  unsigned long startUs = micros();
  long raw = readRaw();
  unsigned long endUs = micros();
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

  if ((long)(startUs - binStartUs) < 0) startUs = binStartUs;  // started before a window reset
  uint8_t closed = 0;
  while (endUs - binStartUs >= BIN_US) {
    unsigned long binEndUs = binStartUs + BIN_US;
    if ((long)(binEndUs - startUs) > 0) {
      addReading(bins[openBin], raw, binEndUs - startUs);
      startUs = binEndUs;
    }
    binStartUs = binEndUs;
    openBin = (openBin + 1) % (N_BINS + 1);
    clearBin(bins[openBin]);
    if (++closed > N_BINS) {  // fell behind (serial, tare)
      resetWindow();
      return;
    }
  }
  if ((long)(endUs - startUs) > 0) addReading(bins[openBin], raw, endUs - startUs);
  if (closed == 0) return;

  long sum = 0;
  unsigned long us = 0;
  long lo = 2147483647L;
  long hi = 0;
  for (uint8_t i = 0; i <= N_BINS; i++) {
    if (i == openBin) continue;
    sum += bins[i].sum;
    us += bins[i].us;
    lo = min(lo, bins[i].lo);
    hi = max(hi, bins[i].hi);
  }
  if (us == 0) return;

  decide(millis(), sum / (long)us, hi - lo);
}

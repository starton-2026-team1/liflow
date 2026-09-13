"""
main_rpi.py: Raspberry Pi + HC-SR04 + 1-Sensor Real-Time Pipeline
Sensor: fridge (1 unit)
Execution: python main_rpi.py
"""

import RPi.GPIO as GPIO
import time
import numpy as np
from collections import deque
from tensorflow import keras

# ── GPIO Configuration ──────────────────────────────────
TRIG_PIN = 23
ECHO_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# ── Model Settings ─────────────────────────────────────
SEQ_LEN     = 10
INPUT_DIM   = 31
MAX_DIST    = 450.0
LABEL_NAMES = {0: "Normal", 1: "Insomnia", 2: "Repetitive Behavior"}

print("Loading models...")
ae        = keras.models.load_model("model/autoencoder_1s.keras")
lstm      = keras.models.load_model("model/lstm_1s.keras")
THRESHOLD = float(np.load("model/threshold_1s.npy")[0])
MSE_MAX   = float(np.load("model/mse_max_1s.npy")[0])
print(f"✅ Models loaded successfully | Threshold: {THRESHOLD:.2f}\n")

seq_buffer = deque(maxlen=SEQ_LEN)


# ── Distance Measurement ───────────────────────────────
def measure_distance() -> float:
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.05)

    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.1
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return MAX_DIST

    pulse_end = time.time()
    timeout = pulse_end + 0.1
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return MAX_DIST

    distance = (pulse_end - pulse_start) * 17150
    return round(min(distance, MAX_DIST), 2)


# ── Preprocessing (31-dimensional) ─────────────────────
def make_feature(hour: int, minute: int, fridge_dist: float) -> np.ndarray:
    h_vec = [0] * 24; h_vec[hour % 24] = 1
    m_vec = [0] * 6;  m_vec[(minute // 10) % 6] = 1
    v = float(np.clip(fridge_dist, 0, MAX_DIST)) / MAX_DIST
    return np.array(h_vec + m_vec + [v], dtype=np.float32)


# ── Anomaly Score ──────────────────────────────────────
def anomaly_score(feature: np.ndarray) -> float:
    x = feature.reshape(1, -1)
    x_pred = ae.predict(x, verbose=0)
    mse = float(np.mean(np.power(x - x_pred, 2)))
    return (mse / MSE_MAX) * 100


# ── LSTM Classification ────────────────────────────────
def classify(seq_buffer: deque) -> tuple[str, float]:
    seq  = np.array(list(seq_buffer), dtype=np.float32).reshape(1, SEQ_LEN, INPUT_DIM)
    pred = lstm.predict(seq, verbose=0)[0]
    label = int(np.argmax(pred))
    return LABEL_NAMES[label], float(pred[label]) * 100


# ── Main Loop ──────────────────────────────────────────
print("Starting measurement (Press Ctrl+C to stop)...\n")

try:
    while True:
        from datetime import datetime
        now = datetime.now()

        dist = measure_distance()
        feature = make_feature(now.hour, now.minute, dist)
        seq_buffer.append(feature)

        score = anomaly_score(feature)
        is_anomaly = score >= THRESHOLD
        time_str = now.strftime("%H:%M:%S")

        if is_anomaly and len(seq_buffer) == SEQ_LEN:
            result, conf = classify(seq_buffer)
            print(f"[{time_str}] ⚠️ Anomaly Detected | dist={dist}cm | score={min(score,999.9):.1f} | Class: {result} ({conf:.1f}%)")
        else:
            status = "✅ Normal" if not is_anomaly else "⏳ Filling Buffer"
            print(f"[{time_str}] {status} | dist={dist}cm | score={score:.1f}")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nProgram stopped by user.")
finally:
    GPIO.cleanup()
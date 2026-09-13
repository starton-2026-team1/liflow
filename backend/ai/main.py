import argparse
import time
import numpy as np
import pandas as pd
from datetime import datetime
from collections import deque
from tensorflow import keras
 
# ── 기본 설정 ─────────────────────────────────────────
SERIAL_PORT      = "/dev/cu.usbserial-AB0N1J2Z"
BAUD_RATE        = 9600
SEQ_LEN          = 10
MAX_DIST         = 450.0
DEFAULT_SENSORS  = ["bed", "fridge", "living"]
LABEL_NAMES      = {0: "정상", 1: "불면", 2: "반복행동"}
 
parser = argparse.ArgumentParser()
parser.add_argument("--sim", type=str, default=None,
                    help="시뮬레이션 CSV 경로 (예: data/abnormal_raw_v3.csv)")
parser.add_argument("--sensors", type=str, nargs="+", default=DEFAULT_SENSORS,
                    help="사용할 센서 목록 (기본: bed bathroom living) "
                         "예) --sensors bed bathroom living door fridge")
args = parser.parse_args()
 
SENSORS   = args.sensors
INPUT_DIM = 24 + 6 + len(SENSORS)  # hour + minute_bin + 센서 수
 
# 모델 로드
print("모델 로딩 중...")
ae        = keras.models.load_model("model/autoencoder.keras")
lstm      = keras.models.load_model("model/lstm.keras")
THRESHOLD = float(np.load("model/threshold.npy")[0])
MSE_MAX   = float(np.load("model/mse_max.npy")[0])
print(f"모델 로드 완료 | 임계값: {THRESHOLD:.2f}")
print(f"   센서 목록: {SENSORS} ({len(SENSORS)}개) | 입력 차원: {INPUT_DIM}\n")
 
 
# 전처리
def make_feature(hour, minute, sensor_vals: dict):
    h_vec = [0] * 24; h_vec[hour % 24] = 1
    m_vec = [0] * 6;  m_vec[(minute // 10) % 6] = 1
    s_vec = []
    for s in SENSORS:
        v = sensor_vals.get(s, MAX_DIST)
        if v is None or v < 0:
            v = MAX_DIST
        s_vec.append(float(np.clip(v, 0, MAX_DIST)) / MAX_DIST)
    return np.array(h_vec + m_vec + s_vec, dtype=np.float32)
 
 
# 이상치 점수
def anomaly_score(feature: np.ndarray) -> float:
    x = feature.reshape(1, -1)
    x_pred = ae.predict(x, verbose=0)
    mse = float(np.mean(np.power(x - x_pred, 2)))
    return (mse / MSE_MAX) * 100
 
 
# LSTM
def classify(seq_buffer: deque) -> tuple[str, float]:
    seq  = np.array(list(seq_buffer), dtype=np.float32).reshape(1, SEQ_LEN, INPUT_DIM)
    pred = lstm.predict(seq, verbose=0)[0]
    label = int(np.argmax(pred))
    return LABEL_NAMES[label], float(pred[label]) * 100
 
 
# 공통 처리
def process(hour, minute, bed_d, bath_d, living_d, seq_buffer, time_str, true_label=None):
    sensor_vals = {"bed": bed_d, "fridge": bath_d, "living": living_d}
    feature = make_feature(hour, minute, sensor_vals)
    seq_buffer.append(feature)
 
    score = anomaly_score(feature)
    is_anomaly = score >= THRESHOLD
 
    label_str = f" (정답: {true_label})" if true_label else ""
 
    if is_anomaly and len(seq_buffer) == SEQ_LEN:
        result, conf = classify(seq_buffer)
        print(f"[{time_str}] ⚠️  이상 감지 | score={score:.1f} | 판정: {result} ({conf:.1f}%){label_str}")
    else:
        status = "✅ 정상" if not is_anomaly else "⏳ 버퍼 부족"
        print(f"[{time_str}] {status} | score={score:.1f}{label_str}")
 
 
# 시뮬레이션
def run_simulation(csv_path: str):
    df = pd.read_csv(csv_path)
    seq_buffer = deque(maxlen=SEQ_LEN)
 
    print(f"📂 시뮬레이션 시작: {csv_path} ({len(df):,}행)")
    print(f"라벨 분포: {df['label'].value_counts().to_dict()}\n")
 
    correct = 0
    total   = 0
 
    for _, row in df.iterrows():
        h, m, _ = map(int, row["time"].split(":"))
        true_label = row.get("label", None)
 
        process(h, m,
                row["bed_dist"], row["fridge_dist"], row["living_dist"],
                seq_buffer, row["time"], true_label)
 
        time.sleep(0.05)  # 빠르게 재생 (조절 가능)
 
    print("\n✅ 시뮬레이션 완료")
 
 
# 실시간
def run_realtime():
    import serial
    seq_buffer = deque(maxlen=SEQ_LEN)
 
    print(f"시리얼 포트 연결 중: {SERIAL_PORT}")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    print("✅ 연결 완료. 수신 시작\n")
 
    try:
        while True:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue
            try:
                parts = line.split(",")
                if len(parts) != len(SENSORS):
                    continue
                dist_vals = list(map(float, parts))
            except ValueError:
                continue
 
            now = datetime.now()
            sensor_vals = {s: v for s, v in zip(SENSORS, dist_vals)}
            feature = make_feature(now.hour, now.minute, sensor_vals)
            seq_buffer.append(feature)
 
            score = anomaly_score(feature)
            is_anomaly = score >= THRESHOLD
            time_str = now.strftime("%H:%M:%S")
 
            if is_anomaly and len(seq_buffer) == SEQ_LEN:
                result, conf = classify(seq_buffer)
                print(f"[{time_str}] ⚠️  이상 감지 | score={min(score,999.9):.1f} | 판정: {result} ({conf:.1f}%)")
            else:
                status = "✅ 정상" if not is_anomaly else "⏳ 버퍼 부족"
                print(f"[{time_str}] {status} | score={score:.1f}")
 
    except KeyboardInterrupt:
        print("\n종료")
    finally:
        ser.close()
 
 
# 진입점
if __name__ == "__main__":
    if args.sim:
        run_simulation(args.sim)
    else:
        run_realtime()
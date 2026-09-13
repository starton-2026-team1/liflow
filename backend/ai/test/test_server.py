"""
server.py: FastAPI 추론 서버 (맥북에서 실행)
1차원 fridge 거리값 → 정상/이상 2분류만 판단
실행: uvicorn server:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
from tensorflow import keras

print("모델 로딩 중...")
ae        = keras.models.load_model("model/autoencoder_1s.keras")
THRESHOLD = float(np.load("model/threshold_1s.npy")[0])
MSE_MAX   = float(np.load("model/mse_max_1s.npy")[0])
print(f"✅ 모델 로드 완료 | 임계값: {THRESHOLD:.2f}")

MAX_DIST = 450.0
app = FastAPI()


class SensorData(BaseModel):
    hour:     int
    minute:   int
    distance: float


def make_feature(distance: float) -> np.ndarray:
    v = float(np.clip(distance, 0, MAX_DIST)) / MAX_DIST
    return np.array([[v]], dtype=np.float32)


def anomaly_score(feature: np.ndarray) -> float:
    x_pred = ae.predict(feature, verbose=0)
    mse = float(np.mean(np.power(feature - x_pred, 2)))
    return (mse / MSE_MAX) * 100


@app.post("/api/sensor")
async def infer(data: SensorData):
    feature = make_feature(data.distance)
    score = anomaly_score(feature)
    is_anomaly = score >= THRESHOLD
    label = "이상" if is_anomaly else "정상"

    print(f"[{data.hour:02d}:{data.minute:02d}] dist={data.distance}cm | score={min(score,999.9):.1f} | {label}")

    return {
        "label":      label,
        "score":      round(min(score, 999.9), 1),
        "is_anomaly": is_anomaly
    }


@app.get("/health")
async def health():
    return {"status": "ok", "threshold": THRESHOLD}
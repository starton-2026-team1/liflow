import logging
from pathlib import Path

import numpy as np
from tensorflow import keras

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parents[2] / "ai" / "model"
MAX_DIST = 450.0

_autoencoder = None
_threshold: float | None = None
_mse_max: float | None = None


def _load_model() -> None:
    global _autoencoder, _threshold, _mse_max
    if _autoencoder is not None:
        return
    _autoencoder = keras.models.load_model(MODEL_DIR / "autoencoder_1s.keras")
    _threshold = float(np.load(MODEL_DIR / "threshold_1s.npy")[0])
    _mse_max = float(np.load(MODEL_DIR / "mse_max_1s.npy")[0])
    logger.info("AI autoencoder model loaded (threshold=%.2f)", _threshold)


def predict_anomaly(distance: float) -> dict:
    """단일 fridge 거리값(cm)에 대한 정상/이상 판단."""
    _load_model()

    feature = np.array([[float(np.clip(distance, 0, MAX_DIST)) / MAX_DIST]], dtype=np.float32)
    reconstructed = _autoencoder.predict(feature, verbose=0)
    mse = float(np.mean(np.power(feature - reconstructed, 2)))
    score = (mse / _mse_max) * 100
    is_anomaly = score >= _threshold

    return {
        "label": "이상" if is_anomaly else "정상",
        "score": round(min(score, 999.9), 1),
        "is_anomaly": is_anomaly,
    }

"""
step3_autoencoder_1sensor.py: fridge 거리값 1차원 Autoencoder
"""

import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt


def build_autoencoder(input_dim=1, hidden_dim=8):
    inputs = keras.Input(shape=(input_dim,))
    encoded = layers.Dense(hidden_dim, activation="relu")(inputs)
    decoded = layers.Dense(input_dim, activation="sigmoid")(encoded)
    model = keras.Model(inputs, decoded, name="autoencoder_1s")
    model.compile(optimizer="adam", loss="mse")
    return model


def compute_anomaly_score(model, X, mse_max=None):
    X_pred = model.predict(X, verbose=0)
    mse = np.mean(np.power(X - X_pred, 2), axis=1)
    if mse_max is None:
        mse_max = mse.max()
    score = (mse / mse_max) * 100
    return score, mse_max


if __name__ == "__main__":
    X_normal   = np.load("test/model/X_normal_1s.npy")
    X_abnormal = np.load("test/model/X_abnormal_1s.npy")

    split = int(len(X_normal) * 0.8)
    X_train       = X_normal[:split]
    X_test_normal = X_normal[split:]

    print(f"학습: {X_train.shape} | 테스트 정상: {X_test_normal.shape} | 이상: {X_abnormal.shape}")

    ae = build_autoencoder(input_dim=1, hidden_dim=8)
    ae.summary()

    history = ae.fit(X_train, X_train, epochs=50, batch_size=32,
                     validation_split=0.1, verbose=1)

    ae.save("test/model/autoencoder_1s.keras")
    print("\n✅ 저장: model/autoencoder_1s.keras")

    score_normal,   mse_max = compute_anomaly_score(ae, X_test_normal)
    score_abnormal, _       = compute_anomaly_score(ae, X_abnormal, mse_max=mse_max)

    THRESHOLD = max(np.percentile(score_normal, 99), 1.0)
    normal_correct    = np.sum(score_normal   < THRESHOLD) / len(score_normal)
    abnormal_detected = np.sum(score_abnormal >= THRESHOLD) / len(score_abnormal)

    print(f"임계값: {THRESHOLD:.2f}")
    print(f"정상 판별율: {normal_correct*100:.2f}%")
    print(f"이상 탐지율: {abnormal_detected*100:.2f}%")

    np.save("test/model/threshold_1s.npy", np.array([THRESHOLD]))
    np.save("test/model/mse_max_1s.npy",   np.array([mse_max]))

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    axes[0].plot(history.history["loss"], label="Train")
    axes[0].plot(history.history["val_loss"], label="Val")
    axes[0].set_title("Autoencoder Loss (MSE)"); axes[0].legend(); axes[0].grid(alpha=0.3)

    clip = THRESHOLD * 5
    axes[1].plot(np.clip(score_abnormal[:200], 0, clip), color="blue", label="Anomaly Score")
    axes[1].axhline(y=THRESHOLD, color="red", linestyle="--", label=f"Threshold ({THRESHOLD:.1f})")
    axes[1].set_title(f"Anomaly Score (detected: {abnormal_detected*100:.1f}%)"); axes[1].legend(); axes[1].grid(alpha=0.3)

    axes[2].hist(np.clip(score_normal,   0, clip), bins=50, alpha=0.6, color="green",  label="Normal")
    axes[2].hist(np.clip(score_abnormal, 0, clip), bins=50, alpha=0.6, color="orange", label="Abnormal")
    axes[2].axvline(x=THRESHOLD, color="red", linestyle="--", label=f"Threshold ({THRESHOLD:.1f})")
    axes[2].set_title("Score Distribution"); axes[2].legend(); axes[2].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("autoencoder_1s_result.png", dpi=150)
    print("📈 그래프: autoencoder_1s_result.png")
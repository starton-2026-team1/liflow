
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt
 
 
def build_autoencoder(input_dim=33, hidden_dim=16):
    inputs = keras.Input(shape=(input_dim,))
    encoded = layers.Dense(hidden_dim, activation="relu")(inputs)
    decoded = layers.Dense(input_dim, activation="sigmoid")(encoded)
    model = keras.Model(inputs, decoded, name="autoencoder")
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
    X_normal   = np.load("data/X_normal.npy")
    X_abnormal = np.load("data/X_abnormal.npy")
 
    split = int(len(X_normal) * 0.8)
    X_train       = X_normal[:split]
    X_test_normal = X_normal[split:]
 
    print(f"학습 데이터: {X_train.shape}")
    print(f"테스트 정상: {X_test_normal.shape}")
    print(f"테스트 이상: {X_abnormal.shape}")
 
    ae = build_autoencoder(input_dim=33, hidden_dim=16)
    ae.summary()
 
    history = ae.fit(
        X_train, X_train,
        epochs=50,
        batch_size=32,
        validation_split=0.1,
        verbose=1
    )
 
    ae.save("autoencoder.keras")
    print("\n오토인코더 저장 완료: autoencoder.keras")
 
    score_normal,   mse_max = compute_anomaly_score(ae, X_test_normal)
    score_abnormal, _       = compute_anomaly_score(ae, X_abnormal, mse_max=mse_max)
 
    THRESHOLD = max(np.percentile(score_normal, 99), 1.0)
    print(f"\n임계값 (정상 99th percentile): {THRESHOLD:.2f}")
    print(f"이상치 점수 (정상): 평균={score_normal.mean():.2f}, 최대={score_normal.max():.2f}")
    print(f"이상치 점수 (이상): 평균={score_abnormal.mean():.2f}, 최대={score_abnormal.max():.2f}")
 
    normal_correct     = np.sum(score_normal   < THRESHOLD) / len(score_normal)
    Y_abnormal = np.load("data/Y_abnormal.npy")
    is_abnormal = np.argmax(Y_abnormal, axis=1) != 0  # 정상(0) 제외
    score_only_abnormal = score_abnormal[is_abnormal]
    abnormal_detected = np.sum(score_only_abnormal >= THRESHOLD) / len(score_only_abnormal)
    print(f"\n정상 데이터 정상 판별율: {normal_correct*100:.2f}%")
    print(f"이상 데이터 탐지율:      {abnormal_detected*100:.2f}%")
 
    np.save("data/threshold.npy", np.array([THRESHOLD]))
    np.save("data/mse_max.npy",   np.array([mse_max]))
    print("임계값/mse_max 저장 완료")
 
    # ── 시각화 ──────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
 
    ax1 = axes[0]
    ax1.plot(history.history["loss"],     label="Train Loss")
    ax1.plot(history.history["val_loss"], label="Val Loss")
    ax1.set_title("Autoencoder Loss (MSE)")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
 
    clip_max = THRESHOLD * 5
    ax2 = axes[1]
    ax2.plot(np.clip(score_abnormal[:200], 0, clip_max), color="blue", alpha=0.7, label="Anomaly Score")
    ax2.axhline(y=THRESHOLD, color="red", linestyle="--", label=f"Threshold ({THRESHOLD:.1f})")
    ax2.set_title(f"Anomaly Score on Abnormal Data (detected: {abnormal_detected*100:.1f}%)")
    ax2.set_xlabel("Logs")
    ax2.set_ylabel("Score (clipped)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
 
    ax3 = axes[2]
    ax3.hist(np.clip(score_normal,   0, clip_max), bins=50, alpha=0.6, color="green",  label="Normal")
    ax3.hist(np.clip(score_abnormal, 0, clip_max), bins=50, alpha=0.6, color="orange", label="Abnormal")
    ax3.axvline(x=THRESHOLD, color="red", linestyle="--", label=f"Threshold ({THRESHOLD:.1f})")
    ax3.set_title("Score Distribution")
    ax3.set_xlabel("Score (clipped)")
    ax3.set_ylabel("Count")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
 
    plt.tight_layout()
    plt.savefig("autoencoder_result.png", dpi=150)
    print("그래프 저장: autoencoder_result.png")
 
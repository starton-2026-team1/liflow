import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report
 
SEQ_LEN   = 10
INPUT_DIM = 33
 
 
def build_lstm(seq_len=SEQ_LEN, input_dim=INPUT_DIM):
    model = keras.Sequential([
        layers.LSTM(32, input_shape=(seq_len, input_dim)),
        layers.Dense(3, activation="softmax")
    ], name="lstm")
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model
 
 
def make_sequences(X, Y, seq_len):
    Xs, Ys = [], []
    for i in range(len(X) - seq_len):
        Xs.append(X[i:i+seq_len])
        Ys.append(Y[i+seq_len-1])
    return np.array(Xs), np.array(Ys)
 
 
if __name__ == "__main__":
    # ── 이상 데이터 로드 ──────────────────────────────
    X_ab = np.load("data/X_abnormal.npy")
    Y_ab = np.load("data/Y_abnormal.npy")
 
    # ── 정상 데이터 일부 추가 (이상 데이터의 50% 분량) ──
    X_normal = np.load("data/X_normal.npy")
    n_normal = int(len(X_ab) * 0.5)
    idx = np.random.choice(len(X_normal), n_normal, replace=False)
    X_norm_sample = X_normal[idx]
    Y_norm_sample = np.zeros((n_normal, 3), dtype=np.float32)
    Y_norm_sample[:, 0] = 1  # 라벨 0: 정상
 
    # ── 합치기 ────────────────────────────────────────
    X_all = np.concatenate([X_ab, X_norm_sample], axis=0)
    Y_all = np.concatenate([Y_ab, Y_norm_sample], axis=0)
 
    # 셔플
    idx = np.random.permutation(len(X_all))
    X_all, Y_all = X_all[idx], Y_all[idx]
 
    print(f"전체 데이터: {X_all.shape}")
    labels = np.argmax(Y_all, axis=1)
    names  = {0:"정상", 1:"불면", 2:"반복행동"}
    for l, n in names.items():
        print(f"  {n}: {np.sum(labels==l):,}개")
 
    # ── 시퀀스 생성 ───────────────────────────────────
    X_seq, Y_seq = make_sequences(X_all, Y_all, SEQ_LEN)
    print(f"\n시퀀스: X={X_seq.shape}, Y={Y_seq.shape}")
 
    split = int(len(X_seq) * 0.8)
    X_train, X_test = X_seq[:split], X_seq[split:]
    Y_train, Y_test = Y_seq[:split], Y_seq[split:]
 
    # ── 학습 ─────────────────────────────────────────
    model = build_lstm()
    model.summary()
 
    history = model.fit(
        X_train, Y_train,
        epochs=30,
        batch_size=64,
        validation_split=0.1,
        verbose=1
    )
 
    # ── 평가 ─────────────────────────────────────────
    loss, acc = model.evaluate(X_test, Y_test, verbose=0)
    print(f"\n✅ LSTM 테스트 정확도: {acc*100:.2f}%")
 
    Y_pred_l = np.argmax(model.predict(X_test, verbose=0), axis=1)
    Y_true_l = np.argmax(Y_test, axis=1)
    print("\n분류 리포트:")
    print(classification_report(Y_true_l, Y_pred_l,
          target_names=["정상", "불면", "반복행동"], digits=3))
 
    model.save("lstm.keras")
    print("LSTM 저장 완료: lstm.keras")
 
    # ── 시각화 ───────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
 
    ax1 = axes[0]
    ax1.plot(history.history["accuracy"],     label="Train")
    ax1.plot(history.history["val_accuracy"], label="Val")
    ax1.set_title("LSTM Accuracy")
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Accuracy")
    ax1.legend(); ax1.grid(True, alpha=0.3)
 
    ax2 = axes[1]
    ax2.plot(history.history["loss"],     label="Train")
    ax2.plot(history.history["val_loss"], label="Val")
    ax2.set_title("LSTM Loss")
    ax2.set_xlabel("Epoch")
    ax2.legend(); ax2.grid(True, alpha=0.3)
 
    plt.tight_layout()
    plt.savefig("lstm_result.png", dpi=150)
    print("그래프 저장: lstm_result.png")
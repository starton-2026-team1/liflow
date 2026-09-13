"""
step4_lstm_1sensor.py: fridge 거리값 1차원 LSTM
"""

import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report

SEQ_LEN   = 10
INPUT_DIM = 1


def build_lstm():
    model = keras.Sequential([
        layers.LSTM(32, input_shape=(SEQ_LEN, INPUT_DIM)),
        layers.Dense(3, activation="softmax")
    ], name="lstm_1s")
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def make_sequences(X, Y, seq_len):
    Xs, Ys = [], []
    for i in range(len(X) - seq_len):
        Xs.append(X[i:i+seq_len])
        Ys.append(Y[i+seq_len-1])
    return np.array(Xs), np.array(Ys)


if __name__ == "__main__":
    X_ab = np.load("test/model/X_abnormal_1s.npy")
    Y_ab = np.load("test/model/Y_abnormal_1s.npy")

    X_normal = np.load("test/model/X_normal_1s.npy")
    n = int(len(X_ab) * 0.5)
    idx = np.random.choice(len(X_normal), n, replace=False)
    X_ns = X_normal[idx]
    Y_ns = np.zeros((n, 3), dtype=np.float32); Y_ns[:, 0] = 1

    X_all = np.concatenate([X_ab, X_ns])
    Y_all = np.concatenate([Y_ab, Y_ns])
    idx = np.random.permutation(len(X_all))
    X_all, Y_all = X_all[idx], Y_all[idx]

    print(f"전체: {X_all.shape}")
    labels = np.argmax(Y_all, axis=1)
    for l, n in {0:"정상", 1:"불면", 2:"반복행동"}.items():
        print(f"  {n}: {(labels==l).sum():,}개")

    X_seq, Y_seq = make_sequences(X_all, Y_all, SEQ_LEN)
    split = int(len(X_seq) * 0.8)
    X_train, X_test = X_seq[:split], X_seq[split:]
    Y_train, Y_test = Y_seq[:split], Y_seq[split:]

    model = build_lstm()
    model.summary()

    history = model.fit(X_train, Y_train, epochs=30, batch_size=64,
                        validation_split=0.1, verbose=1)

    loss, acc = model.evaluate(X_test, Y_test, verbose=0)
    print(f"\n✅ 테스트 정확도: {acc*100:.2f}%")

    Y_pred_l = np.argmax(model.predict(X_test, verbose=0), axis=1)
    Y_true_l = np.argmax(Y_test, axis=1)
    print(classification_report(Y_true_l, Y_pred_l,
          target_names=["정상", "불면", "반복행동"], digits=3))

    model.save("test/model/lstm_1s.keras")
    print("✅ 저장: model/lstm_1s.keras")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(history.history["accuracy"], label="Train")
    axes[0].plot(history.history["val_accuracy"], label="Val")
    axes[0].set_title("LSTM Accuracy"); axes[0].legend(); axes[0].grid(alpha=0.3)
    axes[1].plot(history.history["loss"], label="Train")
    axes[1].plot(history.history["val_loss"], label="Val")
    axes[1].set_title("LSTM Loss"); axes[1].legend(); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("lstm_1s_result.png", dpi=150)
    print("📈 그래프: lstm_1s_result.png")
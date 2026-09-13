"""
Step 5: 전체 파이프라인 연결
논문 그림 3 구현

실시간 센서 로그 → Autoencoder → (이상 의심 시) LSTM → 결과 출력
"""

import numpy as np
import tensorflow as tf
import pandas as pd
from preprocess import preprocess

THRESHOLD = 3.0  # 이상치 기준 (100 스케일 기준)
SEQUENCE_LEN = 10


def run_pipeline(log_buffer, ae_model, lstm_model):
    """
    log_buffer: 최근 SEQUENCE_LEN개 센서 로그 (DataFrame)
    반환: (결과, 이상치_점수)
    """
    label_names = {0: "정상", 1: "불면 감지", 2: "반복행동 감지"}

    # 전처리
    X = preprocess(log_buffer)  # shape: (seq_len, 36)

    # 1단계: Autoencoder 이상치 판별
    X_pred = ae_model.predict(X, verbose=0)
    mse = np.mean(np.power(X - X_pred, 2), axis=1)
    score = (mse / (mse.max() + 1e-8)) * 100
    avg_score = np.mean(score)

    if avg_score < THRESHOLD:
        return label_names[0], avg_score

    # 2단계: LSTM 분류
    X_seq = X.reshape(1, SEQUENCE_LEN, 36)  # (1, seq_len, 36)
    Y_pred = lstm_model.predict(X_seq, verbose=0)
    label = np.argmax(Y_pred[0])

    return label_names[label], avg_score # type: ignore


if __name__ == "__main__":
    import os
    # 모델 파일 확인
    if not os.path.exists("model/autoencoder.keras") or not os.path.exists("model/lstm.keras"):
        print("먼저 step3, step4를 실행해 모델을 학습시키세요.")
        exit()

    ae = tf.keras.models.load_model("model/autoencoder.keras")
    lstm = tf.keras.models.load_model("model/lstm_classifier.keras")
    print("모델 로드 완료")

    # 테스트: 정상 로그 10개
    normal_df = pd.read_csv("data/normal_data.csv").head(SEQUENCE_LEN)
    result, score = run_pipeline(normal_df, ae, lstm)
    print(f"\n[정상 로그 테스트]")
    print(f"  이상치 점수: {score:.2f} / 100")
    print(f"  판정: {result}")

    # 테스트: 이상 로그 10개 (불면 데이터 포함)
    abnormal_df = pd.read_csv("data/abnormal_data.csv")
    insomnia_df = abnormal_df[abnormal_df["label"] == 1].head(SEQUENCE_LEN)
    if len(insomnia_df) >= SEQUENCE_LEN:
        result, score = run_pipeline(insomnia_df, ae, lstm)
        print(f"\n[불면 로그 테스트]")
        print(f"  이상치 점수: {score:.2f} / 100")
        print(f"  판정: {result}")
"""
preprocess_1sensor.py: fridge 거리값만 사용 (1차원)
시간 피처 없이 거리값만으로 학습
"""

import pandas as pd
import numpy as np

MAX_DIST = 450.0


def make_feature(fridge_dist: float) -> np.ndarray:
    v = float(np.clip(fridge_dist, 0, MAX_DIST)) / MAX_DIST
    return np.array([v], dtype=np.float32)


def preprocess(df):
    """DataFrame → numpy array (shape: [n, 1])"""
    X = []
    for _, row in df.iterrows():
        feature = make_feature(row.get("fridge_dist", MAX_DIST))
        X.append(feature)
    return np.array(X, dtype=np.float32)


def preprocess_labels(df):
    label_map = {"정상": 0, "불면": 1, "반복행동": 2}
    labels = df["label"].map(label_map).values
    Y = np.zeros((len(labels), 3), dtype=np.float32)
    for i, l in enumerate(labels):
        Y[i, int(l)] = 1
    return Y


if __name__ == "__main__":
    normal_df = pd.read_csv("data/normal_data.csv")
    X_normal = preprocess(normal_df)
    np.save("test/model/X_normal_1s.npy", X_normal)
    print(f"✅ 정상 데이터 전처리 완료: shape={X_normal.shape}")

    abnormal_df = pd.read_csv("data/abnormal_data.csv")
    X_abnormal = preprocess(abnormal_df)
    Y_abnormal = preprocess_labels(abnormal_df)
    np.save("test/model/X_abnormal_1s.npy", X_abnormal)
    np.save("test/model/Y_abnormal_1s.npy", Y_abnormal)
    print(f"✅ 이상 데이터 전처리 완료: X={X_abnormal.shape}, Y={Y_abnormal.shape}")

    print("\n라벨 분포:")
    for name, count in abnormal_df["label"].value_counts().items():
        print(f"  {name}: {count}개")
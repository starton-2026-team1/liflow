# 치매 환자 이상행동 탐지 시스템

논문 재현: "딥러닝 기반 이상 행동 탐지 시스템" (JICS 2020)

## 실행 순서

```bash
# 1. 데이터 생성
python generate_data.py

# 2. 전처리
python preprocess.py

# 3. Autoencoder 학습
python autoencoder.py

# 4. LSTM 학습
python lstm.py

# 5. 전체 파이프라인 테스트
python pipeline.py
```

## 파일 구조

```
step1_generate_data.py   → 센서 로그 데이터 생성
step2_preprocess.py      → One-hot + 정규화
step3_autoencoder.py     → Autoencoder 학습
step4_lstm.py            → LSTM 분류기 학습
step5_pipeline.py        → 전체 파이프라인
```

## 핵심 설계

```
센서 로그 → Autoencoder → 이상치 < 3% → 정상
                        ↓ 이상치 ≥ 3%
                       LSTM → 0:정상 / 1:불면 / 2:반복행동
```

## 필요 패키지

```
pip install tensorflow pandas numpy scikit-learn matplotlib
```

model 폴더에 드라이브에 있는 autoencoder.keras, lstm.keras, mse_max.npy, threshold.npy 를 다운로드 한 후 폴더에 넣고 실행

## 진행도

2026-09-11 : 냉장고, 방 문 데이터 총합 16만개 수집

수집된 데이터 : [링크](https://drive.google.com/drive/folders/1u3T5-lxgg6bSJd4KziEOuyRAnfeKIGvt?hl=ko)

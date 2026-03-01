# Python Beats Music2

Python 기반 오디오 처리/자동 반주 생성 프로젝트입니다. 현재 저장소는 **비동기 백엔드(FastAPI + Celery)** 와 **오디오 스타일 분류용 ML 파이프라인(scikit-learn)** 을 함께 포함합니다.

---

## 1. 기술 스택 분석

### 언어/런타임
- **Python 3.11 (slim 이미지)**
- 컨테이너 기반 실행 (Docker, Docker Compose)

### 백엔드/API
- **FastAPI**: 업로드/작업 조회/결과 다운로드 API 제공
- **Uvicorn**: ASGI 서버
- **Pydantic + pydantic-settings**: 요청 스키마/환경설정 로딩

### 비동기 작업 처리
- **Celery (Redis broker/result backend)**
- API 서버와 워커를 분리해 MP3 생성 작업을 비동기 처리

### 오디오 처리
- **pydub + ffmpeg**
- 입력 음원 feature 추출 및 출력 MP3 렌더링

### ML 학습
- **NumPy / scikit-learn / joblib**
- Feature 스케일링(StandardScaler) + **SVC(RBF)** 분류기 학습
- 학습 결과물을 `joblib` 모델 + 런타임용 `style_profile.json`으로 저장

---

## 2. 저장소 구조

```text
app/
  main.py                # FastAPI 엔드포인트
  tasks.py               # Celery task (반주 생성)
  audio_features.py      # 오디오 feature 추출
  ml_profile.py          # style_profile.json 로딩/프리셋 해석
  music_pipeline.py      # 반주 렌더링 로직
  config.py              # 환경변수/경로 설정

ml/training/
  train_style_profile.py # 스타일 분류기 학습 + profile 생성
  requirements.txt

tools/
  build_training_dataset.py # 라벨 폴더 -> dataset.csv 생성

Dockerfile*              # api / worker / trainer 이미지
Docker-compose.yml       # api, worker, redis, trainer(profile)
```

---

## 3. 아키텍처

### 온라인 추론(생성) 경로
1. 사용자가 `POST /jobs`로 MP3 업로드
2. API가 파일 저장 후 Celery task 큐잉
3. Worker가 입력 음원 feature 추출 (`duration_sec`, `rms`, `zero_crossing_rate`, `spectral_centroid_norm`)
4. `/data/models/style_profile.json`이 있으면 최근접 centroid 기반으로 스타일 preset 선택
5. preset(코드 진행, dramatic gain bias, bpm bias)을 적용하여 피아노 반주 MP3 생성
6. `GET /jobs/{job_id}` 상태 조회 후 `GET /outputs/{filename}` 다운로드

### 오프라인 ML 학습 경로
1. 라벨별 MP3 데이터셋 준비
2. `tools/build_training_dataset.py`로 tabular CSV 생성
3. `ml/training/train_style_profile.py`로 학습/평가
4. 산출물 저장:
   - `data/models/style_classifier.joblib`
   - `data/models/style_profile.json`

---

## 4. 로컬 실행 가이드 (서비스)

### 4-1. 필수 준비
- Docker / Docker Compose
- 테스트용 MP3 파일

### 4-2. 환경 파일 생성
`docker-compose.yml`에서 `env_file: .env`를 사용하므로 최소 `.env` 파일을 만듭니다.

```bash
cat > .env <<'ENV'
APP_NAME=Python Beats Music Backend
REDIS_URL=redis://redis:6379/0
MAX_UPLOAD_MB=200
ENV
```

### 4-3. 데이터 디렉터리 생성 및 부팅

```bash
mkdir -p data/uploads data/outputs data/models data/training data/labeled
docker compose up --build
```

### 4-4. 동작 확인
- Health: `GET http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

업로드 예시:

```bash
curl -X POST http://localhost:8000/jobs \
  -F "file=@sample.mp3" \
  -F "rights_confirmed=true" \
  -F "dramatic_level=8" \
  -F "target_bpm=120"
```

상태 조회:

```bash
curl http://localhost:8000/jobs/<job_id>
```

완료 파일 다운로드:

```bash
curl -L http://localhost:8000/outputs/<output_filename>.mp3 -o result.mp3
```

---

## 5. ML 작업 상세 가이드

아래 절차는 **“데이터 준비 → CSV 빌드 → 학습 → 결과 반영 → 검증”** 까지 전체 사이클을 다룹니다.

### 5-1. 데이터셋 설계

권장 라벨 폴더 구조:

```text
data/labeled/
  cinematic/
    cin_001.mp3
    cin_002.mp3
  dance/
    dance_001.mp3
  lofi/
    lofi_001.mp3
```

권장 원칙:
- 라벨 간 샘플 수를 가급적 균형 있게 맞추기
- 지나치게 짧거나 무음에 가까운 파일 제외
- 샘플레이트/코덱이 달라도 pydub가 디코딩 가능하면 사용 가능

### 5-2. 학습 CSV 생성

```bash
python tools/build_training_dataset.py \
  --labeled-root data/labeled \
  --output-csv data/training/dataset.csv
```

생성 컬럼:
- `path`: 원본 파일 경로
- `label`: 클래스 라벨
- `duration_sec`: 길이(초)
- `rms`: 에너지 크기
- `zero_crossing_rate`: 파형 부호 변화율
- `spectral_centroid_norm`: 정규화 스펙트럼 중심

빠른 확인:

```bash
python - <<'PY'
import pandas as pd
df = pd.read_csv('data/training/dataset.csv')
print(df.head())
print(df['label'].value_counts())
PY
```

### 5-3. 학습 실행 (추천: trainer 프로파일)

```bash
docker compose --profile training run --rm trainer \
  python ml/training/train_style_profile.py \
  --dataset-csv /data/training/dataset.csv \
  --model-out /data/models/style_classifier.joblib \
  --profile-out /data/models/style_profile.json
```

학습 스크립트 동작:
- train/test split (`test_size=0.25`, `stratify`, `random_state=42`)
- `StandardScaler + SVC(kernel='rbf', probability=True, class_weight='balanced')`
- `classification_report` 출력
- 전체 데이터 기준 label centroid 계산 후 profile 생성

### 5-4. 학습 산출물 이해

#### (A) `style_classifier.joblib`
- scikit-learn 파이프라인 직렬화 결과
- 오프라인 재평가/향후 추론 확장 시 활용 가능

#### (B) `style_profile.json`
런타임에서 실제로 사용되는 파일이며 다음 정보를 포함:
- `feature_columns`
- `feature_centroids` (라벨별 centroid 벡터)
- `presets` (라벨별 코드 진행/드라마틱 게인/BPM bias)

즉, 현재 런타임 반영의 핵심은 **profile 기반 preset 선택**입니다.

### 5-5. 서비스에 학습 결과 반영

별도 코드 수정 없이 `/data/models/style_profile.json` 파일만 존재하면 worker가 자동 로딩합니다.

권장 절차:
1. 기존 서비스 실행 중 학습 수행
2. `data/models/style_profile.json` 갱신
3. 새 작업 제출 후 생성 결과 비교

필요하면 worker 재시작으로 캐시 상태를 초기화하세요:

```bash
docker compose restart worker
```

### 5-6. 반복 개선 루프 (실무형)

1. 실패 케이스 수집 (원하지 않는 반주 스타일)
2. 해당 케이스를 적절한 라벨로 재라벨링/추가
3. CSV 재생성 + 재학습
4. `classification_report`와 실제 청취 결과를 함께 비교
5. 라벨 정의 또는 preset 맵(PRESET_MAP) 조정

---

## 6. 트러블슈팅

### ffmpeg 관련 에러
- pydub는 ffmpeg 실행 파일이 필요합니다.
- 컨테이너에는 설치되어 있으므로, 로컬 실행 시 ffmpeg 설치 여부를 확인하세요.

### 학습 데이터가 비어 있을 때
- `dataset is empty` 예외가 발생합니다.
- `data/labeled/<label>/*.mp3` 구조와 파일 확장자를 점검하세요.

### 라벨 불균형이 심할 때
- 특정 클래스 성능이 급격히 저하될 수 있습니다.
- 샘플 추가 또는 라벨 재정의로 균형을 맞추세요.

---

## 7. 온라인 MP3 변환 스모크 테스트

```bash
python online_mp3_convert_test.py \
  --url "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
```

- 출력: `data/manual_test/sample.mp3`, `data/manual_test/sample.wav`
- 필요 조건: ffmpeg + 외부 네트워크

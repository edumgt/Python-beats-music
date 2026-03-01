# Python Beats Music2

이 프로젝트는 **Python 기반의 오디오/비디오 편집 및 비트 제작 스크립트 모음**이며,
현재는 MP3 업로드 기반의 **AI 편곡 백엔드(FastAPI + Celery)** 와
**ML 학습 데이터 생성/학습 파이프라인(분리 Docker 환경)** 까지 포함합니다.

## 기술 스택

### 1) 서비스 런타임
- Python 3.11
- FastAPI + Uvicorn
- Celery + Redis
- pydub + ffmpeg

### 2) ML 파이프라인 (별도 Docker)
- Dataset builder: 라벨링된 MP3 폴더 -> 학습 CSV 생성
- Trainer: scikit-learn 기반 스타일 분류기 학습
- Runtime profile export: `style_profile.json`을 API/Worker가 읽어 생성 결과에 반영

---

## 아키텍처 요약

### A. 추론/생성 서비스
1. `/jobs`로 MP3 업로드
2. worker가 입력 오디오 특징량 추출
3. `/data/models/style_profile.json` 이 있으면 최근접 스타일 프리셋 선택
4. 스타일 프리셋(코드 진행, gain bias, bpm bias)을 반영해 피아노 반주 MP3 생성

### B. ML 학습 파이프라인 (별도 Docker profile)
1. 라벨링 데이터 준비: `data/labeled/<label_name>/*.mp3`
2. `tools/build_training_dataset.py` 로 `data/training/dataset.csv` 생성
3. `ml/training/train_style_profile.py` 로 학습 실행
4. 산출물:
   - `data/models/style_classifier.joblib` (학습 모델)
   - `data/models/style_profile.json` (런타임 반영 파일)

---

## 빠른 시작 (서비스)

```bash
cp .env.example .env
mkdir -p data/uploads data/outputs data/models

docker compose up --build
```

- Health: `GET http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

업로드 예시:

```bash
curl -X POST http://localhost:8000/jobs \
  -F "file=@sample.mp3" \
  -F "rights_confirmed=true" \
  -F "dramatic_level=8"
```

---

## ML 학습 데이터 생성

라벨 폴더 구조 예시:

```text
data/labeled/
  cinematic/
    a.mp3
    b.mp3
  dance/
    c.mp3
  lofi/
    d.mp3
```

CSV 생성:

```bash
python tools/build_training_dataset.py \
  --labeled-root data/labeled \
  --output-csv data/training/dataset.csv
```

---

## 별도 Docker 환경에서 학습 실행

아래 명령은 `trainer` 컨테이너만 일회성 실행합니다.

```bash
docker compose --profile training run --rm trainer \
  python ml/training/train_style_profile.py \
  --dataset-csv /data/training/dataset.csv \
  --model-out /data/models/style_classifier.joblib \
  --profile-out /data/models/style_profile.json
```

`style_profile.json`이 생성되면, API/Worker는 해당 파일을 자동으로 읽어
다음 작업부터 스타일 프리셋을 반영합니다.

---

## 온라인 MP3 변환 스모크 테스트

```bash
python online_mp3_convert_test.py \
  --url "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
```

- 출력: `data/manual_test/sample.mp3`, `data/manual_test/sample.wav`
- 필요 조건: `ffmpeg` + 외부 네트워크

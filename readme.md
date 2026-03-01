# Python Beats Music2

이 프로젝트는 **Python 기반의 오디오/비디오 편집 및 비트 제작 스크립트 모음**입니다.  
기존 스크립트 방식은 유지하면서, MP3 업로드 기반의 **AI 편곡 백엔드(FastAPI + Celery)** 를 추가했습니다.

## 기술 스택

### 1) 언어/실행 환경
- **Python 3.11**
- 스크립트 중심 CLI 실행 + FastAPI 서비스

### 2) 백엔드/API
- **FastAPI + Uvicorn**: 업로드/상태 조회/다운로드 API
- **Celery + Redis**: 비동기 오디오 작업 큐
- **Pydantic Settings**: 환경변수 설정 관리

### 3) 오디오 처리 핵심
- **pydub**: MP3 로드/합성/인코딩
- **ffmpeg**: MP3 처리용 시스템 런타임
- (기존) **librosa / numpy / scipy / soundfile**: 스크립트 기반 실험 처리

### 4) 기존 유틸 스크립트
- 비트 제작/루프 생성
- 오디오 편집(MP3↔WAV, 자르기, 합치기)
- 영상 보조 처리(오디오 추출)

---

## 신규 백엔드 아키텍처 요약

- `/jobs`로 MP3 업로드 + `rights_confirmed=true` 확인
- Celery worker가 원본 재사용 없이 신규 피아노 반주 MP3 생성
- `/jobs/{job_id}`로 상태 조회 (`queued/processing/done/failed`)
- `/outputs/{filename}`로 결과 다운로드

> 저작권 리스크를 낮추기 위해, 원본 음원을 직접 변형/재배포하지 않고 길이/분위기만 참고한 신규 피아노 합성 결과물을 생성하도록 구성했습니다.

---

## 빠른 시작 (Docker Compose)

```bash
cp .env.example .env
mkdir -p data/uploads data/outputs
docker compose up --build
```

서버 실행 후:
- Health: `GET http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### 업로드 예시

```bash
curl -X POST http://localhost:8000/jobs \
  -F "file=@sample.mp3" \
  -F "rights_confirmed=true" \
  -F "dramatic_level=8"
```

반환된 `job_id`로 상태 조회:

```bash
curl http://localhost:8000/jobs/<job_id>
```

완료 시 `output_file`을 다운로드:

```bash
curl -O http://localhost:8000/outputs/<output_file>
```

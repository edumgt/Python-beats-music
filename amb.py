import ffmpeg
import librosa
import numpy as np
from pydub import AudioSegment
import random
import os

# === 1. BPM 감지 ===
def detect_bpm(mp3_file):
    y, sr = librosa.load(mp3_file)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])
    return int(round(tempo))

# === 2. 앰비언트 드럼 루프 생성 (weirdo 포함) ===
def generate_ambient_drum_loop(kick, snare, tom, weirdo, bpm, duration_ms):
    step_duration = 30000 // bpm
    total_steps = duration_ms // step_duration
    loop = AudioSegment.silent(duration=0)

    for i in range(total_steps):
        beat = AudioSegment.silent(duration=step_duration)

        if random.random() < 0.12:
            beat = beat.overlay(kick - 12)
        if random.random() < 0.08:
            beat = beat.overlay(snare.pan(-0.6) - 14)
        if random.random() < 0.08:
            beat = beat.overlay(tom.pan(0.6) - 16)
        if random.random() < 0.035:  # weirdo는 2~3초에 한 번
            beat = beat.overlay(weirdo.pan(random.uniform(-0.5, 0.5)) - 10)

        loop += beat

    return loop

# === 3. 실행 함수 ===
def process_video(input_file):
    base_name = os.path.splitext(input_file)[0]
    extracted_mp3 = base_name + ".mp3"
    output_mp3 = base_name + "_mixed.mp3"

    # 1. ffmpeg로 MP3 추출
    print(f"🎬 MP3 추출 중: {input_file} → {extracted_mp3}")
    ffmpeg.input(input_file).output(extracted_mp3, format='mp3', acodec='libmp3lame').run()

    # 2. 리소스 로딩
    kick = AudioSegment.from_wav("db/samples/kick.wav")
    snare = AudioSegment.from_wav("db/samples/snare.wav")
    tom = AudioSegment.from_wav("db/samples/tom.wav")
    weirdo = AudioSegment.from_wav("db/samples/perc_weirdo.wav")
    music = AudioSegment.from_mp3(extracted_mp3)

    # 3. BPM 감지 및 드럼 생성
    bpm = detect_bpm(extracted_mp3)
    print(f"🎼 감지된 BPM: {bpm}")
    drum_loop = generate_ambient_drum_loop(kick, snare, tom, weirdo, bpm, duration_ms=len(music))

    # 4. 3초 후부터 드럼 등장
    delay_ms = 3000
    drum_with_delay = AudioSegment.silent(duration=delay_ms) + drum_loop
    drum_with_delay = drum_with_delay[:len(music)]

    # 5. 믹싱
    mixed = music.overlay(drum_with_delay)

    # 6. 25초 ~ 30초 페이드아웃 적용
    max_duration_ms = 30000
    fade_start_ms = 25000
    fade_duration_ms = max_duration_ms - fade_start_ms

    mixed = mixed[:max_duration_ms].fade_out(fade_duration_ms)

    # 7. 저장
    mixed.export(output_mp3, format="mp3")
    print(f"✅ 25~30초 페이드아웃 포함 최종 믹스 완료: {output_mp3}")

# === 4. 실행 시작 ===
if __name__ == "__main__":
    input_file = input("🎥 MP4 파일명을 입력하세요 (예: video.mp4): ").strip()
    if not os.path.isfile(input_file):
        print("❌ 파일을 찾을 수 없습니다.")
    else:
        process_video(input_file)

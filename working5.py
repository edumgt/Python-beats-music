import os
import random
import numpy as np
import librosa
import ffmpeg
import glob
from scipy.io.wavfile import write
from pydub import AudioSegment
import platform
import subprocess

# === 설정 ===
sample_rate = 44100
duration = 25  # 기본 피아노/드럼 생성 길이
total_samples = int(sample_rate * duration)

# === 유틸 함수들 ===
def detect_bpm(mp3_file):
    y, sr = librosa.load(mp3_file)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, (np.ndarray, list)):
        tempo = float(tempo[0])
    return int(round(tempo))

def loop_to_match_length(wave, target_samples):
    repeats = int(np.ceil(target_samples / len(wave)))
    looped = np.tile(wave, repeats)[:target_samples]
    return looped

def load_and_match_bpm_mp3(mp3_path, target_bpm, target_samples):
    y, sr = librosa.load(mp3_path, sr=sample_rate)
    original_bpm = detect_bpm(mp3_path)
    print(f"🎵 {os.path.basename(mp3_path)} BPM: {original_bpm} → {target_bpm} 맞춤")

    if original_bpm <= 0:
        original_bpm = target_bpm

    rate = target_bpm / original_bpm
    try:
        y_stretched = librosa.effects.time_stretch(y, rate)
    except Exception as e:
        print(f"⚠️ time_stretch 실패: {e}")
        y_stretched = y

    return loop_to_match_length(y_stretched, target_samples)

def load_mp3_as_np_array(mp3_path):
    ext = AudioSegment.from_mp3(mp3_path).set_frame_rate(sample_rate).set_channels(1)
    raw = np.array(ext.get_array_of_samples()).astype(np.float32) / 32767.0
    return raw

def generate_note(freq, length_sec, volume=0.1):
    t = np.linspace(0, length_sec, int(sample_rate * length_sec), False)
    wave = np.sin(2 * np.pi * freq * t) * volume
    return wave

def generate_chord(freqs, length_sec, volume=0.1):
    return sum(generate_note(f, length_sec, volume) for f in freqs) / len(freqs)

def generate_kick_pattern(length_sec, bpm, interval=1.0, volume=0.1):
    beat_duration = 80 / bpm
    interval_sec = beat_duration * interval
    kick = np.zeros(int(sample_rate * length_sec))
    pulse = generate_note(60.0, 0.05, volume)
    for i in np.arange(0, length_sec, interval_sec):
        idx = int(i * sample_rate)
        if idx + len(pulse) < len(kick):
            kick[idx:idx + len(pulse)] += pulse
    return kick

def generate_ambient_drum_loop(bpm, duration_sec):
    kick = generate_kick_pattern(duration_sec, bpm, interval=1.0, volume=0.2)
    noise = np.random.randn(len(kick)) * 0.005
    tom = generate_kick_pattern(duration_sec, bpm, interval=2.0, volume=0.1)
    return (kick + tom + noise)

def play_mp3(mp3_filename):
    system = platform.system()
    try:
        if system == 'Windows':
            os.startfile(mp3_filename)
        elif system == 'Darwin':
            subprocess.run(['open', mp3_filename])
        else:
            subprocess.run(['xdg-open', mp3_filename])
        print("🎧 자동 재생 시작")
    except Exception as e:
        print(f"❌ 자동 재생 실패: {e}")

# === 메인 처리 ===
def process_video(input_mp4):
    base = os.path.splitext(input_mp4)[0]
    extracted_mp3 = base + "_extracted.mp3"
    final_mp3 = base + "_final_mix.mp3"

    print(f"🎬 MP3 추출 중: {input_mp4} → {extracted_mp3}")
    ffmpeg.input(input_mp4).output(extracted_mp3, format='mp3', acodec='libmp3lame').run()

    music = load_mp3_as_np_array(extracted_mp3)
    target_samples = len(music)

    bpm = detect_bpm(extracted_mp3)
    print(f"🎼 감지된 BPM: {bpm}")

    base_freqs = {
        "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.00,
        "A2": 110.00, "B2": 123.47, "C3": 130.81, "E3": 164.81, "G3": 196.00
    }
    chords = [["C2", "E2", "G2"], ["F2", "A2", "C3"], ["G2", "B2", "D2"], ["A2", "C3", "E3"]]
    chord_duration = 0.75
    chord_sequence = random.choices(chords, k=int(duration / chord_duration))

    piano = np.concatenate([
        generate_chord([base_freqs[n] for n in chord], chord_duration, 0.45)
        for chord in chord_sequence
    ])
    ambient_drum = generate_ambient_drum_loop(bpm, duration)

    piano_track = loop_to_match_length(piano, target_samples)
    drum_track = loop_to_match_length(ambient_drum, target_samples)

    mixed = 0.4 * music + 0.4 * drum_track + 0.5 * piano_track

    # === makemp3 결과물 bpm 맞춰 포함 ===
    mp3_candidates = sorted(glob.glob("./db/projects/*.mp3"), key=os.path.getmtime, reverse=True)
    if mp3_candidates:
        latest_mp3 = mp3_candidates[0]
        print(f"🎼 makemp3.py 결과 포함: {os.path.basename(latest_mp3)}")
        user_track = load_and_match_bpm_mp3(latest_mp3, bpm, target_samples)
        mixed += user_track

    mixed = mixed / np.max(np.abs(mixed))
    wav_temp = base + "_mix_temp.wav"
    write(wav_temp, sample_rate, np.int16(mixed * 32767))
    AudioSegment.from_wav(wav_temp).export(final_mp3, format="mp3")
    os.remove(wav_temp)

    print(f"✅ 최종 믹스 완료 → {final_mp3}")
    play_mp3(final_mp3)

if __name__ == "__main__":
    mp4_input = input("🎥 MP4 파일명을 입력하세요 (예: video.mp4): ").strip()
    if not os.path.isfile(mp4_input):
        print("❌ 해당 파일을 찾을 수 없습니다.")
    else:
        process_video(mp4_input)

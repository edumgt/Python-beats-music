import os
import random
import numpy as np
from scipy.io.wavfile import write
from pydub import AudioSegment
import platform
import subprocess

# === 설정 ===
sample_rate = 44100
duration = 25
tempo_bpm = 128
total_samples = int(sample_rate * duration)

# === 유틸 함수들 ===

def load_wav_as_np_array(wav_path, duration_sec=25, sample_rate=44100):
    target_samples = int(duration_sec * sample_rate)

    audio = AudioSegment.from_wav(wav_path).set_frame_rate(sample_rate).set_channels(1)
    raw = np.array(audio.get_array_of_samples()).astype(np.float32) / 32767.0

    # 부족하면 0 패딩, 넘치면 자름
    if len(raw) < target_samples:
        raw = np.pad(raw, (0, target_samples - len(raw)))
    else:
        raw = raw[:target_samples]

    return raw




def load_mp3_as_np_array(mp3_path, target_samples, target_rate=44100):
    ext = AudioSegment.from_mp3(mp3_path).set_frame_rate(target_rate).set_channels(1)
    raw = np.array(ext.get_array_of_samples()).astype(np.float32) / 32767.0
    return np.pad(raw, (0, max(0, target_samples - len(raw))))[:target_samples]

def align_and_trim(track):
    return np.pad(track, (0, max(0, total_samples - len(track))))[:total_samples]

def generate_note(freq, length_sec, volume=0.1):
    t = np.linspace(0, length_sec, int(sample_rate * length_sec), False)
    wave = np.sin(2 * np.pi * freq * t) * volume
    # envelope = np.linspace(1, 0.1, len(wave))
    return wave 

def generate_chord(freqs, length_sec, volume=0.1):
    return sum(generate_note(f, length_sec, volume) for f in freqs) / len(freqs)

def generate_kick_pattern(length_sec, bpm, interval=1.0, volume=0.3):
    beat_duration = 128 / bpm
    interval_sec = beat_duration * interval
    kick = np.zeros(int(sample_rate * length_sec))
    pulse = generate_note(60.0, 0.05, volume)
    for i in np.arange(0, length_sec, interval_sec):
        idx = int(i * sample_rate)
        if idx + len(pulse) < len(kick):
            kick[idx:idx + len(pulse)] += pulse
    return kick

def play_mp3(mp3_filename):
    system = platform.system()
    try:
        if system == 'Windows':
            os.startfile(mp3_filename)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', mp3_filename])
        else:  # Linux/Unix
            subprocess.run(['xdg-open', mp3_filename])
        print("🎧 자동 재생 시작")
    except Exception as e:
        print(f"❌ 자동 재생 실패: {e}")

# === 음계 및 코드 진행 ===
base_freqs = {
    "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.00,
    "A2": 110.00, "B2": 123.47, "C3": 130.81, "E3": 164.81, "G3": 196.00
}
chords = [["C2", "E2", "G2"], ["F2", "A2", "C3"], ["G2", "B2", "D2"], ["A2", "C3", "E3"]]
chord_duration = 1.1
chord_sequence = random.choices(chords, k=int(duration / chord_duration))

# === 트랙 생성 ===
piano_track = np.concatenate([
    generate_chord([base_freqs[n] for n in chord], chord_duration, 0.35)
    for chord in chord_sequence
])
piano_track = align_and_trim(piano_track)
kick_track = align_and_trim(generate_kick_pattern(duration, tempo_bpm))

# === mp3 랜덤 선택
mp3_dir = "./db/projects"
mp3_files = [os.path.join(mp3_dir, f) for f in os.listdir(mp3_dir) if f.endswith(".mp3")]
if len(mp3_files) < 3:
    raise RuntimeError("❌ mp3 파일이 3개 이상 필요합니다.")

selected_mp3s = random.sample(mp3_files, 1)
print("🎲 선택된 MP3 파일:")
for f in selected_mp3s:
    print(" -", os.path.basename(f))

# === 외부 트랙 불러오기 및 정렬
external_tracks = [load_mp3_as_np_array(mp3, total_samples) for mp3 in selected_mp3s]

gpt_midi_audio = load_wav_as_np_array("chord_progression.wav", duration_sec=25, sample_rate=44100)

mix = gpt_midi_audio * 0.1 + kick_track
for ext_track in external_tracks:
    mix += ext_track



mix = mix / np.max(np.abs(mix))  # normalize

# === 저장
wav_filename = "orchestral_mix.wav"
mp3_filename = "back.mp3"
write(wav_filename, sample_rate, np.int16(mix * 32767))
AudioSegment.from_wav(wav_filename).export(mp3_filename, format="mp3")
os.remove(wav_filename)

print(f"\n✅ 믹스 완료 → {mp3_filename}")

# === 자동 재생
play_mp3(mp3_filename)

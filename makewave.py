import numpy as np
from scipy.io.wavfile import write
import os

SAMPLE_RATE = 44100
DURATION = 0.5  # 일반적인 단일 타격 지속시간 (0.5초)

os.makedirs("samples", exist_ok=True)

def envelope(t, attack=0.01, decay=0.2):
    attack_samples = int(SAMPLE_RATE * attack)
    decay_samples = int(SAMPLE_RATE * decay)
    sustain_samples = len(t) - attack_samples - decay_samples

    env = np.concatenate([
        np.linspace(0, 1, attack_samples),
        np.ones(sustain_samples),
        np.linspace(1, 0, decay_samples)
    ])
    return env[:len(t)]

def generate_kick(filename):
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), False)
    waveform = np.sin(2 * np.pi * 60 * np.exp(-5 * t))  # pitch drop
    waveform *= envelope(t, 0.005, 0.2)
    write(filename, SAMPLE_RATE, np.int16(waveform * 32767))

def generate_snare(filename):
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), False)
    noise = np.random.randn(len(t)) * 0.4
    tone = np.sin(2 * np.pi * 180 * t) * 0.2
    waveform = (tone + noise) * envelope(t, 0.005, 0.3)
    write(filename, SAMPLE_RATE, np.int16(waveform * 32767))

def generate_hat(filename, open=False):
    t = np.linspace(0, 0.4 if open else 0.1, int(SAMPLE_RATE * (0.4 if open else 0.1)), False)
    noise = np.random.randn(len(t)) * (0.5 if open else 0.3)
    waveform = noise * envelope(t, 0.001, 0.05 if open else 0.02)
    write(filename, SAMPLE_RATE, np.int16(waveform * 32767))

def generate_rim(filename):
    t = np.linspace(0, 0.15, int(SAMPLE_RATE * 0.15), False)
    waveform = np.sin(2 * np.pi * 1800 * t) * np.exp(-20 * t)
    waveform *= envelope(t, 0.001, 0.05)
    write(filename, SAMPLE_RATE, np.int16(waveform * 32767))

def generate_bongo(filename):
    t = np.linspace(0, 0.4, int(SAMPLE_RATE * 0.4), False)
    waveform = np.sin(2 * np.pi * 200 * t) * np.exp(-10 * t)
    waveform *= envelope(t, 0.005, 0.2)
    write(filename, SAMPLE_RATE, np.int16(waveform * 32767))

def generate_shaker(filename):
    t = np.linspace(0, 0.4, int(SAMPLE_RATE * 0.4), False)
    noise = np.random.uniform(-1, 1, len(t)) * 0.3
    waveform = noise * envelope(t, 0.001, 0.1)
    write(filename, SAMPLE_RATE, np.int16(waveform * 32767))

def generate_room_ambience(filename):
    t = np.linspace(0, 2.0, int(SAMPLE_RATE * 2.0), False)
    noise = np.random.normal(0, 0.05, size=len(t))
    waveform = noise * envelope(t, 0.2, 1.0)
    write(filename, SAMPLE_RATE, np.int16(waveform * 32767))

# === 샘플 생성 매핑 ===
sample_map = {
    "kick_brush_soft": generate_kick,
    "snare_brush_swirl": generate_snare,
    "hat_brush_soft": lambda f: generate_hat(f, open=False),
    "ride_warm_clean": lambda f: generate_hat(f, open=True),
    "rim_click_wood": generate_rim,
    "shaker_soft": generate_shaker,
    "bongo_low_mid": generate_bongo,
    "room_ambience_wood": generate_room_ambience
}

# === 생성 실행 ===
for name, func in sample_map.items():
    path = f"db/samples/{name}.wav"
    func(path)
    print(f"🎵 {path} 생성됨")

print("✅ 모든 어쿠스틱 샘플 생성 완료!")

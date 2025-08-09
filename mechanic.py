import numpy as np
from scipy.io.wavfile import write
import os

sr = 44100
duration = 10.0  # 전체 길이 (초)
total_samples = int(sr * duration)
output_dir = "robot_sfx_real"
os.makedirs(output_dir, exist_ok=True)

def save_wav(signal, filename):
    signal = np.clip(signal, -1.0, 1.0)
    signal_int16 = np.int16(signal * 32767)
    write(filename, sr, signal_int16.T)
    print(f"✅ 저장 완료: {filename}")

# 🔧 개별 음향 요소 구성

def motor_grind(t):
    return 0.2 * np.sin(2 * np.pi * 180 * t) + 0.15 * np.sin(2 * np.pi * 90 * t + 0.3 * np.random.randn(len(t)))

def metal_rattle(t):
    return 0.25 * np.random.randn(len(t)) * np.exp(-1.5 * t) + 0.15 * np.sin(2 * np.pi * 600 * t) * np.exp(-3 * t)

def air_blast(t):
    return 0.2 * np.random.randn(len(t)) * np.exp(-5 * t)

def gravel_scrape(t):
    return 0.2 * np.random.rand(len(t)) * np.sin(2 * np.pi * 40 * t) * np.exp(-1.2 * t)

def weight_impact(t):
    bass = 0.5 * np.sin(2 * np.pi * 50 * t) * np.exp(-5 * t)
    ground = 0.3 * np.random.randn(len(t)) * np.exp(-3 * t)
    return bass + ground

# 🎛 Panning (stereo 변환)
def pan_stereo(y, mode="center"):
    if mode == "left":
        return np.stack([y, y * 0.2], axis=0)
    elif mode == "right":
        return np.stack([y * 0.2, y], axis=0)
    else:
        return np.stack([y, y], axis=0)

# 🎬 전체 시퀀스 생성
mix = np.zeros((2, total_samples))

# === 0 ~ 2.5초: 유압 + 모터 준비
t1 = np.linspace(0, 2.5, int(sr * 2.5), endpoint=False)
segment1 = air_blast(t1) + motor_grind(t1)
mix[:, 0:len(t1)] += pan_stereo(segment1, "left")

# === 2.5 ~ 3.0초: 발 착지 (무게감, 마찰)
t2 = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
segment2 = weight_impact(t2) + gravel_scrape(t2)
start2 = int(2.5 * sr)
mix[:, start2:start2 + len(t2)] += pan_stereo(segment2, "center")

# === 3.0 ~ 10.0초: 전신 기계 움직임
t3 = np.linspace(0, 7.0, int(sr * 7.0), endpoint=False)
segment3 = motor_grind(t3) + metal_rattle(t3)
start3 = int(3.0 * sr)
mix[:, start3:start3 + len(t3)] += pan_stereo(segment3, "right")

# 저장
save_wav(mix, os.path.join(output_dir, "robot_realistic_motion.wav"))

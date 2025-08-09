import numpy as np
import soundfile as sf
import os

SAMPLE_RATE = 44100
DURATION = 0.4  # 400ms
OUTPUT_DIR = "samples"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_wav(filename, data):
    filepath = os.path.join(OUTPUT_DIR, filename)
    sf.write(filepath, data, SAMPLE_RATE)
    print(f"✅ {filepath} 생성됨")

def sine_wave(freq, duration, amp=0.5):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.sin(2 * np.pi * freq * t)
    return np.column_stack([wave, wave]) * amp

def white_noise(duration, amp=0.3):
    noise = np.random.normal(0, 1, int(SAMPLE_RATE * duration))
    return np.column_stack([noise, noise]) * amp

def short_click(duration=0.05, amp=0.9):
    click = np.zeros(int(SAMPLE_RATE * duration))
    click[:10] = amp
    return np.column_stack([click, click])

def generate_samples():
    samples = {
        "kick_hard_808.wav": sine_wave(60, 0.4, amp=0.7) * np.exp(-np.linspace(0, 5, int(SAMPLE_RATE * DURATION)))[:, None],

        "snare_snap_crisp.wav": white_noise(0.2) * np.hanning(int(SAMPLE_RATE * 0.2))[:, None],
        "clap_layer_808.wav": white_noise(0.15) * np.hanning(int(SAMPLE_RATE * 0.15))[:, None],
        "hat_closed_digital.wav": white_noise(0.05) * np.hanning(int(SAMPLE_RATE * 0.05))[:, None],
        "perc_roll_trap.wav": sine_wave(300, 0.1) + white_noise(0.1),
        "synth_vocal_chop.wav": sine_wave(700, 0.3) * np.hanning(int(SAMPLE_RATE * 0.3))[:, None],
        "sub_bass_deep.wav": sine_wave(40, 0.5) * np.exp(-np.linspace(0, 3, int(SAMPLE_RATE * 0.5)))[:, None],
        "fx_riser_down.wav": sine_wave(np.linspace(1000, 200, int(SAMPLE_RATE * 0.6)), 0.6)
    }

    for name, data in samples.items():
        save_wav(name, data)

if __name__ == "__main__":
    generate_samples()

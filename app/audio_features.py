from __future__ import annotations

import cmath
import math
from array import array
from dataclasses import dataclass
from pathlib import Path

from pydub import AudioSegment


@dataclass(frozen=True)
class AudioFeatures:
    duration_sec: float
    rms: float
    zero_crossing_rate: float
    spectral_centroid_norm: float


def _to_mono_float(audio: AudioSegment) -> list[float]:
    mono = audio.set_channels(1)
    raw_samples = mono.get_array_of_samples()
    if not isinstance(raw_samples, array):
        raw_samples = array("h", raw_samples)

    max_val = float(1 << (8 * mono.sample_width - 1))
    if max_val <= 0:
        return [float(sample) for sample in raw_samples]

    return [float(sample) / max_val for sample in raw_samples]


def _zero_crossing_rate(samples: list[float]) -> float:
    if len(samples) < 2:
        return 0.0

    crossings = 0
    prev = samples[0] >= 0.0
    for value in samples[1:]:
        sign = value >= 0.0
        if sign != prev:
            crossings += 1
        prev = sign

    return crossings / (len(samples) - 1)


def _downsample(samples: list[float], target_size: int = 2048) -> list[float]:
    if len(samples) <= target_size:
        return samples
    step = len(samples) / target_size
    return [samples[int(i * step)] for i in range(target_size)]


def _spectral_centroid_norm(samples: list[float]) -> float:
    if len(samples) < 2:
        return 0.0

    work = _downsample(samples, target_size=2048)
    n = len(work)
    half = n // 2
    if half == 0:
        return 0.0

    magnitudes: list[float] = []
    for k in range(half + 1):
        total = 0j
        for idx, x in enumerate(work):
            angle = -2j * math.pi * k * idx / n
            total += x * cmath.exp(angle)
        magnitudes.append(abs(total))

    total_mag = sum(magnitudes)
    if total_mag == 0:
        return 0.0

    freqs = [k / n for k in range(half + 1)]
    centroid = sum(f * m for f, m in zip(freqs, magnitudes)) / total_mag
    nyquist = 0.5
    return max(0.0, min(1.0, centroid / nyquist))


def extract_audio_features(input_path: Path) -> AudioFeatures:
    audio = AudioSegment.from_file(input_path)
    samples = _to_mono_float(audio)

    duration_sec = len(audio) / 1000.0
    if samples:
        square_sum = sum(sample * sample for sample in samples)
        rms = math.sqrt(square_sum / len(samples))
    else:
        rms = 0.0

    return AudioFeatures(
        duration_sec=duration_sec,
        rms=rms,
        zero_crossing_rate=_zero_crossing_rate(samples),
        spectral_centroid_norm=_spectral_centroid_norm(samples),
    )

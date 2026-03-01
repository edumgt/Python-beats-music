from __future__ import annotations

import math
from pathlib import Path

from pydub import AudioSegment
from pydub.generators import Sine

from app.audio_features import extract_audio_features
from app.ml_profile import DEFAULT_PRESET, StylePreset


def _midi_to_frequency(midi_note: int) -> float:
    return 440.0 * (2 ** ((midi_note - 69) / 12))


def _chord_segment(root_midi: int, duration_ms: int, velocity_gain_db: float) -> AudioSegment:
    notes = [root_midi, root_midi + 7, root_midi + 12, root_midi + 16]
    chord = AudioSegment.silent(duration=duration_ms)

    for idx, note in enumerate(notes):
        freq = _midi_to_frequency(note)
        tone = (
            Sine(freq)
            .to_audio_segment(duration=duration_ms)
            .fade_in(15)
            .fade_out(int(duration_ms * 0.45))
            .apply_gain(-13 - idx + velocity_gain_db)
        )
        chord = chord.overlay(tone)

    bass = (
        Sine(_midi_to_frequency(root_midi - 12))
        .to_audio_segment(duration=duration_ms)
        .fade_in(10)
        .fade_out(int(duration_ms * 0.5))
        .apply_gain(-9 + velocity_gain_db)
    )
    return chord.overlay(bass)


def _estimate_duration_ms(audio: AudioSegment) -> int:
    return max(30_000, min(len(audio), 180_000))


def render_grand_piano_backing(
    input_path: Path,
    output_path: Path,
    dramatic_level: int = 7,
    target_bpm: int | None = None,
    style_preset: StylePreset | None = None,
) -> Path:
    """
    저작권 리스크를 낮추기 위해 원본 파형을 재사용하지 않고,
    길이/분위기만 참고한 신규 피아노 반주를 합성한다.
    """
    preset = style_preset or DEFAULT_PRESET

    src = AudioSegment.from_file(input_path)
    duration_ms = _estimate_duration_ms(src)

    features = extract_audio_features(input_path)
    inferred_bpm_bias = int((features.rms - 0.08) * 25)

    bpm = target_bpm if target_bpm else 72 + dramatic_level * 3 + preset.bpm_bias + inferred_bpm_bias
    bpm = max(50, min(180, bpm))
    beat_ms = math.floor(60_000 / bpm)

    progression = preset.progression
    arrangement = AudioSegment.silent(duration=duration_ms)

    current_ms = 0
    step = 0
    while current_ms < duration_ms:
        root_note = progression[step % len(progression)]

        local_gain = -1.5 + (dramatic_level * 0.25) + preset.dramatic_gain_bias
        if step % 8 in (6, 7):
            local_gain += 1.0

        bar = _chord_segment(root_note, beat_ms * 2, local_gain)
        arrangement = arrangement.overlay(bar, position=current_ms)

        arp_note = root_note + 24 + (step % 3) * 2
        arp = (
            Sine(_midi_to_frequency(arp_note))
            .to_audio_segment(duration=beat_ms)
            .fade_in(5)
            .fade_out(int(beat_ms * 0.65))
            .apply_gain(-18 + dramatic_level * 0.4 + preset.dramatic_gain_bias)
        )
        arrangement = arrangement.overlay(arp, position=current_ms + beat_ms)

        current_ms += beat_ms * 2
        step += 1

    normalized = arrangement.normalize(headroom=1.2).fade_out(1800)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.export(output_path, format="mp3", bitrate="192k")
    return output_path

from __future__ import annotations

import math
from pathlib import Path

from pydub import AudioSegment
from pydub.generators import Sine


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
    # 30초 ~ 180초 사이로 제한하여 과도한 출력 생성 방지
    return max(30_000, min(len(audio), 180_000))


def render_grand_piano_backing(
    input_path: Path,
    output_path: Path,
    dramatic_level: int = 7,
    target_bpm: int | None = None,
) -> Path:
    """
    저작권 리스크를 낮추기 위해 원본 파형을 재사용하지 않고,
    길이/분위기만 참고한 신규 피아노 반주를 합성한다.
    """
    src = AudioSegment.from_file(input_path)
    duration_ms = _estimate_duration_ms(src)

    bpm = target_bpm if target_bpm else 72 + dramatic_level * 3
    beat_ms = math.floor(60_000 / bpm)

    progression = [45, 48, 41, 43]  # A minor 계열(웅장한 톤)
    arrangement = AudioSegment.silent(duration=duration_ms)

    current_ms = 0
    step = 0
    while current_ms < duration_ms:
        root_note = progression[step % len(progression)]

        local_gain = -1.5 + (dramatic_level * 0.25)
        if step % 8 in (6, 7):
            local_gain += 1.0  # 프레이즈 후반 볼륨 상승

        bar = _chord_segment(root_note, beat_ms * 2, local_gain)
        arrangement = arrangement.overlay(bar, position=current_ms)

        # 고음 아르페지오 레이어 (합창 느낌의 밀도)
        arp_note = root_note + 24 + (step % 3) * 2
        arp = (
            Sine(_midi_to_frequency(arp_note))
            .to_audio_segment(duration=beat_ms)
            .fade_in(5)
            .fade_out(int(beat_ms * 0.65))
            .apply_gain(-18 + dramatic_level * 0.4)
        )
        arrangement = arrangement.overlay(arp, position=current_ms + beat_ms)

        current_ms += beat_ms * 2
        step += 1

    # 마스터 느낌의 간단한 레벨링
    normalized = arrangement.normalize(headroom=1.2).fade_out(1800)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.export(output_path, format="mp3", bitrate="192k")
    return output_path

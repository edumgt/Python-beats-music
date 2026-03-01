from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.audio_features import AudioFeatures


@dataclass(frozen=True)
class StylePreset:
    name: str
    progression: list[int]
    dramatic_gain_bias: float
    bpm_bias: int


DEFAULT_PRESET = StylePreset(
    name="default",
    progression=[45, 48, 41, 43],
    dramatic_gain_bias=0.0,
    bpm_bias=0,
)


class StyleProfile:
    def __init__(self, presets: dict[str, StylePreset], centroids: dict[str, list[float]]) -> None:
        self.presets = presets
        self.centroids = centroids

    @classmethod
    def from_json_path(cls, profile_path: Path) -> "StyleProfile | None":
        if not profile_path.exists():
            return None

        payload = json.loads(profile_path.read_text(encoding="utf-8"))
        presets = {
            key: StylePreset(
                name=key,
                progression=value.get("progression", DEFAULT_PRESET.progression),
                dramatic_gain_bias=float(value.get("dramatic_gain_bias", 0.0)),
                bpm_bias=int(value.get("bpm_bias", 0)),
            )
            for key, value in payload.get("presets", {}).items()
        }

        centroids = {
            key: [float(v) for v in values]
            for key, values in payload.get("feature_centroids", {}).items()
        }

        return cls(presets=presets, centroids=centroids)

    def resolve_preset(self, features: AudioFeatures) -> StylePreset:
        if not self.presets or not self.centroids:
            return DEFAULT_PRESET

        vector = [
            features.duration_sec,
            features.rms,
            features.zero_crossing_rate,
            features.spectral_centroid_norm,
        ]

        label = min(
            self.centroids,
            key=lambda k: sum((a - b) ** 2 for a, b in zip(vector, self.centroids[k])),
        )
        return self.presets.get(label, DEFAULT_PRESET)

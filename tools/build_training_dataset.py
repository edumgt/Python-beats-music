from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.audio_features import extract_audio_features


def build_dataset(labeled_root: Path, output_csv: Path) -> None:
    rows: list[dict[str, str | float]] = []

    for label_dir in sorted([d for d in labeled_root.iterdir() if d.is_dir()]):
        label = label_dir.name
        for audio_file in sorted(label_dir.glob("*.mp3")):
            features = extract_audio_features(audio_file)
            rows.append(
                {
                    "path": str(audio_file),
                    "label": label,
                    "duration_sec": round(features.duration_sec, 4),
                    "rms": round(features.rms, 6),
                    "zero_crossing_rate": round(features.zero_crossing_rate, 6),
                    "spectral_centroid_norm": round(features.spectral_centroid_norm, 6),
                }
            )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "path",
                "label",
                "duration_sec",
                "rms",
                "zero_crossing_rate",
                "spectral_centroid_norm",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"saved {len(rows)} rows to {output_csv}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build labeled training CSV from MP3 directories")
    parser.add_argument("--labeled-root", type=Path, required=True, help="Directory with label subfolders")
    parser.add_argument("--output-csv", type=Path, required=True, help="Path to output CSV")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_dataset(args.labeled_root, args.output_csv)

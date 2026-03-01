from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

FEATURE_COLUMNS = [
    "duration_sec",
    "rms",
    "zero_crossing_rate",
    "spectral_centroid_norm",
]

PRESET_MAP = {
    "cinematic": {"progression": [45, 48, 41, 43], "dramatic_gain_bias": 1.2, "bpm_bias": -6},
    "dance": {"progression": [50, 55, 52, 57], "dramatic_gain_bias": 0.4, "bpm_bias": 12},
    "lofi": {"progression": [45, 40, 43, 38], "dramatic_gain_bias": -0.8, "bpm_bias": -10},
}


def load_dataset(dataset_csv: Path) -> tuple[np.ndarray, np.ndarray]:
    rows: list[list[float]] = []
    labels: list[str] = []

    with dataset_csv.open("r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            rows.append([float(row[col]) for col in FEATURE_COLUMNS])
            labels.append(row["label"])

    if not rows:
        raise ValueError("dataset is empty")

    return np.array(rows, dtype=np.float32), np.array(labels)


def compute_centroids(features: np.ndarray, labels: np.ndarray) -> dict[str, list[float]]:
    grouped: dict[str, list[np.ndarray]] = defaultdict(list)
    for fvec, label in zip(features, labels):
        grouped[str(label)].append(fvec)

    return {
        label: np.mean(np.stack(vectors, axis=0), axis=0).round(6).tolist()
        for label, vectors in grouped.items()
    }


def make_profile_payload(centroids: dict[str, list[float]]) -> dict[str, object]:
    presets = {}
    for label in centroids:
        presets[label] = PRESET_MAP.get(
            label,
            {"progression": [45, 48, 41, 43], "dramatic_gain_bias": 0.0, "bpm_bias": 0},
        )

    return {
        "feature_columns": FEATURE_COLUMNS,
        "feature_centroids": centroids,
        "presets": presets,
    }


def train(dataset_csv: Path, model_out: Path, profile_out: Path) -> None:
    features, labels = load_dataset(dataset_csv)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", SVC(kernel="rbf", probability=True, class_weight="balanced")),
        ]
    )
    pipeline.fit(x_train, y_train)

    pred = pipeline.predict(x_test)
    print(classification_report(y_test, pred))

    model_out.parent.mkdir(parents=True, exist_ok=True)
    profile_out.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, model_out)

    centroids = compute_centroids(features, labels)
    profile = make_profile_payload(centroids)
    profile_out.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"model saved: {model_out}")
    print(f"profile saved: {profile_out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train style classifier and export runtime profile")
    parser.add_argument("--dataset-csv", type=Path, required=True)
    parser.add_argument("--model-out", type=Path, default=Path("/data/models/style_classifier.joblib"))
    parser.add_argument("--profile-out", type=Path, default=Path("/data/models/style_profile.json"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args.dataset_csv, args.model_out, args.profile_out)

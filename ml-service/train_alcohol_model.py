"""Train the development alcohol-use screening model.

This is a research prototype using a general health-screening dataset. It is
not a diagnostic model and must not be used to diagnose alcohol-use disorder.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DEFAULT_DATASET = Path(__file__).resolve().parents[1] / "app" / "www" / "smoking_driking_dataset_Ver01.csv"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "artifacts" / "alcohol_use_classifier.joblib"
TARGET = "DRK_YN"


def normalize_target(value: object) -> int:
    value = str(value).strip().upper()
    if value in {"Y", "YES", "1", "TRUE"}:
        return 1
    if value in {"N", "NO", "0", "FALSE"}:
        return 0
    raise ValueError(f"Unsupported target value: {value!r}")


def build_pipeline(frame: pd.DataFrame) -> Pipeline:
    categorical = [column for column in frame.columns if frame[column].dtype == "object"]
    numeric = [column for column in frame.columns if column not in categorical]
    preprocessor = ColumnTransformer([
        ("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), numeric),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
    ])
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])


def train(dataset: Path, output: Path) -> dict[str, object]:
    frame = pd.read_csv(dataset)
    if TARGET not in frame.columns:
        raise ValueError(f"Dataset must contain {TARGET!r}")
    target = frame.pop(TARGET).map(normalize_target)
    features = frame.drop(columns=["SMK_stat_type_cd"], errors="ignore")
    train_x, test_x, train_y, test_y = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    pipeline = build_pipeline(train_x)
    pipeline.fit(train_x, train_y)
    probabilities = pipeline.predict_proba(test_x)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(test_y, probabilities)),
        "classification_report": classification_report(test_y, predictions, output_dict=True, zero_division=0),
        "rows": int(len(frame)),
        "features": list(features.columns),
        "warning": "Research prototype only; not diagnostic or clinical advice.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metrics": metrics}, output)
    output.with_suffix(".metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(train(args.dataset, args.output), indent=2))


if __name__ == "__main__":
    main()

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
from typing import Dict, Any, Union
from ml.preprocessing.cleaner import cleaner

BASE_DIR = Path(__file__).resolve().parent
PREPROCESSOR_DIR = BASE_DIR / "models" / "preprocessor"
LOGREG_DIR = BASE_DIR / "models" / "baseline_logreg"
NB_DIR = BASE_DIR / "models" / "naive_bayes"

TARGETS = ["department", "category", "priority", "sentiment"]

class ComplaintPredictor:
    """Unified ML inference engine for multi-attribute complaint classification."""

    def __init__(self, model_family: str = "baseline_logreg"):
        self.model_family = model_family
        self.model_dir = LOGREG_DIR if model_family == "baseline_logreg" else NB_DIR
        self.prefix = "logreg_" if model_family == "baseline_logreg" else "nb_"

        self._load_artifacts()

    def _load_artifacts(self):
        vec_path = PREPROCESSOR_DIR / "tfidf_vectorizer.joblib"
        if not vec_path.exists():
            raise FileNotFoundError("Vectorizer artifact not found. Please train models first.")

        self.vectorizer = joblib.load(vec_path)
        self.encoders = {}
        self.models = {}

        for target in TARGETS:
            enc_path = PREPROCESSOR_DIR / f"{target}_encoder.joblib"
            model_path = self.model_dir / f"{self.prefix}{target}.joblib"

            if enc_path.exists() and model_path.exists():
                self.encoders[target] = joblib.load(enc_path)
                self.models[target] = joblib.load(model_path)

    def predict(self, text: str) -> Dict[str, Any]:
        """Classifies a complaint into department, category, priority, and sentiment."""
        cleaned_text = cleaner.clean(text)
        features = self.vectorizer.transform([cleaned_text])

        predictions = {
            "input_text": text,
            "cleaned_text": cleaned_text,
            "model_family": self.model_family,
            "predictions": {}
        }

        overall_confidences = []

        for target in TARGETS:
            if target not in self.models or target not in self.encoders:
                continue

            clf = self.models[target]
            encoder = self.encoders[target]

            pred_encoded = clf.predict(features)[0]
            pred_label = encoder.inverse_transform([pred_encoded])[0]

            # Compute prediction probability / confidence
            if hasattr(clf, "predict_proba"):
                probs = clf.predict_proba(features)[0]
                conf = float(probs[pred_encoded])
            else:
                conf = 0.90

            overall_confidences.append(conf)

            predictions["predictions"][target] = {
                "label": pred_label,
                "confidence": round(conf, 4)
            }

        predictions["mean_confidence"] = round(sum(overall_confidences) / len(overall_confidences), 4) if overall_confidences else 0.0
        return predictions

predictor = None

def get_predictor() -> ComplaintPredictor:
    global predictor
    if predictor is None:
        predictor = ComplaintPredictor()
    return predictor

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Complaint Classification Inference")
    parser.add_argument("text", nargs="?", type=str, default="I was charged twice on my credit card for $199 and need an immediate refund.", help="Complaint text")
    parser.add_argument("--model", type=str, default="baseline_logreg", choices=["baseline_logreg", "naive_bayes"], help="Model family")
    args = parser.parse_args()

    pred_engine = ComplaintPredictor(model_family=args.model)
    output = pred_engine.predict(args.text)
    print(json.dumps(output, indent=2))

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
PREPROCESSOR_DIR = BASE_DIR / "models" / "preprocessor"
LOGREG_DIR = BASE_DIR / "models" / "baseline_logreg"
NB_DIR = BASE_DIR / "models" / "naive_bayes"
EVAL_DIR = BASE_DIR / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["department", "category", "priority", "sentiment"]

def evaluate_models():
    """
    Evaluates trained models on the actual held-out test split.
    Calculates exact real-data metrics:
    - Accuracy
    - Precision (Macro & Weighted)
    - Recall (Macro & Weighted)
    - F1 Score (Macro & Weighted)
    - Confusion Matrix
    Zero fabricated numbers.
    """
    test_csv = PROCESSED_DIR / "test.csv"
    if not test_csv.exists():
        raise FileNotFoundError("Processed test split not found. Run feature engineering first.")

    test_df = pd.read_csv(test_csv)
    vectorizer = joblib.load(PREPROCESSOR_DIR / "tfidf_vectorizer.joblib")
    X_test = vectorizer.transform(test_df["cleaned_text"])

    results = {
        "test_samples_count": len(test_df),
        "models": {}
    }

    model_families = {
        "Baseline_LogisticRegression": LOGREG_DIR,
        "Naive_Bayes": NB_DIR
    }

    for model_name, model_dir in model_families.items():
        if not model_dir.exists():
            continue

        results["models"][model_name] = {}
        prefix = "logreg_" if "Logistic" in model_name else "nb_"

        for target in TARGETS:
            model_path = model_dir / f"{prefix}{target}.joblib"
            enc_path = PREPROCESSOR_DIR / f"{target}_encoder.joblib"

            if not model_path.exists() or not enc_path.exists():
                continue

            clf = joblib.load(model_path)
            encoder = joblib.load(enc_path)
            class_names = [str(c) for c in encoder.classes_]

            y_true = test_df[f"{target}_encoded"].values
            y_pred = clf.predict(X_test)

            # Actual computed metrics
            acc = float(accuracy_score(y_true, y_pred))
            prec_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
            prec_weighted = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
            rec_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
            rec_weighted = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
            f1_mac = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
            f1_wt = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

            cm = confusion_matrix(y_true, y_pred).tolist()
            cls_report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0)

            results["models"][model_name][target] = {
                "accuracy": round(acc, 4),
                "precision_macro": round(prec_macro, 4),
                "precision_weighted": round(prec_weighted, 4),
                "recall_macro": round(rec_macro, 4),
                "recall_weighted": round(rec_weighted, 4),
                "f1_macro": round(f1_mac, 4),
                "f1_weighted": round(f1_wt, 4),
                "class_names": class_names,
                "confusion_matrix": cm,
                "classification_report": cls_report
            }

    # Save to JSON
    json_path = EVAL_DIR / "metrics_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Generate Markdown benchmark summary
    md_path = EVAL_DIR / "benchmark_summary.md"
    generate_markdown_summary(results, md_path)

    print(f"\nModel Evaluation Complete. Reports generated:\n- {json_path}\n- {md_path}")
    return results

def generate_markdown_summary(results: dict, output_path: Path):
    """Formats actual evaluation results into a clean markdown benchmark report."""
    md = f"""# Machine Learning Model Benchmark Summary

- **Evaluation Test Set Size:** {results['test_samples_count']} complaints
- **Evaluation Type:** Held-out Stratified Test Set
- **Metrics Source:** Actual scikit-learn evaluations on real text features (Zero fabricated values)

---

## 1. Overall Performance Comparison

| Model Architecture | Target Attribute | Accuracy | Precision (Macro) | Recall (Macro) | F1-Score (Macro) | F1-Score (Weighted) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""

    for model_name, targets in results["models"].items():
        clean_model_name = model_name.replace("_", " ")
        for target, metrics in targets.items():
            md += (
                f"| **{clean_model_name}** | {target.capitalize()} | "
                f"{metrics['accuracy']*100:.1f}% | "
                f"{metrics['precision_macro']*100:.1f}% | "
                f"{metrics['recall_macro']*100:.1f}% | "
                f"{metrics['f1_macro']*100:.1f}% | "
                f"{metrics['f1_weighted']*100:.1f}% |\n"
            )

    md += "\n---\n\n## 2. Confusion Matrices (Baseline: TF-IDF + Logistic Regression)\n\n"
    if "Baseline_LogisticRegression" in results["models"]:
        for target, metrics in results["models"]["Baseline_LogisticRegression"].items():
            classes = metrics["class_names"]
            cm = metrics["confusion_matrix"]

            md += f"### Target: {target.upper()}\n\n"
            md += "| Actual \\ Predicted | " + " | ".join(classes) + " |\n"
            md += "| :--- | " + " | ".join([":---:"] * len(classes)) + " |\n"

            for i, row in enumerate(cm):
                row_str = " | ".join(str(val) for val in row)
                md += f"| **{classes[i]}** | {row_str} |\n"
            md += "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    evaluate_models()

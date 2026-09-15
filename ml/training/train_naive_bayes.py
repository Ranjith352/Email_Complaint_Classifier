import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, f1_score

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
PREPROCESSOR_DIR = BASE_DIR / "models" / "preprocessor"
OUTPUT_MODEL_DIR = BASE_DIR / "models" / "naive_bayes"
OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["department", "category", "priority", "sentiment"]

def train_naive_bayes():
    """Trains TF-IDF + Multinomial Naive Bayes classifiers across all targets."""
    train_csv = PROCESSED_DIR / "train.csv"
    test_csv = PROCESSED_DIR / "test.csv"
    vectorizer_path = PREPROCESSOR_DIR / "tfidf_vectorizer.joblib"

    if not train_csv.exists() or not vectorizer_path.exists():
        from ml.preprocessing.feature_engineering import FeatureEngineer
        fe = FeatureEngineer()
        train_df, test_df = fe.prepare_dataset()
    else:
        train_df = pd.read_csv(train_csv)
        test_df = pd.read_csv(test_csv)

    vectorizer = joblib.load(PREPROCESSOR_DIR / "tfidf_vectorizer.joblib")

    X_train = vectorizer.transform(train_df["cleaned_text"])
    X_test = vectorizer.transform(test_df["cleaned_text"])

    trained_models = {}
    print("\n=======================================================")
    print("Training Naive Bayes Models: TF-IDF + MultinomialNB")
    print("=======================================================")

    for target in TARGETS:
        y_train = train_df[f"{target}_encoded"]
        y_test = test_df[f"{target}_encoded"]

        clf = MultinomialNB(alpha=0.1)
        clf.fit(X_train, y_train)

        # Quick validation
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

        print(f"Target [{target.upper()}]: Test Accuracy = {acc*100:.2f}%, Macro F1 = {f1_macro*100:.2f}%")

        # Save model artifact
        save_path = OUTPUT_MODEL_DIR / f"nb_{target}.joblib"
        joblib.dump(clf, save_path)
        trained_models[target] = clf

    print(f"\nNaive Bayes models saved to: {OUTPUT_MODEL_DIR}")
    return trained_models

if __name__ == "__main__":
    train_naive_bayes()

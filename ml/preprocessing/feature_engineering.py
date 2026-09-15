import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from ml.preprocessing.cleaner import cleaner

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "datasets" / "raw" / "complaints_raw.csv"
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
MODELS_DIR = BASE_DIR / "models" / "preprocessor"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["department", "category", "priority", "sentiment"]

class FeatureEngineer:
    """Manages text preprocessing, vectorization, label encoding, and dataset splitting."""

    def __init__(self, max_features: int = 5000, ngram_range=(1, 2)):
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True,
            min_df=2,
            strip_accents="unicode"
        )
        self.label_encoders = {t: LabelEncoder() for t in TARGETS}

    def prepare_dataset(self, csv_path: Path = RAW_CSV, test_size: float = 0.20, random_state: int = 42):
        if not csv_path.exists():
            from ml.datasets.dataset_generator import generate_dataset
            csv_path = generate_dataset()

        df = pd.read_csv(csv_path)

        # 1. Clean complaint text
        print("Cleaning text with ComplaintCleaner...")
        df["cleaned_text"] = cleaner.clean_batch(df["complaint_text"].tolist())

        # 2. Encode categorical target variables
        for target in TARGETS:
            self.label_encoders[target].fit(df[target].astype(str))
            df[f"{target}_encoded"] = self.label_encoders[target].transform(df[target].astype(str))

        # 3. Stratified Train/Test Split (stratify on department)
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df["department"]
        )

        train_path = PROCESSED_DIR / "train.csv"
        test_path = PROCESSED_DIR / "test.csv"
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)

        # 4. Fit TF-IDF on training text only
        print("Fitting TF-IDF Vectorizer on training data...")
        self.vectorizer.fit(train_df["cleaned_text"].tolist())

        # 5. Persist artifacts
        joblib.dump(self.vectorizer, MODELS_DIR / "tfidf_vectorizer.joblib")
        for target, enc in self.label_encoders.items():
            joblib.dump(enc, MODELS_DIR / f"{target}_encoder.joblib")

        print(f"Dataset prepared successfully:")
        print(f"  Training split: {len(train_df)} samples -> {train_path}")
        print(f"  Testing split:  {len(test_df)} samples -> {test_path}")
        print(f"  Vocabulary size: {len(self.vectorizer.vocabulary_)} features")
        return train_df, test_df

    def transform_features(self, texts: list):
        """Cleans and vectorizes text inputs."""
        cleaned = cleaner.clean_batch(texts)
        return self.vectorizer.transform(cleaned)

if __name__ == "__main__":
    fe = FeatureEngineer()
    fe.prepare_dataset()

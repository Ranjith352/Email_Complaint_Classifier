import os
import json
import csv
from pathlib import Path
from collections import Counter
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "datasets" / "raw" / "complaints_raw.csv"
EVAL_DIR = BASE_DIR / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)
EDA_JSON = EVAL_DIR / "eda_summary.json"
EDA_MD = EVAL_DIR / "eda_report.md"

def run_eda(csv_path: Path = RAW_CSV) -> dict:
    """Executes thorough exploratory data analysis on complaint text and targets."""
    if not csv_path.exists():
        from ml.datasets.dataset_generator import generate_dataset
        csv_path = generate_dataset()

    df = pd.read_csv(csv_path)

    total_rows = len(df)
    missing_counts = df.isnull().sum().to_dict()
    unique_texts = df["complaint_text"].nunique()

    # Calculate text length stats
    char_lengths = df["complaint_text"].astype(str).apply(len)
    word_lengths = df["complaint_text"].astype(str).apply(lambda s: len(s.split()))

    text_stats = {
        "char_length": {
            "mean": round(float(char_lengths.mean()), 2),
            "median": float(char_lengths.median()),
            "std": round(float(char_lengths.std()), 2),
            "min": int(char_lengths.min()),
            "max": int(char_lengths.max()),
            "p95": round(float(np.percentile(char_lengths, 95)), 2)
        },
        "word_count": {
            "mean": round(float(word_lengths.mean()), 2),
            "median": float(word_lengths.median()),
            "std": round(float(word_lengths.std()), 2),
            "min": int(word_lengths.min()),
            "max": int(word_lengths.max()),
            "p95": round(float(np.percentile(word_lengths, 95)), 2)
        }
    }

    # Distributions
    dept_distribution = df["department"].value_counts().to_dict()
    category_distribution = df["category"].value_counts().to_dict()
    priority_distribution = df["priority"].value_counts().to_dict()
    sentiment_distribution = df["sentiment"].value_counts().to_dict()

    # Vocabulary & Top Words
    words = []
    for text in df["complaint_text"].astype(str):
        words.extend(text.lower().split())
    vocab_size = len(set(words))
    top_words = Counter(w.strip(".,!?:;\"'()") for w in words if len(w) > 3).most_common(20)

    summary = {
        "dataset": {
            "total_samples": total_rows,
            "unique_complaints": unique_texts,
            "missing_values": missing_counts
        },
        "text_statistics": text_stats,
        "vocabulary_size": vocab_size,
        "top_keywords": dict(top_words),
        "target_distributions": {
            "department": dept_distribution,
            "category": category_distribution,
            "priority": priority_distribution,
            "sentiment": sentiment_distribution
        }
    }

    # Save to JSON
    with open(EDA_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Save formatted Markdown report
    md_report = f"""# Exploratory Data Analysis (EDA) Report

## 1. Dataset Overview
- **Total Records:** {total_rows}
- **Unique Texts:** {unique_texts}
- **Missing Attributes:** {sum(missing_counts.values())}

## 2. Text Dimensions
- **Average Word Count:** {text_stats['word_count']['mean']} words (Median: {text_stats['word_count']['median']})
- **95th Percentile Word Count:** {text_stats['word_count']['p95']} words
- **Average Character Length:** {text_stats['char_length']['mean']} chars
- **Unique Vocabulary:** {vocab_size} tokens

## 3. Department Class Distribution
| Department | Samples | Proportion |
| :--- | :---: | :---: |
"""
    for d, c in dept_distribution.items():
        md_report += f"| {d} | {c} | {round(c/total_rows*100, 1)}% |\n"

    md_report += "\n## 4. Priority Tier Distribution\n| Priority | Samples | Proportion |\n| :--- | :---: | :---: |\n"
    for p, c in priority_distribution.items():
        md_report += f"| {p} | {c} | {round(c/total_rows*100, 1)}% |\n"

    md_report += "\n## 5. Sentiment Distribution\n| Sentiment | Samples | Proportion |\n| :--- | :---: | :---: |\n"
    for s, c in sentiment_distribution.items():
        md_report += f"| {s} | {c} | {round(c/total_rows*100, 1)}% |\n"

    with open(EDA_MD, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"EDA successfully completed. Outputs saved:\n- {EDA_JSON}\n- {EDA_MD}")
    return summary

if __name__ == "__main__":
    run_eda()

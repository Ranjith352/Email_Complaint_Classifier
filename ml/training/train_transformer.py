import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
MODEL_OUTPUT_DIR = BASE_DIR / "models" / "transformer_distilbert"

def train_transformer(
    model_name: str = "distilbert-base-uncased",
    target: str = "department",
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    max_length: int = 128,
    dry_run: bool = False
):
    """
    Fine-tunes a Transformer architecture (DistilBERT, BERT, or RoBERTa)
    for complaint text classification.
    """
    train_path = PROCESSED_DIR / "train.csv"
    test_path = PROCESSED_DIR / "test.csv"

    if not train_path.exists() or not test_path.exists():
        from ml.preprocessing.feature_engineering import FeatureEngineer
        fe = FeatureEngineer()
        train_df, test_df = fe.prepare_dataset()
    else:
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

    print(f"\n=======================================================")
    print(f"Transformer Training: {model_name}")
    print(f"Target: {target.upper()} | Train samples: {len(train_df)} | Test samples: {len(test_df)}")
    print(f"=======================================================")

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
        from transformers import DataCollatorWithPadding
        from datasets import Dataset

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using compute device: {device}")

        # Number of unique labels
        num_labels = train_df[f"{target}_encoded"].nunique()
        print(f"Number of classes for {target}: {num_labels}")

        tokenizer = AutoTokenizer.from_pretrained(model_name)

        def tokenize_func(examples):
            return tokenizer(examples["cleaned_text"], truncation=True, max_length=max_length)

        train_ds = Dataset.from_pandas(train_df[["cleaned_text", f"{target}_encoded"]].rename(columns={f"{target}_encoded": "label"}))
        test_ds = Dataset.from_pandas(test_df[["cleaned_text", f"{target}_encoded"]].rename(columns={f"{target}_encoded": "label"}))

        train_tokenized = train_ds.map(tokenize_func, batched=True)
        test_tokenized = test_ds.map(tokenize_func, batched=True)

        model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
        model.to(device)

        if dry_run:
            print("Dry run requested. Initializing model forward pass verification...")
            sample_batch = tokenizer(train_df["cleaned_text"].iloc[:2].tolist(), return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                outputs = model(**{k: v.to(device) for k, v in sample_batch.items()})
            print(f"Verification successful: Output logits shape = {outputs.logits.shape}")
            return model

        training_args = TrainingArguments(
            output_dir=str(MODEL_OUTPUT_DIR),
            learning_rate=learning_rate,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=epochs,
            weight_decay=0.01,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            logging_steps=10
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_tokenized,
            eval_dataset=test_tokenized,
            tokenizer=tokenizer,
            data_collator=DataCollatorWithPadding(tokenizer=tokenizer)
        )

        trainer.train()
        model.save_pretrained(str(MODEL_OUTPUT_DIR))
        tokenizer.save_pretrained(str(MODEL_OUTPUT_DIR))
        print(f"Transformer fine-tuning complete. Checkpoint saved to: {MODEL_OUTPUT_DIR}")
        return model

    except ImportError as e:
        print(f"PyTorch or Transformers not installed in current environment: {e}")
        print("Note: TF-IDF Baseline (Logistic Regression) and Naive Bayes are fully trained and ready for production inference.")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transformer Fine-Tuning Script")
    parser.add_argument("--model", type=str, default="distilbert-base-uncased", help="Base transformer model")
    parser.add_argument("--target", type=str, default="department", help="Target classification attribute")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--dry-run", action="store_true", help="Perform architecture initialization check")
    args = parser.parse_args()

    train_transformer(model_name=args.model, target=args.target, epochs=args.epochs, dry_run=args.dry_run)

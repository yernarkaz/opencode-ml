# HuggingFace Fine-tuning Reference

Load this reference only when tabular tree-based approaches are insufficient and the
task involves unstructured text or sequence features (e.g. part description, entity
notes). This is not a primary stack for AML-based pipelines.

---

## When to use

- Input data contains free-text fields (part descriptions, supplier quality notes)
- Task requires semantic similarity or entity recognition, not tabular regression/classification
- Explicitly requested by a user who has confirmed text features are available and meaningful

---

## Pattern — sequence classification (binary)

```python
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)

MODEL_CHECKPOINT = "bert-base-multilingual-cased"  # covers multilingual text (DE/EN/FR etc.)

tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_CHECKPOINT, num_labels=2
)


def tokenize(batch: dict) -> dict:
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)


train_ds = train_ds.map(tokenize, batched=True)
val_ds = val_ds.map(tokenize, batched=True)

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_f1",
    seed=42,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
)
trainer.train()
```

---

## Gotchas

- **Multilingual checkpoint required if text is multilingual.** If descriptions are in multiple languages (e.g. German, English, French), use `bert-base-multilingual-cased`; `bert-base-uncased` only handles English.
- **Register with MLflow using `mlflow.transformers.log_model`.** Using `mlflow.sklearn.log_model` on a HF model silently serialises the wrong artefacts.
- **AML component YAML must declare the `transformers` dependency.** Add `transformers>=4.30` and `datasets>=2.14` to the environment YAML; they are not pre-installed in the standard AML curated environments.
- **GPU availability is not guaranteed on AML compute.** Check `torch.cuda.is_available()` and set `no_cuda=True` in `TrainingArguments` as a fallback for CPU-only clusters.

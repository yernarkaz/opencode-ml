# PySpark ML Reference

Load this reference only when data volume exceeds single-machine memory or when
the task explicitly requires Databricks compute (e.g. processing the full historical
data extracted from a DWH). This is not a primary stack for AML-based pipelines.

---

## When to use

- Dataset size exceeds ~50 GB (beyond pandas/single-machine capacity)
- Compute environment is Azure Databricks
- Task involves distributed feature engineering over raw DWH tables, not model training

---

## Pattern — GBT classification pipeline

```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator

# Encode categoricals
indexers = [
    StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
    for c in cat_cols
]

assembler = VectorAssembler(
    inputCols=[f"{c}_idx" for c in cat_cols] + num_cols,
    outputCol="features",
)

gbt = GBTClassifier(
    labelCol="label",
    featuresCol="features",
    maxIter=100,
    seed=42,
)

pipeline = Pipeline(stages=indexers + [assembler, gbt])
model = pipeline.fit(train_df)
predictions = model.transform(test_df)

evaluator = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
auc = evaluator.evaluate(predictions)
print(f"Test AUC: {auc:.4f}")
```

---

## Gotchas

- **`StringIndexer(handleInvalid="keep")` is required.** Without it, unseen categorical values at inference time raise a runtime error instead of mapping to an unknown bucket.
- **`VectorAssembler` cannot handle null values.** Run `.fillna()` or use `Imputer` stage before the assembler, otherwise `VectorAssembler` will fail silently or raise `SparkException`.
- **Spark MLlib `GBTClassifier` does not support early stopping.** Set `maxIter` conservatively; there is no equivalent to LightGBM's `early_stopping` callback.
- **Model serialisation uses `model.save(path)`, not MLflow's sklearn flavour.** Use `mlflow.spark.log_model(model, "spark-model")` to log correctly.
- **Databricks `spark` session is pre-created.** Do not call `SparkSession.builder.getOrCreate()` inside a Databricks notebook cell — use the pre-bound `spark` variable.

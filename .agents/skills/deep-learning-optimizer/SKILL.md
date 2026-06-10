---
name: deep-learning-optimizer
description: >
  Use this skill when training, optimizing, or tuning deep learning models (PyTorch/TensorFlow) on Azure ML.
  Trigger on: "deep learning", "neural network", "PyTorch", "TensorFlow", "GPU training", "distributed training",
  "architecture search", "hyperparameter tuning DL", or any mention of neural network models.
  Do NOT use for tree-based models (use ml-model-development).
compatibility: opencode
metadata:
  stage: model-development
  repos: <your-repo-name>
---

# Deep Learning Optimizer Skill

## When to load this skill

Load when the task involves: training neural networks on Azure ML, optimizing deep learning architectures, hyperparameter tuning for PyTorch/TensorFlow models, distributed training setup, GPU compute configuration, or converting a tree-based pipeline to a deep learning approach.

---

## Workflow

### Step 1 — Architecture selection

**Always compare against a tree-based baseline first.** LightGBM/CatBoost are faster to train, require less data, and often match or exceed DL performance on tabular data. Only proceed with DL if:

- The data has sequential/structural patterns (time-series, text, images, graphs) that tree models cannot capture
- You have sufficient data volume (>100K rows for tabular DL, more for image/text)
- The tree-based baseline has plateaued and you have evidence that non-linear representations would help

**Model type selection:**

| Data type | Recommended architecture |
|---|---|
| Tabular (structured) | MLP with residual connections, TabNet |
| Time-series | LSTM/GRU, Temporal Convolutional Network (TCN) |
| Text | Transformer encoder (BERT-style), 1D CNN |
| Image | ResNet, EfficientNet, Vision Transformer |
| Sequential (variable-length) | Transformer with positional encoding |

**Minimal MLP for tabular data:**
```python
import torch
import torch.nn as nn

class TabularMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list[int] | None = None,
                 dropout: float = 0.3, residual: bool = True):
        super().__init__()
        hidden_dims = hidden_dims or [256, 128, 64]
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.LayerNorm(h_dim))
            layers.append(nn.GELU())
            layers.append(nn.Dropout(dropout))
            if residual and prev_dim == h_dim:
                layers.append(ResidualConnection(prev_dim))  # custom wrapper
            prev_dim = h_dim
        self.backbone = nn.Sequential(*layers)
        self.head = nn.Linear(prev_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x)).squeeze(-1)
```

### Step 2 — Training setup on Azure ML

**GPU compute requirements:**
- Single GPU: `STANDARD_NC6` (1x K80) for prototyping
- Production: `STANDARD_NC24s_v3` (1x V100) or `STANDARD_NC4as_T4_v3` (1x T4)
- Multi-GPU DDP: `STANDARD_NC24s_v3` x 2+ with `--distributed` flag

**AML script parameter pattern:**
```python
# train_dl_model.py — argument parsing (matches AML component YAML)
from utils.arg_parsing import str_to_bool

parser = argparse.ArgumentParser()
parser.add_argument("--model_type", type=str, default="mlp")
parser.add_argument("--hidden_dims", type=str, default="256,128,64")
parser.add_argument("--learning_rate", type=float, default=1e-3)
parser.add_argument("--batch_size", type=int, default=1024)
parser.add_argument("--num_epochs", type=int, default=100)
parser.add_argument("--dropout", type=float, default=0.3)
parser.add_argument("--weight_decay", type=float, default=1e-4)
parser.add_argument("--early_stopping_patience", type=int, default=10)
parser.add_argument("--local_compute", type=str_to_bool, default=False)
parser.add_argument("--use_gpu", type=str_to_bool, default=True)
# ... AML workspace args ...
```

**Distributed training with DDP:**
```python
# In AML command, set instance count > 1 and use:
# torchrun --nproc_per_node=$AZUREML_PROCESS_COUNT_PER_INSTANCE \
#          --nnodes=$AZUREML_TRAIING_NODE_COUNT \
#          train_dl_model.py ...
```

**Device selection:**
```python
device = torch.device("cuda" if torch.cuda.is_available() and args.use_gpu else "cpu")
logger.info(f"Training on device: {device}")
```

### Step 3 — Hyperparameter optimization with Optuna

**Search space for DL models:**
```python
def objective(trial: optuna.trial.Trial) -> float:
    lr = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
    batch_size = trial.suggest_categorical("batch_size", [256, 512, 1024, 2048])
    dropout = trial.suggest_float("dropout", 0.1, 0.5)
    weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True)
    hidden_dims = [
        trial.suggest_int(f"hidden_dim_{i}", 32, 512, step=32)
        for i in range(trial.suggest_int("n_layers", 2, 5))
    ]

    model = TabularMLP(input_dim=X_train.shape[1],
                       hidden_dims=hidden_dims,
                       dropout=dropout).to(device)

    # Train with early stopping
    trainer = DLTrainer(model, lr, batch_size, weight_decay,
                        patience=args.early_stopping_patience)
    val_metric = trainer.fit(X_train, y_train, X_val, y_val,
                             max_epochs=args.num_epochs)
    return val_metric  # lower is better (e.g., RMSE)
```

**Optuna study configuration:**
```python
study = optuna.create_study(
    direction="minimize",
    sampler=optuna.samplers.TPESampler(seed=42),
    pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_min_n_trials=3),
)
study.optimize(objective, n_trials=50, timeout=7200)  # 2-hour budget
```

### Step 4 — Regularization and overfitting prevention

**Techniques to apply (in order of priority):**

1. **Early stopping** — monitor validation loss, patience 5-15 epochs
2. **Dropout** — 0.1-0.5 on hidden layers, reduce if underfitting
3. **Weight decay (L2)** — 1e-6 to 1e-3, log-scale search
4. **Layer normalization** — preferred over batch norm for small batches
5. **Gradient clipping** — `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)`
6. **Learning rate scheduling** — ReduceLROnPlateau with factor=0.5, patience=5

**Vanishing/exploding gradient detection:**
```python
def check_gradients(model: nn.Module) -> dict[str, float]:
    grad_norms = {}
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_norms[name] = param.grad.norm().item()
    all_norms = list(grad_norms.values())
    logger.info(f"Gradient norms — min: {min(all_norms):.6f}, "
                f"max: {max(all_norms):.6f}, mean: {np.mean(all_norms):.6f}")
    if max(all_norms) > 10.0:
        logger.warning("Exploding gradients detected — add gradient clipping")
    if min(all_norms) < 1e-8:
        logger.warning("Vanishing gradients detected — check activation functions")
    return grad_norms
```

### Step 5 — Model export and Azure ML inference integration

**Save model for AML inference pipeline:**
```python
# Save state dict (preferred) or full model
torch.save(model.state_dict(), os.path.join(args.model_output_dir, "model.pt"))
torch.save({
    "model_config": {
        "input_dim": input_dim,
        "hidden_dims": hidden_dims,
        "dropout": dropout,
    },
    "best_epoch": best_epoch,
    "best_val_metric": best_val_metric,
}, os.path.join(args.model_output_dir, "model_metadata.json"))
```

**Inference scoring script pattern:**
```python
# inference_model.py — DL variant
import torch
import json

def load_model(model_dir: str, device: torch.device) -> nn.Module:
    with open(os.path.join(model_dir, "model_metadata.json")) as f:
        meta = json.load(f)
    model = TabularMLP(**meta["model_config"]).to(device)
    model.load_state_dict(torch.load(
        os.path.join(model_dir, "model.pt"), map_location=device
    ))
    model.eval()
    return model

def predict(model: nn.Module, X: np.ndarray, device: torch.device) -> np.ndarray:
    with torch.no_grad():
        tensor_x = torch.FloatTensor(X).to(device)
        preds = model(tensor_x).cpu().numpy()
    return preds
```

---

## Gotchas

- **GPU compute is required for meaningful DL training.** CPU training on AML is orders of magnitude slower and may time out. Always request GPU instances (`STANDARD_NC*` SKUs).
- **DL training is expensive — use Optuna pruning aggressively.** Set `n_startup_trials` low (3-5) and use `MedianPruner` to kill bad trials early. A 50-trial study with 2-hour timeout is a reasonable starting budget.
- **Always benchmark against tree-based models first.** LightGBM/CatBoost on tabular data often match DL with 1/10th the training time. Document the baseline comparison.
- **Watch for vanishing/exploding gradients.** Use gradient norm logging every N steps. If gradients explode, add `clip_grad_norm_`. If they vanish, switch from ReLU to GELU/LeakyReLU, or add residual connections.
- **Batch normalization behaves poorly with small batches.** Use LayerNorm instead when batch_size < 256.
- **`torch.save(model)` vs `torch.save(model.state_dict())`.** Always save state dicts — they are smaller, more portable, and the AML inference script reconstructs the model from config + weights.
- **MLflow logging for DL models.** Log the model architecture as a parameter (hidden_dims string), not just hyperparameters. Log training and validation loss curves per epoch.
- **Data loading bottleneck.** Use `torch.utils.data.DataLoader` with `num_workers=4` and `pin_memory=True` on GPU. For tabular data, pre-convert to numpy arrays and use tensor conversion in the loader.
- **Reproducibility.** Set seeds for torch, numpy, and python random. Use `torch.backends.cudnn.deterministic = True` for full reproducibility (slower).

---

## Evaluation criteria checklist

Before handing off a DL model, verify all of the following:

- [ ] Tree-based baseline was trained and compared — DL shows measurable improvement
- [ ] GPU compute was used for training (not CPU fallback)
- [ ] Optuna study completed with pruning enabled; best trial configuration logged
- [ ] Early stopping was active during training; patience value documented
- [ ] Gradient norms were checked — no vanishing or exploding gradients
- [ ] Model saved as state_dict + metadata JSON (not full model pickle)
- [ ] Inference scoring script can load the model and produce predictions on held-out data
- [ ] MLflow run logged: architecture params, hyperparameters, per-epoch loss curves, final metrics
- [ ] Component YAML `ArgumentParser` args match the script definitions
- [ ] Unit tests pass; component argument validation passes

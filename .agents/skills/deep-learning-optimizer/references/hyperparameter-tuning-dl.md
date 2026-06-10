# Hyperparameter Tuning for Deep Learning — Reference

## Optuna Search Spaces

### Learning Rate

```python
# Log-scale search — covers 5 orders of magnitude
lr = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)

# Common starting points by optimizer:
# Adam/AdamW: 1e-4 to 3e-4
# SGD with momentum: 1e-3 to 1e-2
# RMSprop: 1e-4 to 1e-3
```

### Batch Size

```python
# Powers of 2 for memory alignment; cap by GPU memory
batch_size = trial.suggest_categorical("batch_size", [256, 512, 1024, 2048, 4096])

# Rule of thumb:
# - Small models (<1M params): 1024-4096
# - Medium models (1-10M params): 512-2048
# - Large models (>10M params): 256-1024
# - If OOM, halve batch size and scale LR proportionally
```

### Architecture Search

```python
# Number of layers
n_layers = trial.suggest_int("n_layers", 2, 6)

# Hidden dimensions — decreasing width pattern
hidden_dims = []
for i in range(n_layers):
    dim = trial.suggest_int(f"hidden_dim_{i}", 32, 512, step=32)
    hidden_dims.append(dim)

# Dropout per layer
dropout = trial.suggest_float("dropout", 0.1, 0.5)

# Activation function
activation = trial.suggest_categorical("activation", ["gelu", "relu", "leaky_relu"])
```

### Regularization

```python
# Weight decay (L2)
weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True)

# Gradient clipping threshold
clip_value = trial.suggest_float("gradient_clip_norm", 0.5, 5.0)

# Label smoothing (for classification)
label_smoothing = trial.suggest_float("label_smoothing", 0.0, 0.1)
```

---

## Optuna Study Configuration

### Basic Study

```python
import optuna

def create_study(direction: str = "minimize", n_trials: int = 50,
                 timeout: int = 7200) -> optuna.study.Study:
    study = optuna.create_study(
        direction=direction,
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=5,
            n_min_n_trials=3,
            upscale_ratio=1.5,
        ),
    )
    study.optimize(objective, n_trials=n_trials, timeout=timeout)
    return study
```

### Objective Function Template

```python
def objective(trial: optuna.trial.Trial, X_train, y_train,
              X_val, y_val, device: torch.device) -> float:
    # Sample hyperparameters
    lr = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
    batch_size = trial.suggest_categorical("batch_size", [512, 1024, 2048])
    dropout = trial.suggest_float("dropout", 0.1, 0.5)
    n_layers = trial.suggest_int("n_layers", 2, 5)
    hidden_dims = [
        trial.suggest_int(f"hidden_dim_{i}", 64, 512, step=64)
        for i in range(n_layers)
    ]

    # Build model
    model = TabularMLP(
        input_dim=X_train.shape[1],
        hidden_dims=hidden_dims,
        dropout=dropout,
    ).to(device)

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=lr, weight_decay=1e-4
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )

    # Data loaders
    train_loader, val_loader = get_dataloaders(
        X_train, y_train, X_val, y_val, batch_size
    )

    # Training loop with pruning
    best_val_loss = float("inf")
    patience_counter = 0
    max_epochs = 100
    patience = 10

    for epoch in range(max_epochs):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_loss = validate(model, val_loader, device)

        # Report intermediate result to Optuna pruner
        trial.report(val_loss, epoch)
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()

        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    return best_val_loss
```

### Analyzing Study Results

```python
# Best trial
best = study.best_trial
print(f"Best value: {best.value:.4f}")
print(f"Best params: {best.params}")

# Hyperparameter importance
importances = optuna.importance.get_param_importances(study)
for param, importance in sorted(importances.items(),
                                  key=lambda x: x[1], reverse=True):
    print(f"  {param}: {importance:.4f}")

# Parallel coordinate plot
optuna.visualization.plot_parallel_coordinate(study)

# Optimization history
optuna.visualization.plot_optimization_history(study)
```

---

## Learning Rate Schedules

### ReduceLROnPlateau (recommended for tabular DL)

```python
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode="min", factor=0.5, patience=5, min_lr=1e-6
)
# Call after each validation epoch:
scheduler.step(val_loss)
```

### Cosine Annealing

```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
    optimizer, T_0=10, T_mult=2, eta_min=1e-6
)
# Call after each epoch:
scheduler.step()
```

### One-Cycle Learning Rate

```python
scheduler = torch.optim.lr_scheduler.OneCycleLR(
    optimizer, max_lr=1e-3,
    steps_per_epoch=len(train_loader),
    epochs=num_epochs,
    pct_start=0.3,  # warmup for 30% of training
)
# Call after each batch:
scheduler.step()
```

---

## Early Stopping Implementation

```python
import torch
from typing import Optional

class EarlyStopping:
    def __init__(self, patience: int = 10, min_delta: float = 1e-6,
                 mode: str = "min", verbose: bool = True):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.verbose = verbose
        self.counter = 0
        self.best_score: Optional[float] = None
        self.early_stop = False
        self.best_model_state: Optional[dict] = None

    def __call__(self, val_metric: float, model: torch.nn.Module) -> bool:
        if self.best_score is None:
            self.best_score = val_metric
            self.best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
            return False

        improved = (
            val_metric < self.best_score - self.min_delta
            if self.mode == "min"
            else val_metric > self.best_score + self.min_delta
        )

        if improved:
            self.best_score = val_metric
            self.best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
            self.counter = 0
        else:
            self.counter += 1
            if self.verbose:
                logger.info(f"EarlyStopping counter: {self.counter}/{self.patience}")

        if self.counter >= self.patience:
            self.early_stop = True
        return self.early_stop

    def restore_best_model(self, model: torch.nn.Module) -> None:
        if self.best_model_state:
            model.load_state_dict(self.best_model_state)
```

---

## Common Pitfalls

| Issue | Symptom | Fix |
|---|---|---|
| LR too high | Loss NaN or diverges | Reduce LR by 10x; add gradient clipping |
| LR too low | Training stalls, no improvement | Increase LR 10x; use warmup |
| Batch size too large | Overfitting, poor generalization | Reduce batch size; add more dropout |
| Batch size too small | Noisy gradients, slow convergence | Increase batch size; use gradient accumulation |
| Too many layers | Overfitting, long training | Reduce depth; add dropout per layer |
| Too few layers | Underfitting, high train loss | Add layers; increase hidden dims |
| No early stopping | Wastes compute, overfits | Always use early stopping with patience 5-15 |
| No LR schedule | Suboptimal convergence | Add ReduceLROnPlateau or cosine annealing |

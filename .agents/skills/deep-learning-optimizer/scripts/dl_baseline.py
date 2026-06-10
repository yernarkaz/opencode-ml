"""Minimal PyTorch training script template for Azure ML.

This script demonstrates the standard pattern for training a deep learning
model on Azure ML: argument parsing, data loading, training loop with early
stopping, MLflow logging, and model export.

Usage:
    python dl_baseline.py \
        --learning_rate 1e-3 \
        --batch_size 1024 \
        --num_epochs 100 \
        --model_output_dir ./outputs/model \
        --metrics_output_dir ./outputs/metrics \
        --workspace_name my-workspace \
        --resource_group my-rg \
        --subscription_id my-sub \
        --local_compute True
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
from utils.arg_parsing import str_to_bool  # noqa: E402


def get_args() -> argparse.Namespace:
    """Parse command-line arguments for DL training on Azure ML."""
    parser = argparse.ArgumentParser(description="Deep Learning Baseline Training")
    # Model architecture
    parser.add_argument("--model_type", type=str, default="mlp",
                        help="Model architecture type")
    parser.add_argument("--hidden_dims", type=str, default="256,128,64",
                        help="Comma-separated hidden layer dimensions")
    parser.add_argument("--dropout", type=float, default=0.3,
                        help="Dropout rate for hidden layers")
    # Training hyperparameters
    parser.add_argument("--learning_rate", type=float, default=1e-3,
                        help="Initial learning rate")
    parser.add_argument("--batch_size", type=int, default=1024,
                        help="Training batch size")
    parser.add_argument("--num_epochs", type=int, default=100,
                        help="Maximum number of training epochs")
    parser.add_argument("--weight_decay", type=float, default=1e-4,
                        help="L2 weight decay for optimizer")
    parser.add_argument("--early_stopping_patience", type=int, default=10,
                        help="Early stopping patience (epochs)")
    # Infrastructure
    parser.add_argument("--local_compute", type=str_to_bool, default=False,
                        help="Run locally instead of on AML compute")
    parser.add_argument("--use_gpu", type=str_to_bool, default=True,
                        help="Use GPU if available")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    # Azure ML
    parser.add_argument("--workspace_name", type=str, required=True,
                        help="Azure ML workspace name")
    parser.add_argument("--resource_group", type=str, required=True,
                        help="Azure resource group")
    parser.add_argument("--subscription_id", type=str, required=True,
                        help="Azure subscription ID")
    parser.add_argument("--client_id", type=str, default="",
                        help="Managed identity client ID (AML compute)")
    # Paths
    parser.add_argument("--train_data_path", type=str, required=True,
                        help="Path to training parquet/CSV data")
    parser.add_argument("--model_output_dir", type=str, required=True,
                        help="Output directory for model artifacts")
    parser.add_argument("--metrics_output_dir", type=str, required=True,
                        help="Output directory for metrics")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Model definition
# ---------------------------------------------------------------------------
class TabularMLP(nn.Module):
    """Multi-layer perceptron for tabular data with LayerNorm and GELU."""

    def __init__(self, input_dim: int, hidden_dims: list[int],
                 dropout: float = 0.3):
        super().__init__()
        layers: list[nn.Module] = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.LayerNorm(h_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            ])
            prev_dim = h_dim
        self.backbone = nn.Sequential(*layers)
        self.head = nn.Linear(prev_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x)).squeeze(-1)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class TabularDataset(Dataset):
    """PyTorch Dataset for tabular numpy arrays."""

    def __init__(self, X: np.ndarray, y: np.ndarray | None = None):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y) if y is not None else None

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor] | torch.Tensor:
        if self.y is not None:
            return self.X[idx], self.y[idx]
        return self.X[idx]


# ---------------------------------------------------------------------------
# Training utilities
# ---------------------------------------------------------------------------
def train_one_epoch(model: nn.Module, loader: DataLoader,
                    optimizer: torch.optim.Optimizer,
                    criterion: nn.Module,
                    device: torch.device) -> float:
    """Train for one epoch and return average loss."""
    model.train()
    total_loss = 0.0
    n_batches = 0
    for batch_X, batch_y in loader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        optimizer.zero_grad()
        preds = model(batch_X)
        loss = criterion(preds, batch_y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total_loss += loss.item()
        n_batches += 1
    return total_loss / max(n_batches, 1)


def validate(model: nn.Module, loader: DataLoader,
             criterion: nn.Module,
             device: torch.device) -> float:
    """Evaluate model and return average loss."""
    model.eval()
    total_loss = 0.0
    n_batches = 0
    with torch.no_grad():
        for batch_X, batch_y in loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            preds = model(batch_X)
            loss = criterion(preds, batch_y)
            total_loss += loss.item()
            n_batches += 1
    return total_loss / max(n_batches, 1)


# ---------------------------------------------------------------------------
# MLflow setup
# ---------------------------------------------------------------------------
def setup_mlflow(args: argparse.Namespace) -> None:
    """Configure MLflow tracking URI and start run if needed."""
    # Resolve tracking URI from workspace (never hardcode)
    if args.local_compute:
        from azure.ai.ml import MLClient
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
    else:
        from azure.ai.ml import MLClient
        from azure.identity import ManagedIdentityCredential
        credential = ManagedIdentityCredential(client_id=args.client_id)

    ml_client = MLClient(
        credential, args.subscription_id, args.resource_group, args.workspace_name
    )
    tracking_uri = ml_client.workspaces.get(args.workspace_name).mlflow_tracking_uri
    mlflow.set_tracking_uri(tracking_uri)

    # Only start run locally; AML manages runs automatically
    if not os.environ.get("AZUREML_RUN_ID"):
        if not mlflow.active_run():
            mlflow.start_run(run_name=f"dl_baseline_{args.model_type}")


def log_params(args: argparse.Namespace) -> None:
    """Log hyperparameters and architecture to MLflow."""
    mlflow.log_param("model_type", args.model_type)
    mlflow.log_param("hidden_dims", args.hidden_dims)
    mlflow.log_param("learning_rate", args.learning_rate)
    mlflow.log_param("batch_size", args.batch_size)
    mlflow.log_param("num_epochs", args.num_epochs)
    mlflow.log_param("dropout", args.dropout)
    mlflow.log_param("weight_decay", args.weight_decay)
    mlflow.log_param("early_stopping_patience", args.early_stopping_patience)
    mlflow.log_param("seed", args.seed)


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------
def main() -> None:
    args = get_args()

    # Reproducibility
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if torch.cuda.is_available():
        torch.backends.cudnn.deterministic = True

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() and args.use_gpu else "cpu")
    logger.info(f"Training on device: {device}")

    # Parse hidden dims
    hidden_dims = [int(d) for d in args.hidden_dims.split(",")]

    # Setup MLflow
    setup_mlflow(args)
    log_params(args)

    # Load data (placeholder — replace with actual data loading)
    # In practice, load from args.train_data_path (parquet/CSV)
    logger.info(f"Loading data from {args.train_data_path}")
    # Example:
    # import pandas as pd
    # df = pd.read_parquet(args.train_data_path)
    # feature_cols = [c for c in df.columns if c != "target"]
    # X = df[feature_cols].values.astype(np.float32)
    # y = df["target"].values.astype(np.float32)
    # X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Placeholder data for template demonstration
    X = np.random.randn(10000, 20).astype(np.float32)
    y = np.random.randn(10000).astype(np.float32)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    input_dim = X_train.shape[1]

    # Build model
    model = TabularMLP(input_dim, hidden_dims, args.dropout).to(device)
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate,
                                  weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5, min_lr=1e-6
    )
    criterion = nn.MSELoss()

    # Data loaders
    train_loader = DataLoader(
        TabularDataset(X_train, y_train),
        batch_size=args.batch_size, shuffle=True,
        num_workers=0, pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        TabularDataset(X_val, y_val),
        batch_size=args.batch_size * 2, shuffle=False,
        num_workers=0, pin_memory=torch.cuda.is_available(),
    )

    # Training loop with early stopping
    best_val_loss = float("inf")
    patience_counter = 0
    best_model_state: dict[str, torch.Tensor] = {}

    for epoch in range(1, args.num_epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = validate(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        # Log to MLflow
        mlflow.log_metric("train_loss", train_loss, step=epoch)
        mlflow.log_metric("val_loss", val_loss, step=epoch)
        mlflow.log_metric("learning_rate", optimizer.param_groups[0]["lr"], step=epoch)

        logger.info(f"Epoch {epoch}/{args.num_epochs} — "
                     f"train_loss: {train_loss:.4f}, val_loss: {val_loss:.4f}, "
                     f"lr: {optimizer.param_groups[0]['lr']:.6f}")

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= args.early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break

    # Restore best model
    model.load_state_dict(best_model_state)

    # Log final metrics
    mlflow.log_metric("best_val_loss", best_val_loss)
    mlflow.log_metric("best_epoch", args.num_epochs - patience_counter)

    # Save model
    os.makedirs(args.model_output_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(args.model_output_dir, "model.pt"))
    model_metadata: dict[str, Any] = {
        "model_type": args.model_type,
        "input_dim": input_dim,
        "hidden_dims": hidden_dims,
        "dropout": args.dropout,
        "best_val_loss": best_val_loss,
    }
    with open(os.path.join(args.model_output_dir, "model_metadata.json"), "w") as f:
        json.dump(model_metadata, f, indent=2)

    # Save metrics
    os.makedirs(args.metrics_output_dir, exist_ok=True)
    with open(os.path.join(args.metrics_output_dir, "metrics.json"), "w") as f:
        json.dump({"best_val_loss": best_val_loss}, f, indent=2)

    logger.info(f"Model saved to {args.model_output_dir}")
    logger.info(f"Best validation loss: {best_val_loss:.4f}")

    # End MLflow run (only if we started it)
    if not os.environ.get("AZUREML_RUN_ID"):
        mlflow.end_run()


if __name__ == "__main__":
    main()

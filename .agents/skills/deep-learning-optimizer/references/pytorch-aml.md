# PyTorch on Azure ML — Reference

## AML Script Parameter Pattern

Azure ML command jobs pass arguments via the `arguments` field in the component YAML.
Every argument must have a corresponding `ArgumentParser` entry in the Python script.

### Component YAML example

```yaml
type: command
name: train_dl_model
display_name: Train Deep Learning Model
inputs: {}
outputs:
  model_dir:
    type: uri_folder
  metrics_dir:
    type: uri_folder
properties:
  azureml_prompt_for_collection_of_job_metrics_on_prompt_level: true
code: training_script/
environment: azureml:PyTorch-2.0:1
command: >-
  python train_dl_model.py
  --model_type ${{inputs.model_type}}
  --learning_rate ${{inputs.learning_rate}}
  --batch_size ${{inputs.batch_size}}
  --num_epochs ${{inputs.num_epochs}}
  --model_output_dir ${{outputs.model_dir}}
  --metrics_output_dir ${{outputs.metrics_dir}}
  --local_compute ${{inputs.local_compute}}
  --use_gpu ${{inputs.use_gpu}}
  --workspace_name ${{inputs.workspace_name}}
  --resource_group ${{inputs.resource_group}}
  --subscription_id ${{inputs.subscription_id}}
```

### Argument parsing in Python

```python
import argparse
from utils.arg_parsing import str_to_bool

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Train DL model on Azure ML")
    # Model architecture
    parser.add_argument("--model_type", type=str, default="mlp")
    parser.add_argument("--hidden_dims", type=str, default="256,128,64")
    parser.add_argument("--dropout", type=float, default=0.3)
    # Training hyperparameters
    parser.add_argument("--learning_rate", type=float, default=1e-3)
    parser.add_argument("--batch_size", type=int, default=1024)
    parser.add_argument("--num_epochs", type=int, default=100)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--early_stopping_patience", type=int, default=10)
    # Infrastructure
    parser.add_argument("--local_compute", type=str_to_bool, default=False)
    parser.add_argument("--use_gpu", type=str_to_bool, default=True)
    # Azure ML
    parser.add_argument("--workspace_name", type=str, required=True)
    parser.add_argument("--resource_group", type=str, required=True)
    parser.add_argument("--subscription_id", type=str, required=True)
    # Paths
    parser.add_argument("--model_output_dir", type=str, required=True)
    parser.add_argument("--metrics_output_dir", type=str, required=True)
    return parser.parse_args()
```

---

## Environment Setup

### AML Curated Environment

Use the curated PyTorch environment for standard setups:

```yaml
environment: azureml:PyTorch-2.0:1
```

### Custom Environment (Docker)

For custom dependencies, define a Docker-based environment:

```yaml
name: dl-training-env
image: mcr.microsoft.com/azureml/openmpi4.1.0-cuda11.8-cudnn8:20230508.v1
conda_file: environment.yml
```

`environment.yml`:
```yaml
name: dl-training
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.10
  - pip
  - pip:
    - torch>=2.0
    - torchvision
    - optuna>=3.0
    - mlflow>=2.0
    - azure-ai-ml
    - azure-identity
    - numpy
    - pandas
    - scikit-learn
    - pyarrow
```

---

## Distributed Training

### Data Parallel (single node, multi-GPU)

For a single AML compute instance with multiple GPUs:

```python
import torch
from torch.nn.parallel import DistributedDataParallel as DDP

# Setup
local_rank = int(os.environ["LOCAL_RANK"])
torch.cuda.set_device(local_rank)
device = torch.device(f"cuda:{local_rank}")

model = TabularMLP(input_dim, hidden_dims, dropout).to(device)
model = DDP(model, device_ids=[local_rank])

# In AML command:
# torchrun --nproc_per_node=$AZUREML_PROCESS_COUNT_PER_INSTANCE \
#          train_dl_model.py ...
```

### Fully Sharded Data Parallel (FSDP)

For large models that don't fit in a single GPU:

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import ShardingStrategy

model = FSDP(
    TabularMLP(input_dim, hidden_dims, dropout),
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    device_id=torch.cuda.current_device(),
)
```

### Multi-node Training on AML

Set `instance_count > 1` on the AML compute target:

```yaml
code: training_script/
environment: azureml:PyTorch-2.0:1
instance_count: 4
command: >-
  torchrun
  --nproc_per_node=$AZUREML_PROCESS_COUNT_PER_INSTANCE
  --nnodes=$AZUREML_TRAIING_NODE_COUNT
  --node_rank=$AZUREML_CR_NODE_RANK
  --master_addr=$AZUREML_MASTER_NODE_IP
  --master_port=29500
  train_dl_model.py ...
```

---

## MLflow Integration

### Tracking URI resolution

```python
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

def get_mlflow_tracking_uri(args) -> str:
    credential = (
        DefaultAzureCredential() if args.local_compute
        else ManagedIdentityCredential(client_id=args.client_id)
    )
    ml_client = MLClient(
        credential, args.subscription_id, args.resource_group, args.workspace_name
    )
    return ml_client.workspaces.get(args.workspace_name).mlflow_tracking_uri
```

### Logging DL training metrics

```python
import mlflow

# Log architecture and hyperparameters
mlflow.log_param("model_type", args.model_type)
mlflow.log_param("hidden_dims", args.hidden_dims)
mlflow.log_param("learning_rate", args.learning_rate)
mlflow.log_param("batch_size", args.batch_size)
mlflow.log_param("dropout", args.dropout)
mlflow.log_param("weight_decay", args.weight_decay)

# Log per-epoch metrics
for epoch in range(num_epochs):
    train_loss = train_one_epoch(model, train_loader, optimizer, device)
    val_loss = validate(model, val_loader, device)
    mlflow.log_metric("train_loss", train_loss, step=epoch)
    mlflow.log_metric("val_loss", val_loss, step=epoch)
    mlflow.log_metric("learning_rate", optimizer.param_groups[0]["lr"], step=epoch)

# Log final metrics
mlflow.log_metric("best_val_loss", best_val_loss)
mlflow.log_metric("best_epoch", best_epoch)
```

### Model registration

```python
# Log model to MLflow
mlflow.pytorch.log_model(
    model, "model",
    artifact_path="model",
)

# Or register directly
mlflow.register_model(
    model_uri=f"runs:/{mlflow.active_run().info.run_id}/model",
    name=f"{args.model_name}_{args.environment}"
)
```

---

## Data Loading for Tabular DL

```python
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np

class TabularDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray | None = None):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y) if y is not None else None

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor] | torch.Tensor:
        if self.y is not None:
            return self.X[idx], self.y[idx]
        return self.X[idx]

def get_dataloaders(X_train, y_train, X_val, y_val,
                    batch_size: int, num_workers: int = 4):
    train_loader = DataLoader(
        TabularDataset(X_train, y_train),
        batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True,
    )
    val_loader = DataLoader(
        TabularDataset(X_val, y_val),
        batch_size=batch_size * 2, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )
    return train_loader, val_loader
```

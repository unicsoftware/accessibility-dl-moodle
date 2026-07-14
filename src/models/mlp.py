# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/models/mlp.py
# Descrição: Rede Neural MLP (Multi-Layer Perceptron) em PyTorch.
# =====================================================================
"""
Modelo MLP (Multi-Layer Perceptron)
====================================

Implementa uma rede neural *feedforward* simples em PyTorch para o
problema de classificação multiclasse.

Arquitetura:
    Input(11)
      → Linear(hidden_1) → ReLU → Dropout
      → Linear(hidden_2) → ReLU → Dropout
      → Linear(num_classes) → Softmax

Hiperparâmetros definidos em `src/config.py`:
- MLP_HIDDEN_LAYERS
- MLP_DROPOUT
- MLP_LEARNING_RATE
- MLP_BATCH_SIZE
- MLP_EPOCHS
- MLP_PATIENCE
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from src.config import (
    MLP_BATCH_SIZE,
    MLP_DROPOUT,
    MLP_EPOCHS,
    MLP_HIDDEN_LAYERS,
    MLP_LEARNING_RATE,
    MLP_MODEL_FILE,
    MLP_PATIENCE,
    MLP_WEIGHT_DECAY,
    NUM_CLASSES,
    NUM_FEATURES,
)


# =====================================================================
# Definição da arquitetura
# =====================================================================


class MLP(nn.Module):
    """Rede neural *feedforward* (MLP) para classificação multiclasse.

    Parâmetros:
        input_dim: número de features de entrada.
        hidden_layers: tupla com tamanhos das camadas ocultas.
        num_classes: número de classes de saída.
        dropout: taxa de dropout entre camadas.
    """

    def __init__(
        self,
        input_dim: int = NUM_FEATURES,
        hidden_layers: Tuple[int, ...] = MLP_HIDDEN_LAYERS,
        num_classes: int = NUM_CLASSES,
        dropout: float = MLP_DROPOUT,
    ) -> None:
        super().__init__()

        layers: list[nn.Module] = []
        prev_dim = input_dim

        for h in hidden_layers:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = h

        layers.append(nn.Linear(prev_dim, num_classes))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass — retorna logits."""
        return self.network(x)


# =====================================================================
# Wrapper de alto nível
# =====================================================================


class MLPAccessibilityModel:
    """Wrapper de alto nível para treinar, avaliar, salvar e carregar."""

    def __init__(
        self,
        input_dim: int = NUM_FEATURES,
        hidden_layers: Tuple[int, ...] = MLP_HIDDEN_LAYERS,
        num_classes: int = NUM_CLASSES,
        dropout: float = MLP_DROPOUT,
        learning_rate: float = MLP_LEARNING_RATE,
        weight_decay: float = MLP_WEIGHT_DECAY,
        device: Optional[str] = None,
    ) -> None:
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.input_dim = input_dim
        self.hidden_layers = hidden_layers
        self.num_classes = num_classes
        self.dropout = dropout

        self.model = MLP(
            input_dim=input_dim,
            hidden_layers=hidden_layers,
            num_classes=num_classes,
            dropout=dropout,
        ).to(self.device)

        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        self.criterion = nn.CrossEntropyLoss()

        self.history: dict[str, list[float]] = {
            "train_loss": [],
            "val_loss": [],
            "train_acc": [],
            "val_acc": [],
        }

    # ------------------------------------------------------------------
    # Treinamento
    # ------------------------------------------------------------------
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = MLP_EPOCHS,
        batch_size: int = MLP_BATCH_SIZE,
        patience: int = MLP_PATIENCE,
        verbose: bool = True,
    ) -> dict:
        """Treina o modelo com early stopping.

        Args:
            X_train, y_train: dados de treino.
            X_val, y_val: dados de validação (opcional).
            epochs: número máximo de epochs.
            batch_size: tamanho do batch.
            patience: paciência para early stopping.
            verbose: imprimir progresso.

        Returns:
            Histórico de treinamento.
        """
        # Tensores
        X_train_t = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        y_train_t = torch.tensor(y_train, dtype=torch.long).to(self.device)

        train_ds = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(
            train_ds, batch_size=batch_size, shuffle=True, drop_last=False,
        )

        if X_val is not None and y_val is not None:
            X_val_t = torch.tensor(X_val, dtype=torch.float32).to(self.device)
            y_val_t = torch.tensor(y_val, dtype=torch.long).to(self.device)

        best_state: Optional[dict] = None
        best_val_loss = float("inf")
        epochs_no_improve = 0

        for epoch in range(1, epochs + 1):
            # --- Treino ---
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for xb, yb in train_loader:
                self.optimizer.zero_grad()
                logits = self.model(xb)
                loss = self.criterion(logits, yb)
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item() * xb.size(0)
                preds = logits.argmax(dim=1)
                train_correct += (preds == yb).sum().item()
                train_total += xb.size(0)

            train_loss /= max(train_total, 1)
            train_acc = train_correct / max(train_total, 1)

            self.history["train_loss"].append(train_loss)
            self.history["train_acc"].append(train_acc)

            # --- Validação ---
            val_loss: Optional[float] = None
            val_acc: Optional[float] = None

            if X_val is not None and y_val is not None:
                self.model.eval()
                with torch.no_grad():
                    val_logits = self.model(X_val_t)
                    v_loss = self.criterion(val_logits, y_val_t).item()
                    v_preds = val_logits.argmax(dim=1)
                    v_acc = (v_preds == y_val_t).float().mean().item()

                val_loss = v_loss
                val_acc = v_acc
                self.history["val_loss"].append(v_loss)
                self.history["val_acc"].append(v_acc)

                # Early stopping
                if v_loss < best_val_loss - 1e-6:
                    best_val_loss = v_loss
                    best_state = copy.deepcopy(self.model.state_dict())
                    epochs_no_improve = 0
                else:
                    epochs_no_improve += 1

            if verbose and (epoch % 5 == 0 or epoch == 1):
                msg = (
                    f"[Epoch {epoch:03d}/{epochs}] "
                    f"train_loss={train_loss:.4f} train_acc={train_acc:.4f}"
                )
                if val_loss is not None:
                    msg += f" | val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
                print(msg)

            if epochs_no_improve >= patience:
                if verbose:
                    print(f"[INFO] Early stopping em epoch {epoch} (paciência={patience}).")
                break

        # Restaura o melhor estado
        if best_state is not None:
            self.model.load_state_dict(best_state)
            if verbose:
                print(f"[INFO] Restaurado melhor modelo (val_loss={best_val_loss:.4f}).")

        return self.history

    # ------------------------------------------------------------------
    # Predição
    # ------------------------------------------------------------------
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prediz as classes."""
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
            logits = self.model(X_t)
            preds = np.array(logits.argmax(dim=1).cpu().tolist())
        return preds

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Retorna as probabilidades (softmax)."""
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
            logits = self.model(X_t)
            probs = np.array(F.softmax(logits, dim=1).cpu().tolist())
        return probs

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def save(self, path: Union[str, Path] = MLP_MODEL_FILE) -> None:
        """Salva o estado do modelo."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": self.model.state_dict(),
            "input_dim": self.input_dim,
            "hidden_layers": self.hidden_layers,
            "num_classes": self.num_classes,
            "dropout": self.dropout,
            "history": self.history,
        }, path)

    @classmethod
    def load(cls, path: Union[str, Path] = MLP_MODEL_FILE) -> "MLPAccessibilityModel":
        """Carrega o modelo de disco."""
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        model = cls(
            input_dim=checkpoint["input_dim"],
            hidden_layers=checkpoint["hidden_layers"],
            num_classes=checkpoint["num_classes"],
            dropout=checkpoint.get("dropout", MLP_DROPOUT),
        )
        model.model.load_state_dict(checkpoint["state_dict"])
        model.history = checkpoint.get("history", model.history)
        model.model.eval()
        return model

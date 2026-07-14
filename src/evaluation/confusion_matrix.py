# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/evaluation/confusion_matrix.py
# Descrição: Geração de heatmap da matriz de confusão.
# =====================================================================
"""
Módulo de matriz de confusão.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import confusion_matrix


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: List[str],
    path: Union[str, Path],
    normalize: bool = True,
    title: str = "Matriz de Confusão",
) -> None:
    """Gera e salva um heatmap da matriz de confusão.

    Args:
        y_true: rótulos verdadeiros.
        y_pred: rótulos preditos.
        class_names: nomes das classes.
        path: caminho do PNG de saída.
        normalize: normalizar por linha.
        title: título do gráfico.
    """
    cm = confusion_matrix(y_true, y_pred, labels=range(len(class_names)))

    if normalize:
        cm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
        cm = np.nan_to_num(cm)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt=".2f" if normalize else "d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=True,
        ax=ax,
    )
    ax.set_xlabel("Predito")
    ax.set_ylabel("Verdadeiro")
    ax.set_title(title)
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Matriz de confusão salva em {path}")

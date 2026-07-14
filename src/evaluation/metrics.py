# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/evaluation/metrics.py
# Descrição: Cálculo de métricas de classificação.
# =====================================================================
"""
Módulo de métricas.

Fornece funções para cálculo de accuracy, precision, recall e F1.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    average: str = "macro",
) -> Dict[str, float]:
    """Calcula métricas de classificação multiclasse.

    Args:
        y_true: rótulos verdadeiros (codificados).
        y_pred: rótulos preditos.
        average: tipo de média para P/R/F1 ('macro', 'weighted', 'micro').

    Returns:
        Dicionário com accuracy, precision, recall, f1.
    """
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average=average, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average=average, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
    }

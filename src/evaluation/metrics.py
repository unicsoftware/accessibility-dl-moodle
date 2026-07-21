# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/evaluation/metrics.py
# Descrição: Cálculo de métricas de classificação e avaliação por critérios WCAG.
# =====================================================================
"""
Módulo de métricas.

Fornece funções para cálculo de accuracy, precision, recall, F1 e métricas
por critério WCAG individual (Weak Supervision vs Modelo ML).
"""

from __future__ import annotations

from typing import Dict, List, Union

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

from src import config


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


def compute_wcag_metrics(
    y_true_wcag: List[List[str]],
    y_pred_wcag: List[List[str]],
    wcag_criteria: List[str] = config.WCAG_CRITERIA,
) -> Dict[str, Dict[str, float]]:
    """Calcula Precision, Recall e F1-score por critério WCAG individual.

    Args:
        y_true_wcag: Lista de listas de critérios WCAG detectados como ground truth / Weak Supervision.
        y_pred_wcag: Lista de listas de critérios WCAG previstos pelo modelo.
        wcag_criteria: Lista de critérios a serem avaliados.

    Returns:
        Dicionário mapeando cada critério às suas métricas (precision, recall, f1).
    """
    metrics_per_criterion: Dict[str, Dict[str, float]] = {}

    for criterion in wcag_criteria:
        bin_true = [1 if criterion in sample else 0 for sample in y_true_wcag]
        bin_pred = [1 if criterion in sample else 0 for sample in y_pred_wcag]

        p = float(precision_score(bin_true, bin_pred, zero_division=0))
        r = float(recall_score(bin_true, bin_pred, zero_division=0))
        f1 = float(f1_score(bin_true, bin_pred, zero_division=0))

        metrics_per_criterion[criterion] = {
            "precision": p,
            "recall": r,
            "f1": f1,
        }

    return metrics_per_criterion

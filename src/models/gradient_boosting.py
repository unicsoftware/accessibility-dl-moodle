# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/models/gradient_boosting.py
# Descrição: Wrapper do modelo Gradient Boosting (scikit-learn).
# =====================================================================
"""
Modelo Gradient Boosting
========================

Modelo de ensamble baseado em árvores de decisão impulsionadas por gradiente.
Fornece excelente desempenho preditivo em dados tabulares estruturados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from src.config import (
    GB_LEARNING_RATE,
    GB_MAX_DEPTH,
    GB_MODEL_FILE,
    GB_N_ESTIMATORS,
    RANDOM_SEED,
)


class GradientBoostingAccessibilityModel:
    """Wrapper para o modelo Gradient Boosting."""

    def __init__(
        self,
        n_estimators: int = GB_N_ESTIMATORS,
        learning_rate: float = GB_LEARNING_RATE,
        max_depth: int = GB_MAX_DEPTH,
        random_state: int = RANDOM_SEED,
    ) -> None:
        self.model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
        )
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GradientBoostingAccessibilityModel":
        """Treina o modelo."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prediz as classes."""
        if not self.is_fitted:
            raise RuntimeError("Modelo não foi treinado. Chame fit() primeiro.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Retorna as probabilidades por classe."""
        if not self.is_fitted:
            raise RuntimeError("Modelo não foi treinado. Chame fit() primeiro.")
        return self.model.predict_proba(X)

    def save(self, path: Union[str, Path] = GB_MODEL_FILE) -> None:
        """Salva o modelo em disco."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Union[str, Path] = GB_MODEL_FILE) -> "GradientBoostingAccessibilityModel":
        """Carrega o modelo de disco."""
        obj = joblib.load(path)
        if isinstance(obj, cls):
            return obj
        new = cls()
        new.model = obj
        new.is_fitted = True
        return new


def build_gradient_boosting_model(
    n_estimators: int = GB_N_ESTIMATORS,
    learning_rate: float = GB_LEARNING_RATE,
    max_depth: int = GB_MAX_DEPTH,
    random_state: Optional[int] = RANDOM_SEED,
) -> GradientBoostingClassifier:
    """Constrói uma instância simples de GradientBoostingClassifier."""
    return GradientBoostingClassifier(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        random_state=random_state,
    )

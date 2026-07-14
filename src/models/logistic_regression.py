# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/models/logistic_regression.py
# Descrição: Wrapper do modelo Logistic Regression (scikit-learn).
# =====================================================================
"""
Modelo de Regressão Logística.

Modelo linear usado como baseline interpretável. Para problemas
multiclasse, o scikit-learn utiliza a estratégia one-vs-rest por padrão,
ou multinomial se especificado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from src.config import (
    LOGISTIC_C,
    LOGISTIC_MAX_ITER,
    LOGISTIC_MODEL_FILE,
    LOGISTIC_SOLVER,
)


class LogisticAccessibilityModel:
    """Wrapper para o modelo de Regressão Logística."""

    def __init__(
        self,
        max_iter: int = LOGISTIC_MAX_ITER,
        C: float = LOGISTIC_C,
        solver: str = LOGISTIC_SOLVER,
        random_state: int = 42,
    ) -> None:
        self.model = LogisticRegression(
            max_iter=max_iter,
            C=C,
            solver=solver,
            multi_class="multinomial",
            random_state=random_state,
            n_jobs=-1,
        )
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticAccessibilityModel":
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

    def save(self, path: Union[str, Path] = LOGISTIC_MODEL_FILE) -> None:
        """Salva o modelo em disco."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Union[str, Path] = LOGISTIC_MODEL_FILE) -> "LogisticAccessibilityModel":
        """Carrega o modelo de disco."""
        obj = joblib.load(path)
        if isinstance(obj, cls):
            return obj
        # Compatibilidade: se foi salvo apenas o estimador
        new = cls()
        new.model = obj
        new.is_fitted = True
        return new


def build_logistic_model(
    max_iter: int = LOGISTIC_MAX_ITER,
    C: float = LOGISTIC_C,
    random_state: Optional[int] = 42,
) -> LogisticRegression:
    """Constrói uma instância de LogisticRegression (forma simples)."""
    return LogisticRegression(
        max_iter=max_iter,
        C=C,
        solver=LOGISTIC_SOLVER,
        multi_class="multinomial",
        random_state=random_state,
        n_jobs=-1,
    )

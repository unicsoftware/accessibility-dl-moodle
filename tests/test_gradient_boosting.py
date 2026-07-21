# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_gradient_boosting.py
# Descrição: Testes unitários do Gradient Boosting.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.gradient_boosting import (
    GradientBoostingAccessibilityModel,
    build_gradient_boosting_model,
)


class TestGradientBoostingModel:
    """Testes para o modelo Gradient Boosting."""

    def test_fit_and_predict(self):
        X = np.random.randn(20, 22)
        y = np.random.randint(0, 4, size=20)

        model = GradientBoostingAccessibilityModel(n_estimators=10, random_state=42)
        model.fit(X, y)

        preds = model.predict(X)
        probs = model.predict_proba(X)

        assert len(preds) == 20
        assert probs.shape == (20, 4)

    def test_unfitted_raises(self):
        model = GradientBoostingAccessibilityModel()
        with pytest.raises(RuntimeError):
            model.predict(np.zeros((5, 22)))

    def test_save_and_load(self, tmp_path):
        X = np.random.randn(20, 22)
        y = np.random.randint(0, 4, size=20)

        model = GradientBoostingAccessibilityModel(n_estimators=5, random_state=42)
        model.fit(X, y)

        save_path = tmp_path / "gb_test.pkl"
        model.save(save_path)
        assert save_path.exists()

        loaded_model = GradientBoostingAccessibilityModel.load(save_path)
        assert loaded_model.is_fitted
        np.testing.assert_array_equal(model.predict(X), loaded_model.predict(X))

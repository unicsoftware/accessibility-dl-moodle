# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_models.py
# Descrição: Testes dos modelos Logistic e MLP.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import ACTION_CLASSES, NUM_CLASSES, NUM_FEATURES
from src.models.logistic_regression import LogisticAccessibilityModel, build_logistic_model
from src.models.mlp import MLP, MLPAccessibilityModel


# =====================================================================
# Dados sintéticos para testes
# =====================================================================


@pytest.fixture
def synthetic_data():
    """Gera dados sintéticos pequenos para testar os modelos."""
    rng = np.random.default_rng(42)
    n_samples = 200
    n_features = NUM_FEATURES

    X = rng.integers(0, 2, size=(n_samples, n_features)).astype(float)
    # y depende de algumas features para que o modelo consiga aprender
    y = (X[:, 0] * 2 + X[:, 1]).astype(int) % NUM_CLASSES
    return X, y


# =====================================================================
# Testes da Logistic Regression
# =====================================================================


class TestLogisticRegression:
    """Testes do modelo de Regressão Logística."""

    def test_build(self):
        model = build_logistic_model()
        assert model is not None
        assert model.max_iter >= 100

    def test_fit_predict(self, synthetic_data):
        X, y = synthetic_data
        model = LogisticAccessibilityModel(random_state=42)
        model.fit(X, y)
        preds = model.predict(X)
        assert preds.shape == y.shape
        assert set(preds.tolist()).issubset(set(range(NUM_CLASSES)))

    def test_predict_proba(self, synthetic_data):
        X, y = synthetic_data
        model = LogisticAccessibilityModel(random_state=42)
        model.fit(X, y)
        proba = model.predict_proba(X)
        assert proba.shape == (len(X), NUM_CLASSES)
        # Soma das probabilidades = 1
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-6)

    def test_predict_without_fit_raises(self):
        model = LogisticAccessibilityModel()
        with pytest.raises(RuntimeError):
            model.predict(np.array([[0] * NUM_FEATURES]))


# =====================================================================
# Testes do MLP
# =====================================================================


class TestMLP:
    """Testes do modelo MLP."""

    def test_architecture(self):
        model = MLP(input_dim=11, hidden_layers=(64, 32), num_classes=4, dropout=0.3)
        assert model is not None
        # Verifica tamanho da primeira e última camada
        assert model.network[0].in_features == 11
        assert model.network[-1].out_features == 4

    def test_forward_shape(self):
        import torch

        model = MLP(input_dim=NUM_FEATURES, hidden_layers=(32, 16), num_classes=NUM_CLASSES)
        x = torch.randn(8, NUM_FEATURES)
        out = model(x)
        assert out.shape == (8, NUM_CLASSES)

    def test_fit_predict(self, synthetic_data):
        X, y = synthetic_data
        model = MLPAccessibilityModel(
            input_dim=NUM_FEATURES,
            hidden_layers=(16, 8),
            num_classes=NUM_CLASSES,
        )
        history = model.fit(
            X[:150], y[:150],
            X_val=X[150:], y_val=y[150:],
            epochs=10,
            batch_size=32,
            patience=5,
            verbose=False,
        )
        assert "train_loss" in history
        assert "val_loss" in history
        assert len(history["train_loss"]) > 0

        preds = model.predict(X[150:])
        assert preds.shape[0] == X[150:].shape[0]

    def test_predict_proba(self, synthetic_data):
        X, y = synthetic_data
        model = MLPAccessibilityModel(
            input_dim=NUM_FEATURES,
            hidden_layers=(16,),
            num_classes=NUM_CLASSES,
        )
        model.fit(X[:150], y[:150], epochs=3, batch_size=32, verbose=False)
        proba = model.predict_proba(X[150:])
        assert proba.shape == (X[150:].shape[0], NUM_CLASSES)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-5)

    def test_save_load(self, synthetic_data, tmp_path):
        X, y = synthetic_data
        path = tmp_path / "mlp_test.pt"
        model = MLPAccessibilityModel(
            input_dim=NUM_FEATURES,
            hidden_layers=(8,),
            num_classes=NUM_CLASSES,
        )
        model.fit(X[:100], y[:100], epochs=2, batch_size=32, verbose=False)
        model.save(path)

        loaded = MLPAccessibilityModel.load(path)
        preds_original = model.predict(X[100:])
        preds_loaded = loaded.predict(X[100:])
        np.testing.assert_array_equal(preds_original, preds_loaded)

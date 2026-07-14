# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_preprocessing.py
# Descrição: Testes do pré-processamento e split.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import ACTION_CLASSES, FEATURE_COLUMNS
from src.dataset.preprocessing import (
    decode_labels,
    encode_labels,
    handle_missing_values,
    normalize_features,
    preprocess_pipeline,
    remove_duplicates,
)
from src.dataset.split import split_dataset


# =====================================================================
# Limpeza
# =====================================================================


class TestCleaning:
    """Testes das funções de limpeza."""

    def test_remove_duplicates(self):
        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "html": ["<img>", "<img>", "<button>", "<table>"],
            "action": ["A", "A", "B", "C"],
        })
        cleaned = remove_duplicates(df)
        assert len(cleaned) == 3

    def test_handle_missing_features(self):
        df = pd.DataFrame({
            "id": [1, 2],
            "html": ["<img>", "<button>"],
            "action": ["A", "B"],
            "has_img": [1, np.nan],
            "has_button": [0, 1],
            "has_alt": [0, 0],
            "has_aria": [0, 0],
            "has_form": [0, 0],
            "has_link": [0, 0],
            "has_table": [0, 0],
            "heading_count": [0, 0],
            "invalid_heading": [0, 0],
            "text_length": [10, 5],
            "tag_count": [1, 1],
        })
        out = handle_missing_values(df)
        assert out["has_img"].iloc[1] == 0
        assert out["has_img"].iloc[0] == 1

    def test_handle_missing_html(self):
        df = pd.DataFrame({
            "id": [1, 2],
            "html": [None, "<p>"],
            "action": ["A", "B"],
            "has_img": [0, 0],
            "has_alt": [0, 0],
            "has_aria": [0, 0],
            "has_button": [0, 0],
            "has_form": [0, 0],
            "has_link": [0, 0],
            "has_table": [0, 0],
            "heading_count": [0, 0],
            "invalid_heading": [0, 0],
            "text_length": [0, 5],
            "tag_count": [0, 1],
        })
        out = handle_missing_values(df)
        assert out["html"].iloc[0] == ""


# =====================================================================
# Codificação
# =====================================================================


class TestEncoding:
    """Testes de codificação e decodificação de rótulos."""

    def test_encode_decode_roundtrip(self):
        y = pd.Series(["ADD_ALT", "NO_ACTION", "FIX_HEADING"])
        y_enc, le = encode_labels(y)
        assert len(y_enc) == 3
        assert all(isinstance(v, (int, np.integer)) for v in y_enc)
        y_dec = decode_labels(y_enc, le)
        assert list(y_dec) == list(y)

    def test_encoder_classes_fixed(self):
        y = pd.Series(["ADD_ALT", "NO_ACTION"])
        _, le = encode_labels(y)
        assert list(le.classes_) == ACTION_CLASSES


# =====================================================================
# Normalização
# =====================================================================


class TestNormalization:
    """Testes de normalização."""

    def test_normalize_fit_transform(self):
        X = pd.DataFrame({
            "f1": [1, 2, 3, 4, 5],
            "f2": [10, 20, 30, 40, 50],
        })
        X_scaled, scaler = normalize_features(X, fit=True)
        # Média próxima de 0, std próximo de 1
        assert np.abs(X_scaled.mean()) < 1e-6
        assert np.abs(X_scaled.std() - 1.0) < 1e-6

    def test_normalize_transform_uses_fitted_scaler(self):
        X1 = pd.DataFrame({"f1": [1, 2, 3]})
        X2 = pd.DataFrame({"f1": [2, 4, 6]})
        _, scaler = normalize_features(X1, fit=True)
        X2_scaled, _ = normalize_features(X2, scaler=scaler, fit=False)
        # Não refaz o fit
        assert X2_scaled.shape == (3, 1)


# =====================================================================
# Pipeline completo
# =====================================================================


class TestPipeline:
    """Testes do pipeline completo de pré-processamento."""

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "id": list(range(1, 11)),
            "profile": ["VISUAL"] * 10,
            "html": [
                '<img src="x.png">',                 # ADD_ALT
                '<button>A</button>',                # ADD_ARIA
                '<h3>A</h3><h1>B</h1>',              # FIX_HEADING
                '<img src="x.png" alt="X">',         # NO_ACTION
                '<a href="#">X</a>',                 # ADD_ARIA
                '<table></table>',                   # NO_ACTION
                '<img src="a.jpg">',                 # ADD_ALT
                '<h1>A</h1><h2>B</h2>',              # NO_ACTION
                '<button>B</button>',                # ADD_ARIA
                '<h5>A</h5><h1>B</h1>',              # FIX_HEADING
            ],
            "has_img": [1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
            "has_alt": [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            "has_aria": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "has_button": [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
            "has_form": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "has_link": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
            "has_table": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            "heading_count": [0, 0, 2, 0, 0, 0, 0, 2, 0, 2],
            "invalid_heading": [0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            "text_length": [0, 1, 10, 1, 1, 0, 0, 5, 1, 10],
            "tag_count": [1, 1, 2, 1, 1, 1, 1, 2, 1, 2],
            "action": [
                "ADD_ALT", "ADD_ARIA", "FIX_HEADING", "NO_ACTION", "ADD_ARIA",
                "NO_ACTION", "ADD_ALT", "NO_ACTION", "ADD_ARIA", "FIX_HEADING",
            ],
        })

    def test_pipeline_shape(self, sample_df):
        X, y, scaler, le = preprocess_pipeline(sample_df, fit=True)
        assert X.shape[0] == 10
        assert X.shape[1] == len(FEATURE_COLUMNS)
        assert len(y) == 10

    def test_pipeline_scaler_reuse(self, sample_df):
        df_train = sample_df.iloc[:8]
        df_test = sample_df.iloc[8:]
        _, _, scaler, le = preprocess_pipeline(df_train, fit=True)
        X_test, y_test, _, _ = preprocess_pipeline(df_test, scaler=scaler, fit=False)
        assert X_test.shape == (2, len(FEATURE_COLUMNS))


# =====================================================================
# Split
# =====================================================================


class TestSplit:
    """Testes da divisão treino/validação/teste."""

    @pytest.fixture
    def large_df(self):
        # Cria dataset balanceado pequeno
        data = []
        for action in ACTION_CLASSES:
            for i in range(100):
                data.append({
                    "id": len(data) + 1,
                    "profile": "VISUAL",
                    "html": f"<p>{action}-{i}</p>",
                    "has_img": 0, "has_alt": 0, "has_aria": 0,
                    "has_button": 0, "has_form": 0, "has_link": 0, "has_table": 0,
                    "heading_count": 0, "invalid_heading": 0,
                    "text_length": 10, "tag_count": 1,
                    "action": action,
                })
        return pd.DataFrame(data)

    def test_split_sizes(self, large_df):
        train, val, test = split_dataset(large_df, seed=42)
        assert len(train) + len(val) + len(test) == len(large_df)
        assert abs(len(train) / len(large_df) - 0.70) < 0.05
        assert abs(len(val) / len(large_df) - 0.15) < 0.05
        assert abs(len(test) / len(large_df) - 0.15) < 0.05

    def test_split_stratified(self, large_df):
        train, val, test = split_dataset(large_df, seed=42)
        for split in (train, val, test):
            assert set(split["action"].unique()) == set(ACTION_CLASSES)

    def test_split_invalid_proportions(self, large_df):
        with pytest.raises(ValueError):
            split_dataset(large_df, train_size=0.5, val_size=0.2, test_size=0.1)

# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_dataset.py
# Descrição: Testes do módulo de dataset e feature engineering.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import ACTION_CLASSES, FEATURE_COLUMNS
from src.dataset.feature_engineering import (
    count_tags,
    extract_features,
    has_alt,
    has_aria,
    has_button,
    has_form,
    has_img,
    has_link,
    has_table,
    heading_count,
    invalid_heading,
    visible_text_length,
)


# =====================================================================
# Feature engineering
# =====================================================================


class TestFeatureExtraction:
    """Testes para a extração de features estruturais."""

    def test_has_img_true(self):
        assert has_img('<img src="x.png">') == 1

    def test_has_img_false(self):
        assert has_img('<button>OK</button>') == 0

    def test_has_alt_true(self):
        assert has_alt('<img src="x.png" alt="X">') == 1

    def test_has_alt_false(self):
        assert has_alt('<img src="x.png">') == 0

    def test_has_aria_true(self):
        assert has_aria('<button aria-label="OK">X</button>') == 1

    def test_has_aria_false(self):
        assert has_aria('<button>X</button>') == 0

    def test_has_button(self):
        assert has_button("<button>X</button>") == 1
        assert has_button("<a>X</a>") == 0

    def test_has_form(self):
        assert has_form("<form>X</form>") == 1
        assert has_form("<div>X</div>") == 0

    def test_has_link(self):
        assert has_link('<a href="#">X</a>') == 1
        assert has_link("<p>X</p>") == 0

    def test_has_table(self):
        assert has_table("<table><tr></tr></table>") == 1
        assert has_table("<div></div>") == 0

    def test_count_tags(self):
        assert count_tags("<div><p>X</p></div>") == 4
        assert count_tags("") == 0

    def test_text_length(self):
        assert visible_text_length("<p>Olá mundo</p>") > 0
        assert visible_text_length("") == 0

    def test_heading_count(self):
        assert heading_count("<h1>A</h1><h2>B</h2><h3>C</h3>") == 3
        assert heading_count("<p>X</p>") == 0

    def test_invalid_heading_clean(self):
        assert invalid_heading("<h1>A</h1><h2>B</h2>") == 0

    def test_invalid_heading_skip(self):
        assert invalid_heading("<h1>A</h1><h4>B</h4>") == 1

    def test_invalid_heading_no_h1(self):
        assert invalid_heading("<h3>A</h3>") == 1

    def test_invalid_heading_regression(self):
        assert invalid_heading("<h2>A</h2><h1>B</h1>") == 1

    def test_invalid_heading_single(self):
        assert invalid_heading("<h1>A</h1>") == 0
        assert invalid_heading("") == 0

    def test_invalid_heading_starts_with_h2(self):
        assert invalid_heading("<h2>A</h2>") == 1

    def test_invalid_heading_starts_with_h3(self):
        assert invalid_heading("<h3>A</h3>") == 1

    def test_valid_incremental_headings(self):
        assert invalid_heading("<h1>A</h1><h2>B</h2><h3>C</h3>") == 0

    def test_invalid_heading_double_h1_then_skip(self):
        assert invalid_heading("<h1>A</h1><h1>B</h1><h3>C</h3>") == 1


class TestExtractFeatures:
    """Testes para a função agregadora extract_features."""

    def test_returns_all_features(self):
        html = '<img src="x.png" alt="X">'
        features = extract_features(html)
        assert set(features.keys()) == set(FEATURE_COLUMNS)
        assert len(features) == len(FEATURE_COLUMNS)

    def test_values_are_ints(self):
        features = extract_features('<img src="x.png">')
        for v in features.values():
            assert isinstance(v, int)
            assert v >= 0

    def test_alt_image(self):
        features = extract_features('<img src="x.png" alt="Foto">')
        assert features["has_img"] == 1
        assert features["has_alt"] == 1
        assert "action" not in features  # action não está nas features

    def test_button_with_aria(self):
        features = extract_features('<button aria-label="OK">X</button>')
        assert features["has_button"] == 1
        assert features["has_aria"] == 1

    def test_complex_html(self):
        html = '<form><input aria-label="Nome"><button>Enviar</button></form>'
        features = extract_features(html)
        assert features["has_form"] == 1
        assert features["has_aria"] == 1
        assert features["has_button"] == 1


# =====================================================================
# Dataset sintético
# =====================================================================


class TestSyntheticDataset:
    """Testes do gerador sintético."""

    @pytest.fixture(scope="class")
    def sample_df(self):
        """Gera um dataset pequeno para testes."""
        from dataset.synthetic.dataset_generator import generate_dataset

        return generate_dataset(samples=400, seed=42)

    def test_shape(self, sample_df):
        assert sample_df.shape[0] == 400

    def test_columns(self, sample_df):
        from src.config import DATASET_COLUMNS

        assert set(sample_df.columns) == set(DATASET_COLUMNS)

    def test_balanced(self, sample_df):
        counts = sample_df["action"].value_counts()
        assert len(counts) == 4
        # Tolerância: todas as classes devem ter pelo menos 90 amostras em 400
        assert (counts >= 90).all()

    def test_actions(self, sample_df):
        assert set(sample_df["action"].unique()).issubset(set(ACTION_CLASSES))

    def test_profile(self, sample_df):
        assert (sample_df["profile"] == "VISUAL").all()

    def test_no_nan(self, sample_df):
        assert not sample_df.isna().any().any()

    def test_features_consistent_with_html(self, sample_df):
        # has_img == 1 → HTML deve conter "<img"
        with_img = sample_df[sample_df["has_img"] == 1]
        if len(with_img) > 0:
            assert with_img["html"].str.contains("<img", case=False).all()

    def test_id_unique(self, sample_df):
        assert sample_df["id"].nunique() == len(sample_df)

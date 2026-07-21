# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_dataset_builder.py
# Descrição: Testes unitários do DatasetBuilder.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dataset.builder import DatasetBuilder


class TestDatasetBuilder:
    """Testes para os modos de geração do DatasetBuilder."""

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            DatasetBuilder(mode="INVALID_MODE")

    def test_synthetic_only_mode(self, tmp_path):
        csv_file = tmp_path / "test_dataset.csv"
        parquet_file = tmp_path / "test_dataset.parquet"

        builder = DatasetBuilder(mode="SYNTHETIC_ONLY")
        df = builder.build_dataset(
            num_synthetic_samples=100,
            csv_path=csv_file,
            parquet_path=parquet_file,
        )
        assert len(df) == 100
        assert csv_file.exists()
        assert "has_select" in df.columns
        assert "wcag_violations" in df.columns

    def test_real_only_mode(self, tmp_path):
        csv_file = tmp_path / "test_real.csv"
        parquet_file = tmp_path / "test_real.parquet"

        builder = DatasetBuilder(mode="REAL_ONLY")
        df = builder.build_dataset(
            csv_path=csv_file,
            parquet_path=parquet_file,
        )
        assert len(df) > 0
        assert (df["source_type"] == "REAL_MOODLE").all()
        assert csv_file.exists()

    def test_hybrid_mode(self, tmp_path):
        csv_file = tmp_path / "test_hybrid.csv"
        parquet_file = tmp_path / "test_hybrid.parquet"

        builder = DatasetBuilder(mode="HYBRID")
        df = builder.build_dataset(
            num_synthetic_samples=52,
            csv_path=csv_file,
            parquet_path=parquet_file,
        )
        assert len(df) > 50
        assert set(df["source_type"].unique()).issubset({"REAL_MOODLE", "SYNTHETIC"})
        assert csv_file.exists()

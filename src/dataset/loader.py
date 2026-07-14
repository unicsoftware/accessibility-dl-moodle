# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/dataset/loader.py
# Descrição: Carregamento de CSVs do dataset.
# =====================================================================
"""
Módulo de carregamento de dados.

Fornece funções para ler datasets brutos e processados a partir do
diretório `dataset/`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

from src.config import (
    PROCESSED_DIR,
    RAW_DATASET_FILE,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
)


def load_raw_dataset(path: Union[str, Path] = RAW_DATASET_FILE) -> pd.DataFrame:
    """Carrega o dataset bruto.

    Args:
        path: caminho do CSV.

    Returns:
        DataFrame com o dataset completo.
    """
    return pd.read_csv(path)


def load_train(path: Union[str, Path] = TRAIN_FILE) -> pd.DataFrame:
    """Carrega o conjunto de treino."""
    return pd.read_csv(path)


def load_validation(path: Union[str, Path] = VAL_FILE) -> pd.DataFrame:
    """Carrega o conjunto de validação."""
    return pd.read_csv(path)


def load_test(path: Union[str, Path] = TEST_FILE) -> pd.DataFrame:
    """Carrega o conjunto de teste."""
    return pd.read_csv(path)


def load_splits(
    train_path: Union[str, Path] = TRAIN_FILE,
    val_path: Union[str, Path] = VAL_FILE,
    test_path: Union[str, Path] = TEST_FILE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega os três splits (treino, validação, teste).

    Returns:
        Tupla (train_df, val_df, test_df).
    """
    return load_train(train_path), load_validation(val_path), load_test(test_path)


def ensure_processed_dir() -> None:
    """Garante que o diretório processed/ existe."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

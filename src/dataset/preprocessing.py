# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/dataset/preprocessing.py
# Descrição: Limpeza, normalização e codificação.
# =====================================================================
"""
Módulo de pré-processamento.

Implementa:
- Remoção de duplicatas
- Tratamento de valores faltantes
- Normalização de features numéricas (StandardScaler)
- Codificação de classes (LabelEncoder)
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler

from src.config import ACTION_CLASSES, FEATURE_COLUMNS


# =====================================================================
# Limpeza
# =====================================================================


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove registros duplicados."""
    before = len(df)
    df_clean = df.drop_duplicates(subset="html", keep="first").reset_index(drop=True)
    after = len(df_clean)
    if before != after:
        print(f"[INFO] {before - after} duplicatas removidas.")
    return df_clean


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Trata valores faltantes.

    Estratégia:
    - Features numéricas: preenchidas com 0 (ausência de tag/feature).
    - Coluna 'html': preenchida com string vazia.
    - Coluna 'action': linhas com NaN são descartadas.
    """
    df = df.copy()
    for col in FEATURE_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            df[col] = 0
    if "html" in df.columns:
        df["html"] = df["html"].fillna("")
    if "action" in df.columns:
        df = df.dropna(subset=["action"])
    return df.reset_index(drop=True)


# =====================================================================
# Codificação
# =====================================================================


def encode_labels(y: pd.Series) -> Tuple[np.ndarray, LabelEncoder]:
    """Codifica rótulos categóricos em inteiros.

    Returns:
        Tupla (y_encoded, encoder).
    """
    le = LabelEncoder()
    le.fit(ACTION_CLASSES)  # garante ordem fixa
    y_encoded = le.transform(y)
    return y_encoded, le


def decode_labels(y: np.ndarray, encoder: LabelEncoder) -> list[str]:
    """Decodifica rótulos inteiros em strings."""
    return encoder.inverse_transform(y).tolist()


# =====================================================================
# Normalização
# =====================================================================


def normalize_features(
    X: pd.DataFrame,
    scaler: StandardScaler | None = None,
    fit: bool = True,
) -> Tuple[np.ndarray, StandardScaler]:
    """Normaliza features numéricas com StandardScaler.

    Args:
        X: DataFrame com as features.
        scaler: scaler pré-treinado (opcional).
        fit: se True, ajusta o scaler aos dados.

    Returns:
        Tupla (X_normalizado, scaler).
    """
    if scaler is None:
        scaler = StandardScaler()

    if fit:
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = scaler.transform(X)

    return X_scaled, scaler


# =====================================================================
# Pipeline completo
# =====================================================================


def preprocess_pipeline(
    df: pd.DataFrame,
    scaler: StandardScaler | None = None,
    fit: bool = True,
) -> Tuple[np.ndarray, np.ndarray, StandardScaler, LabelEncoder]:
    """Pipeline completo: limpeza + extração + normalização + codificação.

    Args:
        df: DataFrame de entrada.
        scaler: scaler pré-treinado.
        fit: se True, ajusta o scaler.

    Returns:
        Tupla (X, y, scaler, label_encoder).
    """
    df = remove_duplicates(df)
    df = handle_missing_values(df)

    X = df[FEATURE_COLUMNS].astype(int)
    y, le = encode_labels(df["action"])

    X_scaled, scaler = normalize_features(X, scaler=scaler, fit=fit)

    return X_scaled, y, scaler, le

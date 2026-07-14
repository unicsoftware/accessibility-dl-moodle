# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/dataset/split.py
# Descrição: Divisão treino/validação/teste estratificada.
# =====================================================================
"""
Módulo de divisão dos dados.

Implementa split estratificado em 70/15/15 com seed fixa.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import (
    PROCESSED_DIR,
    RANDOM_SEED,
    TEST_SIZE,
    TRAIN_FILE,
    TRAIN_SIZE,
    VAL_FILE,
    VAL_SIZE,
    TEST_FILE,
)


def split_dataset(
    df: pd.DataFrame,
    train_size: float = TRAIN_SIZE,
    val_size: float = VAL_SIZE,
    test_size: float = TEST_SIZE,
    seed: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Divide o dataset em treino, validação e teste de forma estratificada.

    Args:
        df: DataFrame completo.
        train_size: proporção de treino (0..1).
        val_size: proporção de validação (0..1).
        test_size: proporção de teste (0..1).
        seed: seed do split.

    Returns:
        Tupla (train_df, val_df, test_df).

    Raises:
        ValueError: se as proporções não somarem 1.0.
    """
    total = train_size + val_size + test_size
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Soma das proporções deve ser 1.0 (recebido: {total}).")

    # 1ª divisão: treino vs. (validação+teste)
    train_df, temp_df = train_test_split(
        df,
        test_size=(1.0 - train_size),
        stratify=df["action"],
        random_state=seed,
    )

    # 2ª divisão: validação vs. teste
    relative_test = test_size / (val_size + test_size)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test,
        stratify=temp_df["action"],
        random_state=seed,
    )

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    print(f"[INFO] Split: train={len(train_df)} | val={len(val_df)} | test={len(test_df)}")
    return train_df, val_df, test_df


def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    out_dir: Union[str, Path] = PROCESSED_DIR,
) -> None:
    """Persiste os splits em CSV."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(out_dir / "train.csv", index=False, encoding="utf-8")
    val_df.to_csv(out_dir / "validation.csv", index=False, encoding="utf-8")
    test_df.to_csv(out_dir / "test.csv", index=False, encoding="utf-8")
    print(f"[INFO] Splits salvos em {out_dir}")


def load_and_split(
    df: pd.DataFrame,
    out_dir: Union[str, Path] = PROCESSED_DIR,
    seed: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Atalho: divide e salva."""
    train_df, val_df, test_df = split_dataset(df, seed=seed)
    save_splits(train_df, val_df, test_df, out_dir=out_dir)
    return train_df, val_df, test_df


if __name__ == "__main__":
    import argparse
    from src.config import RAW_DATASET_FILE

    parser = argparse.ArgumentParser(description="Divide o dataset bruto em treino, validação e teste.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(RAW_DATASET_FILE),
        help="Caminho do CSV de entrada.",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(PROCESSED_DIR),
        help="Diretório de saída para os splits.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Seed do split.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Arquivo de entrada não encontrado: {input_path}")
        sys.exit(1)

    print(f"[INFO] Carregando dataset de {input_path}...")
    df = pd.read_csv(input_path)
    load_and_split(df, out_dir=args.out_dir, seed=args.seed)


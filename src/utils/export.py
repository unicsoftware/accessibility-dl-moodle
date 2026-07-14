# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/utils/export.py
# Descrição: Funções utilitárias para exportação de artefatos.
# =====================================================================
"""
Módulo de exportação.

Fornece funções para serializar DataFrames, métricas, modelos e
metadados de execução em formatos padronizados.
"""

from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import RANDOM_SEED


def export_dataframe(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    """Exporta um DataFrame para CSV.

    Args:
        df: DataFrame a ser exportado.
        path: caminho do arquivo de saída.
        index: incluir índice no CSV.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index, encoding="utf-8")


def export_model(model: Any, path: Path) -> None:
    """Serializa um modelo em disco.

    Args:
        model: modelo a ser serializado.
        path: caminho de saída.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: Path) -> Any:
    """Carrega um modelo serializado.

    Args:
        path: caminho do arquivo.

    Returns:
        Modelo carregado.
    """
    return joblib.load(path)


def export_metrics(metrics: dict, path: Path) -> None:
    """Exporta métricas em CSV (a partir de um dict).

    Args:
        metrics: dicionário {modelo: {métrica: valor}}.
        path: caminho de saída.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(metrics).T.reset_index().rename(columns={"index": "model"})
    df.to_csv(path, index=False, encoding="utf-8")


def export_metadata(config: dict, path: Path) -> None:
    """Exporta metadados da execução (config + timestamp + seed).

    Args:
        config: dicionário de configuração.
        path: caminho de saída.
    """
    metadata = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "seed": RANDOM_SEED,
        "config": {k: str(v) if isinstance(v, Path) else v for k, v in config.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)


def file_hash(path: Path, algo: str = "sha256") -> str:
    """Calcula o hash de um arquivo."""
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

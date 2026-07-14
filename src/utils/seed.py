# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/utils/seed.py
# Descrição: Fixação de seeds para reprodutibilidade.
# =====================================================================
"""
Módulo de reprodutibilidade.

Garante que todos os geradores aleatórios (Python, NumPy, PyTorch)
sejam inicializados com a mesma seed.
"""

from __future__ import annotations

import os
import random

import numpy as np

from src.config import RANDOM_SEED


def set_seed(seed: int = RANDOM_SEED) -> None:
    """Fixa seeds em Python, NumPy e PyTorch.

    Args:
        seed: valor da seed.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

        # Modo determinístico (mais lento, mas reprodutível)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        torch.use_deterministic_algorithms(True, warn_only=True)
    except ImportError:
        # PyTorch não está instalado; segue sem ele.
        pass


def get_seed() -> int:
    """Retorna a seed padrão do projeto."""
    return RANDOM_SEED

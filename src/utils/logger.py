# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/utils/logger.py
# Descrição: Configuração centralizada de logging.
# =====================================================================
"""
Módulo de logging.

Fornece funções utilitárias para inicializar e obter loggers
em todo o projeto, garantindo formato consistente.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _logger

from src.config import LOG_FORMAT, LOG_LEVEL, RESULTS_DIR


def configure_logger(
    level: str = LOG_LEVEL,
    log_file: Optional[Path] = None,
) -> None:
    """Configura o logger global (Loguru).

    Args:
        level: nível de log (DEBUG, INFO, WARNING, ERROR).
        log_file: caminho opcional para arquivo de log.
    """
    _logger.remove()
    _logger.add(sys.stderr, format=LOG_FORMAT, level=level, colorize=True)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        _logger.add(
            log_file,
            format=LOG_FORMAT,
            level=level,
            rotation="10 MB",
            retention="30 days",
            encoding="utf-8",
        )


def get_logger(name: str = "accessibility-dl-moodle"):
    """Retorna o logger configurado.

    Args:
        name: nome do módulo solicitante (apenas para identificação).

    Returns:
        Instância do logger Loguru.
    """
    return _logger.bind(module=name)


# Configuração inicial ao importar o módulo
configure_logger(log_file=RESULTS_DIR / "run.log")

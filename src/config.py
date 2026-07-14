# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/config.py
# Descrição: Configurações globais do projeto.
# =====================================================================
"""
Configurações globais do projeto.

Este módulo centraliza constantes utilizadas em todo o pipeline.
Qualquer ajuste de hiperparâmetro, caminho de arquivo ou seed deve
ser feito aqui para garantir reprodutibilidade.
"""

from __future__ import annotations

from pathlib import Path

# =====================================================================
# Diretórios
# =====================================================================

# Caminho raiz do projeto (parent do diretório 'src')
ROOT_DIR: Path = Path(__file__).resolve().parents[1]

DATA_DIR: Path = ROOT_DIR / "dataset"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
SYNTHETIC_DIR: Path = DATA_DIR / "synthetic"
MODELS_DIR: Path = ROOT_DIR / "models"
RESULTS_DIR: Path = ROOT_DIR / "results"
NOTEBOOKS_DIR: Path = ROOT_DIR / "notebooks"
DOCS_DIR: Path = ROOT_DIR / "docs"

# =====================================================================
# Arquivos
# =====================================================================

RAW_DATASET_FILE: Path = RAW_DIR / "accessibility_dataset.csv"
TRAIN_FILE: Path = PROCESSED_DIR / "train.csv"
VAL_FILE: Path = PROCESSED_DIR / "validation.csv"
TEST_FILE: Path = PROCESSED_DIR / "test.csv"

LOGISTIC_MODEL_FILE: Path = MODELS_DIR / "logistic_model.pkl"
MLP_MODEL_FILE: Path = MODELS_DIR / "mlp_model.pt"

METRICS_FILE: Path = RESULTS_DIR / "metrics.csv"
PREDICTIONS_FILE: Path = RESULTS_DIR / "predictions.csv"
CLASSIFICATION_REPORT_FILE: Path = RESULTS_DIR / "classification_report.txt"
CONFUSION_MATRIX_FILE: Path = RESULTS_DIR / "confusion_matrix.png"
LEARNING_CURVE_FILE: Path = RESULTS_DIR / "learning_curve.png"

# =====================================================================
# Reprodutibilidade
# =====================================================================

RANDOM_SEED: int = 42

# =====================================================================
# Classes do problema
# =====================================================================

# Perfis de acessibilidade suportados (apenas VISUAL nesta versão)
PROFILES: list[str] = ["VISUAL", "AUDITIVO", "MOTOR", "COGNITIVO"]
ACTIVE_PROFILES: list[str] = ["VISUAL"]

# Classes de saída (ações de acessibilidade recomendadas)
ACTION_CLASSES: list[str] = [
    "ADD_ALT",
    "ADD_ARIA",
    "FIX_HEADING",
    "NO_ACTION",
]
NUM_CLASSES: int = len(ACTION_CLASSES)

# =====================================================================
# Schema do dataset
# =====================================================================

DATASET_COLUMNS: list[str] = [
    "id",
    "profile",
    "html",
    "has_img",
    "has_alt",
    "has_aria",
    "has_button",
    "has_form",
    "has_link",
    "has_table",
    "heading_count",
    "invalid_heading",
    "text_length",
    "tag_count",
    "action",
]

# Features de entrada (X) — 11 features estruturais
FEATURE_COLUMNS: list[str] = [
    "has_img",
    "has_alt",
    "has_aria",
    "has_button",
    "has_form",
    "has_link",
    "has_table",
    "heading_count",
    "invalid_heading",
    "text_length",
    "tag_count",
]
NUM_FEATURES: int = len(FEATURE_COLUMNS)

# =====================================================================
# Divisão dos dados
# =====================================================================

TRAIN_SIZE: float = 0.70
VAL_SIZE: float = 0.15
TEST_SIZE: float = 0.15

# =====================================================================
# Hiperparâmetros — Regressão Logística
# =====================================================================

LOGISTIC_MAX_ITER: int = 1000
LOGISTIC_C: float = 1.0
LOGISTIC_SOLVER: str = "lbfgs"

# =====================================================================
# Hiperparâmetros — MLP (Multilayer Perceptron)
# =====================================================================

MLP_HIDDEN_LAYERS: tuple[int, ...] = (64, 32)
MLP_DROPOUT: float = 0.3
MLP_LEARNING_RATE: float = 1e-3
MLP_BATCH_SIZE: int = 64
MLP_EPOCHS: int = 100
MLP_PATIENCE: int = 10  # early stopping
MLP_WEIGHT_DECAY: float = 1e-4

# =====================================================================
# Logging
# =====================================================================

LOG_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
    "<level>{message}</level>"
)
LOG_LEVEL: str = "INFO"

# =====================================================================
# Tamanho do dataset sintético
# =====================================================================

DATASET_TOTAL_SAMPLES: int = 20_000
DATASET_SAMPLES_PER_CLASS: int = DATASET_TOTAL_SAMPLES // NUM_CLASSES

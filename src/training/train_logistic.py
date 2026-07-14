# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/training/train_logistic.py
# Descrição: Treinamento do baseline de Regressão Logística.
# =====================================================================
"""
Script de treinamento da Regressão Logística.

Uso:
    python src/training/train_logistic.py [--seed 42]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    LOGISTIC_MODEL_FILE,
    METRICS_FILE,
    NUM_FEATURES,
    RANDOM_SEED,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
)
from src.dataset.loader import load_splits  # noqa: E402
from src.dataset.preprocessing import preprocess_pipeline  # noqa: E402
from src.evaluation.metrics import compute_classification_metrics  # noqa: E402
from src.models.logistic_regression import LogisticAccessibilityModel  # noqa: E402
from src.utils.export import export_dataframe, export_metrics, export_metadata  # noqa: E402
from src.utils.seed import set_seed  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treina o modelo Logistic Regression.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    print(f"[INFO] Carregando splits (seed={args.seed})...")
    train_df, val_df, test_df = load_splits(TRAIN_FILE, VAL_FILE, TEST_FILE)

    # Pipeline de pré-processamento
    X_train, y_train, scaler, le = preprocess_pipeline(train_df, fit=True)
    X_val, y_val, _, _ = preprocess_pipeline(val_df, scaler=scaler, fit=False)
    X_test, y_test, _, _ = preprocess_pipeline(test_df, scaler=scaler, fit=False)

    print(f"[INFO] Shapes: X_train={X_train.shape} | X_val={X_val.shape} | X_test={X_test.shape}")

    # Treinamento
    model = LogisticAccessibilityModel(random_state=args.seed)
    model.fit(X_train, y_train)
    print("[INFO] Modelo treinado.")

    # Avaliação
    metrics = {
        "train": compute_classification_metrics(y_train, model.predict(X_train)),
        "val": compute_classification_metrics(y_val, model.predict(X_val)),
        "test": compute_classification_metrics(y_test, model.predict(X_test)),
    }

    print("\n[RESULT] Métricas (test):")
    for k, v in metrics["test"].items():
        print(f"  {k}: {v:.4f}")

    # Persistência
    model.save(LOGISTIC_MODEL_FILE)
    print(f"[INFO] Modelo salvo em {LOGISTIC_MODEL_FILE}")

    # Salva predições no conjunto de teste
    y_pred = model.predict(X_test)
    test_df_clean = test_df.drop_duplicates(subset="html", keep="first").reset_index(drop=True)
    predictions_df = pd.DataFrame({
        "html": test_df_clean["html"].values,
        "y_true": le.inverse_transform(y_test),
        "y_pred": le.inverse_transform(y_pred),
    })
    export_dataframe(predictions_df, ROOT / "results" / "predictions_logistic.csv")

    # Salva métricas e metadados
    export_metrics({"logistic": metrics["test"]}, METRICS_FILE)
    export_metadata(
        {
            "model": "logistic_regression",
            "seed": args.seed,
            "n_features": NUM_FEATURES,
            "train_size": len(train_df),
            "val_size": len(val_df),
            "test_size": len(test_df),
        },
        ROOT / "results" / "metadata_logistic.json",
    )

    print(f"[INFO] Métricas salvas em {METRICS_FILE}")


if __name__ == "__main__":
    main()

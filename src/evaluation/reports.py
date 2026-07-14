# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/evaluation/reports.py
# Descrição: Geração consolidada de relatórios.
# =====================================================================
"""
Módulo de relatórios.

Orquestra a geração de:
- metrics.csv
- classification_report.txt
- confusion_matrix.png
- predictions.csv (consolidado)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    ACTION_CLASSES,
    CLASSIFICATION_REPORT_FILE,
    CONFUSION_MATRIX_FILE,
    LOGISTIC_MODEL_FILE,
    METRICS_FILE,
    MLP_MODEL_FILE,
    PREDICTIONS_FILE,
    TEST_FILE,
)
from src.dataset.loader import load_test  # noqa: E402
from src.dataset.preprocessing import preprocess_pipeline  # noqa: E402
from src.evaluation.confusion_matrix import plot_confusion_matrix  # noqa: E402
from src.evaluation.metrics import compute_classification_metrics  # noqa: E402
from src.models.logistic_regression import LogisticAccessibilityModel  # noqa: E402
from src.models.mlp import MLPAccessibilityModel  # noqa: E402
from src.utils.export import export_dataframe, export_metrics  # noqa: E402


def main() -> None:
    print("[INFO] Carregando modelos treinados e conjunto de teste...")

    test_df = load_test(TEST_FILE)
    X_test, y_test, scaler, le = preprocess_pipeline(test_df, fit=True)
    class_names = le.classes_.tolist()

    results: dict[str, dict] = {}
    predictions: dict[str, np.ndarray] = {}

    # Logistic Regression
    if LOGISTIC_MODEL_FILE.exists():
        print(f"[INFO] Carregando {LOGISTIC_MODEL_FILE}...")
        log_model = LogisticAccessibilityModel.load(LOGISTIC_MODEL_FILE)
        y_pred_log = log_model.predict(X_test)
        y_pred_log_str = le.inverse_transform(y_pred_log)
        results["logistic_regression"] = compute_classification_metrics(y_test, y_pred_log)
        predictions["logistic_regression"] = y_pred_log_str
    else:
        print(f"[WARN] Modelo logistic não encontrado em {LOGISTIC_MODEL_FILE}")

    # MLP
    if MLP_MODEL_FILE.exists():
        print(f"[INFO] Carregando {MLP_MODEL_FILE}...")
        mlp_model = MLPAccessibilityModel.load(MLP_MODEL_FILE)
        y_pred_mlp = mlp_model.predict(X_test)
        y_pred_mlp_str = le.inverse_transform(y_pred_mlp)
        results["mlp"] = compute_classification_metrics(y_test, y_pred_mlp)
        predictions["mlp"] = y_pred_mlp_str
    else:
        print(f"[WARN] Modelo MLP não encontrado em {MLP_MODEL_FILE}")

    if not results:
        print("[ERROR] Nenhum modelo encontrado. Execute 'make train' primeiro.")
        return

    # Métricas
    export_metrics(results, METRICS_FILE)
    print(f"[INFO] Métricas consolidadas em {METRICS_FILE}")

    # Classification report (do MLP, preferencialmente)
    if "mlp" in predictions:
        report_target = "mlp"
    else:
        report_target = next(iter(predictions))

    cls_report = classification_report(
        y_test,
        le.transform(predictions[report_target]),
        target_names=class_names,
        zero_division=0,
        digits=4,
    )
    CLASSIFICATION_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLASSIFICATION_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Classification Report — modelo: {report_target}\n")
        f.write("=" * 60 + "\n")
        f.write(cls_report)
    print(f"[INFO] Classification report salvo em {CLASSIFICATION_REPORT_FILE}")

    # Matriz de confusão (do MLP)
    if "mlp" in predictions:
        plot_confusion_matrix(
            y_test,
            le.transform(predictions["mlp"]),
            class_names=class_names,
            path=CONFUSION_MATRIX_FILE,
            normalize=True,
            title="Matriz de Confusão — MLP",
        )

    # Predições consolidadas
    test_df_clean = test_df.drop_duplicates(subset="html", keep="first").reset_index(drop=True)
    pred_df = pd.DataFrame({
        "html": test_df_clean["html"].values,
        "y_true": le.inverse_transform(y_test),
        **{f"y_pred_{k}": v for k, v in predictions.items()},
    })
    export_dataframe(pred_df, PREDICTIONS_FILE)
    print(f"[INFO] Predições consolidadas em {PREDICTIONS_FILE}")

    # Sumário
    print("\n[RESULT] Sumário das métricas:")
    for model_name, m in results.items():
        print(f"\n  {model_name}:")
        for k, v in m.items():
            print(f"    {k}: {v:.4f}")


if __name__ == "__main__":
    main()

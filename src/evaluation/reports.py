# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/evaluation/reports.py
# Descrição: Geração consolidada de relatórios e comparação inter-modelos / axe-core.
# =====================================================================
"""
Módulo de relatórios.

Orquestra a geração de:
- metrics.csv
- classification_report.txt
- confusion_matrix.png
- wcag_evaluation.csv
- predictions.csv (consolidado com Logistic Regression, Gradient Boosting e MLP)
"""

from __future__ import annotations

import json
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
    GB_MODEL_FILE,
    LOGISTIC_MODEL_FILE,
    METRICS_FILE,
    MLP_MODEL_FILE,
    PREDICTIONS_FILE,
    TEST_FILE,
    WCAG_EVALUATION_FILE,
)
from src.dataset.loader import load_test  # noqa: E402
from src.dataset.preprocessing import preprocess_pipeline  # noqa: E402
from src.evaluation.confusion_matrix import plot_confusion_matrix  # noqa: E402
from src.evaluation.metrics import (  # noqa: E402
    compute_classification_metrics,
    compute_wcag_metrics,
)
from src.models.gradient_boosting import GradientBoostingAccessibilityModel  # noqa: E402
from src.models.logistic_regression import LogisticAccessibilityModel  # noqa: E402
from src.models.mlp import MLPAccessibilityModel  # noqa: E402
from src.utils.export import export_dataframe, export_metrics  # noqa: E402


def main() -> None:
    print("[INFO] Carregando modelos treinados (Logistic, Gradient Boosting, MLP) e conjunto de teste...")

    test_df = load_test(TEST_FILE)
    X_test, y_test, scaler, le = preprocess_pipeline(test_df, fit=True)
    class_names = le.classes_.tolist()

    results: dict[str, dict] = {}
    predictions: dict[str, np.ndarray] = {}

    # 1. Logistic Regression
    if LOGISTIC_MODEL_FILE.exists():
        print(f"[INFO] Carregando {LOGISTIC_MODEL_FILE}...")
        log_model = LogisticAccessibilityModel.load(LOGISTIC_MODEL_FILE)
        y_pred_log = log_model.predict(X_test)
        y_pred_log_str = le.inverse_transform(y_pred_log)
        results["logistic_regression"] = compute_classification_metrics(y_test, y_pred_log)
        predictions["logistic_regression"] = y_pred_log_str
    else:
        print(f"[WARN] Modelo logistic não encontrado em {LOGISTIC_MODEL_FILE}")

    # 2. Gradient Boosting
    if GB_MODEL_FILE.exists():
        print(f"[INFO] Carregando {GB_MODEL_FILE}...")
        gb_model = GradientBoostingAccessibilityModel.load(GB_MODEL_FILE)
        y_pred_gb = gb_model.predict(X_test)
        y_pred_gb_str = le.inverse_transform(y_pred_gb)
        results["gradient_boosting"] = compute_classification_metrics(y_test, y_pred_gb)
        predictions["gradient_boosting"] = y_pred_gb_str
    else:
        print(f"[WARN] Modelo Gradient Boosting não encontrado em {GB_MODEL_FILE}")

    # 3. MLP
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
        print("[ERROR] Nenhum modelo encontrado. Execute os scripts de treinamento primeiro.")
        return

    # Métricas globais consolidadas
    export_metrics(results, METRICS_FILE)
    print(f"[INFO] Métricas consolidadas salvas em {METRICS_FILE}")

    # Classification report (do MLP ou do melhor disponível)
    report_target = "mlp" if "mlp" in predictions else next(iter(predictions))
    cls_report = classification_report(
        y_test,
        le.transform(predictions[report_target]),
        labels=list(range(len(class_names))),
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

    # Matriz de confusão (do modelo selecionado)
    plot_confusion_matrix(
        y_test,
        le.transform(predictions[report_target]),
        class_names=class_names,
        path=CONFUSION_MATRIX_FILE,
        normalize=True,
        title=f"Matriz de Confusão — {report_target}",
    )

    # Avaliação por Critério WCAG (Weak Supervision vs Modelo)
    test_df_clean = test_df.drop_duplicates(subset="html", keep="first").reset_index(drop=True)
    if "wcag_violations" in test_df_clean.columns:
        y_true_wcag = [
            json.loads(v) if isinstance(v, str) and v.startswith("[") else []
            for v in test_df_clean["wcag_violations"].values
        ]
        # Mapeia predições das ações para critérios WCAG simplificados
        wcag_map_action = {
            "ADD_ALT": ["WCAG_1_1_1"],
            "FIX_HEADING": ["WCAG_1_3_1"],
            "ADD_ARIA": ["WCAG_4_1_2"],
            "NO_ACTION": [],
        }
        y_pred_wcag = [
            wcag_map_action.get(act, []) for act in predictions[report_target]
        ]
        wcag_metrics = compute_wcag_metrics(y_true_wcag, y_pred_wcag)
        wcag_df = pd.DataFrame.from_dict(wcag_metrics, orient="index")
        export_dataframe(wcag_df, WCAG_EVALUATION_FILE)
        print(f"[INFO] Avaliação por critério WCAG salva em {WCAG_EVALUATION_FILE}")

    # Predições consolidadas
    test_df_clean = test_df.drop_duplicates(subset="html", keep="first").reset_index(drop=True)
    pred_dict = {
        "html": test_df_clean["html"].values if len(test_df_clean) == len(y_test) else test_df["html"].values,
        "y_true": le.inverse_transform(y_test),
    }
    for model_k, model_preds in predictions.items():
        pred_dict[f"y_pred_{model_k}"] = model_preds

    pred_df = pd.DataFrame(pred_dict)
    export_dataframe(pred_df, PREDICTIONS_FILE)
    print(f"[INFO] Predições consolidadas em {PREDICTIONS_FILE}")

    # Sumário no terminal
    print("\n[RESULT] Sumário de comparação entre modelos:")
    for model_name, m in results.items():
        print(f"\n  {model_name}:")
        for k, v in m.items():
            print(f"    {k}: {v:.4f}")


if __name__ == "__main__":
    main()

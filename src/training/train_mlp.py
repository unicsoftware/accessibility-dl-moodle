# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/training/train_mlp.py
# Descrição: Treinamento do modelo MLP (PyTorch).
# =====================================================================
"""
Script de treinamento do MLP.

Uso:
    python src/training/train_mlp.py [--seed 42] [--epochs 100]
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
    METRICS_FILE,
    MLP_BATCH_SIZE,
    MLP_EPOCHS,
    MLP_MODEL_FILE,
    MLP_PATIENCE,
    NUM_FEATURES,
    RANDOM_SEED,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
)
from src.dataset.loader import load_splits  # noqa: E402
from src.dataset.preprocessing import preprocess_pipeline  # noqa: E402
from src.evaluation.metrics import compute_classification_metrics  # noqa: E402
from src.models.mlp import MLPAccessibilityModel  # noqa: E402
from src.utils.export import export_dataframe, export_metrics, export_metadata  # noqa: E402
from src.utils.seed import set_seed  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treina o modelo MLP.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--epochs", type=int, default=MLP_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=MLP_BATCH_SIZE)
    parser.add_argument("--patience", type=int, default=MLP_PATIENCE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    print(f"[INFO] Carregando splits (seed={args.seed})...")
    train_df, val_df, test_df = load_splits(TRAIN_FILE, VAL_FILE, TEST_FILE)

    X_train, y_train, scaler, le = preprocess_pipeline(train_df, fit=True)
    X_val, y_val, _, _ = preprocess_pipeline(val_df, scaler=scaler, fit=False)
    X_test, y_test, _, _ = preprocess_pipeline(test_df, scaler=scaler, fit=False)

    print(f"[INFO] Shapes: X_train={X_train.shape} | X_val={X_val.shape} | X_test={X_test.shape}")

    model = MLPAccessibilityModel(input_dim=NUM_FEATURES)

    history = model.fit(
        X_train, y_train,
        X_val=X_val, y_val=y_val,
        epochs=args.epochs,
        batch_size=args.batch_size,
        patience=args.patience,
    )

    # Avaliação
    metrics = {
        "train": compute_classification_metrics(y_train, model.predict(X_train)),
        "val": compute_classification_metrics(y_val, model.predict(X_val)),
        "test": compute_classification_metrics(y_test, model.predict(X_test)),
    }

    print("\n[RESULT] Métricas (test):")
    for k, v in metrics["test"].items():
        print(f"  {k}: {v:.4f}")

    model.save(MLP_MODEL_FILE)
    print(f"[INFO] Modelo salvo em {MLP_MODEL_FILE}")

    # Predições
    y_pred = model.predict(X_test)
    test_df_clean = test_df.drop_duplicates(subset="html", keep="first").reset_index(drop=True)
    predictions_df = pd.DataFrame({
        "html": test_df_clean["html"].values,
        "y_true": le.inverse_transform(y_test),
        "y_pred": le.inverse_transform(y_pred),
    })
    export_dataframe(predictions_df, ROOT / "results" / "predictions_mlp.csv")

    # Curva de aprendizado
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].plot(history["train_loss"], label="Treino")
        if history["val_loss"]:
            axes[0].plot(history["val_loss"], label="Validação")
        axes[0].set_title("Loss")
        axes[0].set_xlabel("Epoch")
        axes[0].legend()

        axes[1].plot(history["train_acc"], label="Treino")
        if history["val_acc"]:
            axes[1].plot(history["val_acc"], label="Validação")
        axes[1].set_title("Accuracy")
        axes[1].set_xlabel("Epoch")
        axes[1].legend()

        fig.tight_layout()
        learning_curve_path = ROOT / "results" / "learning_curve_mlp.png"
        fig.savefig(learning_curve_path, dpi=120)
        plt.close(fig)
        print(f"[INFO] Curva de aprendizado salva em {learning_curve_path}")
    except Exception as e:
        print(f"[WARN] Não foi possível gerar learning curve: {e}")

    # Métricas e metadados
    export_metrics({"mlp": metrics["test"]}, METRICS_FILE)
    export_metadata(
        {
            "model": "mlp",
            "seed": args.seed,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "patience": args.patience,
            "n_features": NUM_FEATURES,
            "train_size": len(train_df),
            "val_size": len(val_df),
            "test_size": len(test_df),
        },
        ROOT / "results" / "metadata_mlp.json",
    )

    print(f"[INFO] Métricas salvas em {METRICS_FILE}")


if __name__ == "__main__":
    main()

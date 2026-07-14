# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/inference/predict.py
# Descrição: Inferência para novos pares (HTML, perfil).
# =====================================================================
"""
Módulo de inferência.

Permite classificar um par (HTML, perfil) usando o modelo treinado.

Uso:
    python src/inference/predict.py \\
        --html '<img src="foto.png">' \\
        --profile VISUAL
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    ACTIVE_PROFILES,
    ACTION_CLASSES,
    LOGISTIC_MODEL_FILE,
    MLP_MODEL_FILE,
    NUM_FEATURES,
)
from src.dataset.feature_engineering import extract_features  # noqa: E402
from src.models.logistic_regression import LogisticAccessibilityModel  # noqa: E402
from src.models.mlp import MLPAccessibilityModel  # noqa: E402


# Cache local para scaler e label encoder
_scaler: Optional[object] = None
_label_encoder: Optional[object] = None


def _load_artifacts():
    """Carrega scaler e label encoder.

    Para o projeto, reutilizamos o pipeline de preprocessamento.
    Em produção, esses artefatos deveriam ser serializados separadamente.
    """
    global _scaler, _label_encoder
    if _scaler is None or _label_encoder is None:
        from src.dataset.loader import load_train
        from src.dataset.preprocessing import preprocess_pipeline

        df_train = load_train()
        _, _, scaler, le = preprocess_pipeline(df_train, fit=True)
        _scaler, _label_encoder = scaler, le
    return _scaler, _label_encoder


def predict_action(
    html: str,
    profile: str = "VISUAL",
    model_type: str = "mlp",
) -> dict:
    """Prediz a ação de acessibilidade recomendada.

    Args:
        html: trecho HTML.
        profile: perfil do usuário (sempre VISUAL nesta versão).
        model_type: 'mlp' ou 'logistic'.

    Returns:
        Dicionário com classe predita e confiança.
    """
    if profile not in ACTIVE_PROFILES:
        raise ValueError(
            f"Perfil '{profile}' não está ativo. "
            f"Perfis disponíveis: {ACTIVE_PROFILES}"
        )

    # Extrai e normaliza
    features = extract_features(html)
    scaler, le = _load_artifacts()

    feature_order = [
        "has_img", "has_alt", "has_aria", "has_button", "has_form",
        "has_link", "has_table", "heading_count", "invalid_heading",
        "text_length", "tag_count",
    ]
    x = np.array([[features[c] for c in feature_order]], dtype=float)
    x_scaled = scaler.transform(x)

    # Carrega modelo
    if model_type == "mlp":
        model = MLPAccessibilityModel.load(MLP_MODEL_FILE)
        proba = model.predict_proba(x_scaled)[0]
        pred_idx = int(np.argmax(proba))
    elif model_type == "logistic":
        model = LogisticAccessibilityModel.load(LOGISTIC_MODEL_FILE)
        proba = model.predict_proba(x_scaled)[0]
        pred_idx = int(np.argmax(proba))
    else:
        raise ValueError(f"model_type deve ser 'mlp' ou 'logistic' (recebido: {model_type})")

    pred_class = le.inverse_transform([pred_idx])[0]
    confidence = float(proba[pred_idx])

    return {
        "html": html,
        "profile": profile,
        "predicted_action": pred_class,
        "confidence": confidence,
        "probabilities": {
            le.inverse_transform([i])[0]: float(proba[i])
            for i in range(len(ACTION_CLASSES))
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prediz ação de acessibilidade.")
    parser.add_argument(
        "--html",
        type=str,
        required=True,
        help="Trecho HTML a ser classificado.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="VISUAL",
        choices=ACTIVE_PROFILES,
        help="Perfil de acessibilidade.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mlp",
        choices=["mlp", "logistic"],
        help="Modelo a ser utilizado.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = predict_action(args.html, profile=args.profile, model_type=args.model)

    print("=" * 60)
    print(f"HTML:    {result['html']}")
    print(f"Profile: {result['profile']}")
    print(f"Predicted Action: {result['predicted_action']}")
    print(f"Confidence: {result['confidence']:.4f}")
    print("Probabilities:")
    for cls, p in result["probabilities"].items():
        print(f"  {cls:12s} : {p:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()

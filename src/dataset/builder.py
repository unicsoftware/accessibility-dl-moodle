# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/dataset/builder.py
# Descrição: Construção e consolidação automatizada de datasets.
# =====================================================================
"""
Dataset Builder
===============

Camada responsável por consolidar HTML, metadados, features e rótulos
em 3 modos distintos:
- REAL_ONLY: apenas componentes HTML extraídos do Moodle.
- SYNTHETIC_ONLY: apenas HTMLs gerados sinteticamente pelo dataset_generator.py.
- HYBRID: combinação de componentes reais e sintéticos.

Gera automaticamente:
- dataset/raw/accessibility_dataset.csv
- dataset/raw/accessibility_dataset.parquet
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
import pandas as pd

from src import config
from src.dataset.feature_engineering import extract_features
from src.extractor.component_extractor import ComponentExtractor
from src.labeler.axe_labeler import AxeLabeler
from src.moodle.adapter import MoodleAdapter


class DatasetBuilder:
    """Builder responsável por orquestrar a construção e exportação dos datasets."""

    def __init__(
        self,
        mode: str = config.DEFAULT_DATASET_MODE,
        adapter: Optional[MoodleAdapter] = None,
        extractor: Optional[ComponentExtractor] = None,
        labeler: Optional[AxeLabeler] = None,
    ) -> None:
        if mode not in config.DATASET_MODES:
            raise ValueError(f"Modo inválido '{mode}'. Escolha um de {config.DATASET_MODES}")
        self.mode = mode
        self.adapter = adapter or MoodleAdapter()
        self.extractor = extractor or ComponentExtractor()
        self.labeler = labeler or AxeLabeler(use_playwright=False)

    def build_dataset(
        self,
        num_synthetic_samples: int = 1000,
        csv_path: Path = config.RAW_DATASET_FILE,
        parquet_path: Path = config.RAW_DATASET_PARQUET_FILE,
    ) -> pd.DataFrame:
        """Constrói e consolida o dataset de acordo com o modo selecionado.

        Args:
            num_synthetic_samples: Quantidade de amostras sintéticas caso o modo inclua dados sintéticos.
            csv_path: Caminho para salvar o CSV.
            parquet_path: Caminho para salvar o Parquet.

        Returns:
            DataFrame consolidado com metadados, features e rótulos.
        """
        logger.info(f"Iniciando construção do dataset no modo '{self.mode}'...")
        real_df = pd.DataFrame()
        synthetic_df = pd.DataFrame()

        if self.mode in ["REAL_ONLY", "HYBRID"]:
            real_df = self._generate_real_data()

        if self.mode in ["SYNTHETIC_ONLY", "HYBRID"]:
            synthetic_df = self._generate_synthetic_data(num_synthetic_samples)

        if self.mode == "REAL_ONLY":
            final_df = real_df
        elif self.mode == "SYNTHETIC_ONLY":
            final_df = synthetic_df
        else:  # HYBRID
            final_df = pd.concat([real_df, synthetic_df], ignore_index=True)

        if final_df.empty:
            logger.warning("Dataset gerado está vazio. Utilizando dados sintéticos de salvaguarda.")
            final_df = self._generate_synthetic_data(num_synthetic_samples)

        # Garantir reordenação consistente de colunas
        for col in config.DATASET_COLUMNS:
            if col not in final_df.columns:
                final_df[col] = 0 if "has_" in col or "count" in col else ""

        final_df = final_df[config.DATASET_COLUMNS]

        # Salvar em arquivos
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.parent.mkdir(parents=True, exist_ok=True)

        final_df.to_csv(csv_path, index=False, encoding="utf-8")
        try:
            final_df.to_parquet(parquet_path, index=False)
            logger.info(f"Dataset Parquet exportado em '{parquet_path}'.")
        except Exception as err:
            logger.warning(f"Exportação Parquet ignorada ({err}). Instale 'pyarrow' ou 'fastparquet' para exportação Parquet.")

        logger.info(f"Dataset exportado com sucesso em '{csv_path}' ({len(final_df)} registros).")
        return final_df

    def _generate_real_data(self) -> pd.DataFrame:
        """Coleta e rotula dados reais extraídos do Moodle conforme o modo configurado."""
        records: List[Dict[str, Any]] = []

        pages = self.adapter.fetch_real_pages()
        for page_data in pages:
            # 2. Fragmenta a página em componentes
            components = self.extractor.extract_components(page_data["html"], page_data)

            # 3. Executa Weak Supervision via axe-core Labeler
            for comp in components:
                label_res = self.labeler.label_component(comp["html"])
                features = extract_features(comp["html"])

                record = {
                    "id": len(records) + 1,
                    "profile": "VISUAL",
                    "html": comp["html"],
                    "component_type": comp.get("component_type", "element"),
                    "source_type": comp.get("source_type", "REAL_MOODLE"),
                    "course_id": comp.get("course_id", 101),
                    "activity_id": comp.get("activity_id", 1001),
                    "url": comp.get("url", ""),
                    "timestamp": comp.get("timestamp", ""),
                    "action": label_res["action"],
                    "wcag_violations": json.dumps(label_res["wcag_criteria"]),
                }
                record.update(features)
                records.append(record)

        return pd.DataFrame(records)

    def _generate_synthetic_data(self, samples: int) -> pd.DataFrame:
        """Gera dados sintéticos parametrizados utilizando o dataset_generator original."""
        from dataset.synthetic.dataset_generator import generate_dataset

        raw_synth = generate_dataset(samples=samples, seed=config.RANDOM_SEED)
        records: List[Dict[str, Any]] = []

        for _, row in raw_synth.iterrows():
            html = row["html"]
            features = extract_features(html)
            label_res = self.labeler.label_component(html)

            record = {
                "id": row.get("id", len(records) + 1),
                "profile": row.get("profile", "VISUAL"),
                "html": html,
                "component_type": "synthetic",
                "source_type": "SYNTHETIC",
                "course_id": 0,
                "activity_id": 0,
                "url": "http://synthetic.local",
                "timestamp": "",
                "action": row.get("action", label_res["action"]),
                "wcag_violations": json.dumps(label_res["wcag_criteria"]),
            }
            record.update(features)
            records.append(record)

        return pd.DataFrame(records)

# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/extractor/component_extractor.py
# Descrição: Extrator e fragmentador de componentes HTML.
# =====================================================================
"""
Component Extractor
===================

Camada responsável por receber páginas/conteúdos HTML extraídos do Moodle e
subdividi-los automaticamente em componentes HTML independentes.

Elementos identificados:
- img, button, input, form, table, a, select, textarea, video, audio, figure, svg, canvas.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from src import config


class ComponentExtractor:
    """Extrai e fragmenta elementos HTML independentes a partir de páginas completas."""

    SUPPORTED_TAGS: List[str] = config.COMPONENT_TAGS

    def __init__(self, target_tags: Optional[List[str]] = None) -> None:
        self.target_tags = target_tags or self.SUPPORTED_TAGS

    def extract_components(
        self,
        page_html: str,
        page_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Extrai todos os componentes HTML independentes encontrados na página.

        Args:
            page_html: HTML completo da página ou atividade.
            page_metadata: Metadados da origem fornecidos pelo MoodleAdapter.

        Returns:
            Lista de dicionários contendo os componentes fragmentados e seus metadados.
        """
        if not page_html or not page_html.strip():
            return []

        soup = BeautifulSoup(page_html, "html.parser")
        components: List[Dict[str, Any]] = []
        metadata = page_metadata or {}

        # Busca todos os elementos que correspondem aos tags suportados
        for tag_name in self.target_tags:
            elements = soup.find_all(tag_name)
            for elem in elements:
                if not isinstance(elem, Tag):
                    continue

                component_html = str(elem).strip()
                comp_id = str(uuid.uuid4())[:8]

                comp_record = {
                    "component_id": f"comp_{tag_name}_{comp_id}",
                    "component_type": tag_name,
                    "html": component_html,
                    "course_id": metadata.get("course_id", 0),
                    "activity_id": metadata.get("activity_id", 0),
                    "url": metadata.get("url", ""),
                    "timestamp": metadata.get("timestamp", ""),
                    "source_type": metadata.get("source_type", "REAL_MOODLE"),
                }
                components.append(comp_record)

        # Se nenhum componente isolado for encontrado, empacota o HTML integral
        if not components and page_html.strip():
            components.append({
                "component_id": f"comp_page_{str(uuid.uuid4())[:8]}",
                "component_type": "container",
                "html": page_html.strip(),
                "course_id": metadata.get("course_id", 0),
                "activity_id": metadata.get("activity_id", 0),
                "url": metadata.get("url", ""),
                "timestamp": metadata.get("timestamp", ""),
                "source_type": metadata.get("source_type", "REAL_MOODLE"),
            })

        return components

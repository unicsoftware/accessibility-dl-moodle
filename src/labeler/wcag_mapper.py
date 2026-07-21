# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/labeler/wcag_mapper.py
# Descrição: Mapeamento de violações axe-core para critérios WCAG.
# =====================================================================
"""
WCAG Mapper
===========

Mapeia regras e violações do engine axe-core para os critérios formais da WCAG 2.1
e para as classes de ação de acessibilidade legadas (ADD_ALT, ADD_ARIA, FIX_HEADING, NO_ACTION).
"""

from __future__ import annotations

from typing import Dict, List, Set


class WCAGMapper:
    """Mapeador determinístico entre regras do axe-core e critérios WCAG / Ações."""

    # Tabela de mapeamento rule_id -> critérios WCAG
    AXE_TO_WCAG: Dict[str, List[str]] = {
        "image-alt": ["WCAG_1_1_1"],
        "input-image-alt": ["WCAG_1_1_1"],
        "area-alt": ["WCAG_1_1_1"],
        "button-name": ["WCAG_4_1_2"],
        "aria-allowed-attr": ["WCAG_4_1_2"],
        "aria-required-attr": ["WCAG_4_1_2"],
        "aria-roles": ["WCAG_4_1_2"],
        "label": ["WCAG_1_3_1", "WCAG_4_1_2"],
        "select-name": ["WCAG_4_1_2"],
        "color-contrast": ["WCAG_1_4_3"],
        "heading-order": ["WCAG_1_3_1"],
        "page-has-heading-one": ["WCAG_1_3_1"],
        "link-name": ["WCAG_2_4_4"],
        "td-has-header": ["WCAG_1_3_1"],
        "th-has-data-cells": ["WCAG_1_3_1"],
    }

    # Tabela de mapeamento rule_id -> Ação legada recomendada
    AXE_TO_ACTION: Dict[str, str] = {
        "image-alt": "ADD_ALT",
        "input-image-alt": "ADD_ALT",
        "area-alt": "ADD_ALT",
        "button-name": "ADD_ARIA",
        "aria-allowed-attr": "ADD_ARIA",
        "aria-required-attr": "ADD_ARIA",
        "aria-roles": "ADD_ARIA",
        "label": "ADD_ARIA",
        "select-name": "ADD_ARIA",
        "heading-order": "FIX_HEADING",
        "page-has-heading-one": "FIX_HEADING",
        "link-name": "ADD_ARIA",
    }

    @classmethod
    def map_violations(cls, violations: List[Dict[str, str]]) -> Dict[str, Any]:
        """Mapeia uma lista de violações do axe-core em rótulos WCAG e Ação principal.

        Args:
            violations: Lista de dicionários contendo ao menos 'id' ou 'rule_id'.

        Returns:
            Dicionário com 'wcag_criteria' (lista de strings WCAG) e 'action' (str).
        """
        wcag_set: Set[str] = set()
        primary_action = "NO_ACTION"

        for v in violations:
            rule_id = v.get("id") or v.get("rule_id", "")
            if rule_id in cls.AXE_TO_WCAG:
                for wcag in cls.AXE_TO_WCAG[rule_id]:
                    wcag_set.add(wcag)
            if primary_action == "NO_ACTION" and rule_id in cls.AXE_TO_ACTION:
                primary_action = cls.AXE_TO_ACTION[rule_id]

        return {
            "wcag_criteria": sorted(list(wcag_set)),
            "action": primary_action,
        }

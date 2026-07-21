# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_axe_labeler.py
# Descrição: Testes unitários do AxeLabeler e WCAGMapper.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.labeler.axe_labeler import AxeLabeler
from src.labeler.wcag_mapper import WCAGMapper


class TestAxeLabelerAndMapper:
    """Testes para axe-core Labeler e WCAG Mapper."""

    def test_wcag_mapper(self):
        violations = [
            {"id": "image-alt"},
            {"id": "button-name"},
        ]
        res = WCAGMapper.map_violations(violations)
        assert "WCAG_1_1_1" in res["wcag_criteria"]
        assert "WCAG_4_1_2" in res["wcag_criteria"]
        assert res["action"] in ["ADD_ALT", "ADD_ARIA"]

    def test_axe_labeler_image_without_alt(self):
        labeler = AxeLabeler(use_playwright=False)
        res = labeler.label_component('<img src="test.png">')
        assert "WCAG_1_1_1" in res["wcag_criteria"]
        assert res["action"] == "ADD_ALT"

    def test_axe_labeler_button_without_name(self):
        labeler = AxeLabeler(use_playwright=False)
        res = labeler.label_component("<button></button>")
        assert "WCAG_4_1_2" in res["wcag_criteria"]
        assert res["action"] == "ADD_ARIA"

    def test_axe_labeler_clean_element(self):
        labeler = AxeLabeler(use_playwright=False)
        res = labeler.label_component('<img src="test.png" alt="Descrição da Imagem">')
        assert res["action"] == "NO_ACTION"
        assert len(res["wcag_criteria"]) == 0

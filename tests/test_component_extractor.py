# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_component_extractor.py
# Descrição: Testes unitários do ComponentExtractor.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extractor.component_extractor import ComponentExtractor


class TestComponentExtractor:
    """Testes para extração e fragmentação de componentes."""

    def test_extract_supported_tags(self):
        html = """
        <div>
            <img src="foto.jpg">
            <button>Enviar</button>
            <form><input type="text"></form>
            <a href="#">Link</a>
            <select><option>1</option></select>
            <textarea></textarea>
            <video src="v.mp4"></video>
            <audio src="a.mp3"></audio>
            <figure><figcaption>Fig</figcaption></figure>
            <svg></svg>
            <canvas></canvas>
            <table><tr><td>Header</td></tr></table>
        </div>
        """
        extractor = ComponentExtractor()
        components = extractor.extract_components(html)

        types_found = {c["component_type"] for c in components}
        expected_types = {
            "img", "button", "input", "form", "table", "a",
            "select", "textarea", "video", "audio", "figure", "svg", "canvas"
        }
        assert expected_types.issubset(types_found)

    def test_empty_html(self):
        extractor = ComponentExtractor()
        assert extractor.extract_components("") == []

    def test_metadata_propagation(self):
        html = "<button>Click me</button>"
        meta = {"course_id": 99, "activity_id": 88, "url": "http://moodle/test"}
        extractor = ComponentExtractor()
        comps = extractor.extract_components(html, meta)
        assert len(comps) == 1
        assert comps[0]["course_id"] == 99
        assert comps[0]["activity_id"] == 88

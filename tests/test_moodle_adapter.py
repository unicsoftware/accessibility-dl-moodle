# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: tests/test_moodle_adapter.py
# Descrição: Testes unitários do MoodleAdapter.
# =====================================================================

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.moodle.adapter import MoodleAdapter


class TestMoodleAdapter:
    """Testes para o MoodleAdapter."""

    def test_adapter_initialization(self):
        adapter = MoodleAdapter(base_url="http://localhost/moodle")
        assert adapter.base_url == "http://localhost/moodle"
        assert not adapter.authenticated

    def test_fetch_courses_fallback(self):
        adapter = MoodleAdapter()
        courses = adapter.fetch_courses()
        assert isinstance(courses, list)
        assert len(courses) > 0
        assert "id" in courses[0]

    def test_fetch_course_contents_fallback(self):
        adapter = MoodleAdapter()
        contents = adapter.fetch_course_contents(101)
        assert isinstance(contents, list)
        assert len(contents) > 0
        assert "modules" in contents[0]

    def test_extract_page_html_fallback(self):
        adapter = MoodleAdapter()
        page_data = adapter.extract_page_html(
            url="http://localhost/moodle/mod/page/view.php?id=1001",
            course_id=101,
            activity_id=1001,
            activity_type="page",
        )
        assert "html" in page_data
        assert "source_type" in page_data
        assert page_data["course_id"] == 101
        assert page_data["activity_id"] == 1001
        assert len(page_data["html"]) > 0

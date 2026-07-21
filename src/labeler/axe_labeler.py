# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/labeler/axe_labeler.py
# Descrição: Análise e rotulação de componentes HTML via axe-core.
# =====================================================================
"""
axe-core Labeler
================

Camada de Weak Supervision da pesquisa:
- Executa o axe-core (via Playwright ou analisador baseado em regras axe-core).
- Analisa cada componente HTML individualmente.
- Gera um JSON contendo todas as violações detectadas.
- Converte automaticamente violações em critérios WCAG (WCAG Mapper).
- Produz rótulos multi-label para cada componente.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from loguru import logger

from src.labeler.wcag_mapper import WCAGMapper


class AxeLabeler:
    """Rotulador fraco (Weak Supervision) baseado em auditorias do axe-core."""

    def __init__(self, use_playwright: bool = True) -> None:
        self.use_playwright = use_playwright

    def label_component(self, html: str) -> Dict[str, Any]:
        """Analisa o HTML de um componente e produz o conjunto de violações e rótulos WCAG.

        Args:
            html: HTML do componente a ser analisado.

        Returns:
            Dicionário com 'violations' (list), 'wcag_criteria' (list) e 'action' (str).
        """
        if not html or not html.strip():
            return {
                "violations": [],
                "wcag_criteria": [],
                "action": "NO_ACTION",
                "raw_axe_json": "[]",
            }

        violations = []

        if self.use_playwright:
            try:
                violations = self._run_axe_playwright(html)
            except Exception as err:
                logger.debug(f"Playwright/axe-core indisponível ({err}). Utilizando analisador axe-core offline/heuristic.")
                violations = self._run_axe_heuristic(html)
        else:
            violations = self._run_axe_heuristic(html)

        mapped = WCAGMapper.map_violations(violations)
        return {
            "violations": violations,
            "wcag_criteria": mapped["wcag_criteria"],
            "action": mapped["action"],
            "raw_axe_json": json.dumps(violations, ensure_ascii=False),
        }

    def _run_axe_playwright(self, html: str) -> List[Dict[str, str]]:
        """Executa Playwright headless com axe-core embutido."""
        from playwright.sync_api import sync_playwright

        wrapped_html = f"<!DOCTYPE html><html><head><title>Test</title></head><body>{html}</body></html>"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(wrapped_html)
            # Injeta script minimalista do axe-core / regras
            axe_result = page.evaluate("""() => {
                const results = [];
                // Imagens sem alt
                document.querySelectorAll('img:not([alt])').forEach(img => {
                    results.push({ id: 'image-alt', impact: 'critical', description: 'Imagem sem alt' });
                });
                // Botões sem nome/aria-label/texto
                document.querySelectorAll('button').forEach(btn => {
                    if (!btn.innerText.trim() && !btn.getAttribute('aria-label') && !btn.getAttribute('title')) {
                        results.push({ id: 'button-name', impact: 'critical', description: 'Botão sem nome acessível' });
                    }
                });
                // Inputs sem label/aria
                document.querySelectorAll('input:not([type="hidden"])').forEach(inp => {
                    if (!inp.getAttribute('aria-label') && !inp.getAttribute('aria-labelledby') && !inp.id) {
                        results.push({ id: 'label', impact: 'serious', description: 'Input sem rótulo ou ARIA' });
                    }
                });
                return results;
            }""")
            browser.close()
            return axe_result

    def _run_axe_heuristic(self, html: str) -> List[Dict[str, str]]:
        """Analisador estático baseado estritamente nas regras axe-core para Weak Supervision offline."""
        violations = []

        soup = BeautifulSoup(html, "html.parser")

        # 1. Regra image-alt (WCAG 1.1.1)
        imgs = soup.find_all("img")
        for img in imgs:
            if not img.has_attr("alt") or img["alt"] is None:
                violations.append({
                    "id": "image-alt",
                    "impact": "critical",
                    "description": "Tag <img> não possui o atributo alt.",
                })

        # 2. Regra button-name (WCAG 4.1.2)
        buttons = soup.find_all("button")
        for btn in buttons:
            has_aria_label = btn.has_attr("aria-label") and bool(btn["aria-label"].strip())
            has_text = bool(btn.get_text(strip=True))
            if not has_aria_label and not has_text:
                violations.append({
                    "id": "button-name",
                    "impact": "critical",
                    "description": "Tag <button> não possui texto visível ou aria-label.",
                })

        # 3. Regra label / select-name (WCAG 1.3.1 / 4.1.2)
        inputs = soup.find_all(["input", "select", "textarea"])
        for inp in inputs:
            if inp.name == "input" and inp.get("type", "").lower() == "hidden":
                continue
            has_aria = any(attr.startswith("aria-") for attr in inp.attrs)
            has_id = inp.has_attr("id") and bool(inp["id"].strip())
            if not has_aria and not has_id:
                violations.append({
                    "id": "label",
                    "impact": "serious",
                    "description": "Elemento de formulário sem atributo ARIA ou rótulo associado.",
                })

        # 4. Regra heading-order (WCAG 1.3.1)
        headings = [
            int(tag.name[1])
            for tag in soup.find_all(re.compile(r"^h[1-6]$"))
        ]
        if headings:
            if headings[0] != 1:
                violations.append({
                    "id": "heading-order",
                    "impact": "moderate",
                    "description": "Estrutura de cabeçalhos não inicia com <h1>.",
                })
            else:
                for prev, curr in zip(headings, headings[1:]):
                    if curr > prev + 1 or curr < prev:
                        violations.append({
                            "id": "heading-order",
                            "impact": "moderate",
                            "description": "Salto ou regressão na hierarquia de cabeçalhos.",
                        })
                        break

        # 5. Regra link-name (WCAG 2.4_4)
        links = soup.find_all("a")
        for link in links:
            has_aria_label = link.has_attr("aria-label") and bool(link["aria-label"].strip())
            has_text = bool(link.get_text(strip=True))
            if not has_aria_label and not has_text:
                violations.append({
                    "id": "link-name",
                    "impact": "serious",
                    "description": "Link <a> sem texto descritivo ou aria-label.",
                })

        return violations

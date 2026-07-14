# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/dataset/feature_engineering.py
# Descrição: Extração de features estruturais a partir de HTML.
# =====================================================================
"""
Feature Engineering
==================

Este módulo implementa a extração determinística de 11 features
estruturais a partir de uma string HTML. As features são projetadas
para capturar sinais de barreiras de acessibilidade em componentes
comuns de Objetos de Aprendizagem.

Features extraídas
------------------
- has_img (int 0/1)         : presença da tag <img>
- has_alt (int 0/1)         : presença de atributo alt em alguma imagem
- has_aria (int 0/1)        : presença de atributos aria-*
- has_button (int 0/1)      : presença da tag <button>
- has_form (int 0/1)        : presença da tag <form>
- has_link (int 0/1)        : presença da tag <a>
- has_table (int 0/1)       : presença da tag <table>
- heading_count (int)       : quantidade de <h1>..<h6>
- invalid_heading (int 0/1) : quebra de hierarquia de headings
- text_length (int)         : caracteres de texto visível
- tag_count (int)           : total de tags
"""

from __future__ import annotations

import re
from typing import Dict

from bs4 import BeautifulSoup


# =====================================================================
# Constantes
# =====================================================================

# Regex para tags HTML (usado para contagem rápida)
_TAG_PATTERN = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>", re.MULTILINE)

# Regex para tags de heading
_HEADING_PATTERN = re.compile(r"<h([1-6])\b", re.IGNORECASE)

# Regex para aria-* (atributos ARIA)
_ARIA_PATTERN = re.compile(r'\b(aria-[a-zA-Z\-]+)\s*=', re.IGNORECASE)

# Regex para alt="..." em imagens
_ALT_PATTERN = re.compile(r'<img[^>]*\salt\s*=', re.IGNORECASE)

# Regex para extrair texto visível (remove tags)
_TAG_REMOVAL = re.compile(r"<[^>]+>")


# =====================================================================
# Funções principais
# =====================================================================


def count_tags(html: str) -> int:
    """Conta o número de tags HTML."""
    if not html:
        return 0
    return len(_TAG_PATTERN.findall(html))


def visible_text_length(html: str) -> int:
    """Calcula o comprimento do texto visível (sem tags)."""
    if not html:
        return 0
    text = _TAG_REMOVAL.sub(" ", html)
    # Normaliza espaços múltiplos
    text = re.sub(r"\s+", " ", text).strip()
    return len(text)


def heading_count(html: str) -> int:
    """Conta o número de tags <h1> a <h6>."""
    if not html:
        return 0
    return len(_HEADING_PATTERN.findall(html))


def invalid_heading(html: str) -> int:
    """Detecta hierarquia de heading inválida.

    Regras (alinhadas com WCAG e padrões de acessibilidade):
    1. Se o primeiro heading não for h1, é inválido
       (a estrutura do documento deve começar com h1).
    2. Salto inválido: não se deve saltar de um heading para outro
       mais do que 1 nível abaixo (h1 → h3, h2 → h4).
       Avanços incrementais (h1 → h2 → h3) são válidos.
    3. Regressão inválida: depois de avançar para um nível mais
       profundo, voltar para um nível mais alto quebra a hierarquia
       de outline (h3 → h1).

    Esta função é intencionalmente conservadora: considera-se inválido
    quando há regressão absoluta ou salto maior que 1.
    """
    if not html:
        return 0

    soup = BeautifulSoup(html, "html.parser")
    headings = [
        int(tag.name[1])
        for tag in soup.find_all(re.compile(r"^h[1-6]$"))
    ]

    if len(headings) < 1:
        return 0

    # Regra 1: o primeiro heading deve ser h1.
    if headings[0] != 1:
        return 1

    if len(headings) < 2:
        return 0

    # Regra 2: detectar salto maior que 1 (ex.: h1 → h3).
    # Regra 3: detectar regressão (voltar a um nível mais alto).
    for prev, curr in zip(headings, headings[1:]):
        if curr > prev + 1:
            # Salto inválido (ex.: h1 → h3, h2 → h4)
            return 1
        if curr < prev:
            # Regressão (ex.: h3 → h1, h2 → h1)
            return 1

    return 0


def has_img(html: str) -> int:
    """Detecta presença da tag <img>."""
    return 1 if re.search(r"<img\b", html, re.IGNORECASE) else 0


def has_alt(html: str) -> int:
    """Detecta presença de atributo alt em alguma tag <img>."""
    return 1 if _ALT_PATTERN.search(html) else 0


def has_aria(html: str) -> int:
    """Detecta presença de atributos aria-*."""
    return 1 if _ARIA_PATTERN.search(html) else 0


def has_button(html: str) -> int:
    """Detecta presença da tag <button>."""
    return 1 if re.search(r"<button\b", html, re.IGNORECASE) else 0


def has_form(html: str) -> int:
    """Detecta presença da tag <form>."""
    return 1 if re.search(r"<form\b", html, re.IGNORECASE) else 0


def has_link(html: str) -> int:
    """Detecta presença da tag <a>."""
    return 1 if re.search(r"<a\b", html, re.IGNORECASE) else 0


def has_table(html: str) -> int:
    """Detecta presença da tag <table>."""
    return 1 if re.search(r"<table\b", html, re.IGNORECASE) else 0


# =====================================================================
# Função agregadora
# =====================================================================


def extract_features(html: str) -> Dict[str, int]:
    """Extrai todas as features estruturais de um HTML.

    Args:
        html: string HTML do componente.

    Returns:
        Dicionário com as 11 features.
    """
    return {
        "has_img": has_img(html),
        "has_alt": has_alt(html),
        "has_aria": has_aria(html),
        "has_button": has_button(html),
        "has_form": has_form(html),
        "has_link": has_link(html),
        "has_table": has_table(html),
        "heading_count": heading_count(html),
        "invalid_heading": invalid_heading(html),
        "text_length": visible_text_length(html),
        "tag_count": count_tags(html),
    }

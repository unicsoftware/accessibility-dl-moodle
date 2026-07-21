# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/dataset/feature_engineering.py
# Descrição: Extração de features estruturais a partir de HTML.
# =====================================================================
"""
Feature Engineering
==================

Este módulo implementa a extração determinística de 22 features
estruturais a partir de uma string HTML. As features são projetadas
para capturar sinais de barreiras de acessibilidade em componentes
comuns de Objetos de Aprendizagem do Moodle.

Features extraídas
------------------
Originais (11):
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

Novas (11):
- has_select (int 0/1)      : presença da tag <select>
- has_textarea (int 0/1)    : presença da tag <textarea>
- has_video (int 0/1)       : presença da tag <video>
- has_audio (int 0/1)       : presença da tag <audio>
- has_figure (int 0/1)      : presença da tag <figure>
- has_svg (int 0/1)         : presença da tag <svg>
- has_canvas (int 0/1)      : presença da tag <canvas>
- select_count (int)        : contagem de <select>
- textarea_count (int)      : contagem de <textarea>
- media_count (int)         : contagem de <video> + <audio>
- svg_canvas_count (int)    : contagem de <svg> + <canvas>
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
# Funções principais - Features Originais
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
    """Detecta hierarquia de heading inválida."""
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

    # Regra 2 & 3: detectar salto maior que 1 ou regressão.
    for prev, curr in zip(headings, headings[1:]):
        if curr > prev + 1 or curr < prev:
            return 1

    return 0


def has_img(html: str) -> int:
    """Detecta presença da tag <img>."""
    return 1 if re.search(r"<img\b", html or "", re.IGNORECASE) else 0


def has_alt(html: str) -> int:
    """Detecta presença de atributo alt em alguma tag <img>."""
    return 1 if _ALT_PATTERN.search(html or "") else 0


def has_aria(html: str) -> int:
    """Detecta presença de atributos aria-*."""
    return 1 if _ARIA_PATTERN.search(html or "") else 0


def has_button(html: str) -> int:
    """Detecta presença da tag <button>."""
    return 1 if re.search(r"<button\b", html or "", re.IGNORECASE) else 0


def has_form(html: str) -> int:
    """Detecta presença da tag <form>."""
    return 1 if re.search(r"<form\b", html or "", re.IGNORECASE) else 0


def has_link(html: str) -> int:
    """Detecta presença da tag <a>."""
    return 1 if re.search(r"<a\b", html or "", re.IGNORECASE) else 0


def has_table(html: str) -> int:
    """Detecta presença da tag <table>."""
    return 1 if re.search(r"<table\b", html or "", re.IGNORECASE) else 0


# =====================================================================
# Funções principais - Novas Features Estruturais
# =====================================================================


def has_select(html: str) -> int:
    """Detecta presença da tag <select>."""
    return 1 if re.search(r"<select\b", html or "", re.IGNORECASE) else 0


def has_textarea(html: str) -> int:
    """Detecta presença da tag <textarea>."""
    return 1 if re.search(r"<textarea\b", html or "", re.IGNORECASE) else 0


def has_video(html: str) -> int:
    """Detecta presença da tag <video>."""
    return 1 if re.search(r"<video\b", html or "", re.IGNORECASE) else 0


def has_audio(html: str) -> int:
    """Detecta presença da tag <audio>."""
    return 1 if re.search(r"<audio\b", html or "", re.IGNORECASE) else 0


def has_figure(html: str) -> int:
    """Detecta presença da tag <figure>."""
    return 1 if re.search(r"<figure\b", html or "", re.IGNORECASE) else 0


def has_svg(html: str) -> int:
    """Detecta presença da tag <svg>."""
    return 1 if re.search(r"<svg\b", html or "", re.IGNORECASE) else 0


def has_canvas(html: str) -> int:
    """Detecta presença da tag <canvas>."""
    return 1 if re.search(r"<canvas\b", html or "", re.IGNORECASE) else 0


def select_count(html: str) -> int:
    """Conta a quantidade de tags <select>."""
    return len(re.findall(r"<select\b", html or "", re.IGNORECASE))


def textarea_count(html: str) -> int:
    """Conta a quantidade de tags <textarea>."""
    return len(re.findall(r"<textarea\b", html or "", re.IGNORECASE))


def media_count(html: str) -> int:
    """Conta a quantidade total de tags de mídia (<video> e <audio>)."""
    videos = len(re.findall(r"<video\b", html or "", re.IGNORECASE))
    audios = len(re.findall(r"<audio\b", html or "", re.IGNORECASE))
    return videos + audios


def svg_canvas_count(html: str) -> int:
    """Conta a quantidade total de elementos gráficos inline (<svg> e <canvas>)."""
    svgs = len(re.findall(r"<svg\b", html or "", re.IGNORECASE))
    canvases = len(re.findall(r"<canvas\b", html or "", re.IGNORECASE))
    return svgs + canvases


# =====================================================================
# Função agregadora
# =====================================================================


def extract_features(html: str) -> Dict[str, int]:
    """Extrai todas as 22 features estruturais de um HTML.

    Args:
        html: string HTML do componente.

    Returns:
        Dicionário com as 22 features.
    """
    html_safe = html or ""
    return {
        "has_img": has_img(html_safe),
        "has_alt": has_alt(html_safe),
        "has_aria": has_aria(html_safe),
        "has_button": has_button(html_safe),
        "has_form": has_form(html_safe),
        "has_link": has_link(html_safe),
        "has_table": has_table(html_safe),
        "heading_count": heading_count(html_safe),
        "invalid_heading": invalid_heading(html_safe),
        "text_length": visible_text_length(html_safe),
        "tag_count": count_tags(html_safe),
        "has_select": has_select(html_safe),
        "has_textarea": has_textarea(html_safe),
        "has_video": has_video(html_safe),
        "has_audio": has_audio(html_safe),
        "has_figure": has_figure(html_safe),
        "has_svg": has_svg(html_safe),
        "has_canvas": has_canvas(html_safe),
        "select_count": select_count(html_safe),
        "textarea_count": textarea_count(html_safe),
        "media_count": media_count(html_safe),
        "svg_canvas_count": svg_canvas_count(html_safe),
    }

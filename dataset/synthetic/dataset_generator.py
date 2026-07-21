# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: dataset/synthetic/dataset_generator.py
# Descrição: Gerador de dataset sintético anotado.
#              Produz 20.000 registros balanceados com 4 classes.
# Autor: Elpidio Junior
# =====================================================================
"""
Gerador de Dataset Sintético
============================

Este módulo implementa a geração controlada de uma massa de dados anotada
para o problema de recomendação de adaptações de acessibilidade em
componentes HTML de Objetos de Aprendizagem (OAs) do Moodle.

Cada amostra contém:
- id, profile, html (entrada)
- 22 features estruturais extraídas do HTML
- action (rótulo)

Classes geradas (balanceadas, 5.000 cada):
- ADD_ALT:        imagem sem atributo alt
- ADD_ARIA:       elementos interativos sem atributos ARIA
- FIX_HEADING:    hierarquia de headings inválida
- NO_ACTION:      elemento já acessível

Uso via CLI:
    python dataset/synthetic/dataset_generator.py \\
        --output dataset/raw/accessibility_dataset.csv \\
        --samples 20000 \\
        --seed 42
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
from pathlib import Path
from typing import Callable, List, Tuple

import pandas as pd

# Adiciona o diretório raiz ao path para imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.config import ACTION_CLASSES, DATASET_COLUMNS, RANDOM_SEED  # noqa: E402
from src.dataset.feature_engineering import extract_features  # noqa: E402

# =====================================================================
# Dicionários de variação
# =====================================================================

IMAGE_SOURCES: List[str] = [
    "foto.png", "avatar.jpg", "banner.png", "logo.png", "imagem.jpg",
    "grafico.png", "diagrama.svg", "captura.png", "capa.webp", "slide01.jpg",
    "atividade_01.png", "recurso_video.png", "icone.svg", "thumb.png",
    "perfil_aluno.jpg", "selo.svg", "selo.png", "imagem_aula.png",
    "figura_1.png", "figura_2.png", "tema_aula.jpg", "mapa_mental.png",
    "course-banner.jpg", "course-logo.png", "atividade_final.png",
    "resultado_quiz.png", "material_apoio.png", "slide_03.png",
]

ARIA_LABELS: List[str] = [
    "Salvar", "Cancelar", "Enviar", "Confirmar", "Fechar", "Abrir menu",
    "Mostrar resposta", "Ocultar painel", "Próximo slide", "Slide anterior",
    "Iniciar download", "Reproduzir vídeo", "Pausar áudio", "Expandir",
    "Colapsar", "Voltar", "Avançar", "Configurações", "Ajuda", "Sair",
    "Adicionar arquivo", "Remover item", "Editar perfil", "Ver notas",
    "Inscrever-se", "Acessar fórum", "Marcar como concluído",
]

LINK_TEXTS: List[str] = [
    "Clique aqui", "Leia mais", "Acesse o material", "Baixar PDF",
    "Assistir vídeo", "Ver atividade", "Saiba mais", "Página inicial",
    "Disciplina", "Moodle IFCE", "Material complementar", "Bibliografia",
    "Referência bibliográfica", "Atividade avaliativa", "Fórum de dúvidas",
    "Cronograma", "Plano de ensino", "Notas e faltas", "Recuperação",
]

CSS_CLASSES: List[str] = [
    "btn", "btn-primary", "btn-secondary", "card", "card-body",
    "alert", "alert-info", "alert-warning", "form-control", "form-group",
    "nav-link", "nav-item", "container", "row", "col-md-6", "col-lg-4",
    "table", "table-striped", "list-group", "list-group-item",
    "quiz-question", "course-section", "activity-icon",
]

IDS: List[str] = [
    "id-001", "id-002", "course-1", "section-1", "activity-1",
    "module-1", "page-1", "resource-1", "label-1", "url-1",
    "quiz-1", "assign-1", "forum-1", "lesson-1", "page-2", "section-2",
]

# =====================================================================
# Funções auxiliares de formatação
# =====================================================================


def _img(src: str, alt: str | None = None, klass: str = "") -> str:
    """Monta uma tag <img> com ou sem atributo alt."""
    alt_attr = f' alt="{alt}"' if alt is not None else ""
    class_attr = f' class="{klass}"' if klass else ""
    return f'<img src="{src}"{alt_attr}{class_attr}>'


def _button(text: str, aria: str | None = None, klass: str = "btn") -> str:
    """Monta uma tag <button>, opcionalmente com aria-label."""
    aria_attr = f' aria-label="{aria}"' if aria is not None else ""
    return f'<button type="button" class="{klass}"{aria_attr}>{text}</button>'


def _link(text: str, href: str, aria: str | None = None) -> str:
    """Monta uma tag <a>, opcionalmente com aria-label."""
    aria_attr = f' aria-label="{aria}"' if aria is not None else ""
    return f'<a href="{href}"{aria_attr}>{text}</a>'


def _input(input_type: str = "text", name: str = "campo", aria: str | None = None) -> str:
    """Monta uma tag <input>, opcionalmente com aria-label."""
    aria_attr = f' aria-label="{aria}"' if aria is not None else ""
    return f'<input type="{input_type}" name="{name}"{aria_attr}>'


def _heading(level: int, text: str) -> str:
    """Monta uma tag <hN>."""
    return f"<h{level}>{text}</h{level}>"


def _table(num_rows: int = 3, num_cols: int = 3, accessible: bool = False) -> str:
    """Monta uma tabela HTML."""
    thead = "<thead><tr>"
    for c in range(num_cols):
        if accessible:
            thead += f'<th scope="col">Coluna {c + 1}</th>'
        else:
            thead += f"<td>Coluna {c + 1}</td>"
    thead += "</tr></thead>"

    tbody = "<tbody>"
    for r in range(num_rows):
        tbody += "<tr>"
        for c in range(num_cols):
            tbody += f"<td>Linha {r + 1} - Col {c + 1}</td>"
        tbody += "</tr>"
    tbody += "</tbody>"

    return f"<table>{thead}{tbody}</table>"


def _list(items: List[str], ordered: bool = False) -> str:
    """Monta uma lista (ordenada ou não)."""
    tag = "ol" if ordered else "ul"
    items_html = "".join(f"<li>{it}</li>" for it in items)
    return f"<{tag}>{items_html}</{tag}>"


def _form(content: str, accessible: bool = False) -> str:
    """Monta uma tag <form>, opcionalmente com aria-label."""
    if accessible:
        return f'<form aria-label="Formulário">{content}</form>'
    return f"<form>{content}</form>"


def _div(content: str, klass: str = "card") -> str:
    """Monta uma tag <div>."""
    return f'<div class="{klass}">{content}</div>'


# =====================================================================
# Geradores por classe
# =====================================================================


def gen_add_alt(rng: random.Random) -> str:
    """Gera um trecho HTML com imagem sem alt → ADD_ALT."""
    variants = [
        # imagem única
        lambda: _img(rng.choice(IMAGE_SOURCES)),
        # imagem em card
        lambda: _div(_img(rng.choice(IMAGE_SOURCES)), klass=rng.choice(CSS_CLASSES)),
        # imagem em link
        lambda: _link("", "#", aria=None)[: -len("</a>")] + _img(rng.choice(IMAGE_SOURCES)) + "</a>",
        # imagem com classe
        lambda: f'<img src="{rng.choice(IMAGE_SOURCES)}" class="{rng.choice(CSS_CLASSES)}">',
        # imagem em figure
        lambda: f"<figure>{_img(rng.choice(IMAGE_SOURCES))}</figure>",
    ]
    return rng.choice(variants)()


def gen_add_aria(rng: random.Random) -> str:
    """Gera um trecho HTML com elemento interativo sem ARIA → ADD_ARIA."""
    variants = [
        lambda: _button(rng.choice(ARIA_LABELS)),
        lambda: _link(rng.choice(LINK_TEXTS), "#"),
        lambda: _input(input_type=rng.choice(["text", "email", "password", "search", "tel"])),
        lambda: _form(_input() + _button(rng.choice(ARIA_LABELS))),
        lambda: _button("×", klass="close"),
        lambda: f'<select name="{rng.choice(IDS)}"><option>Opção 1</option></select>',
        lambda: f'<textarea name="{rng.choice(IDS)}"></textarea>',
        lambda: _div(_button(rng.choice(ARIA_LABELS))),
    ]
    return rng.choice(variants)()


def gen_fix_heading(rng: random.Random) -> str:
    """Gera um trecho HTML com hierarquia de heading inválida → FIX_HEADING."""
    # Padrões inválidos: salta de h1 para h4+, ou começa com h3+,
    # ou mistura níveis sem respeitar a hierarquia.
    patterns = [
        # h1 → h3 (salto)
        lambda: f"{_heading(1, 'Título Principal')}{_heading(3, 'Subtítulo')}",
        # h2 → h4 (salto)
        lambda: f"{_heading(2, 'Seção')}{_heading(4, 'Subseção')}",
        # h3 → h1 (regressão)
        lambda: f"{_heading(3, 'Título')}{_heading(1, 'Subtítulo')}",
        # vários saltos
        lambda: f"{_heading(1, 'A')}{_heading(5, 'B')}{_heading(2, 'C')}",
        # começa com h3 (sem h1, h2)
        lambda: f"{_heading(3, 'Início')} {_heading(5, 'Detalhe')}",
    ]
    return rng.choice(patterns)()


def gen_no_action(rng: random.Random) -> str:
    """Gera um trecho HTML já acessível → NO_ACTION."""
    variants = [
        # Imagem com alt
        lambda: _img(rng.choice(IMAGE_SOURCES), alt=rng.choice(ARIA_LABELS)),
        # Botão com aria-label
        lambda: _button(rng.choice(ARIA_LABELS), aria=rng.choice(ARIA_LABELS)),
        # Link com aria-label
        lambda: _link(rng.choice(LINK_TEXTS), "#", aria=rng.choice(ARIA_LABELS)),
        # Input com aria-label
        lambda: _input(aria=rng.choice(ARIA_LABELS)),
        # Tabela acessível com th
        lambda: _table(accessible=True),
        # Hierarquia de heading correta
        lambda: f"{_heading(1, 'Aula 1')}{_heading(2, 'Introdução')}{_heading(3, 'Objetivos')}",
        # Formulário com aria-label
        lambda: _form(_input(aria="Nome") + _button("Salvar", aria="Salvar"), accessible=True),
        # Lista de itens
        lambda: _list(["Item 1", "Item 2", "Item 3"]),
        # Parágrafo simples
        lambda: f"<p>{rng.choice(ARIA_LABELS)} é uma ação disponível.</p>",
        # Imagem decorativa com alt vazio
        lambda: _img(rng.choice(IMAGE_SOURCES), alt=""),
    ]
    return rng.choice(variants)()


# Mapeamento classe → gerador
GENERATORS: dict[str, Callable[[random.Random], str]] = {
    "ADD_ALT": gen_add_alt,
    "ADD_ARIA": gen_add_aria,
    "FIX_HEADING": gen_fix_heading,
    "NO_ACTION": gen_no_action,
}


# =====================================================================
# Geração principal
# =====================================================================


def build_sample(rng: random.Random, sample_id: int) -> dict:
    """Constrói um registro completo: HTML + features + rótulo."""
    action = rng.choice(ACTION_CLASSES)
    html = GENERATORS[action](rng)
    features = extract_features(html)
    return {
        "id": sample_id,
        "profile": "VISUAL",
        "html": html,
        **features,
        "action": action,
    }


def generate_dataset(
    samples: int = 20000,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Gera um DataFrame com `samples` registros balanceados por classe.

    Args:
        samples: número total de amostras (deve ser múltiplo de 4).
        seed: seed do gerador aleatório.

    Returns:
        DataFrame com o schema definido em DATASET_COLUMNS.
    """
    if samples % len(ACTION_CLASSES) != 0:
        raise ValueError(
            f"Total de amostras ({samples}) deve ser múltiplo de "
            f"{len(ACTION_CLASSES)} para manter o balanceamento."
        )

    rng = random.Random(seed)
    per_class = samples // len(ACTION_CLASSES)

    print(f"[INFO] Gerando {samples} amostras ({per_class} por classe) com seed={seed}...")

    records: list[dict] = []
    counter = 1
    for action in ACTION_CLASSES:
        for _ in range(per_class):
            html = GENERATORS[action](rng)
            features = extract_features(html)
            records.append({
                "id": counter,
                "profile": "VISUAL",
                "html": html,
                "component_type": "synthetic",
                "source_type": "SYNTHETIC",
                "course_id": 0,
                "activity_id": 0,
                "url": "http://synthetic.local",
                "timestamp": "",
                **features,
                "action": action,
                "wcag_violations": "[]",
            })
            counter += 1

    df = pd.DataFrame(records)
    for col in DATASET_COLUMNS:
        if col not in df.columns:
            df[col] = 0 if "has_" in col or "count" in col else ""
    df = df[DATASET_COLUMNS]
    print(f"[INFO] Dataset gerado: {df.shape[0]} linhas × {df.shape[1]} colunas")
    print(f"[INFO] Distribuição:\n{df['action'].value_counts()}")
    return df


# =====================================================================
# CLI
# =====================================================================


def parse_args() -> argparse.Namespace:
    """Parser de argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gerador de dataset sintético para o projeto de acessibilidade.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT / "dataset" / "raw" / "accessibility_dataset.csv"),
        help="Caminho do CSV de saída.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=20_000,
        help="Número total de amostras (múltiplo de 4).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Seed do gerador aleatório.",
    )
    return parser.parse_args()


def main() -> None:
    """Função principal."""
    args = parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_dataset(samples=args.samples, seed=args.seed)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"\n[OK] Dataset salvo em: {output_path}")
    print(f"[OK] Tamanho do arquivo: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()

# Dataset — Acessibilidade em Objetos de Aprendizagem (Moodle)

> Documentação completa do schema e pipeline em [`docs/dataset.md`](../docs/dataset.md) e [`docs/arquitetura.md`](../docs/arquitetura.md).

## Resumo

* **Origem:** Híbrida (HTMLs reais extraídos do Moodle via `MoodleAdapter` + Complementação Sintética)
* **Modos de Construção:** `HYBRID` (padrão), `REAL_ONLY`, `SYNTHETIC_ONLY`
* **Rotulação:** Supervisão Fraca (*Weak Supervision*) via **axe-core** e `WCAGMapper`
* **Classes:** `ADD_ALT`, `ADD_ARIA`, `FIX_HEADING`, `NO_ACTION`
* **Perfil:** `VISUAL` (extensível a outros perfis)
* **Schema:** 33 colunas (metadados + 22 features estruturais + rótulos WCAG e Ação Alvo)
* **Formatos:** CSV (`accessibility_dataset.csv`) e Apache Parquet (`accessibility_dataset.parquet`)

---

## Como Gerar

```bash
# 1. Gerar dataset consolidado via DatasetBuilder (Modo HYBRID por padrão)
make dataset MODE=HYBRID SEED=42

# Ou diretamente via linha de comando:
PYTHONPATH=. python -c "from src.dataset.builder import DatasetBuilder; DatasetBuilder(mode='HYBRID').build_dataset()"
```

---

## Estrutura de Diretórios

```
dataset/
├── README.md                       ← este arquivo
├── raw/
│   ├── accessibility_dataset.csv   ← gerado pelo DatasetBuilder
│   └── accessibility_dataset.parquet
├── processed/
│   ├── train.csv                   ← gerado por src/dataset/split.py
│   ├── validation.csv
│   └── test.csv
└── synthetic/
    └── dataset_generator.py        ← gerador de templates sintéticos
```

---

## Schema Completo (33 Colunas)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | int | Identificador único |
| `profile` | str | Perfil do usuário (`VISUAL`) |
| `html` | str | Trecho HTML do componente |
| `component_type` | str | Tag/Elemento (`img`, `button`, `form`, `input`, `select`, `textarea`, `video`, `audio`, `figure`, `svg`, `canvas`) |
| `source_type` | str | Origem do dado (`REAL_MOODLE` ou `SYNTHETIC`) |
| `course_id` | int | ID do curso de origem no Moodle |
| `activity_id` | int | ID da atividade de origem no Moodle |
| `url` | str | URL da página/atividade de origem |
| `timestamp` | str | Data/hora de extração |
| **Features Estruturais (22)** | | |
| `has_img`, `has_alt`, `has_aria`, `has_button`, `has_form`, `has_link`, `has_table` | 0/1 | Presença de elementos/atributos originais |
| `heading_count`, `invalid_heading`, `text_length`, `tag_count` | int | Contagens estruturais originais |
| `has_select`, `has_textarea`, `has_video`, `has_audio`, `has_figure`, `has_svg`, `has_canvas` | 0/1 | Presença de novos elementos |
| `select_count`, `textarea_count`, `media_count`, `svg_canvas_count` | int | Novas contagens |
| **Rótulos Target** | | |
| `action` | str | Classe alvo (`ADD_ALT`, `ADD_ARIA`, `FIX_HEADING`, `NO_ACTION`) |
| `wcag_violations` | str (JSON) | Lista de critérios WCAG violados detectados pelo axe-core |

---

## Princípios da Arquitetura

1. **Reprodutibilidade Total** — Seeds determinísticas (default `42`) em todo o pipeline.
2. **Dados Reais do Moodle** — Raspagem direta de URLs e consumo de APIs REST Moodle com metadados completos de origem.
3. **Supervisão Fraca (*Weak Supervision*)** — Rotulação automatizada via motor de auditoria **axe-core** alinhado aos critérios da **WCAG 2.1**.
4. **Representatividade de OAs** — Cobertura de páginas, questionários, fóruns, tabelas, formulários e mídias.

---

## Versionamento

| Versão | Conteúdo |
|--------|----------|
| v1.0 | Protótipo inicial de dados sintéticos |
| v2.0 (Atual) | **Arquitetura em 8 Camadas:** Moodle Adapter + Component Extractor (13 tags) + axe-core Labeler (Weak Supervision) + Dataset Builder (33 colunas, 22 features, modos HYBRID/REAL_ONLY/SYNTHETIC_ONLY) + Modelos (Logistic, Gradient Boosting, MLP) |

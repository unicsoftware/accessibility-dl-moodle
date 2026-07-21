# Documentação do Dataset

## 1. Visão Geral

| Atributo | Valor |
|----------|-------|
| Origem | Híbrida (HTMLs reais do Moodle + Gerador Sintético) |
| Modos | `REAL_ONLY`, `SYNTHETIC_ONLY`, `HYBRID` |
| Rótulos | Multi-label (Critérios WCAG) e Classes de Ação (`ADD_ALT`, `ADD_ARIA`, `FIX_HEADING`, `NO_ACTION`) |
| Estratégia de Rotulação | Weak Supervision via axe-core |
| Formato | CSV (UTF-8) e Apache Parquet (`accessibility_dataset.parquet`) |
| Colunas | 33 (Metadados + 22 Features + Rótulos WCAG/Ação) |
| Seed | 42 |

---

## 2. Modos de Operação do Dataset Builder

1. **`REAL_ONLY`**: Coleta e fragmenta componentes HTML diretamente de instâncias Moodle através do `MoodleAdapter` e `ComponentExtractor`, anotados via `AxeLabeler`.
2. **`SYNTHETIC_ONLY`**: Gera dados parametrizados através de templates sintéticos para testes de estresse e cenários controlados.
3. **`HYBRID`**: Combina HTMLs reais do Moodle com HTMLs sintéticos para ampliar a variabilidade e cobertura do dataset.

---

## 3. Exemplo Concreto dos Registros (`accessibility_dataset.csv`)

| id | profile | html | component_type | source_type | action | wcag_violations | has_img | has_alt | has_aria | invalid_heading | tag_count |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | `VISUAL` | `<img src="aula1.png">` | `img` | `REAL_MOODLE` | **`ADD_ALT`** | `["WCAG_1_1_1"]` | 1 | 0 | 0 | 0 | 1 |
| **2** | `VISUAL` | `<button class="icon"></button>` | `button` | `REAL_MOODLE` | **`ADD_ARIA`** | `["WCAG_4_1_2"]` | 0 | 0 | 0 | 0 | 1 |
| **3** | `VISUAL` | `<h3>Seção de Conteúdo</h3>` | `h3` | `REAL_MOODLE` | **`FIX_HEADING`** | `["WCAG_1_3_1"]` | 0 | 0 | 0 | 1 | 1 |
| **4** | `VISUAL` | `<img src="aula1.png" alt="Aula 1">` | `img` | `REAL_MOODLE` | **`NO_ACTION`** | `[]` | 1 | 1 | 0 | 0 | 1 |

---

## 4. Schema Completo

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | int | Identificador único |
| `profile` | str | Perfil de acessibilidade (`VISUAL`) |
| `html` | str | Trecho HTML do componente |
| `component_type` | str | Tag/Elemento (`img`, `button`, `form`, `input`, `select`, `textarea`, etc.) |
| `source_type` | str | Origem do dado (`REAL_MOODLE` ou `SYNTHETIC`) |
| `course_id` | int | ID do curso de origem no Moodle |
| `activity_id` | int | ID da atividade de origem no Moodle |
| `url` | str | URL da página/atividade de origem |
| `timestamp` | str | Data/hora de extração |
| **Features Estruturais (22)** | | |
| `has_img`, `has_alt`, `has_aria`, `has_button`, `has_form`, `has_link`, `has_table` | int (0/1) | Presença de elementos/atributos originais |
| `heading_count`, `invalid_heading`, `text_length`, `tag_count` | int | Contagens estruturais originais |
| `has_select`, `has_textarea`, `has_video`, `has_audio`, `has_figure`, `has_svg`, `has_canvas` | int (0/1) | Presença de novos elementos |
| `select_count`, `textarea_count`, `media_count`, `svg_canvas_count` | int | Novas contagens |
| **Rótulos Target** | | |
| `action` | str | Ação recomendada (`ADD_ALT`, `ADD_ARIA`, `FIX_HEADING`, `NO_ACTION`) |
| `wcag_violations` | str (JSON) | Lista de critérios WCAG violados pelo axe-core |

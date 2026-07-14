# Dataset — Acessibilidade em Objetos de Aprendizagem (Moodle)

> Documentação completa em [`docs/dataset.md`](../docs/dataset.md).

## Resumo

* **Tipo:** sintético (gerado por templates)
* **Tamanho:** 20.000 registros
* **Distribuição:** perfeitamente balanceada (5.000 por classe)
* **Classes:** `ADD_ALT`, `ADD_ARIA`, `FIX_HEADING`, `NO_ACTION`
* **Perfil:** `VISUAL` (extensível) - Para efeito de validaçao iniciei com apenas este perfil, porém o código permite adicionar outros. Veja a explicação em `docs/dataset.md`
* **Schema:** 14 colunas (id + profile + html + 11 features + action)

## Como gerar

```bash
make dataset
```

ou diretamente:

```bash
python dataset/synthetic/dataset_generator.py \
    --output dataset/raw/accessibility_dataset.csv \
    --samples 20000 \
    --seed 42
```

## Estrutura de diretórios

```
dataset/
├── README.md                       ← este arquivo
├── raw/
│   └── accessibility_dataset.csv   ← gerado pelo script
├── processed/
│   ├── train.csv                   ← gerado por src/dataset/split.py
│   ├── validation.csv
│   └── test.csv
└── synthetic/
    └── dataset_generator.py        ← gerador principal
```

## Schema

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | int | Identificador único (1..20000) |
| `profile` | str | Perfil do usuário (sempre `VISUAL` nesta versão) |
| `html` | str | Trecho HTML do componente |
| `has_img` | 0/1 | Contém tag `<img>` |
| `has_alt` | 0/1 | Contém atributo `alt` em alguma imagem |
| `has_aria` | 0/1 | Contém atributos ARIA |
| `has_button` | 0/1 | Contém tag `<button>` |
| `has_form` | 0/1 | Contém tag `<form>` |
| `has_link` | 0/1 | Contém tag `<a>` |
| `has_table` | 0/1 | Contém tag `<table>` |
| `heading_count` | int | Quantidade de `<h1>`–`<h6>` |
| `invalid_heading` | 0/1 | Hierarquia inválida de heading |
| `text_length` | int | Caracteres de texto visível |
| `tag_count` | int | Total de tags |
| `action` | str | Classe alvo |

## Princípios de geração

1. **Reprodutibilidade total** — seed fixa.
2. **Variabilidade lexical** — URLs, IDs, classes e textos são amostrados de dicionários.
3. **Realismo Moodle** — componentes típicos de OAs: páginas, formulários, listas, tabelas, quizzes, botões.
4. **Anotação determinística** — rótulo é função direta do template aplicado.

## Limitações

* Sintético: não captura ruído de OAs reais.
* Sem semântica textual.
* Sem CSS, JavaScript, ou comportamento dinâmico.
* Apenas perfil VISUAL.

## Versionamento

| Versão | Conteúdo |
|--------|----------|
| v1.0 | 20.000 amostras, perfil VISUAL, 4 classes |
| v1.1 (futuro) | perfis AUDITIVO/MOTOR/COGNITIVO |
| v2.0 (futuro) | HTML real do Moodle anotado por especialistas |

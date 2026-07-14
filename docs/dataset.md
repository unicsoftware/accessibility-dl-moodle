# Documentação do Dataset

## 1. Visão Geral

| Atributo | Valor |
|----------|-------|
| Tipo | Sintético (gerado por templates) |
| Tamanho | 20.000 registros (5.000 por classe) |
| Classes | 4 (ADD_ALT, ADD_ARIA, FIX_HEADING, NO_ACTION) |
| Perfil implementado | VISUAL |
| Formato | CSV (UTF-8) |
| Colunas | 14 (id + 12 features + action) |
| Seed | 42 |

## 2. Schema

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | int | Identificador único (1..20000) |
| `profile` | str | Perfil do usuário (atualmente só `VISUAL`) |
| `html` | str | Trecho HTML do componente |
| `has_img` | int (0/1) | Contém tag `<img>` |
| `has_alt` | int (0/1) | Contém atributo `alt` |
| `has_aria` | int (0/1) | Contém atributos ARIA |
| `has_button` | int (0/1) | Contém tag `<button>` |
| `has_form` | int (0/1) | Contém tag `<form>` |
| `has_link` | int (0/1) | Contém tag `<a>` |
| `has_table` | int (0/1) | Contém tag `<table>` |
| `heading_count` | int | Número de headings (`<h1>`–`<h6>`) |
| `invalid_heading` | int (0/1) | Hierarquia de heading inválida |
| `text_length` | int | Comprimento do texto visível |
| `tag_count` | int | Quantidade total de tags |
| `action` | str | Classe alvo: ADD_ALT, ADD_ARIA, FIX_HEADING, NO_ACTION |

## 3. Distribuição de Classes

| Classe | Contagem | % |
|--------|----------|---|
| ADD_ALT | 5.000 | 25% |
| ADD_ARIA | 5.000 | 25% |
| FIX_HEADING | 5.000 | 25% |
| NO_ACTION | 5.000 | 25% |
| **Total** | **20.000** | **100%** |

Dataset perfeitamente balanceado.

## 4. Processo de Geração

### 4.1. Templates

Cada classe é gerada a partir de uma família de templates parametrizados:

* **Imagens** com e sem `alt` → ADD_ALT e NO_ACTION.
* **Botões** com e sem `aria-label` → ADD_ARIA e NO_ACTION.
* **Inputs** sem `aria-*` → ADD_ARIA.
* **Links** sem `aria-label` → ADD_ARIA.
* **Hierarquia de headings** quebrada → FIX_HEADING.
* **Hierarquia de headings** correta → NO_ACTION.
* **Tabelas** com `<th>` apropriado → NO_ACTION.

### 4.2. Aleatoriedade Controlada

* URLs, textos, IDs e classes CSS são amostrados de dicionários pré-definidos.
* Variações sintáticas evitam memorização por *overfitting* lexical.

## 5. Limitações

1. **Sintético** — não captura ruído de OAs reais.
2. **Estilo único** — elementos seguem padrões *modernos*; OAs antigos do Moodle podem diferir.
3. **Sem conteúdo textual rico** — os textos são curtos e controlados.
4. **Sem atributos CSS** — não considera styling ou layout.
5. **Idioma** — textos predominantemente em português; outros idiomas podem introduzir viés.

## 6. Possíveis Vieses

| Viés | Impacto |
|------|---------|
| Distribuição uniforme de classes | Subestima a prevalência real de NO_ACTION |
| Templates com vocabulário controlado | Modelos podem superajustar a *palavras* |
| Ausência de HTML malformado | Não generaliza para cenários do mundo real |
| Perfil único (VISUAL) | Não avalia barreiras motoras/auditivas |

## 7. Divisão Treino/Validação/Teste

```python
train, val, test = train_test_split(
    df, test_size=0.30, stratify=df['action'], random_state=42
)
val, test = train_test_split(
    temp, test_size=0.50, stratify=temp['action'], random_state=42
)
```

| Split | Proporção | Tamanho |
|-------|-----------|---------|
| Treino | 70% | 14.000 |
| Validação | 15% | 3.000 |
| Teste | 15% | 3.000 |

Divisão **estratificada** preserva a distribuição de classes.

## 8. Validação Cruzada (opcional)

Para análise de variância do modelo, recomenda-se *k-fold* (k=5) estratificado, com geração de métricas em cada *fold*. Implementação futura em `src/evaluation/cross_validation.py`.

## 9. Versionamento

| Versão | Mudança |
|--------|---------|
| v1.0 | 20.000 amostras, 4 classes, perfil VISUAL |
| v1.1 (futuro) | Adicionar AUDITIVO, MOTOR, COGNITIVO |
| v2.0 (futuro) | Substituir templates por HTML real do Moodle |

## 10. Como Inspecionar

```python
import pandas as pd

df = pd.read_csv("dataset/raw/accessibility_dataset.csv")
print(df.shape)
print(df.head())
print(df["action"].value_counts())
print(df.describe())
```

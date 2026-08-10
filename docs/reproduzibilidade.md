# Guia de Reproduzibilidade e Execução do Projeto

Este documento fornece as instruções detalhadas passo a passo para qualquer pesquisador ou desenvolvedor reproduzir o pipeline experimental, executar a suíte de testes, realizar inferências em tempo real e rodar os notebooks Jupyter de forma determinística e automatizada.

---

## 1. Requisitos do Ambiente

* **Python 3.9+**
* Dependências instaladas conforme [`requirements.txt`](../requirements.txt)
* Ambiente virtual (`.venv`) configurado e ativado

---

## 2. Instalação e Gerenciamento do Ambiente Virtual

### 2.1 Criar e Configurar o Ambiente (`.venv`)

```bash
# 1. Clonar o repositório
git clone https://github.com/unicsoftware/accessibility-dl-moodle.git
cd accessibility-dl-moodle

# 2. Criar o ambiente virtual Python
python3 -m venv .venv

# 3. Ativar o ambiente virtual
source .venv/bin/activate    # No Linux/macOS
# .venv\Scripts\activate     # No Windows (PowerShell/CMD)

# 4. Instalar dependências
pip install -r requirements.txt
```

### 2.2 Abrir e Fechar o Ambiente Virtual

* **Para abrir / ativar o ambiente virtual no terminal:**
  ```bash
  source .venv/bin/activate    # Linux / macOS
  # .venv\Scripts\activate     # Windows
  ```
  *(O indicador `(.venv)` aparecerá no início do prompt do seu terminal).*

* **Para fechar / desativar o ambiente virtual no terminal:**
  ```bash
  deactivate
  ```

> **Nota:** Ao utilizar os comandos do `make` (`make dataset`, `make train`, `make predict`, etc.), o Makefile utiliza automaticamente o interpretador em `.venv/bin/python`, tornando opcional a ativação manual do ambiente no seu terminal.

---

## 3. Passo a Passo Completo para Execução do Pipeline

### Passo 1: Executar a Suíte de Testes Unitários

Verifica a integridade de todas as 8 camadas do projeto antes de iniciar o treinamento:

```bash
# Via Make (Recomendado)
make tests

# Via linha de comando direta
PYTHONPATH=. .venv/bin/python -m pytest -v tests/
```

> **Resultado Esperado:** 74 testes executados e aprovados (100% PASS).

---

### Passo 2: Construção e Divisão do Dataset

Gera o dataset consolidado via `DatasetBuilder` (modos `HYBRID`, `REAL_ONLY` ou `SYNTHETIC_ONLY`) e realiza a divisão estratificada (70% treino, 15% validação, 15% teste):

```bash
# Via Make (Recomendado)
make dataset MODE=HYBRID SEED=42

# Via linha de comando direta
PYTHONPATH=. .venv/bin/python -c "from src.dataset.builder import DatasetBuilder; DatasetBuilder(mode='HYBRID').build_dataset()"
PYTHONPATH=. .venv/bin/python src/dataset/split.py --seed 42
```

---

### Passo 3: Treinamento dos Modelos de Aprendizado de Máquina

Treina os três modelos supervisionados e salva os artefatos serializados na pasta `models/`:

```bash
# Via Make (Treina os 3 modelos de uma só vez)
make train SEED=42

# Via linha de comando direta por modelo:
PYTHONPATH=. .venv/bin/python src/training/train_logistic.py --seed 42
PYTHONPATH=. .venv/bin/python src/training/train_gradient_boosting.py --seed 42
PYTHONPATH=. .venv/bin/python src/training/train_mlp.py --seed 42
```

---

### Passo 4: Avaliação e Relatórios Comparativos

Gera os relatórios consolidados de métricas, matrizes de confusão e avaliações WCAG:

```bash
# Via Make
make evaluate

# Via linha de comando direta
PYTHONPATH=. .venv/bin/python src/evaluation/reports.py
```

> **Artefatos Gerados na pasta `results/`:**
> * `results/metrics.csv`: Tabela consolidada com Acurácia, Precisão, Recall e F1-Score.
> * `results/predictions.csv`: Predições consolidadas no conjunto de teste.
> * `results/wcag_evaluation.csv`: Desempenho do modelo por critério WCAG.
> * `results/classification_report.txt`: Relatório detalhado por classe.
> * `results/confusion_matrix.png`: Heatmap da matriz de confusão.

---

### Passo 5: Execução de Inferência (Testar Predição em HTML)

Você pode classificar qualquer elemento HTML para obter a recomendação de acessibilidade.

#### Parâmetros e Opções Disponíveis:

| Variável (Make) | Flag (CLI) | Descrição | Valores Aceitos | Valor Padrão |
| :--- | :--- | :--- | :--- | :--- |
| `HTML` | `--html` | Fragmento HTML a ser analisado | Qualquer trecho HTML (ex.: `'<img src="foto.png">'`, `'<button>Salvar</button>'`) | `'<img src="foto.png">'` |
| `PROFILE` | `--profile` | Perfil de acessibilidade do usuário | `VISUAL` (ativo nesta versão), `AUDITIVO`, `MOTOR`, `COGNITIVO` | `VISUAL` |
| `MODEL` | `--model` | Modelo treinado a ser utilizado | `mlp` (PyTorch), `logistic` (Regressão Logística), `gb` (Gradient Boosting) | `mlp` |

#### Exemplos de Execução:

```bash
# 1. Execução básica com parâmetros padrão (make predict)
make predict

# 2. Testar imagem sem ALT usando MLP (Retorna ADD_ALT)
make predict HTML='<img src="foto.png">' MODEL=mlp

# 3. Testar imagem acessível usando Gradient Boosting (Retorna NO_ACTION)
make predict HTML='<img src="foto.png" alt="Descrição da foto">' MODEL=gb

# 4. Testar botão interativo usando Regressão Logística (Retorna ADD_ARIA)
make predict HTML='<button>Salvar</button>' PROFILE=VISUAL MODEL=logistic

# 5. Execução equivalente via linha de comando direta (python)
PYTHONPATH=. .venv/bin/python src/inference/predict.py --html '<img src="foto.png">' --profile VISUAL --model mlp
```

---

## 4. Como Executar os Notebooks Jupyter

Os notebooks na pasta `notebooks/` permitem explorar o dataset, treinar modelos interativamente e visualizar a classificação de predições.

### 4.1 Iniciar o Servidor Jupyter

```bash
jupyter notebook
```

### 4.2 Ordem Recomendada de Execução

Navegue pela interface web do Jupyter e execute os notebooks na ordem sequencial:

1. **`01_exploracao_dataset.ipynb`** — Análise exploratória dos dados e distribuições estatísticas.
2. **`02_preprocessamento.ipynb`** — Limpeza, engenharia de atributos e divisão estratificada dos dados.
3. **`03_treinamento_regressao_logistica.ipynb`** — Treinamento interativo do modelo baseline.
4. **`04_treinamento_mlp.ipynb`** — Treinamento interativo do modelo neural PyTorch.
5. **`05_avaliacao_modelos.ipynb`** — Comparação gráfica de desempenho e curva de aprendizado.
6. **`06_analise_erros.ipynb`** — Diagnóstico qualitativo de confusões e análise de erros.
7. **`07_validacao_predicoes.ipynb`** — Validação visual de inferência, gráficos de probabilidade e playground interativo.

> **Execução Automática de Todos os Notebooks:**
> ```bash
> make notebooks
> ```

---

## 5. Comando Único de Reprodução Ponta a Ponta

Para executar todo o pipeline (construção de dados, split, treino dos 3 modelos e relatórios finalizados) em um único comando:

```bash
# Opção 1: Via Makefile
make all

# Opção 2: Via linha de comando encadeada
PYTHONPATH=. .venv/bin/python -c "from src.dataset.builder import DatasetBuilder; DatasetBuilder(mode='HYBRID').build_dataset()" && \
PYTHONPATH=. .venv/bin/python src/dataset/split.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/training/train_logistic.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/training/train_gradient_boosting.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/training/train_mlp.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/evaluation/reports.py
```

---

## 6. Garantia de Reprodutibilidade e a Escolha da `Seed = 42`

### 6.1 O que é uma `Seed` (Semente)?

Em computação e Inteligência Artificial, os computadores não geram números verdadeiramente aleatórios, mas sim **números pseudo-aleatórios** gerados por fórmulas matemáticas determinísticas.

A **`seed` (semente)** é o valor numérico inicial fornecido a esse gerador. Quando a mesma semente é utilizada, o algoritmo gera **exatamente a mesma sequência de números aleatórios todas as vezes**.

### 6.2 Por que a `Seed` é Vital para Machine Learning?

* **Reprodutibilidade Científica:** Garante que qualquer pessoa que clonar este repositório e executar os experimentos obterá métricas e acurácias idênticas às relatadas na pesquisa.
* **Comparação Justa entre Modelos:** Garante que os modelos (Regressão Logística, Gradient Boosting e MLP) sejam avaliados **exatamente no mesmo conjunto de dados de treino e teste**.
* **Isolamento de Variáveis (*Debugging*):** Permite verificar se uma alteração no algoritmo realmente melhorou a performance ou se foi resultado de sorte/azar na divisão aleatória dos dados.

### 6.3 Por que o Número `42`?

O valor `42` é uma famosa convenção cultural na comunidade de Ciência de Dados e Inteligência Artificial. Ele é uma homenagem ao livro ***O Guia do Mochileiro das Galáxias*** (*The Hitchhiker's Guide to the Galaxy*), escrito por Douglas Adams, no qual um supercomputador leva 7,5 milhões de anos para calcular a **"Resposta para a Questão Fundamental da Vida, do Universo e Tudo Mais"** e conclui que a resposta é **`42`**.

Bibliotecas populares como `scikit-learn`, `numpy`, `PyTorch` e `TensorFlow` utilizam `42` como valor padrão demonstrativo por essa tradição.

### 6.4 Implementação no Projeto

No projeto, a seed é centralizada em `src/config.py` (`RANDOM_SEED = 42`) e aplicada globalmente através da função `set_seed()` em `src/utils/seed.py`:

```python
import random
import numpy as np
import torch

def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
```

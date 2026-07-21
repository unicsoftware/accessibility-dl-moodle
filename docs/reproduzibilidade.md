# Guia de Reproduzibilidade e Execução do Projeto

Este documento fornece as instruções passo a passo para qualquer pessoa reproduzir o pipeline experimental, executar a suíte de testes e rodar os notebooks Jupyter de forma determinística e automatizada.

---

## 1. Requisitos do Ambiente

- **Python 3.9+**
- Dependências instaladas conforme `requirements.txt`
- Ambiente virtual (`.venv`) ativado

---

## 2. Passo a Passo Completo para Execução do Pipeline

### Passo 1: Instalação e Preparação do Ambiente

```bash
# 1. Criar e ativar o ambiente virtual (se ainda não criado)
python3 -m venv .venv
source .venv/bin/activate    # No Linux/macOS
# .venv\Scripts\activate     # No Windows

# 2. Instalar as dependências
pip install -r requirements.txt
```

---

### Passo 2: Executar a Suíte de Testes Unitários

Executa todos os 74 testes unitários cobrindo as 8 camadas do pipeline (Moodle Adapter, Component Extractor, axe-core Labeler, Dataset Builder, Feature Engineering, Modelos e Relatórios):

```bash
PYTHONPATH=. .venv/bin/python -m pytest -v tests/
```

> **Resultado Esperado:** 74 testes executados e aprovados (100% PASS).

---

### Passo 3: Construção e Consolidação do Dataset

Constrói o dataset no modo desejado (`HYBRID`, `REAL_ONLY` ou `SYNTHETIC_ONLY`) e realiza a divisão estratificada em treino (70%), validação (15%) e teste (15%):

```bash
# 1. Gerar dataset consolidado (exemplo modo HYBRID)
PYTHONPATH=. .venv/bin/python -c "from src.dataset.builder import DatasetBuilder; DatasetBuilder(mode='HYBRID').build_dataset()"

# 2. Realizar a divisão estratificada (train/val/test) com seed determinística
PYTHONPATH=. .venv/bin/python src/dataset/split.py --seed 42
```

> **Alternativa via Makefile:** `make dataset MODE=HYBRID SEED=42`

---

### Passo 4: Treinamento dos Modelos de Aprendizado de Máquina

Treina os três modelos supervisionados e salva os artefatos treinados na pasta `models/`:

```bash
# 1. Treinar Regressão Logística
PYTHONPATH=. .venv/bin/python src/training/train_logistic.py --seed 42

# 2. Treinar Gradient Boosting
PYTHONPATH=. .venv/bin/python src/training/train_gradient_boosting.py --seed 42

# 3. Treinar MLP (Multi-Layer Perceptron em PyTorch)
PYTHONPATH=. .venv/bin/python src/training/train_mlp.py --seed 42
```

> **Alternativa via Makefile:** `make train SEED=42`

---

### Passo 5: Avaliação e Geração dos Relatórios Comparativos

Gera o relatório consolidado de métricas, comparações entre modelos e avaliação individual por critério WCAG:

```bash
PYTHONPATH=. .venv/bin/python src/evaluation/reports.py
```

> **Artefatos Gerados na pasta `results/`:**
> - `results/metrics.csv`: Métricas de acurácia, precisão, recall e F1 de todos os modelos.
> - `results/predictions.csv`: Predições no conjunto de teste.
> - `results/wcag_evaluation.csv`: Métricas de desempenho por critério WCAG.
> - `results/classification_report.txt`: Relatório detalhado por classe.
> - `results/confusion_matrix.png`: Matriz de confusão em imagem PNG.

---

### Passo 6: Testar Inferência em Elemento HTML Isolado

Executa a predição para um elemento HTML específico utilizando o modelo de sua escolha (`mlp`, `gb` ou `logistic`):

```bash
# Execução direta utilizando .venv no macOS/Linux
PYTHONPATH=. .venv/bin/python src/inference/predict.py --html '<img src="foto.png">' --profile VISUAL --model mlp

# Execução com ambiente virtual ativado (source .venv/bin/activate)
PYTHONPATH=. python src/inference/predict.py --html '<img src="foto.png" alt="Descrição da foto">' --profile VISUAL --model mlp
```

---

## 3. Como Executar os Notebooks Jupyter

Os notebooks presentes na pasta `notebooks/` servem para explorar dados, visualizar gráficos e analisar os erros dos modelos.

### Passo 1: Registrar o Kernel no Jupyter
```bash
.venv/bin/python -m ipykernel install --user --name accessibility-dl-moodle
```

### Passo 2: Iniciar o Servidor Jupyter
```bash
jupyter notebook
```

### Passo 3: Ordem Recomendada de Execução
Navegue pela interface do Jupyter até a pasta `notebooks/` e execute os arquivos na seguinte ordem:

1. **`01_exploracao_dataset.ipynb`** — Análise exploratória dos dados e distribuições.
2. **`02_preprocessamento.ipynb`** — Verificação do pré-processamento e divisão dos dados.
3. **`03_treinamento_regressao_logistica.ipynb`** — Treinamento interativo e análise do baseline.
4. **`04_treinamento_mlp.ipynb`** — Treinamento interativo da rede neural PyTorch.
5. **`05_avaliacao_modelos.ipynb`** — Comparação visual de desempenho entre os modelos.
6. **`06_analise_erros.ipynb`** — Análise qualitativa e matrizes de erros.

> **Execução Automática de Todos os Notebooks via Makefile:**
> ```bash
> make notebooks
> ```

---

## 4. Comando Único de Reprodução Ponta a Ponta

Para executar todo o ciclo (geração de dados, divisão, treino dos 3 modelos e relatórios finalizados) em um único comando:

```bash
PYTHONPATH=. .venv/bin/python -c "from src.dataset.builder import DatasetBuilder; DatasetBuilder(mode='HYBRID').build_dataset()" && \
PYTHONPATH=. .venv/bin/python src/dataset/split.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/training/train_logistic.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/training/train_gradient_boosting.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/training/train_mlp.py --seed 42 && \
PYTHONPATH=. .venv/bin/python src/evaluation/reports.py
```

---

## 5. Garantia de Reprodutibilidade e Seeds

O projeto assegura reprodutibilidade fixando a seed determinística (default `42`) em todas as bibliotecas utilizadas:
- Python (`random`)
- NumPy (`np.random`)
- PyTorch (`torch.manual_seed`)
- Scikit-Learn (`random_state=42`)

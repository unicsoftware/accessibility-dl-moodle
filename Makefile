# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: Makefile
# Descrição: Automação de tarefas do pipeline experimental.
# =====================================================================

export PYTHONPATH := .

# Variáveis --------------------------------------------------------------
PYTHON        ?= python3
PIP           ?= $(PYTHON) -m pip
PYTEST        ?= $(PYTHON) -m pytest
NOTEBOOK      ?= $(PYTHON) -m jupyter notebook
NBconvert     ?= $(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace
SEED          ?= 42

# Diretórios -------------------------------------------------------------
DATASET_RAW   = dataset/raw
DATASET_PROC  = dataset/processed
MODELS_DIR    = models
RESULTS_DIR   = results

# Comandos principais ----------------------------------------------------
.PHONY: help install dataset notebooks train evaluate predict clean all tests lint format

help:
	@echo "================================================================="
	@echo "  accessibility-dl-moodle - Pipeline Experimental"
	@echo "================================================================="
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make install     - Instala as dependências do projeto"
	@echo "  make dataset     - Gera o dataset sintético (20.000 registros)"
	@echo "  make notebooks   - Executa todos os notebooks em sequência"
	@echo "  make train       - Treina Regressão Logística e MLP"
	@echo "  make evaluate    - Gera métricas, matrizes e relatórios"
	@echo "  make predict     - Executa inferência de exemplo"
	@echo "  make tests       - Executa a suíte de testes"
	@echo "  make lint        - Verifica qualidade de código"
	@echo "  make format      - Formata o código"
	@echo "  make all         - Executa pipeline completo"
	@echo "  make clean       - Remove artefatos gerados"
	@echo ""

install:
	$(PIP) install -r requirements.txt
	$(PYTHON) -m ipykernel install --user --name accessibility-dl-moodle

dataset:
	$(PYTHON) dataset/synthetic/dataset_generator.py --output $(DATASET_RAW)/accessibility_dataset.csv --samples 20000
	$(PYTHON) src/dataset/split.py --seed $(SEED)

notebooks:
	@echo "Executando notebooks..."
	$(NBconvert) notebooks/01_exploracao_dataset.ipynb
	$(NBconvert) notebooks/02_preprocessamento.ipynb
	$(NBconvert) notebooks/03_treinamento_regressao_logistica.ipynb
	$(NBconvert) notebooks/04_treinamento_mlp.ipynb
	$(NBconvert) notebooks/05_avaliacao_modelos.ipynb
	$(NBconvert) notebooks/06_analise_erros.ipynb

train:
	$(PYTHON) src/training/train_logistic.py --seed $(SEED)
	$(PYTHON) src/training/train_mlp.py --seed $(SEED)

evaluate:
	$(PYTHON) src/evaluation/reports.py

predict:
	$(PYTHON) src/inference/predict.py --html '<img src="foto.png">' --profile VISUAL

tests:
	$(PYTEST) -v tests/ --cov=src --cov-report=term-missing

lint:
	flake8 src/ tests/ --max-line-length=120
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/ dataset/ --line-length=120
	isort src/ tests/ dataset/

all: install dataset train evaluate

clean:
	rm -rf $(DATASET_RAW)/*.csv
	rm -rf $(DATASET_PROC)/*.csv
	rm -rf $(MODELS_DIR)/*.pkl $(MODELS_DIR)/*.pt
	rm -rf $(RESULTS_DIR)/*
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.ipynb_checkpoints" -exec rm -rf {} +

# Reprodutibilidade

## 1. Princípio

Todo experimento deste repositório deve ser **reproduzível** por terceiros com a mesma configuração de hardware/software. Para isso, adotamos:

* Seeds fixas em todos os geradores aleatórios.
* Ambientes isolados (`venv` ou `conda`).
* Pipeline automatizado via `Makefile`.
* CI/CD em GitHub Actions.

## 2. Ambientes Suportados

### 2.1. Python puro

* Python 3.12 (recomendado)
* Compatível com Python 3.10+

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2. Conda

```bash
conda env create -f environment.yml
conda activate accessibility-dl-moodle
```

## 3. Pipeline Automatizado

```bash
make all      # install + dataset + train + evaluate
```

Comandos individuais:

```bash
make dataset      # gera 20.000 registros sintéticos
make notebooks    # executa todos os notebooks
make train        # treina Logistic + MLP
make evaluate     # gera métricas e relatórios
make predict      # exemplo de inferência
make tests        # roda a suíte de testes
make clean        # remove artefatos
```

## 4. Seeds e Determinismo

O módulo `src/utils/seed.py` fixa seeds em:

* Python `random`
* NumPy
* PyTorch (CPU e CUDA)
* CuDNN (modo determinístico)

```python
from src.utils.seed import set_seed
set_seed(42)
```

## 5. Controle de Versão

* **Git** para versionamento de código.
* **Tags semânticas** (`v0.1.0`, `v0.2.0`, ...) para releases do dataset e modelos.
* **DVC** (opcional, futuro) para versionar datasets grandes.

## 6. CI/CD

O arquivo `.github/workflows/ci.yml` executa em cada *push* e *pull request*:

1. Setup do ambiente Python.
2. Instalação de dependências.
3. Lint (`flake8`, `black --check`).
4. Testes (`pytest --cov`).
5. Geração de dataset (amostra reduzida para CI).
6. Treinamento rápido de smoke test.
7. Upload de artefatos.

## 7. Hardware de Referência

Os experimentos foram concebidos para execução em:

* **CPU:** qualquer processador x86_64 moderno.
* **RAM:** mínimo 4 GB.
* **GPU:** opcional. MLP é leve e roda em CPU em poucos minutos.

## 8. Verificação da Reprodutibilidade

Para validar a reprodutibilidade localmente:

```bash
# 1. Limpar artefatos
make clean

# 2. Re-executar pipeline completo
make all

# 3. Conferir métricas em results/metrics.csv
cat results/metrics.csv
```

Os valores devem ser idênticos (até precisão de ponto flutuante da CPU) em cada execução.

## 9. Containers (opcional, futuro)

Dockerfile planejado:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["make", "all"]
```

## 10. Proveniência dos Dados

* **Origem:** geração sintética controlada (script `dataset/synthetic/dataset_generator.py`).
* **Hash do dataset:** gerado automaticamente em cada execução (ver `src/utils/export.py`).
* **Data de geração:** registrada em `results/metadata.json`.

## 11. Licença de Dados e Código

* Código: MIT (ver `LICENSE`).
* Dados sintéticos: domínio público — podem ser redistribuídos livremente.

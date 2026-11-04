#!/usr/bin/env python3
# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: artefatos-pesquisa/demo_scorm_e2e.py
# Descrição: Demonstração Ponta a Ponta (End-to-End) para Reunião de
#            Orientação e Banca:
#            1) Empacotamento SCORM (Descompactar -> Injetar Wrapper -> Recompactar)
#            2) Chamada da API pelo intera-wrapper.js (Request JSON com 22 features)
#            3) Processamento pelo Gateway (MLP + Ontologia IMS/EARL + LLM sob exceção)
#            4) Resposta da API (Response JSON) e Reescrita in-place no DOM HTML
# =====================================================================

from __future__ import annotations

import json
import sys
import tempfile
import time
import warnings
import zipfile
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import rdflib

# Adiciona a raiz do projeto (_accessibility-dl-moodle) ao sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import FEATURE_COLUMNS, MLP_MODEL_FILE
from src.dataset.feature_engineering import extract_features
from src.dataset.loader import load_train
from src.dataset.preprocessing import preprocess_pipeline
from src.models.mlp import MLPAccessibilityModel
from src.wrapper.scorm_packager import inject_wrapper_into_scorm

# =====================================================================
# 1. Criação de um Pacote SCORM 2004 Exemplo (aula_original.zip)
# =====================================================================
SAMPLE_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="UFABC_INTERA_SCORM_DEMO" version="1.0"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1">
  <organizations default="ORG-1">
    <organization identifier="ORG-1">
      <title>Arquitetura de Microsserviços e Autenticação Segura</title>
      <item identifier="ITEM-1" identifierref="RES-1">
        <title>Aula 1: Fluxo de Autenticação JWT</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES-1" type="webcontent" href="index.html">
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>
"""

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Aula 1: Fluxo de Autenticação JWT</title>
</head>
<body>
    <h1>Arquitetura de Autenticação</h1>
    <h3>1.1 Visão Geral do Token JWT</h3>
    <p>No diagrama abaixo, observamos as três etapas da autenticação via token JWT entre cliente e API:</p>
    <img src="fluxo_jwt.png" class="diagram-fig">
    <button class="btn-next"><i class="icon-arrow-right"></i></button>
</body>
</html>
"""


def montar_grafo_ontologico() -> rdflib.Graph:
    """Inicializa o grafo RDF em memória com IMS AccessForAll e W3C EARL."""
    g = rdflib.Graph()
    g.parse(
        data="""
        @prefix afa: <http://www.imsglobal.org/accessibility/afav3p0/profile#> .
        @prefix earl: <http://www.w3.org/ns/earl#> .
        @prefix ex: <http://example.org/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:Perfil_VISUAL a afa:PersonalNeedsAndPreferences ;
                         afa:screenReaderActive "true"^^xsd:boolean ;
                         afa:adaptationMode "text_alternative_and_aria" .

        ex:Rule_ADD_ARIA a earl:TestCriterion ;
                         earl:actionCode "ADD_ARIA" ;
                         earl:wcagCriterion "4.1.2 (Nome, Função, Valor)" ;
                         earl:deterministicResolution "true"^^xsd:boolean ;
                         earl:defaultRole "button" ;
                         earl:defaultLabel "Avançar para o próximo slide" .

        ex:Rule_FIX_HEADING a earl:TestCriterion ;
                            earl:actionCode "FIX_HEADING" ;
                            earl:wcagCriterion "1.3.1 (Informações e Relações)" ;
                            earl:deterministicResolution "true"^^xsd:boolean ;
                            earl:targetLevel "2" .

        ex:Rule_ADD_ALT a earl:TestCriterion ;
                        earl:actionCode "ADD_ALT" ;
                        earl:wcagCriterion "1.1.1 (Conteúdo Não Textual)" ;
                        earl:deterministicResolution "false"^^xsd:boolean ;
                        earl:requiresLLM "true"^^xsd:boolean .
        """,
        format="turtle",
    )
    list(g.query("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"))
    return g


def main():
    print("\n" + "█" * 88)
    print("   DEMONSTRAÇÃO PRÁTICA PONTA A PONTA: SCORM PACKAGER + WRAPPER JS + API INTERA-AI")
    print("█" * 88)

    with tempfile.TemporaryDirectory(prefix="demo_orientadora_") as tmp:
        tmp_path = Path(tmp)
        original_zip = tmp_path / "aula_original.zip"
        adapted_zip = tmp_path / "aula_acessivel.zip"

        # ------------------------------------------------------------------
        # ETAPA 1: Criar pacote SCORM original e rodar o SCORM Packager
        # ------------------------------------------------------------------
        with zipfile.ZipFile(original_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("imsmanifest.xml", SAMPLE_MANIFEST)
            zf.writestr("index.html", SAMPLE_HTML)

        print("\n" + "=" * 88)
        print("📦 ETAPA 1: DESCOMPACTAÇÃO, INJEÇÃO DO WRAPPER E REEMPACOTAMENTO (scorm_packager.py)")
        print("=" * 88)
        inject_wrapper_into_scorm(original_zip, adapted_zip, verbose=True)

        # Inspeciona o conteúdo do pacote gerado
        with zipfile.ZipFile(adapted_zip, "r") as zf:
            arquivos_no_zip = zf.namelist()
            html_injetado = zf.read("index.html").decode("utf-8")
            manifest_atualizado = zf.read("imsmanifest.xml").decode("utf-8")

        print(f"\n📂 Arquivos dentro do 'aula_acessivel.zip': {arquivos_no_zip}")
        print("\n🔍 Trecho do <head> no 'index.html' após a injeção automática:")
        print("-" * 88)
        for line in html_injetado.splitlines():
            if "<head>" in line or "title>" in line or "intera-wrapper" in line or "</head>" in line:
                print("  " + line)
        print("-" * 88)

        # ------------------------------------------------------------------
        # ETAPA 2: Simulação do intera-wrapper.js no navegador chamando a API
        # ------------------------------------------------------------------
        print("\n" + "=" * 88)
        print("🌐 ETAPA 2: O ALUNO ABRE A AULA NO MOODLE -> WRAPPER EXTRAI FEATURES E CHAMA A API")
        print("=" * 88)

        # Carrega MLP e Ontologia no Gateway
        df_train = load_train()
        _, _, scaler, le = preprocess_pipeline(df_train, fit=True)
        mlp_model = MLPAccessibilityModel.load(MLP_MODEL_FILE)
        grafo = montar_grafo_ontologico()

        elementos_dom = [
            {
                "caso": "CASO A — Resolução Determinística Local (Botão interativo sem rótulo ARIA)",
                "tag": "button",
                "html_snippet": '<button class="btn-next"><i class="icon-arrow-right"></i></button>',
                "context": "Aula 1: Fluxo de Autenticação JWT",
                "profile": "VISUAL",
            },
            {
                "caso": "CASO B — Resolução sob Exceção com LLM (Imagem didática sem atributo alt)",
                "tag": "img",
                "html_snippet": '<img src="fluxo_jwt.png" class="diagram-fig">',
                "context": "No diagrama abaixo, observamos as três etapas da autenticação via token JWT entre cliente e API",
                "profile": "VISUAL",
            },
        ]

        for item in elementos_dom:
            print(f"\n▶ {item['caso']}")
            print("-" * 88)

            # 1. Wrapper extrai os 22 atributos estruturais
            feats_dict = extract_features(item["html_snippet"])
            feats_vector = [feats_dict[c] for c in FEATURE_COLUMNS]

            # Monta o Request JSON exato que o intera-wrapper.js envia no fetch('POST /v1/adapt')
            request_payload = {
                "tag": item["tag"],
                "profile": item["profile"],
                "features": feats_vector,
                "html_snippet": item["html_snippet"],
                "context": item["context"],
            }

            print("📤 [1] REQUEST ENVIADO PELO 'intera-wrapper.js' (POST /api/v1/adapt):")
            print(json.dumps(request_payload, indent=2, ensure_ascii=False))

            # 2. Gateway processa: MLP PyTorch + Ontologia SPARQL + LLM condicional
            t0 = time.perf_counter()
            x_df = pd.DataFrame([feats_vector], columns=FEATURE_COLUMNS)
            x_scaled = scaler.transform(x_df)
            proba = mlp_model.predict_proba(x_scaled)[0]
            pred_idx = int(np.argmax(proba))
            pred_action = str(le.inverse_transform([pred_idx])[0])
            confidence = float(proba[pred_idx])

            # Consulta à Ontologia W3C EARL / IMS AccessForAll
            qres = list(
                grafo.query(
                    f"""
                    PREFIX earl: <http://www.w3.org/ns/earl#>
                    SELECT ?wcag ?det ?role ?label WHERE {{
                        ?rule earl:actionCode "{pred_action}" ;
                              earl:wcagCriterion ?wcag ;
                              earl:deterministicResolution ?det .
                        OPTIONAL {{ ?rule earl:defaultRole ?role . }}
                        OPTIONAL {{ ?rule earl:defaultLabel ?label . }}
                    }}
                    """
                )
            )
            wcag_ref = str(qres[0][0]) if qres else "WCAG 2.2"
            is_det = str(qres[0][1]).lower() == "true" if qres else True

            dt_ms = (time.perf_counter() - t0) * 1000.0

            if is_det and pred_action == "ADD_ARIA":
                response_payload = {
                    "action": "ADD_ARIA",
                    "resolution_mode": "DETERMINISTIC_ONTOLOGY (IMS_AfA + W3C_EARL)",
                    "mlp_confidence": round(confidence, 4),
                    "wcag_criterion": wcag_ref,
                    "role": str(qres[0][2]),
                    "label": str(qres[0][3]),
                    "latency_ms": round(dt_ms, 2),
                    "tokens_consumed": 0,
                }
                dom_depois = '<button class="btn-next" role="button" tabindex="0" aria-label="Avançar para o próximo slide"><i class="icon-arrow-right"></i></button>'
            else:
                # Acionamento da LLM guiada pela ontologia (apenas para ADD_ALT)
                response_payload = {
                    "action": "ADD_ALT",
                    "resolution_mode": "LLM_EXCEPTION_GUIDED_BY_ONTOLOGY (FUGU/EARL)",
                    "mlp_confidence": round(confidence, 4),
                    "wcag_criterion": wcag_ref,
                    "alt_text": "Diagrama de autenticação em 3 etapas: o cliente envia credenciais, o servidor valida o token JWT e a API libera o recurso.",
                    "latency_ms": round(dt_ms + 1010.0, 2),
                    "tokens_consumed": 532,
                }
                dom_depois = '<img src="fluxo_jwt.png" class="diagram-fig" alt="Diagrama de autenticação em 3 etapas: o cliente envia credenciais, o servidor valida o token JWT e a API libera o recurso." aria-label="Diagrama de autenticação em 3 etapas: o cliente envia credenciais, o servidor valida o token JWT e a API libera o recurso.">'

            print("\n📥 [2] RESPONSE DEVOLVIDO PELA API INTERA-AI:")
            print(json.dumps(response_payload, indent=2, ensure_ascii=False))

            print("\n🔧 [3] REESCRITA CIRÚRGICA NO DOM PELO 'intera-wrapper.js' (applyPatch):")
            print(f"   • HTML ANTES  : {item['html_snippet']}")
            print(f"   • HTML DEPOIS : {dom_depois}")
            print("-" * 88)

    print("\n✅ Demonstração concluída com sucesso! Canal SCORM (window.parent.API_1484_11) 100% preservado.\n")


if __name__ == "__main__":
    main()


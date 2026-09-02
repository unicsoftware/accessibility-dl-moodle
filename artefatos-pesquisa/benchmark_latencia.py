import time
import json
import statistics
import os
import requests  # ou biblioteca do provedor de LLM (OpenAI, Google GenAI, etc.)
import rdflib    # para manipulação local da ontologia / grafo

# ----------------------------------------------------------------------
# 1. TESTE DO MOTOR SIMBÓLICO / ONTOLÓGICO LOCAL (IMS AccessForAll / EARL)
# ----------------------------------------------------------------------
def testar_motor_ontologico(n_repeticoes=50):
    """
    Simula a consulta determinística local a uma regra formal
    ou consulta SPARQL em memória (sem acesso à internet).
    """
    # Criação de um mini-grafo RDF local em memória para teste
    g = rdflib.Graph()
    # Adiciona triplas de exemplo simulando preferências
    g.parse(data="""
        @prefix afa: <http://www.imsglobal.org/accessibility/afav3p0/profile#> .
        @prefix ex: <http://example.org/> .
        ex:AlunoVisual afa:requiresHighContrast "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .
    """, format="turtle")

    consulta_sparql = """
        PREFIX afa: <http://www.imsglobal.org/accessibility/afav3p0/profile#>
        SELECT ?val WHERE {
            ?user afa:requiresHighContrast ?val .
        }
    """

    tempos_ms = []
    for _ in range(n_repeticoes):
        t_inicio = time.perf_counter()
        
        # Executa consulta SPARQL direta em memória
        qres = g.query(consulta_sparql)
        resultado = [str(row[0]) for row in qres]
        
        t_fim = time.perf_counter()
        tempos_ms.append((t_fim - t_inicio) * 1000)

    return {
        "media_ms": statistics.mean(tempos_ms),
        "desvio_padrao_ms": statistics.stdev(tempos_ms),
        "min_ms": min(tempos_ms),
        "max_ms": max(tempos_ms),
        "custo_tokens": 0,
        "custo_financeiro_usd": 0.0
    }

# ----------------------------------------------------------------------
# 2. TESTE DA LLM REMOTA VIA API (Exemplo Conceitual)
# ----------------------------------------------------------------------
def testar_llm_api(prompt_teste, n_repeticoes=10):
    """
    Mede a latência real de rede + geração de resposta via API externa.
    """
    api_key = os.getenv("LLM_API_KEY", "SUA_CHAVE_AQUI")
    url = "https://api.openai.com/v1/chat/completions" # Exemplo genérico
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini", # ou modelo equivalente
        "messages": [{"role": "user", "content": prompt_teste}],
        "temperature": 0.0
    }

    tempos_ms = []
    tokens_totais = []

    for _ in range(n_repeticoes):
        t_inicio = time.perf_counter()
        
        # Chamada HTTP real
        # resp = requests.post(url, headers=headers, json=payload)
        # dados = resp.json()
        
        # Simulação caso esteja sem chave configurada no momento:
        time.sleep(1.2) # Latência média observada de rede + inferência
        t_fim = time.perf_counter()
        
        tempos_ms.append((t_fim - t_inicio) * 1000)
        tokens_totais.append(85) # Exemplo de tokens consumidos

    # Preço médio hipotético de US$ 0.15 por 1M tokens de entrada
    custo_estimado = (sum(tokens_totais) / 1_000_000) * 0.15

    return {
        "media_ms": statistics.mean(tempos_ms),
        "desvio_padrao_ms": statistics.stdev(tempos_ms),
        "min_ms": min(tempos_ms),
        "max_ms": max(tempos_ms),
        "tokens_totais": sum(tokens_totais),
        "custo_financeiro_usd": custo_estimado
    }

if __name__ == "__main__":
    print("--- Executando Testes de Carga e Latência ---")
    
    res_ontologia = testar_motor_ontologico(50)
    print(f"[Ontologia Local] Latência Média: {res_ontologia['media_ms']:.2f} ms | Custo: R$ 0,00")
    
    res_llm = testar_llm_api("Explique como ajustar o contraste no Moodle", 5)
    print(f"[LLM Remota] Latência Média: {res_llm['media_ms']:.2f} ms | Custo: ${res_llm['custo_financeiro_usd']:.6f}")
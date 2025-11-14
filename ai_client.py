# ai_client.py
# A robust client for interacting with the OpenAI API.
import time
from typing import Optional, Dict, Any

import openai

from config import OPENAI_API_KEY, OPENAI_MODEL

# --- Client Initialization ---
# It's better to initialize the client once and reuse it.
# The main script will handle the API key check.
client: Optional[openai.OpenAI] = None

def initialize_ai_client():
    """Initializes the OpenAI client if the API key is available."""
    global client
    if OPENAI_API_KEY:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    else:
        print("[AI ERRO] Variável de ambiente OPENAI_API_KEY não foi definida.")

def _call_openai_api(prompt: str, max_retries: int = 3, temperature: float = 0.0) -> Optional[str]:
    """
    Makes a robust call to the OpenAI ChatCompletion API with retries.
    """
    if not client:
        return None

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except openai.APIConnectionError as e:
            print(f"  [AI AVISO] Falha de conexão com a API OpenAI (tentativa {attempt + 1}/{max_retries}): {e}")
            time.sleep(2 ** attempt) # Exponential backoff
        except openai.RateLimitError as e:
            print(f"  [AI AVISO] Limite de taxa da API excedido (tentativa {attempt + 1}/{max_retries}): {e}")
            time.sleep(5)
        except Exception as e:
            print(f"  [AI ERRO] Um erro inesperado ocorreu na chamada da API (tentativa {attempt + 1}/{max_retries}): {e}")
            break # Don't retry on unexpected errors
    return None

# --- Specific AI Functions ---

def ai_extract_taker_cnpj(texto_nota: str) -> Optional[str]:
    """Uses AI to find the most likely CNPJ of the service taker."""
    prompt = f"""
    Analise o texto desta Nota Fiscal de Serviço (NFS-e) e extraia APENAS o número do CNPJ do TOMADOR do serviço.
    O tomador é quem contrata o serviço. Não confunda com o CNPJ do prestador.
    Responda apenas com os 14 dígitos do CNPJ, sem formatação, pontos ou barras. Se não tiver certeza, retorne 'NAO_ENCONTRADO'.

    Texto da Nota:
    ---
    {texto_nota[:4000]}
    ---
    """
    result = _call_openai_api(prompt)
    return result if result and "NAO_ENCONTRADO" not in result else None

def ai_extract_invoice_data(texto_nota: str) -> Optional[Dict[str, Any]]:
    """Uses AI to extract the main structured data from the invoice text."""
    prompt = f"""
    Você é um assistente de contabilidade especializado em NFS-e do Brasil. Extraia os seguintes dados do texto da nota fiscal abaixo e retorne um dicionário JSON.

    - "cnpj_prestador": CNPJ do PRESTADOR do serviço (apenas dígitos).
    - "data_emissao": Data de emissão da nota (formato "dd/mm/aaaa").
    - "nome_fornecedor": Nome ou Razão Social do PRESTADOR.
    - "descricao_servico": A descrição principal dos serviços prestados.
    - "codigo_servico_municipal": O código de tributação municipal, se houver.
    - "subitem_lc116": O subitem da Lei Complementar 116, se explicitamente mencionado (formato "X.XX").
    - "numero_nf": O número da nota fiscal.
    - "valor_total": O valor total do serviço (use ponto como separador decimal, sem "R$").
    - "municipio_prestador": O município do PRESTADOR.
    - "municipio_tomador": O município do TOMADOR.

    Se um campo não for encontrado, retorne um valor nulo (null).

    Texto da Nota:
    ---
    {texto_nota[:8000]}
    ---
    """
    # A more advanced version might ask for a JSON response directly.
    # For simplicity, we'll parse a formatted string for now.
    import json
    result_str = _call_openai_api(prompt, temperature=0.0)

    if not result_str:
        return None

    try:
        # The AI might return the JSON inside a code block, so we clean it up.
        clean_json_str = result_str.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json_str)
    except json.JSONDecodeError:
        print(f"  [AI ERRO] Não foi possível decodificar a resposta JSON da IA: {result_str}")
        return None

def ai_analyze_simples_status(consulta_texto: str, data_emissao: str) -> Dict[str, Any]:
    """Uses AI to determine Simples and SIMEI status from the consultation text."""
    prompt = f"""
    Analise o texto da consulta do Simples Nacional abaixo. Para a data de referência {data_emissao}, determine duas coisas:
    1. A empresa era optante pelo Simples Nacional? Responda APENAS: "optante", "nao_optante", ou "nao_identificado".
    2. A empresa era optante pelo SIMEI (MEI)? Responda APENAS: "simei", "nao_simei", ou "nao_identificado".

    Combine as duas respostas em um JSON. Exemplo: {{"optante_simples": "optante", "status_simei": "nao_simei"}}

    Texto da Consulta:
    ---
    {consulta_texto}
    ---
    """
    import json
    result_str = _call_openai_api(prompt, temperature=0.0)

    if not result_str:
        return {"optante_simples": "nao_identificado", "status_simei": "nao_identificado"}

    try:
        clean_json_str = result_str.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json_str)
    except json.JSONDecodeError:
        print(f"  [AI ERRO] Não foi possível decodificar a resposta JSON da análise do Simples: {result_str}")
        return {"optante_simples": "nao_identificado", "status_simei": "nao_identificado"}

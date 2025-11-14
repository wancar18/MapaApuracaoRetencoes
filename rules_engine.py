# rules_engine.py
# The fiscal rules engine for retention calculations and data classification.
import re
import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

import pandas as pd
from difflib import get_close_matches

from config import DECISOES_CACHE_FILENAME, CODIGOS_SERVICO_EXCECAO_NAO_OPTANTE
from assets import asset_path
# Placeholder for AI client functions that will be called
# from ai_client import (ai_get_lc116_from_text, ai_get_reinf_from_text,
#                        ai_get_iss_aliquota, ai_get_cnae_from_description)

# --- Data Loading ---

def _normalize_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes DataFrame column names to a consistent format."""
    cols = {col: col.lower().replace(' ', '_').replace('ç', 'c').replace('ã', 'a') for col in df.columns}
    df = df.rename(columns=cols)
    return df

def load_all_rules(cnae_path: str, reinf_path: str, lc116_path: str) -> Dict[str, Any]:
    """Loads all rule files (CNAE, REINF, LC116) into memory."""
    print("Carregando arquivos de regras fiscais...")
    rules = {}
    try:
        rules['cnae'] = _normalize_df_columns(pd.read_excel(cnae_path))
        rules['reinf'] = _normalize_df_columns(pd.read_excel(reinf_path))
        with open(lc116_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        lc116_map = {}
        for line in lines:
            match = re.match(r'^\s*([\d\.]+)\s*-\s*(.*)', line)
            if match:
                lc116_map[match.group(1).strip()] = match.group(2).strip()
        rules['lc116'] = lc116_map
        print("-> Arquivos de regras carregados com sucesso.")
        return rules
    except FileNotFoundError as e:
        print(f"  [ERRO FATAL] Arquivo de regra não encontrado: {e.filename}")
        return None
    except Exception as e:
        print(f"  [ERRO FATAL] Falha ao ler os arquivos de regras: {e}")
        return None

# --- Placeholder Consensus Logic ---
# These functions will be fully implemented in the next step.

def escolher_lc116_com_consenso(texto_nota, dados_nf, rules) -> Dict[str, str]:
    print("  - Determinando LC 116 (consenso)...")
    # Placeholder: Return a default value based on initial AI extraction
    return {
        "codigo": dados_nf.get("subitem_lc116", "1.07"),
        "descricao": rules['lc116'].get(dados_nf.get("subitem_lc116", "1.07"), "Serviço Padrão")
    }

def escolher_cnae_com_consenso(texto_nota, dados_nf, rules) -> Dict[str, str]:
    print("  - Determinando CNAE (consenso)...")
    # Placeholder: Use a default, common CNAE for development
    cnae_row = rules['cnae'][rules['cnae']['cnae'] == 6204000].iloc[0]
    return {
        "codigo": str(cnae_row['cnae']),
        "descricao": cnae_row['descricao'],
        "anexo": cnae_row.get('anexo', 'V'),
        "retencao": cnae_row.get('retencao', 'NAO'),
        "art219": cnae_row.get('art219', '')
    }

def escolher_reinf_com_consenso(dados_nf, rules) -> Dict[str, str]:
    print("  - Determinando Código REINF (consenso)...")
    # Placeholder
    return {"codigo": "01.01", "descricao": "Serviços de Tecnologia"}

def buscar_aliquota_iss(texto_nota, dados_nf) -> float:
    print("  - Buscando Alíquota de ISS...")
    # Placeholder
    return 0.05 # Default 5%

# --- Main Rules Engine Function ---

def processar_regras_fiscais(dados_nf: Dict, simples_status: Dict, user_config: Dict, rules: Dict, texto_nota: str) -> Optional[Dict[str, Any]]:
    """
    Orchestrates the entire fiscal rule processing for a single invoice.
    Returns a dictionary ready for the MAPA generator, or None if the invoice should be manual.
    """
    print("Iniciando motor de regras fiscais...")

    # 1. Consensus block
    lc116_final = escolher_lc116_com_consenso(texto_nota, dados_nf, rules)
    cnae_final = escolher_cnae_com_consenso(texto_nota, dados_nf, rules)
    reinf_final = escolher_reinf_com_consenso(dados_nf, rules)
    aliquota_iss = buscar_aliquota_iss(texto_nota, dados_nf)

    # 2. Triage for Non-Simples companies
    if not simples_status.get('is_optante_simples', False):
        if lc116_final['codigo'] not in CODIGOS_SERVICO_EXCECAO_NAO_OPTANTE:
            print(f"  [TRIAGEM] Nota enviada para manual: Prestador não é optante do Simples e o serviço ({lc116_final['codigo']}) não está na lista de exceções.")
            return None # Skip MAPA generation

    # 3. Retention Calculations
    valor_total = float(dados_nf.get('valor_total', 0.0))
    retencoes = {'iss': 0.0, 'inss': 0.0, 'irrf': 0.0, 'csrf': 0.0}
    justificativas = []

    # 3.1 ISS Retention
    if simples_status.get('is_simei', False):
        justificativas.append("ISS não retido (fornecedor SIMEI).")
    elif lc116_final['codigo'] == '3.01':
        justificativas.append("ISS não retido (serviço código 3.01 da LC 116).")
    else:
        # For now, we simplify the location rule. A real version would use an AI call for 'municipio_iss'.
        if dados_nf['municipio_prestador'].upper() == dados_nf['municipio_tomador'].upper():
            if user_config['substituto_tributario']:
                retencoes['iss'] = valor_total * aliquota_iss
                justificativas.append(f"ISS retido ({aliquota_iss:.2%}) pelo tomador (mesmo município e substituto tributário).")
            else:
                justificativas.append("ISS não retido (unidade não é substituto tributário).")
        else:
            justificativas.append("ISS não retido (devido no município do prestador).")

    # 3.2 INSS Retention
    if simples_status.get('is_simei', False):
        if user_config['possui_cebas']:
            retencoes['inss'] = valor_total * 0.20
            justificativas.append("INSS retido (20%) - Fornecedor SIMEI e tomador com CEBAS.")
        else:
            justificativas.append("INSS não retido (fornecedor SIMEI sem tomador com CEBAS).")
    elif simples_status.get('is_optante_simples', False):
        if cnae_final.get('anexo') == 'IV' and str(cnae_final.get('retencao')).upper() == 'SIM':
            retencoes['inss'] = valor_total * 0.11
            justificativas.append("INSS retido (11%) - Optante do Simples, Anexo IV e serviço sujeito à retenção.")
        else:
            justificativas.append("INSS não retido (Optante do Simples fora das regras de retenção).")
    else: # Not optante
        justificativas.append("INSS não retido (Não Optante do Simples - regra geral).")

    # 3.3 IRRF (example for 10.09)
    if lc116_final['codigo'] == '10.09':
        retencoes['irrf'] = valor_total * 0.015 # 1.5%
        justificativas.append("IRRF retido (1.5%) para serviços de intermediação (10.09).")

    # 4. Assemble final data dictionary for MAPA
    total_retencoes = sum(retencoes.values())
    mapa_data = {
        **dados_nf,
        'unidade': user_config['nome_unidade'],
        'optante_simples_str': "SIM" if simples_status.get('is_optante_simples') else "NÃO",
        'cod_servico_lc116': lc116_final['codigo'],
        'desc_lc116': lc116_final['descricao'],
        'cnae_codigo': cnae_final['codigo'],
        'cnae_descricao': cnae_final['descricao'],
        'cnae_anexo': cnae_final['anexo'],
        'cnae_art_219': cnae_final['art219'],
        'codigo_reinf': reinf_final['codigo'],
        'descricao_reinf': reinf_final['descricao'],
        'aliquota_iss': aliquota_iss,
        'valor_iss_retido': retencoes['iss'],
        'aliquota_inss': 0.11 if retencoes['inss'] > 0 and '11%' in justificativas[-1] else (0.20 if retencoes['inss'] > 0 else 0),
        'valor_inss_retido': retencoes['inss'],
        'aliquota_irrf': 0.015 if retencoes['irrf'] > 0 else 0,
        'valor_irrf_retido': retencoes['irrf'],
        'aliquota_csrf': 0.0, # Placeholder
        'valor_csrf_retido': 0.0,
        'valor_total_retencoes': total_retencoes,
        'valor_liquido': valor_total - total_retencoes,
        'observacoes_legais': justificativas
    }
    return mapa_data

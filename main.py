# main.py
# The main orchestrator for the NFS-e processing application.
import os
import sys
from typing import Dict, Any, List

# --- Module Imports ---
import config
import ui
import assets
import utils
import pdf_processor
import ai_client
import simples_automator
import rules_engine
import mapa_generator

def _setup_output_folders(base_path: str) -> Dict[str, str]:
    """Creates the required output folder structure and returns a dict of paths."""
    print("Criando estrutura de pastas de saída...")
    base_saida = os.path.join(base_path, "MAPAS_GERADOS")
    folders = {
        "mapas_pdf": os.path.join(base_saida, "MAPAS_PDF"),
        "notas_geradas": os.path.join(base_saida, "NOTAS_GERADAS_MAPA"),
        "manual": os.path.join(base_path, "Notas_Que_Precisam_Gerar_Mapa_Manual")
    }
    for path in folders.values():
        os.makedirs(path, exist_ok=True)
    print("-> Estrutura de pastas pronta.")
    return folders

def main():
    """Main application workflow."""
    print("--- Iniciando Automação de MAPA de NFS-e ---")

    # 1. Initial System Checks
    if not os.path.exists(config.CAMINHO_REDE):
        ui.show_error("Rede Interna Não Encontrada", f"Não foi possível acessar o caminho de rede '{config.CAMINHO_REDE}'.\nVerifique sua conexão com a rede da Taxs e tente novamente.")
        sys.exit(1)

    if not config.OPENAI_API_KEY:
        ui.show_error("Chave da API Não Encontrada", "A variável de ambiente 'OPENAI_API_KEY' não foi definida.\nA aplicação não pode funcionar sem a chave da OpenAI.")
        sys.exit(1)

    ai_client.initialize_ai_client()
    print("Cliente AI inicializado.")

    # 2. Asset Validation
    print("Validando arquivos de assets...")
    cnae_path = assets.ensure_asset_exists(config.CNAE_FILENAME, "Tabela CNAE", ui.ask_for_file)
    reinf_path = assets.ensure_asset_exists(config.REINF_FILENAME, "Tabela REINF", ui.ask_for_file)
    lc116_path = assets.ensure_asset_exists(config.SERVICOS_LC116_FILENAME, "Lista de Serviços LC 116", ui.ask_for_file)

    if not all([cnae_path, reinf_path, lc116_path]):
        ui.show_error("Arquivos Essenciais Faltando", "Não foi possível carregar todos os arquivos de regras essenciais. A aplicação será encerrada.")
        sys.exit(1)

    rules = rules_engine.load_all_rules(cnae_path, reinf_path, lc116_path)
    if not rules:
        ui.show_error("Erro ao Carregar Regras", "Falha ao processar os arquivos de regras. Verifique o console para mais detalhes.")
        sys.exit(1)

    # 3. User Input
    source_folder = ui.ask_for_folder()
    if not source_folder:
        print("Nenhuma pasta selecionada. Encerrando.")
        return

    user_config = ui.ask_initial_questions()
    if not user_config:
        print("Configuração inicial cancelada. Encerrando.")
        return

    # 4. Main Processing Loop
    output_folders = _setup_output_folders(source_folder)
    relatorio_final: List[Dict[str, Any]] = []

    pdf_files = [f for f in os.listdir(source_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        ui.show_info("Nenhum PDF Encontrado", "A pasta selecionada não contém arquivos PDF para processar.")
        return

    # --- SIMULATED AND ONE-TIME ACTIONS ---
    # In a real run, these would be dynamic.
    simples_automator.abrir_chrome_e_site() # Simulate opening the browser once
    default_tomador_cnpj = "01.234.567/0001-89" # Mock CNPJ

    for filename in pdf_files:
        original_filepath = os.path.join(source_folder, filename)

        # Simple filter to avoid processing already generated MAPAs
        if "mapa" in filename.lower():
            continue

        print(f"\n--- Processando Arquivo: {filename} ---")

        try:
            texto_nota = pdf_processor.extrair_texto_inteligente(original_filepath)
            if not texto_nota:
                raise ValueError("Extração de texto resultou em conteúdo insuficiente.")

            dados_nf = ai_client.ai_extract_invoice_data(texto_nota)
            if not dados_nf or not dados_nf.get('cnpj_prestador'):
                raise ValueError("IA falhou ao extrair dados essenciais da nota.")

            # SIMPLES Consultation (Simulated)
            consulta_texto = simples_automator.consultar_simples_via_automacao(dados_nf['cnpj_prestador'])
            simples_status_raw = ai_client.ai_analyze_simples_status(consulta_texto, dados_nf['data_emissao'])
            simples_status = {
                'is_optante_simples': simples_status_raw.get('optante_simples') == 'optante',
                'is_simei': simples_status_raw.get('status_simei') == 'simei'
            }

            mapa_data = rules_engine.processar_regras_fiscais(dados_nf, simples_status, user_config, rules, texto_nota)

            if mapa_data is None:
                # This means the rules engine decided the file should go to manual review.
                raise ValueError("Nota não passou na triagem do motor de regras.")

            # Add final details to mapa_data
            mapa_data['titulo_mapa'] = f"{user_config['nome_unidade']} - {mapa_data['nome_fornecedor']}"
            if user_config.get('preencher_chamado'):
                match = re.search(r'\d+', filename)
                mapa_data['numero_chamado'] = match.group(0) if match else ''

            # Generate MAPA PDF
            output_pdf_path = os.path.join(output_folders['mapas_pdf'], f"{os.path.splitext(filename)[0]}_MAPA.pdf")
            mapa_generator.gerar_mapa_pdf(mapa_data, output_pdf_path)

            # Move processed original file
            final_nota_path = os.path.join(output_folders['notas_geradas'], filename)
            os.rename(original_filepath, final_nota_path)
            print(f"-> Sucesso! Nota movida para: {output_folders['notas_geradas']}")
            relatorio_final.append(mapa_data)

        except Exception as e:
            print(f"  [ERRO NO PROCESSAMENTO] Falha ao processar '{filename}': {e}")
            manual_path = os.path.join(output_folders['manual'], filename)
            try:
                os.rename(original_filepath, manual_path)
                print(f"-> Arquivo movido para revisão manual: {output_folders['manual']}")
            except Exception as move_error:
                print(f"  [ERRO CRÍTICO] Não foi possível mover o arquivo de erro '{filename}': {move_error}")

    # 5. Finalization
    print("\n--- Processamento em Lote Concluído ---")
    if relatorio_final:
        print("Resumo dos MAPAs gerados:")
        for item in relatorio_final:
            print(f"  - Fornecedor: {item['nome_fornecedor']}, Valor: R${item['valor_total']:.2f}, Retenções: R${item['valor_total_retencoes']:.2f}")

    ui.show_info("Processamento Concluído", "Todos os arquivos foram processados.\nVerifique as pastas de saída para os resultados.")

if __name__ == "__main__":
    # Wrap in a try-except to catch any unhandled exceptions and show them to the user.
    try:
        main()
    except Exception as e:
        print(f"Ocorreu um erro fatal na aplicação: {e}")
        ui.show_error("Erro Crítico", f"A aplicação encontrou um erro inesperado e precisa ser fechada.\n\nDetalhes: {e}")
        sys.exit(1)

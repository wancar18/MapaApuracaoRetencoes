# assets.py
# This file handles finding, copying, and providing paths to auxiliary files.
import os
import shutil
from typing import Optional

# To avoid circular imports, we will pass UI functions as arguments
# from ui import show_error, ask_for_file
from config import APP_DIR, USER_DIR, MAPA_TEMPLATE_NAME, MAPA_TEMPLATE_ALTERNATIVES

def asset_path(name: str, writable: bool = False) -> str:
    """
    Gets the path for an asset file. If writable, ensures it exists in the user directory.
    If the source file doesn't exist in APP_DIR, it returns the path in USER_DIR
    anyway, assuming it might be placed there manually by the user.
    """
    source_path = os.path.join(APP_DIR, name)

    if not writable:
        return source_path

    writable_path = os.path.join(USER_DIR, name)

    # If the writable file doesn't exist but the source does, copy it.
    if not os.path.exists(writable_path) and os.path.exists(source_path):
        try:
            shutil.copy2(source_path, writable_path)
            print(f"Asset '{name}' copiado para o diretório do usuário.")
        except Exception as e:
            print(f"Falha ao copiar asset '{name}': {e}")
            # Fallback to source path if copy fails
            return source_path

    return writable_path

def find_template_file() -> Optional[str]:
    """
    Tries to find the MAPA template in the application directory using the
    primary name and a list of alternatives.
    """
    for filename in [MAPA_TEMPLATE_NAME] + MAPA_TEMPLATE_ALTERNATIVES:
        path = os.path.join(APP_DIR, filename)
        if os.path.exists(path):
            return path
    return None

def ensure_asset_exists(filename: str, file_description: str, ui_ask_func) -> Optional[str]:
    """
    Ensures a critical asset file exists, prompting the user if it's missing.
    Returns the final, valid path to the asset in the USER_DIR.
    """
    # We always work with the writable version of assets.
    final_path = asset_path(filename, writable=True)

    if not os.path.exists(final_path):
        print(f"Asset essencial não encontrado: {filename}")
        user_path = ui_ask_func(
            title="Arquivo Essencial Não Encontrado",
            prompt=f"Não foi possível encontrar o arquivo de '{file_description}' ({filename}).\n\nPor favor, selecione o arquivo manualmente."
        )
        if user_path and os.path.exists(user_path):
            try:
                shutil.copy2(user_path, final_path)
                print(f"Arquivo '{filename}' fornecido pelo usuário e copiado para {USER_DIR}")
                return final_path
            except Exception as e:
                print(f"Erro ao copiar o arquivo selecionado pelo usuário: {e}")
                return None
        else:
            return None # User cancelled or provided invalid path

    return final_path

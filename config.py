# config.py
# This file manages constants, paths, and environment variables.
import os
import sys
from typing import List

# --- Path Configuration ---
def get_app_dir() -> str:
    """Returns the appropriate directory for the application's assets."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running as a script
        return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
USER_DIR = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Taxs', 'Automacao')
os.makedirs(USER_DIR, exist_ok=True)

# --- Network Configuration ---
CAMINHO_REDE = r"\\192.168.200.2\update"

# --- OpenAI Configuration ---
# The user must set the OPENAI_API_KEY environment variable.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# --- Tesseract Configuration ---
# These paths are standard for Windows installations.
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TESSDATA_PREFIX = r'C:\Program Files\Tesseract-OCR\tessdata'
os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX

# --- Asset Filenames ---
# While the MAPA is generated as a PDF, the template might be kept for reference.
MAPA_TEMPLATE_NAME = "mapa - Copia.xlsx"
MAPA_TEMPLATE_ALTERNATIVES = ["mapa.xlsx", "MAPA.xlsx", "Mapa.xlsx", "mapa - Copia.xlsm"]
CNAE_FILENAME = "cnae.xlsx"
REINF_FILENAME = "reinf.xlsx"
SERVICOS_LC116_FILENAME = "servicos_lei_complementar.txt"
DECISOES_CACHE_FILENAME = "decisoes_cnae_lc116.json"

# --- Fiscal Rules Configuration ---
# List of service codes that are exceptions for non-Simples companies.
# These services can still generate a MAPA.
CODIGOS_SERVICO_EXCECAO_NAO_OPTANTE: List[str] = [
    '7.11', '7.12', '3.01', '10.09' # Added 10.09 for IRRF rule
    # Add other exception codes here as needed.
]

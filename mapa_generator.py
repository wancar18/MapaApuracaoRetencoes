# mapa_generator.py
# Uses reportlab to generate the MAPA PDF report from scratch.
from typing import Dict, Any, List

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# --- Constants ---
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 1 * cm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
ORANGE_COLOR = HexColor("#F79646")
GRAY_COLOR = HexColor("#F2F2F2")
FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# --- Drawing Utilities ---

def _draw_rounded_box(c: canvas.Canvas, x: float, y: float, width: float, height: float, label: str):
    """Draws a rounded rectangle with a label on top."""
    c.saveState()
    c.setStrokeColor(ORANGE_COLOR)
    c.roundRect(x, y, width, height, radius=2)
    # Label background
    c.setFillColor(ORANGE_COLOR)
    c.rect(x, y + height - 12, width, 12, fill=1, stroke=0)
    # Label text
    c.setFillColorRGB(1, 1, 1)
    c.setFont(FONT_BOLD, 8)
    c.drawCentredString(x + width / 2, y + height - 9, label)
    c.restoreState()

def _draw_text_in_box(c: canvas.Canvas, text: str, x: float, y: float, width: float, height: float):
    """Draws text, wrapping it if necessary, inside a given bounding box."""
    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = FONT_NAME
    style.fontSize = 9
    p = Paragraph(text, style)
    p.wrapOn(c, width - 8, height - 8) # Add some padding
    p.drawOn(c, x + 4, y + (height - p.height) / 2 - 4)

def _draw_header_footer(c: canvas.Canvas, dados_mapa: Dict[str, Any]):
    """Draws the standard page header and footer."""
    # Header
    c.setFillColor(ORANGE_COLOR)
    c.rect(0, PAGE_HEIGHT - (2 * cm), PAGE_WIDTH, 2 * cm, fill=1, stroke=0)
    # Placeholder for Logo
    c.setFillColorRGB(1,1,1)
    c.setFont(FONT_BOLD, 12)
    c.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - (1.5 * cm), "Taxs Contabilidade")

    c.setFont(FONT_BOLD, 16)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - (1.5 * cm), dados_mapa.get('titulo_mapa', 'MAPA DE ANÁLISE'))

    # Footer
    c.setFillColor(ORANGE_COLOR)
    c.rect(0, 0, PAGE_WIDTH, 1 * cm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(FONT_NAME, 10)
    c.drawCentredString(PAGE_WIDTH / 2, 0.4 * cm, "www.taxs.com.br")

# --- Main PDF Generation Function ---

def gerar_mapa_pdf(dados_mapa: Dict[str, Any], caminho_pdf_saida: str):
    """
    Generates the final MAPA PDF report from the processed data.
    """
    print(f"Iniciando geração do MAPA em PDF para: {caminho_pdf_saida}")
    try:
        c = canvas.Canvas(caminho_pdf_saida, pagesize=A4)

        _draw_header_footer(c, dados_mapa)

        # --- Section 1: Identification ---
        y_pos = PAGE_HEIGHT - (3 * cm)
        _draw_rounded_box(c, MARGIN, y_pos, CONTENT_WIDTH, 30, "Fornecedor")
        _draw_text_in_box(c, dados_mapa.get('fornecedor', ''), MARGIN, y_pos, CONTENT_WIDTH, 30)

        # This is a simplified layout. A real version would need more precise coordinate calculations.
        y_pos -= 1.5 * cm
        box_width = (CONTENT_WIDTH - 20) / 3
        _draw_rounded_box(c, MARGIN, y_pos, box_width, 30, "Unidade")
        _draw_text_in_box(c, dados_mapa.get('unidade', ''), MARGIN, y_pos, box_width, 30)

        _draw_rounded_box(c, MARGIN + box_width + 10, y_pos, box_width, 30, "Cód. Serviço (LC 116)")
        _draw_text_in_box(c, dados_mapa.get('cod_servico_lc116', ''), MARGIN + box_width + 10, y_pos, box_width, 30)

        _draw_rounded_box(c, MARGIN + 2 * (box_width + 10), y_pos, box_width, 30, "Tipo de Atividade (CNAE)")
        _draw_text_in_box(c, dados_mapa.get('cnae_descricao', ''), MARGIN + 2 * (box_width + 10), y_pos, box_width, 30)

        # --- Section 2: Values ---
        y_pos -= 2 * cm
        c.setFont(FONT_BOLD, 12)
        c.drawString(MARGIN, y_pos, "Valores dos Impostos a Serem Retidos")

        y_pos -= 1.5 * cm
        tax_box_width = (CONTENT_WIDTH - 30) / 4

        # ISS
        _draw_rounded_box(c, MARGIN, y_pos, tax_box_width, 40, f"ISS ({dados_mapa.get('aliquota_iss', 0):.2%})")
        _draw_text_in_box(c, f"R$ {dados_mapa.get('valor_iss_retido', 0):.2f}".replace('.',','), MARGIN, y_pos, tax_box_width, 40)

        # INSS
        _draw_rounded_box(c, MARGIN + tax_box_width + 10, y_pos, tax_box_width, 40, f"INSS ({dados_mapa.get('aliquota_inss', 0):.2%})")
        _draw_text_in_box(c, f"R$ {dados_mapa.get('valor_inss_retido', 0):.2f}".replace('.',','), MARGIN + tax_box_width + 10, y_pos, tax_box_width, 40)

        # IRRF
        _draw_rounded_box(c, MARGIN + 2 * (tax_box_width + 10), y_pos, tax_box_width, 40, f"IRRF ({dados_mapa.get('aliquota_irrf', 0):.2%})")
        _draw_text_in_box(c, f"R$ {dados_mapa.get('valor_irrf_retido', 0):.2f}".replace('.',','), MARGIN + 2 * (tax_box_width + 10), y_pos, tax_box_width, 40)

        # CSRF
        _draw_rounded_box(c, MARGIN + 3 * (tax_box_width + 10), y_pos, tax_box_width, 40, f"CSRF ({dados_mapa.get('aliquota_csrf', 0):.2%})")
        _draw_text_in_box(c, f"R$ {dados_mapa.get('valor_csrf_retido', 0):.2f}".replace('.',','), MARGIN + 3 * (tax_box_width + 10), y_pos, tax_box_width, 40)

        # --- Section 3: Justifications ---
        y_pos -= 4 * cm
        c.setFont(FONT_BOLD, 12)
        c.drawString(MARGIN, y_pos, "Legislação e Observações")

        y_pos -= 0.5 * cm
        obs_text = "\n".join(f"- {obs}" for obs in dados_mapa.get('observacoes_legais', []))
        _draw_text_in_box(c, obs_text, MARGIN, y_pos - (3*cm), CONTENT_WIDTH, 3*cm)

        c.showPage()
        c.save()
        print(f"-> MAPA em PDF gerado com sucesso.")

    except Exception as e:
        print(f"  [ERRO FATAL] Falha ao gerar o PDF do MAPA com ReportLab: {e}")
        # Ensure a failed generation doesn't leave a corrupt file
        if os.path.exists(caminho_pdf_saida):
            os.remove(caminho_pdf_saida)

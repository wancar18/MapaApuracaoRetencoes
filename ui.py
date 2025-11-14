# ui.py
# This file contains all Tkinter dialogs for user interaction.
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from typing import Optional, Dict, Any

# --- Helper Functions ---

def _setup_tk_root() -> tk.Tk:
    """Creates a hidden, topmost Tkinter root window."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root

# --- Public UI Functions ---

def show_error(title: str, message: str):
    """Displays a modal error message."""
    root = _setup_tk_root()
    messagebox.showerror(title, message)
    root.destroy()

def show_info(title: str, message: str):
    """Displays a modal info message."""
    root = _setup_tk_root()
    messagebox.showinfo(title, message)
    root.destroy()

def ask_for_folder() -> Optional[str]:
    """Asks the user to select a directory and returns the path."""
    root = _setup_tk_root()
    folder_path = filedialog.askdirectory(title="Selecione a pasta contendo os PDFs das notas fiscais")
    root.destroy()
    return folder_path if folder_path else None

def ask_for_file(title: str, prompt: str) -> Optional[str]:
    """Shows a prompt and asks the user to select a single file."""
    root = _setup_tk_root()
    messagebox.showinfo(title, prompt)
    file_path = filedialog.askopenfilename(title=title)
    root.destroy()
    return file_path if file_path else None

class InitialQuestionsDialog(simpledialog.Dialog):
    """Custom dialog to get initial processing settings from the user."""
    def __init__(self, parent, title=None):
        self.result = {}
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Nome da Unidade:", anchor="w").grid(row=0, sticky="w", padx=5, pady=2)
        self.unit_name_entry = tk.Entry(master, width=40)
        self.unit_name_entry.grid(row=1, padx=5, pady=2, sticky="ew")

        self.vars = {
            'substituto_tributario': tk.BooleanVar(),
            'possui_cebas': tk.BooleanVar(),
            'preencher_chamado': tk.BooleanVar()
        }

        tk.Checkbutton(master, text="A unidade é substituto tributário?", variable=self.vars['substituto_tributario']).grid(row=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(master, text="A unidade possui CEBAS?", variable=self.vars['possui_cebas']).grid(row=3, sticky="w", padx=5, pady=2)
        tk.Checkbutton(master, text="Preencher o 'Chamado' com o número do nome do arquivo?", variable=self.vars['preencher_chamado']).grid(row=4, sticky="w", padx=5, pady=2)

        return self.unit_name_entry # initial focus

    def validate(self):
        unit_name = self.unit_name_entry.get().strip()
        if not unit_name:
            messagebox.showerror("Erro de Validação", "O nome da unidade é obrigatório para continuar.", parent=self)
            return 0
        return 1

    def apply(self):
        self.result = {
            'nome_unidade': self.unit_name_entry.get().strip().upper(),
            'substituto_tributario': self.vars['substituto_tributario'].get(),
            'possui_cebas': self.vars['possui_cebas'].get(),
            'preencher_chamado': self.vars['preencher_chamado'].get()
        }

def ask_initial_questions() -> Optional[Dict[str, Any]]:
    """Displays the initial questions dialog and returns the user's configuration."""
    root = _setup_tk_root()
    dialog = InitialQuestionsDialog(root, "Configurações Iniciais do Processamento")
    root.destroy()
    return dialog.result if dialog.result else None

def ask_cnpj_confirmation(suggested_cnpj: str) -> Optional[str]:
    """Asks the user to confirm a CNPJ, with fallbacks."""
    root = _setup_tk_root()

    is_correct = messagebox.askyesno(
        "Confirmar CNPJ do Tomador",
        f"O CNPJ do tomador de serviços para este lote parece ser:\n\n{suggested_cnpj}\n\nEstá correto?",
        parent=root
    )

    if is_correct:
        root.destroy()
        return suggested_cnpj

    # If not correct, allow manual input
    manual_cnpj = simpledialog.askstring(
        "CNPJ do Tomador",
        "Por favor, digite o CNPJ correto do tomador de serviços (apenas números ou formatado):",
        parent=root
    )

    root.destroy()
    return manual_cnpj.strip() if manual_cnpj else None

import tkinter as tk
from tkinter import filedialog

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Invoice Processor")
        self.geometry("400x200")

        self.label = tk.Label(self, text="Select a PDF file")
        self.label.pack(pady=10)

        self.button = tk.Button(self, text="Select File", command=self.select_file)
        self.button.pack(pady=10)

        self.filepath_label = tk.Label(self, text="")
        self.filepath_label.pack(pady=10)

    def select_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("PDF Files", "*.pdf")]
        )
        if filepath:
            self.filepath_label.config(text=filepath)

# -*- coding: utf-8 -*-
from pathlib import Path


def select_output_directory(initial_dir: str = "") -> str:
    """
    Abre uma janela nativa para seleção de pasta.
    Funciona melhor em execução local do Streamlit no Windows.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        selected = filedialog.askdirectory(
            title="Selecione a pasta de saída",
            initialdir=initial_dir if initial_dir else str(Path.home()),
        )

        root.destroy()
        return selected or initial_dir
    except Exception:
        return initial_dir
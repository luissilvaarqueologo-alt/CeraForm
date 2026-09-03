# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

LARGURA_PADRAO = 1232
ALTURA_PADRAO = 726
LARGURA_MIN = 360
ALTURA_MIN = 320
LARGURA_DIALOGO = 720
MARGEM_TITULO = 36
MARGEM_PAINEL = 48


def aplicar_geometria(jan: tk.Tk) -> None:
    """Janela padrão 1232×726, centrada; encolhe na tela pequena até 360×320.

    Não chama update_idletasks antes de geometry: isso mapeava a janela
    padrão (canto superior esquerdo) e o usuário via um retângulo pequeno
    antes do tamanho certo.
    """
    sw = jan.winfo_screenwidth()
    sh = jan.winfo_screenheight()
    util_w = max(LARGURA_MIN, sw - 16)
    util_h = max(ALTURA_MIN, sh - MARGEM_TITULO - MARGEM_PAINEL)
    w = max(LARGURA_MIN, min(LARGURA_PADRAO, util_w))
    h = max(ALTURA_MIN, min(ALTURA_PADRAO, util_h))
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    jan.minsize(LARGURA_MIN, ALTURA_MIN)
    jan.geometry(f"{w}x{h}+{x}+{y}")


def mostrar_quando_pronta(jan: tk.Tk) -> None:
    """Calcula o layout invisível e só então exibe no tamanho final."""
    jan.update_idletasks()
    jan.deiconify()
    jan.lift()


def centrar_janela(jan: tk.Toplevel, parent: tk.Misc, w: int, h: int) -> None:
    """Coloca a janela no centro do pai; se o pai ainda não tiver tamanho, no centro da tela.

    No Wine, winfo_rootx/width às vezes vêm 0/1 antes do mapeamento — daí a
    janela nascia no canto superior esquerdo.
    """
    parent.update_idletasks()
    try:
        jan.update_idletasks()
    except tk.TclError:
        pass
    try:
        sw = max(int(jan.winfo_screenwidth()), 1)
        sh = max(int(jan.winfo_screenheight()), 1)
    except tk.TclError:
        sw, sh = 1280, 720
    try:
        px = int(parent.winfo_rootx())
        py = int(parent.winfo_rooty())
        pw = int(parent.winfo_width())
        ph = int(parent.winfo_height())
    except tk.TclError:
        px = py = 0
        pw, ph = sw, sh
    if pw < 80 or ph < 80:
        pw, ph = sw, sh
        px = py = 0
    w = max(280, min(int(w), sw))
    h = max(160, min(int(h), sh))
    x = px + (pw - w) // 2
    y = py + (ph - h) // 2
    x = max(0, min(x, sw - w))
    y = max(0, min(y, sh - h))
    jan.geometry(f"{w}x{h}+{x}+{y}")


def _centrar_dialogo(jan: tk.Toplevel, parent: tk.Misc, w: int, h: int) -> None:
    w = min(LARGURA_DIALOGO, max(280, w))
    centrar_janela(jan, parent, w, h)


def dialogo(
    parent: tk.Misc,
    titulo: str,
    mensagem: str,
    *,
    botoes: tuple[str, ...] = ("OK",),
) -> str:
    """Alerta modal, no máximo 720 px de largura, centrado na janela do sistema."""
    jan = tk.Toplevel(parent)
    jan.withdraw()
    jan.title(titulo)
    jan.transient(parent.winfo_toplevel())
    jan.resizable(False, False)
    escolhido = {"v": botoes[-1]}

    corpo = ttk.Frame(jan, padding=14)
    corpo.pack(fill=tk.BOTH, expand=True)
    ttk.Label(corpo, text=mensagem, wraplength=680, justify="left").pack(
        anchor="w", pady=(0, 12)
    )
    barra = ttk.Frame(corpo)
    barra.pack(fill=tk.X)

    def escolher(txt: str) -> None:
        escolhido["v"] = txt
        jan.destroy()

    for i, txt in enumerate(botoes):
        lado = tk.RIGHT if i == 0 else tk.LEFT
        ttk.Button(barra, text=txt, command=lambda t=txt: escolher(t)).pack(
            side=lado, padx=4, ipady=2
        )
    jan.bind("<Return>", lambda _e: escolher(botoes[0]))
    jan.bind("<Escape>", lambda _e: escolher(botoes[-1]))
    jan.update_idletasks()
    w = min(LARGURA_DIALOGO, max(320, jan.winfo_reqwidth() + 8))
    h = jan.winfo_reqheight() + 8
    _centrar_dialogo(jan, parent.winfo_toplevel(), w, h)
    jan.deiconify()
    jan.lift()
    jan.grab_set()
    jan.wait_window()
    return escolhido["v"]


def aviso(parent: tk.Misc, titulo: str, mensagem: str) -> None:
    dialogo(parent, titulo, mensagem)


def erro(parent: tk.Misc, titulo: str, mensagem: str) -> None:
    dialogo(parent, titulo, mensagem)


def sim_nao(parent: tk.Misc, titulo: str, mensagem: str) -> bool:
    return dialogo(parent, titulo, mensagem, botoes=("Sim", "Não")) == "Sim"

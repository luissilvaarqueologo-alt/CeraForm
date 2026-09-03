# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

TAMANHO = 12
_CANDIDATOS = (
    "Times New Roman",
    "TimesNewRoman",
    "Times",
    "Liberation Serif",
    "Nimbus Roman",
    "NimbusRoman",
    "FreeSerif",
    "DejaVu Serif",
)

FAMILIA = "Times New Roman"
FONTE = (FAMILIA, TAMANHO)
FONTE_NEGRITO = (FAMILIA, TAMANHO, "bold")
_FAMILIA_CACHE: str | None = None
_MATPLOTLIB_APLICADO = False


def resolver_familia(raiz: tk.Misc) -> str:
    """Times New Roman, ou o serif equivalente instalado no sistema.

    Evita tkfont.families() — no Linux a enumeração de todas as fontes
    atrasa o primeiro desenho da janela em mais de um segundo.
    """
    global _FAMILIA_CACHE
    if _FAMILIA_CACHE:
        return _FAMILIA_CACHE
    for nome in _CANDIDATOS:
        try:
            fnt = tkfont.Font(root=raiz, family=nome, size=TAMANHO)
            real = str(fnt.actual("family") or "")
        except tk.TclError:
            continue
        pedido = nome.lower().replace(" ", "")
        obtido = real.lower().replace(" ", "")
        if obtido == pedido or pedido in obtido or obtido in pedido:
            _FAMILIA_CACHE = real or nome
            return _FAMILIA_CACHE
    _FAMILIA_CACHE = "Times"
    return _FAMILIA_CACHE


def aplicar_fonte(raiz: tk.Tk) -> str:
    """Times New Roman 12 em Tk, ttk e Matplotlib."""
    global FAMILIA, FONTE, FONTE_NEGRITO
    FAMILIA = resolver_familia(raiz)
    FONTE = (FAMILIA, TAMANHO)
    FONTE_NEGRITO = (FAMILIA, TAMANHO, "bold")
    for nome in (
        "TkDefaultFont",
        "TkTextFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
        "TkFixedFont",
    ):
        try:
            fnt = tkfont.nametofont(nome)
            fnt.configure(family=FAMILIA, size=TAMANHO)
        except tk.TclError:
            continue
    try:
        tkfont.nametofont("TkHeadingFont").configure(family=FAMILIA, size=TAMANHO, weight="bold")
    except tk.TclError:
        pass
    estilo = ttk.Style(raiz)
    estilo.configure(".", font=FONTE)
    estilo.configure("TLabel", font=FONTE)
    estilo.configure("TButton", font=FONTE)
    estilo.configure("TEntry", font=FONTE)
    estilo.configure("TCombobox", font=FONTE)
    estilo.configure("TLabelframe.Label", font=FONTE)
    estilo.configure("TNotebook.Tab", font=FONTE)
    estilo.configure("Treeview", font=FONTE, rowheight=26)
    estilo.configure("Treeview.Heading", font=FONTE_NEGRITO)
    raiz.option_add("*Font", FONTE)
    raiz.option_add("*TCombobox*Listbox.font", FONTE)
    raiz.option_add("*Menu.font", FONTE)
    return FAMILIA


def aplicar_matplotlib() -> None:
    """Aplica a fonte ao Matplotlib só quando o perfil 2D/3D é aberto."""
    global _MATPLOTLIB_APLICADO
    if _MATPLOTLIB_APLICADO:
        return
    try:
        import matplotlib as mpl

        mpl.rcParams["font.family"] = "serif"
        mpl.rcParams["font.serif"] = [FAMILIA, "Times New Roman", "Times", "Liberation Serif"]
        mpl.rcParams["font.size"] = TAMANHO
        mpl.rcParams["axes.titlesize"] = TAMANHO
        mpl.rcParams["axes.labelsize"] = TAMANHO
        mpl.rcParams["xtick.labelsize"] = TAMANHO
        mpl.rcParams["ytick.labelsize"] = TAMANHO
        mpl.rcParams["legend.fontsize"] = TAMANHO
        _MATPLOTLIB_APLICADO = True
    except Exception:
        pass

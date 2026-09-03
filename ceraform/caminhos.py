# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

"""Pastas do programa: recursos embarcados vs dados ao lado do executável."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


def congelado() -> bool:
    return bool(getattr(sys, "frozen", False))


def pasta_recursos() -> Path:
    """Ajuda, documentação, imagens e cabeçalho.

    No .exe (PyInstaller --onefile) esses arquivos saem em uma pasta
    temporária (_MEIPASS). No desenvolvimento é a raiz do repositório.
    """
    if congelado():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def pasta_dados() -> Path:
    """Onde fica o SQLite e os arquivos que a usuária grava.

    Ao lado do .exe no Windows; na raiz do projeto quando se corre pelos .py.
    """
    if congelado():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def anotar_inicio(msg: str) -> None:
    """No .exe, rastro com horário de cada etapa da abertura."""
    if not congelado():
        return
    try:
        dest = pasta_dados() / "ceraform_inicio.txt"
        marca = datetime.now().strftime("%H:%M:%S")
        with dest.open("a", encoding="utf-8") as arq:
            arq.write(f"{marca} {msg.rstrip()}\n")
    except OSError:
        pass

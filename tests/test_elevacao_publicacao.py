# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matplotlib.figure import Figure

from ceraform.perfil import perfil_raios
from ceraform.visual_2d import desenhar_elevacao_publicacao


class TestElevacaoPublicacao(unittest.TestCase):
    def test_desenha_tigela_rasa_sem_erro(self) -> None:
        z, r = perfil_raios(
            h=7.0,
            db=22.5,
            dmax=22.5,
            hmax=7.0,
            dbase=0.0,
            dmeio=0.0,
            perfil_geometrico="Côncavo",
            tipo_base="Côncava",
        )
        dados = {
            "sitio": "Aldeia da Queimada Nova",
            "numero": "QMN-0001-00",
            "h": 7.0,
            "db": 22.5,
            "dmax": 22.5,
            "hmax": 7.0,
            "dbase": 0.0,
        }
        fig = Figure(figsize=(8, 6), dpi=120)
        ax = fig.add_subplot(111)
        desenhar_elevacao_publicacao(
            ax,
            z,
            r,
            dados,
            forma="Ovoide Invertido",
            volume_l=1.571,
            tipo_base="Côncava",
            modo="tela",
        )
        self.assertTrue(str(getattr(ax, "_perfil_modo", "")).startswith("publicacao"))
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "publicacao.png"
            fig.savefig(str(dest), format="png", facecolor="white", dpi=150)
            self.assertTrue(dest.is_file() and dest.stat().st_size > 1000)


if __name__ == "__main__":
    unittest.main()

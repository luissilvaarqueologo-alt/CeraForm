# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import unittest

from ceraform.ui_desktop import (
    _envolver_texto_png,
    _largura_texto_png,
    _truetype_serif,
    _FONTES_SERIF_NEGRITO,
)


class TestEnvolverTextoPngFicha(unittest.TestCase):
    def test_nome_do_sitio_nao_e_cortado(self) -> None:
        font = _truetype_serif(_FONTES_SERIF_NEGRITO, 12)
        nome = "Aldeia do Boqueirão da Serra Nova"
        # Coluna estreita (o bug do PNG antigo: valor colado em x=184 duma faixa de 420).
        linhas = _envolver_texto_png(nome, font, 180)
        self.assertGreaterEqual(len(linhas), 1)
        self.assertEqual(" ".join(linhas).replace("  ", " "), nome)
        for trecho in linhas:
            self.assertLessEqual(_largura_texto_png(font, trecho), 180 + 1.0)

    def test_texto_curto_fica_numa_so_linha(self) -> None:
        font = _truetype_serif(_FONTES_SERIF_NEGRITO, 12)
        linhas = _envolver_texto_png("761305-62", font, 220)
        self.assertEqual(linhas, ["761305-62"])


if __name__ == "__main__":
    unittest.main()

# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import unittest

from ceraform.volume import faixa_tamanho, observacao_volume, rotulo_tamanho


class TestFaixasDeTamanho(unittest.TestCase):
    """Intervalos semiabertos da seção 10, com recortes nas pontas."""

    def test_pequeno_abaixo_de_0_150(self) -> None:
        self.assertEqual(faixa_tamanho(0.149), "Pequeno")
        self.assertEqual(observacao_volume(0.149), "abaixo de 0,150 L")
        self.assertEqual(rotulo_tamanho(0.149), "Pequeno (abaixo de 0,150 L)")

    def test_pequeno_no_limiar_0_150(self) -> None:
        self.assertEqual(faixa_tamanho(0.150), "Pequeno")
        self.assertEqual(observacao_volume(0.150), "")

    def test_pequeno_ate_1_litro_exclusive(self) -> None:
        self.assertEqual(faixa_tamanho(0.999), "Pequeno")
        self.assertEqual(faixa_tamanho(1.0), "Médio")

    def test_medio_ate_4_litros_exclusive(self) -> None:
        self.assertEqual(faixa_tamanho(3.999), "Médio")
        self.assertEqual(faixa_tamanho(4.0), "Grande")

    def test_grande_ate_16_litros_exclusive(self) -> None:
        self.assertEqual(faixa_tamanho(15.999), "Grande")
        self.assertEqual(faixa_tamanho(16.0), "Extra grande")

    def test_extra_grande_antes_de_50(self) -> None:
        self.assertEqual(faixa_tamanho(49.999), "Extra grande")
        self.assertEqual(observacao_volume(49.999), "")

    def test_extra_grande_a_partir_de_50(self) -> None:
        self.assertEqual(faixa_tamanho(50.0), "Extra grande")
        self.assertEqual(observacao_volume(50.0), "a partir de 50,0 L")
        self.assertEqual(rotulo_tamanho(50.0), "Extra grande (a partir de 50,0 L)")


if __name__ == "__main__":
    unittest.main()

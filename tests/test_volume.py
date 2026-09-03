# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import math
import unittest

from ceraform.volume import calcular_volume


class TestCalcularVolumeCasosIdeais(unittest.TestCase):
    """Cilindro, cone e esfera analíticos; desconto da espessura da parede."""

    def _conversoes(self, res, cm3_esperado: float, casas: int = 6) -> None:
        """Verifica cm³, mL (= cm³) e litros (cm³ / 1000)."""
        self.assertAlmostEqual(res.mm3, cm3_esperado, places=casas)
        self.assertAlmostEqual(res.ml, cm3_esperado, places=casas)          # 1 mL = 1 cm³
        self.assertAlmostEqual(res.litros, cm3_esperado / 1_000.0, places=casas)

    def test_cilindro_100x100(self) -> None:
        res = calcular_volume(
            altura_total=100,
            diametro_maximo=100,
            diametro_borda=100,
            diametro_base=100,
            altura_diametro_max=50,
            perfil="Retilineo",
        )
        esperado = math.pi * 50.0 ** 2 * 100.0
        self._conversoes(res, esperado)

    def test_cone_120x100(self) -> None:
        res = calcular_volume(
            altura_total=120,
            diametro_maximo=100,
            diametro_borda=100,
            diametro_base=0,
            altura_diametro_max=120,
            perfil="Retilineo",
        )
        esperado = math.pi * 50.0 ** 2 * 120.0 / 3.0
        self._conversoes(res, esperado)

    def test_esfera_100(self) -> None:
        res = calcular_volume(
            altura_total=100,
            diametro_maximo=100,
            diametro_borda=0,
            diametro_base=0,
            altura_diametro_max=50,
            perfil="Convexo",
        )
        esperado = (4.0 / 3.0) * math.pi * 50.0 ** 3
        self._conversoes(res, esperado)

    def test_desconto_espessura_parede(self) -> None:
        t = 5.0
        cheio = calcular_volume(
            altura_total=100,
            diametro_maximo=100,
            diametro_borda=100,
            diametro_base=100,
            altura_diametro_max=50,
            perfil="Retilineo",
            espessura_parede=0.0,
        )
        oco = calcular_volume(
            altura_total=100,
            diametro_maximo=100,
            diametro_borda=100,
            diametro_base=100,
            altura_diametro_max=50,
            perfil="Retilineo",
            espessura_parede=t,
        )
        self.assertLess(oco.mm3, cheio.mm3)
        raio_interno = (100.0 - 2.0 * t) / 2.0
        altura_interna = 100.0 - t
        esperado = math.pi * raio_interno ** 2 * altura_interna
        self._conversoes(oco, esperado)


if __name__ == "__main__":
    unittest.main()

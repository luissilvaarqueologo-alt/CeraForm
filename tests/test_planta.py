# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import math
import unittest

import numpy as np

from ceraform.vista_solido import _xy_secao
from ceraform.volume import area_secao_mm2, volume_ate_altura_litros, volume_litros


class TestPlantaQuadrangular3D(unittest.TestCase):
    """Seção polar do retângulo: ρ = min(A/|cos θ|, B/|sin θ|)."""

    def test_eixos_do_quadrado(self) -> None:
        r = np.array([40.0])
        x0, y0 = _xy_secao(r, np.array([0.0]), 1.0, "Quadrangular")
        x90, y90 = _xy_secao(r, np.array([math.pi / 2.0]), 1.0, "Quadrangular")
        self.assertAlmostEqual(float(x0[0]), 40.0, places=9)
        self.assertAlmostEqual(float(y0[0]), 0.0, places=9)
        self.assertAlmostEqual(float(x90[0]), 0.0, places=9)
        self.assertAlmostEqual(float(y90[0]), 40.0, places=9)

    def test_canto_a_quarenta_e_cinco_graus(self) -> None:
        r = np.array([40.0])
        x, y = _xy_secao(r, np.array([math.pi / 4.0]), 1.0, "Quadrangular")
        self.assertAlmostEqual(float(x[0]), 40.0, places=6)
        self.assertAlmostEqual(float(y[0]), 40.0, places=6)

    def test_circular_a_quarenta_e_cinco_graus_nao_e_o_canto(self) -> None:
        r = np.array([40.0])
        x, y = _xy_secao(r, np.array([math.pi / 4.0]), 1.0, "Circular")
        self.assertAlmostEqual(float(x[0]), 40.0 / math.sqrt(2.0), places=6)
        self.assertAlmostEqual(float(y[0]), 40.0 / math.sqrt(2.0), places=6)

    def test_rectangulo_com_escala_sy(self) -> None:
        r = np.array([20.0])
        sy = 1.5
        _x, y = _xy_secao(r, np.array([math.pi / 2.0]), sy, "Quadrangular")
        self.assertAlmostEqual(float(y[0]), 20.0 * sy, places=9)

    def test_area_quadrangular_nao_e_a_elipse(self) -> None:
        r = 25.0
        a_q = float(area_secao_mm2(r, tipo_planta="Quadrangular"))
        a_c = float(area_secao_mm2(r, tipo_planta="Circular"))
        self.assertAlmostEqual(a_q, 4.0 * r * r, places=9)
        self.assertAlmostEqual(a_c, math.pi * r * r, places=9)
        self.assertNotAlmostEqual(a_q, a_c, places=6)

    def test_volume_prisma_quadrangular(self) -> None:
        h = 80.0
        raio = 20.0
        z = np.linspace(0.0, h, 41)
        r = np.full_like(z, raio)
        v = volume_litros(z, r, tipo_planta="Quadrangular")
        esperado_cm3 = 4.0 * raio * raio * h
        self.assertAlmostEqual(v, esperado_cm3 / 1_000.0, places=9)


class TestVolumeTrapezoidalMalha(unittest.TestCase):
    """Integral da ficha (seção 9.2) nos mesmos sólidos da suíte analítica."""

    def test_cilindro_coincide_com_pi_r2_h(self) -> None:
        h = 100.0
        raio = 50.0
        z = np.linspace(0.0, h, 241)
        r = np.full_like(z, raio)
        v = volume_litros(z, r, tipo_planta="Circular")
        esperado = math.pi * raio * raio * h / 1_000.0
        self.assertAlmostEqual(v, esperado, places=9)

    def test_cone_trapezio_aproxima_pi_r2_h_sobre_3(self) -> None:
        h = 120.0
        raio = 50.0
        z = np.linspace(0.0, h, 241)
        r = raio * (z / h)
        v = volume_litros(z, r, tipo_planta="Circular")
        esperado = math.pi * raio * raio * h / 3.0 / 1_000.0
        self.assertAlmostEqual(v, esperado, places=2)

    def test_corte_a_85_por_cento_inclui_o_limite(self) -> None:
        h = 100.0
        raio = 50.0
        z = np.linspace(0.0, h, 21)
        r = np.full_like(z, raio)
        v85 = volume_ate_altura_litros(z, r, 0.85 * h)
        esperado = math.pi * raio * raio * 0.85 * h / 1_000.0
        self.assertAlmostEqual(v85, esperado, places=9)


if __name__ == "__main__":
    unittest.main()

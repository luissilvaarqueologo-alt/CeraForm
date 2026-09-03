# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import math
import unittest

import numpy as np

from ceraform.perfil import quebras_meridiano


def _meridiano_com_angulo(graus: float) -> tuple[np.ndarray, np.ndarray]:
    """Três estações: o vértice interior forma exactamente `graus` entre v1 e v2."""
    rad = math.radians(graus)
    z = np.array([0.0, 10.0, 10.0 + 10.0 * math.cos(rad)])
    r = np.array([20.0, 20.0, 20.0 + 10.0 * math.sin(rad)])
    return z, r


class TestQuebrasMeridiano18Graus(unittest.TestCase):
    """Carena visível: θ ≥ 18° no vértice interior (seção 7)."""

    def test_parede_recta_sem_quebra(self) -> None:
        z = np.array([0.0, 50.0, 100.0])
        r = np.array([40.0, 40.0, 40.0])
        self.assertEqual(quebras_meridiano(z, r), [])

    def test_angulo_recto_e_quebra(self) -> None:
        """Parede vertical e depois radial: Z cresce, para as estações não se fundirem."""
        z = np.array([0.0, 50.0, 50.01])
        r = np.array([40.0, 40.0, 90.0])
        q = quebras_meridiano(z, r)
        self.assertEqual(len(q), 1)
        self.assertAlmostEqual(q[0][0], 50.0, places=2)
        self.assertGreater(q[0][1], 80.0)

    def test_dezassete_graus_nao_e_carena(self) -> None:
        z, r = _meridiano_com_angulo(17.0)
        self.assertEqual(quebras_meridiano(z, r), [])

    def test_dezoito_graus_e_carena(self) -> None:
        """18,01° evita o arccos(cos(18°)) cair um ulp abaixo do limiar."""
        z, r = _meridiano_com_angulo(18.01)
        q = quebras_meridiano(z, r)
        self.assertEqual(len(q), 1)
        self.assertGreaterEqual(q[0][1], 18.0)

    def test_dezanove_graus_e_carena(self) -> None:
        z, r = _meridiano_com_angulo(19.0)
        q = quebras_meridiano(z, r)
        self.assertEqual(len(q), 1)
        self.assertGreater(q[0][1], 18.0)

    def test_duas_quebras_distintas(self) -> None:
        z = np.array([0.0, 30.0, 60.0, 100.0])
        r = np.array([20.0, 60.0, 20.0, 55.0])
        q = quebras_meridiano(z, r)
        self.assertEqual(len(q), 2)
        self.assertAlmostEqual(q[0][0], 30.0, places=9)
        self.assertAlmostEqual(q[1][0], 60.0, places=9)

    def test_menos_de_tres_estacoes_sem_quebra(self) -> None:
        self.assertEqual(quebras_meridiano(np.array([0.0, 10.0]), np.array([5.0, 8.0])), [])


if __name__ == "__main__":
    unittest.main()

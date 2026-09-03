# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import unittest

import numpy as np

from ceraform.perfil import (
    _forcar_pico_horizontal,
    _hermite_cubico,
    _pchip_derivadas,
    _pchip_perfil,
    perfil_raios,
)


class TestPchipHermitePontoAPonto(unittest.TestCase):
    """Interpolação nas estações medidas; monotonicidade de Fritsch–Carlson."""

    def test_hermite_recupera_os_extremos_do_intervalo(self) -> None:
        z_c = np.array([0.0, 10.0])
        r_c = np.array([20.0, 40.0])
        deriv = np.array([1.0, 1.0])
        r = _hermite_cubico(z_c, r_c, deriv, z_c)
        np.testing.assert_allclose(r, r_c, rtol=0.0, atol=1e-12)

    def test_hermite_linear_quando_derivadas_sao_a_secante(self) -> None:
        z_c = np.array([0.0, 100.0])
        r_c = np.array([10.0, 50.0])
        delta = (50.0 - 10.0) / 100.0
        deriv = np.array([delta, delta])
        z = np.array([0.0, 25.0, 50.0, 75.0, 100.0])
        r = _hermite_cubico(z_c, r_c, deriv, z)
        esperado = 10.0 + delta * z
        np.testing.assert_allclose(r, esperado, rtol=0.0, atol=1e-10)

    def test_pchip_passa_exactamente_pelas_estacoes(self) -> None:
        z_c = np.array([0.0, 40.0, 100.0])
        r_c = np.array([15.0, 50.0, 20.0])
        r = _pchip_perfil(z_c, r_c, z_c)
        np.testing.assert_allclose(r, r_c, rtol=0.0, atol=1e-9)

    def test_pchip_nao_ultrapassa_o_maximo_local(self) -> None:
        """Fritsch–Carlson: sem overshoot além do maior raio medido no intervalo."""
        z_c = np.array([0.0, 50.0, 100.0])
        r_c = np.array([10.0, 50.0, 12.0])
        z = np.linspace(0.0, 100.0, 401)
        r = _pchip_perfil(z_c, r_c, z, z_pico=50.0)
        self.assertLessEqual(float(np.max(r)), 50.0 + 1e-6)
        self.assertGreaterEqual(float(np.min(r)), 10.0 - 1e-6)

    def test_pchip_monotono_em_troco_crescente(self) -> None:
        z_c = np.array([0.0, 50.0, 100.0])
        r_c = np.array([10.0, 30.0, 55.0])
        z = np.linspace(0.0, 100.0, 201)
        r = _pchip_perfil(z_c, r_c, z)
        self.assertTrue(np.all(np.diff(r) >= -1e-9))

    def test_derivada_nula_quando_a_secante_muda_de_sinal(self) -> None:
        z = np.array([0.0, 40.0, 80.0])
        r = np.array([10.0, 50.0, 15.0])
        d = _pchip_derivadas(z, r)
        self.assertAlmostEqual(float(d[1]), 0.0, places=12)

    def test_pico_horizontal_no_maior_diametro(self) -> None:
        z = np.array([0.0, 50.0, 100.0])
        r = np.array([20.0, 50.0, 25.0])
        d = _pchip_derivadas(z, r)
        d = _forcar_pico_horizontal(d, z, r, 50.0)
        self.assertAlmostEqual(float(d[1]), 0.0, places=12)

    def test_perfil_reto_e_linear_entre_estacoes(self) -> None:
        """Tronco: maior diâmetro na borda; a meia altura é a média dos raios."""
        z, r = perfil_raios(
            h=100,
            db=80,
            dmax=80,
            hmax=100,
            dbase=40,
            perfil_geometrico="Reto",
        )
        r_base = float(np.interp(0.0, z, r))
        r_borda = float(np.interp(100.0, z, r))
        r_meio = float(np.interp(50.0, z, r))
        self.assertAlmostEqual(r_base, 20.0, places=6)
        self.assertAlmostEqual(r_borda, 40.0, places=6)
        self.assertAlmostEqual(r_meio, 30.0, places=5)

    def test_perfil_convexo_passa_pelo_maior_diametro(self) -> None:
        z, r = perfil_raios(
            h=100,
            db=30,
            dmax=100,
            hmax=50,
            dbase=30,
            perfil_geometrico="Convexo",
        )
        r_max = float(np.interp(50.0, z, r))
        self.assertAlmostEqual(r_max, 50.0, places=6)
        i_pico = int(np.argmin(np.abs(z - 50.0)))
        if 0 < i_pico < z.size - 1:
            dr = (r[i_pico + 1] - r[i_pico - 1]) / (z[i_pico + 1] - z[i_pico - 1])
            self.assertLess(abs(float(dr)), 0.05)


class TestMedicoesFracao(unittest.TestCase):
    """Diâmetros opcionais a 1/4, 1/2 e 3/4 da altura total em qualquer peça."""

    def test_diametros_fracao_nao_confundem_pescoco_com_tres_quartos(self) -> None:
        from ceraform.perfil import diametros_fracao

        d14, d12, d34 = diametros_fracao("8.0, 10.4", 10.3)
        self.assertEqual((d14, d12, d34), (0.0, 0.0, 0.0))

    def test_diametros_fracao_reconhecem_cotas_gravadas(self) -> None:
        from ceraform.perfil import diametros_fracao, texto_medicoes_fracao

        texto = texto_medicoes_fracao(20.0, 8.0, 14.0, 12.0)
        d14, d12, d34 = diametros_fracao(texto, 20.0)
        self.assertAlmostEqual(d14, 8.0, places=5)
        self.assertAlmostEqual(d12, 14.0, places=5)
        self.assertAlmostEqual(d34, 12.0, places=5)

    def test_base_zero_respeita_diametro_a_um_quarto_da_altura(self) -> None:
        """Cota abaixo da barriga não é ignorada quando o fundo é calota."""
        z, r = perfil_raios(
            h=20.0,
            db=12.0,
            dmax=16.0,
            hmax=10.0,
            dbase=0.0,
            amostras=[(5.0, 12.0)],
            perfil_geometrico="Convexo",
            tipo_base="Côncava",
        )
        self.assertAlmostEqual(float(np.interp(5.0, z, r)) * 2.0, 12.0, places=3)
        self.assertAlmostEqual(float(np.interp(10.0, z, r)) * 2.0, 16.0, places=3)
        self.assertAlmostEqual(float(r[0]), 0.0, places=6)
        self.assertLess(float(z[1] / max(r[1], 1e-9)), 0.6)

    def test_base_zero_respeita_diametro_a_tres_quartos_da_altura(self) -> None:
        z, r = perfil_raios(
            h=20.0,
            db=12.0,
            dmax=16.0,
            hmax=10.0,
            dbase=0.0,
            amostras=[(15.0, 13.0)],
            perfil_geometrico="Convexo",
            tipo_base="Côncava",
        )
        self.assertAlmostEqual(float(np.interp(15.0, z, r)) * 2.0, 13.0, places=3)
        self.assertAlmostEqual(float(np.interp(10.0, z, r)) * 2.0, 16.0, places=3)

    def test_anel_na_base_respeita_as_tres_fracoes(self) -> None:
        z, r = perfil_raios(
            h=20.0,
            db=12.0,
            dmax=16.0,
            hmax=10.0,
            dbase=8.0,
            amostras=[(5.0, 10.0), (10.0, 16.0), (15.0, 13.0)],
            perfil_geometrico="Convexo",
            tipo_base="Reta",
        )
        self.assertAlmostEqual(float(np.interp(5.0, z, r)) * 2.0, 10.0, places=3)
        self.assertAlmostEqual(float(np.interp(15.0, z, r)) * 2.0, 13.0, places=3)

    def test_tigela_base_zero_respeita_fracao_abaixo_da_borda(self) -> None:
        """Maior diâmetro na borda: 1/4 e 1/2 ainda entram no meridiano."""
        z, r = perfil_raios(
            h=10.0,
            db=20.0,
            dmax=20.0,
            hmax=10.0,
            dbase=0.0,
            amostras=[(2.5, 10.0), (5.0, 16.0)],
            perfil_geometrico="Convexo",
            tipo_base="Côncava",
        )
        self.assertAlmostEqual(float(np.interp(2.5, z, r)) * 2.0, 10.0, places=3)
        self.assertAlmostEqual(float(np.interp(5.0, z, r)) * 2.0, 16.0, places=3)
        self.assertAlmostEqual(float(r[-1]) * 2.0, 20.0, places=3)

    def test_juncao_com_barriga_perto_da_borda_e_base_zero(self) -> None:
        """Ovoide invertido (H_max perto da boca, base 0): a junção não pode sumir."""
        z, r = perfil_raios(
            h=8.5,
            db=16.0,
            dmax=17.0,
            hmax=8.0,
            dbase=0.0,
            perfil_geometrico="Convexo",
            tipo_base="Convexa",
            altura_juncao=8.2,
            diametro_juncao=10.4,
        )
        self.assertAlmostEqual(float(np.interp(8.0, z, r)) * 2.0, 17.0, places=2)
        self.assertAlmostEqual(float(np.interp(8.2, z, r)) * 2.0, 10.4, places=2)
        self.assertAlmostEqual(float(r[-1]) * 2.0, 16.0, places=2)
        self.assertLess(float(np.interp(8.2, z, r)), float(np.interp(8.0, z, r)))

    def test_juncao_em_peca_com_anel_e_perfil_convexo(self) -> None:
        """Junção bojo–pescoço entra no desenho sem exigir perfil Composto."""
        z, r = perfil_raios(
            h=20.0,
            db=12.0,
            dmax=16.0,
            hmax=10.0,
            dbase=8.0,
            perfil_geometrico="Convexo",
            tipo_base="Reta",
            altura_juncao=15.0,
            diametro_juncao=9.0,
        )
        self.assertAlmostEqual(float(np.interp(15.0, z, r)) * 2.0, 9.0, places=3)
        self.assertAlmostEqual(float(np.interp(10.0, z, r)) * 2.0, 16.0, places=3)


if __name__ == "__main__":
    unittest.main()

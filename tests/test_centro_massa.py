# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import unittest

import numpy as np

from ceraform.perfil import centro_massa_casca, curva_base, raio_curvatura_base


class TestCentroMassaCasca(unittest.TestCase):
    """Casca fina de revolução: parede 2π R ds + fundo (disco ou calota)."""

    def test_cilindro_com_fundo_plano(self) -> None:
        """Z_cm = H² / (2H + R) para parede cilíndrica + disco π R² em Z = 0."""
        h = 100.0
        raio = 50.0
        z_p = np.linspace(0.0, h, 81)
        r_p = np.full_like(z_p, raio)
        r_b, z_b = curva_base("Reta", raio)
        z_cm, nota = centro_massa_casca(z_p, r_p, r_b, z_b, tipo_base="Reta")
        esperado = (h * h) / (2.0 * h + raio)
        self.assertAlmostEqual(z_cm, esperado, places=5)
        self.assertIn("disco", nota.lower())

    def test_parede_sozinha_sem_area_de_fundo_degenerada(self) -> None:
        """Fundo com raio nulo: só a parede; Z_cm cai na meia altura."""
        h = 80.0
        z_p = np.array([0.0, h])
        r_p = np.array([30.0, 30.0])
        z_cm, _nota = centro_massa_casca(
            z_p, r_p, np.array([0.0]), np.array([0.0]), tipo_base="Reta"
        )
        self.assertAlmostEqual(z_cm, h / 2.0, places=6)

    def test_base_convexa_desloca_o_cm_para_cima_da_reta(self) -> None:
        h = 100.0
        raio = 50.0
        z_p = np.linspace(0.0, h, 81)
        r_p = np.full_like(z_p, raio)
        r_reta, z_reta = curva_base("Reta", raio)
        r_cx, z_cx = curva_base("Convexa", raio)
        z_reta_cm, _ = centro_massa_casca(z_p, r_p, r_reta, z_reta, tipo_base="Reta")
        z_cx_cm, nota = centro_massa_casca(z_p, r_p, r_cx, z_cx, tipo_base="Convexa")
        self.assertGreater(z_cx_cm, z_reta_cm)
        self.assertIn("calota", nota.lower())

    def test_raio_de_curvatura_da_base_convexa(self) -> None:
        """ρ = R_b² / (2s) = R_b / 0,40 = 2,5 R_b, com s = 0,20 R_b."""
        raio = 40.0
        rho = raio_curvatura_base("Convexa", raio)
        self.assertIsNotNone(rho)
        self.assertAlmostEqual(float(rho), 2.5 * raio, places=9)
        s = 0.20 * raio
        self.assertAlmostEqual(float(rho), (raio * raio) / (2.0 * s), places=9)

    def test_base_reta_sem_raio_de_curvatura(self) -> None:
        self.assertIsNone(raio_curvatura_base("Reta", 40.0))

    def test_sagita_da_base_concava(self) -> None:
        raio = 50.0
        r, z = curva_base("Côncava", raio)
        self.assertAlmostEqual(float(z[0]), 0.20 * raio, places=9)
        self.assertAlmostEqual(float(z[-1]), 0.0, places=9)
        self.assertAlmostEqual(float(r[-1]), raio, places=9)

    def test_base_concava_diametro_zero_fecha_no_eixo(self) -> None:
        """Tigela (dmax = borda, base 0): arco/elipse, fecha no eixo, sem pontinha."""
        from ceraform.perfil import meridiano_com_base, perfil_arco_borda_a_borda, perfil_raios

        z, r = perfil_raios(
            h=7.0,
            db=22.5,
            dmax=22.5,
            hmax=7.0,
            dbase=0.0,
            perfil_geometrico="Convexo",
            tipo_base="Côncava",
        )
        self.assertAlmostEqual(float(r[0]), 0.0, places=6)
        self.assertAlmostEqual(float(r[-1]), 11.25, places=5)
        self.assertAlmostEqual(float(z[0]), 0.0, places=6)
        self.assertAlmostEqual(float(z[-1]), 7.0, places=5)
        self.assertTrue(np.all(np.diff(r) >= -1e-9))
        i = max(1, z.size // 20)
        self.assertLess(float(z[i] / max(r[i], 1e-9)), 0.40)
        z_w, r_w, r_b, _z_b = meridiano_com_base(z, r, "Côncava")
        self.assertEqual(r_b.size, 1)
        z2, r2 = perfil_arco_borda_a_borda(h=7.0, db=22.5, n=len(z))
        self.assertTrue(np.allclose(z, z2, atol=1e-6))
        self.assertTrue(np.allclose(r, r2, atol=1e-6))
        self.assertTrue(np.allclose(z_w, z, atol=1e-6))
        self.assertTrue(np.allclose(r_w, r, atol=1e-6))

    def test_base_concava_zero_respeita_maior_diametro(self) -> None:
        """Barriga > borda e base 0: elipse pelo maior diâmetro, sem pontinha."""
        from ceraform.perfil import perfil_raios

        z, r = perfil_raios(
            h=45.0,
            db=25.0,
            dmax=65.0,
            hmax=22.0,
            dbase=0.0,
            perfil_geometrico="Convexo",
            tipo_base="Côncava",
        )
        r_hmax = float(np.interp(22.0, z, r))
        self.assertAlmostEqual(r_hmax * 2.0, 65.0, places=4)
        self.assertAlmostEqual(float(r[-1]) * 2.0, 25.0, places=4)
        self.assertAlmostEqual(float(r[0]), 0.0, places=6)
        self.assertGreater(float(np.max(r)) * 2.0, 60.0)
        i = max(1, z.size // 20)
        self.assertLess(float(z[i] / max(r[i], 1e-9)), 0.40)
        r_max = 32.5
        hmax = 22.0
        z_inf = z[z <= hmax + 1e-9]
        r_inf = r[z <= hmax + 1e-9]
        residuo = (r_inf / r_max) ** 2 + ((z_inf - hmax) / hmax) ** 2 - 1.0
        self.assertTrue(np.allclose(residuo, 0.0, atol=2e-3))

    def test_qmn_0003_barriga_ligeiramente_maior_que_borda(self) -> None:
        """QMN-0003-00: 23,5 cm na altura 19; borda 21 — não tratar como tigela."""
        from ceraform.perfil import perfil_raios

        z, r = perfil_raios(
            h=27.5,
            db=21.0,
            dmax=23.5,
            hmax=19.0,
            dbase=0.0,
            perfil_geometrico="Convexo",
            tipo_base="Côncava",
        )
        self.assertAlmostEqual(float(np.interp(19.0, z, r)) * 2.0, 23.5, places=3)
        self.assertAlmostEqual(float(r[-1]) * 2.0, 21.0, places=3)
        self.assertAlmostEqual(float(z[np.argmax(r)]), 19.0, places=1)
        self.assertLess(float(r[-1]), float(np.max(r)) - 0.2)
        i = max(1, z.size // 20)
        self.assertLess(float(z[i] / max(r[i], 1e-9)), 0.40)

    def test_base_zero_respeita_amostra_do_pescoco(self) -> None:
        """Cota extra acima da barriga entra no perfil mesmo com base 0 cm."""
        from ceraform.perfil import perfil_raios

        z, r = perfil_raios(
            h=10.3,
            db=12.0,
            dmax=13.0,
            hmax=5.0,
            dbase=0.0,
            amostras=[(8.0, 10.4)],
            perfil_geometrico="Convexo",
            tipo_base="Côncava",
        )
        self.assertAlmostEqual(float(np.interp(5.0, z, r)) * 2.0, 13.0, places=3)
        self.assertAlmostEqual(float(np.interp(8.0, z, r)) * 2.0, 10.4, places=3)
        self.assertAlmostEqual(float(r[-1]) * 2.0, 12.0, places=3)
        self.assertLess(float(np.interp(8.0, z, r)), float(np.interp(5.0, z, r)))
        self.assertLess(float(np.interp(8.0, z, r)), float(r[-1]))
        from ceraform.perfil import quebras_meridiano

        quebras = quebras_meridiano(z, r)
        self.assertFalse(any(abs(zi - 8.0) < 0.4 for zi, _ang in quebras))

    def test_juncao_bojo_pescoco_sem_canto(self) -> None:
        """Junção bojo–pescoço arredondada: não gera quebra de 18°."""
        from ceraform.perfil import perfil_raios, quebras_meridiano

        z, r = perfil_raios(
            h=10.3,
            db=12.0,
            dmax=13.0,
            hmax=5.0,
            dbase=0.0,
            perfil_geometrico="Composto",
            perfil_trecho_base="Convexo",
            perfil_trecho_borda="Convexo",
            altura_juncao=8.0,
            diametro_juncao=10.4,
            tipo_base="Côncava",
        )
        self.assertAlmostEqual(float(np.interp(8.0, z, r)) * 2.0, 10.4, places=3)
        quebras = quebras_meridiano(z, r)
        self.assertFalse(any(abs(zi - 8.0) < 0.4 for zi, _ang in quebras))

    def test_parede_reta_base_zero_permanece_cone(self) -> None:
        """Perfil reto e diâmetro da base 0: ponta cónica (não arredondar)."""
        from ceraform.perfil import perfil_raios

        z, r = perfil_raios(
            h=120.0,
            db=100.0,
            dmax=100.0,
            hmax=120.0,
            dbase=0.0,
            perfil_geometrico="Reto",
            tipo_base="Reta",
        )
        r_meio = float(np.interp(60.0, z, r))
        self.assertAlmostEqual(r_meio, 25.0, places=4)
        i = max(1, z.size // 20)
        self.assertGreater(float(z[i] / max(r[i], 1e-9)), 0.8)

    def test_arco_profundo_sem_salto_vertical(self) -> None:
        """Curva auxiliar semi-elipse (H > R): contínua até a borda."""
        from ceraform.perfil import perfil_arco_borda_a_borda

        h, db = 27.5, 34.5
        z, r = perfil_arco_borda_a_borda(h=h, db=db, n=240)
        self.assertAlmostEqual(float(z[-1]), h, places=5)
        self.assertAlmostEqual(float(r[-1]), db / 2.0, places=5)
        self.assertAlmostEqual(float(z[0]), 0.0, places=6)
        self.assertAlmostEqual(float(r[0]), 0.0, places=6)
        dz = np.diff(z)
        dr = np.diff(r)
        self.assertTrue(np.all(dz >= -1e-9))
        self.assertTrue(np.all(dr >= -1e-9))  # r monótono: máximo na borda
        self.assertLess(float(np.max(dz)), 0.5)
        # Semi-elipse: (r/R)² + ((H−z)/H)² = 1
        R = db / 2.0
        residuo = (r / R) ** 2 + ((h - z) / h) ** 2 - 1.0
        self.assertTrue(np.allclose(residuo, 0.0, atol=1e-6))


if __name__ == "__main__":
    unittest.main()

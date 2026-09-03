# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import unittest

from ceraform.classificar import classificarForma, razoes_adimensionais
from ceraform.constantes import FORMAS


class TestClassificarFormaCasosIdeais(unittest.TestCase):
    """Nove silhuetas analíticas: razões adimensionais + perfil geométrico."""

    def test_esfera_perfeita(self) -> None:
        self.assertEqual(
            classificarForma(H=100, Dmax=100, Db=30, D0=30, hmax=50, perfil="Convexo").forma,
            "Esférico",
        )

    def test_elipsoide_vertical(self) -> None:
        self.assertEqual(
            classificarForma(H=150, Dmax=100, Db=40, D0=40, hmax=75, perfil="Convexo").forma,
            "Elipsóide Vertical",
        )

    def test_elipsoide_horizontal(self) -> None:
        self.assertEqual(
            classificarForma(H=80, Dmax=160, Db=60, D0=60, hmax=40, perfil="Convexo").forma,
            "Elipsóide Horizontal",
        )

    def test_cilindro_puro(self) -> None:
        self.assertEqual(
            classificarForma(H=120, Dmax=100, Db=100, D0=100, hmax=60, perfil="Retilineo").forma,
            "Cilíndrico",
        )

    def test_cone_simples(self) -> None:
        self.assertEqual(
            classificarForma(H=120, Dmax=100, Db=100, D0=0, hmax=120, perfil="Retilineo").forma,
            "Cônico",
        )

    def test_tronco_conico(self) -> None:
        self.assertEqual(
            classificarForma(H=100, Dmax=120, Db=120, D0=60, hmax=100, perfil="Retilineo").forma,
            "Tronco-Cônico",
        )

    def test_ovoide_direto(self) -> None:
        self.assertEqual(
            classificarForma(H=140, Dmax=100, Db=40, D0=50, hmax=45, perfil="Convexo").forma,
            "Ovoide",
        )

    def test_ovoide_invertido(self) -> None:
        self.assertEqual(
            classificarForma(H=140, Dmax=100, Db=50, D0=40, hmax=95, perfil="Convexo").forma,
            "Ovoide Invertido",
        )

    def test_discoide(self) -> None:
        self.assertEqual(
            classificarForma(H=30, Dmax=150, Db=150, D0=80, hmax=15, perfil="Convexo").forma,
            "Discoide",
        )


class TestClassificarFormaBordaERobustez(unittest.TestCase):
    """Divisão por zero, silhuetas extremas e dados inválidos (sem exceção)."""

    def _sem_excecao(self, **kwargs):
        try:
            return classificarForma(**kwargs)
        except Exception as exc:  # pragma: no cover
            self.fail(f"classificarForma levantou {type(exc).__name__}: {exc}")

    def test_d0_zero_base_pontiaguda(self) -> None:
        razoes = razoes_adimensionais(H=120, Dmax=100, Db=100, D0=0, hmax=120)
        self.assertTrue(all(abs(v) != float("inf") for v in razoes.values()))
        res = self._sem_excecao(
            H=120, Dmax=100, Db=100, D0=0, hmax=120, perfil="Retilineo"
        )
        self.assertTrue(res.valido)
        self.assertIn(res.forma, FORMAS)
        self.assertEqual(res.forma, "Cônico")

    def test_db_zero_borda_fechada(self) -> None:
        razoes = razoes_adimensionais(H=100, Dmax=80, Db=0, D0=50, hmax=50)
        self.assertTrue(all(abs(v) != float("inf") for v in razoes.values()))
        res = self._sem_excecao(
            H=100, Dmax=80, Db=0, D0=50, hmax=50, perfil="Convexo"
        )
        self.assertTrue(res.valido)
        self.assertIn(res.forma, FORMAS)

    def test_d0_e_db_zero(self) -> None:
        razoes = razoes_adimensionais(H=100, Dmax=90, Db=0, D0=0, hmax=50)
        self.assertTrue(all(abs(v) != float("inf") for v in razoes.values()))
        res = self._sem_excecao(
            H=100, Dmax=90, Db=0, D0=0, hmax=50, perfil="Convexo"
        )
        self.assertTrue(res.valido)
        self.assertIn(res.forma, FORMAS)

    def test_tubular(self) -> None:
        res = self._sem_excecao(
            H=300, Dmax=40, Db=40, D0=40, hmax=150, perfil="Retilineo"
        )
        self.assertTrue(res.valido)
        self.assertEqual(res.forma, "Cilíndrico")

    def test_prato_plano(self) -> None:
        res = self._sem_excecao(
            H=8, Dmax=200, Db=200, D0=180, hmax=4, perfil="Convexo"
        )
        self.assertTrue(res.valido)
        self.assertEqual(res.forma, "Discoide")

    def test_bojo_extremo_superior(self) -> None:
        h = 140.0
        res = self._sem_excecao(
            H=h, Dmax=100, Db=50, D0=40, hmax=h, perfil="Convexo"
        )
        self.assertTrue(res.valido)
        self.assertEqual(res.forma, "Ovoide Invertido")

    def test_bojo_extremo_inferior(self) -> None:
        res = self._sem_excecao(
            H=140, Dmax=100, Db=40, D0=50, hmax=0, perfil="Convexo"
        )
        self.assertTrue(res.valido)
        self.assertEqual(res.forma, "Ovoide")

    def test_h_zero_invalido(self) -> None:
        res = self._sem_excecao(
            H=0, Dmax=100, Db=30, D0=30, hmax=0, perfil="Convexo"
        )
        self.assertFalse(res.valido)
        self.assertIn(res.forma, FORMAS)

    def test_dmax_zero_invalido(self) -> None:
        res = self._sem_excecao(
            H=100, Dmax=0, Db=30, D0=30, hmax=50, perfil="Convexo"
        )
        self.assertFalse(res.valido)
        self.assertIn(res.forma, FORMAS)

    def test_valores_negativos_invalidos(self) -> None:
        casos = [
            dict(H=-100, Dmax=100, Db=30, D0=30, hmax=50, perfil="Convexo"),
            dict(H=100, Dmax=-100, Db=30, D0=30, hmax=50, perfil="Convexo"),
            dict(H=100, Dmax=100, Db=-30, D0=30, hmax=50, perfil="Convexo"),
            dict(H=100, Dmax=100, Db=30, D0=-30, hmax=50, perfil="Convexo"),
            dict(H=100, Dmax=100, Db=30, D0=30, hmax=-10, perfil="Convexo"),
        ]
        for kwargs in casos:
            with self.subTest(**{k: kwargs[k] for k in ("H", "Dmax", "Db", "D0", "hmax")}):
                res = self._sem_excecao(**kwargs)
                self.assertFalse(res.valido)
                self.assertIn(res.forma, FORMAS)

    def test_hmax_maior_que_h_invalido(self) -> None:
        res = self._sem_excecao(
            H=100, Dmax=80, Db=40, D0=40, hmax=150, perfil="Convexo"
        )
        self.assertFalse(res.valido)
        self.assertIn(res.forma, FORMAS)


class TestCarenaAntesDeSilhuetaLisa(unittest.TestCase):
    """Quebra de tangente no meridiano manda; pera só com parede contínua."""

    def test_piriforme_parede_lisa(self) -> None:
        res = classificarForma(
            H=180, Dmax=140, Db=48, D0=62, hmax=50, perfil="Convexo"
        )
        self.assertEqual(res.forma, "Piriforme")

    def test_tb031_quebra_nao_e_pera(self) -> None:
        """TB-031: 77° no maior diâmetro — Carenado, não Piriforme."""
        res = classificarForma(
            H=23.74,
            Dmax=18.09,
            Db=6.21,
            D0=7.94,
            hmax=6.67,
            perfil="Composto",
            perfil_trecho_base="Reto",
            perfil_trecho_borda="Convexo",
            altura_juncao=13.3,
            diametro_juncao=7.1,
        )
        self.assertEqual(res.forma, "Carenado")

    def test_bicone_reto_nao_vira_carenado(self) -> None:
        res = classificarForma(
            H=160, Dmax=130, Db=50, D0=52, hmax=80, perfil="Retilineo"
        )
        self.assertEqual(res.forma, "Bicônico (Cone Duplo)")


class TestVizinhoMaisProximoSemLixeira(unittest.TestCase):
    """Fora da faixa: o centro de i_H mais perto, sempre com aproximação."""

    def test_etiq_67083_horizontal_aproximado(self) -> None:
        """ETIQ-67083: i_H=0,43 — mais perto do elipsóide horizontal (0,50) que do lenticular."""
        res = classificarForma(
            H=7.3, Dmax=16.9, Db=16.6, D0=0.0, hmax=3.65, perfil="Convexo"
        )
        self.assertEqual(res.forma, "Elipsóide Horizontal")
        self.assertTrue(res.aproximacao)

    def test_166422_subglobular_aproximado(self) -> None:
        """166422-15: i_H=0,79 na faixa subglobular; boca quase o bojo → aproximação."""
        res = classificarForma(
            H=10.3, Dmax=13.0, Db=12.0, D0=0.0, hmax=5.0, perfil="Côncavo"
        )
        self.assertEqual(res.forma, "Subglobular")
        self.assertTrue(res.aproximacao)

    def test_761305_ovoide_invertido_exato(self) -> None:
        res = classificarForma(
            H=8.5, Dmax=17.0, Db=16.0, D0=0.0, hmax=8.0, perfil="Convexo"
        )
        self.assertEqual(res.forma, "Ovoide Invertido")
        self.assertFalse(res.aproximacao)

    def test_ih_1_25_mais_perto_de_globular(self) -> None:
        """i_H=1,25 está mais perto do centro globular (1,03) que do vertical (1,50)."""
        res = classificarForma(
            H=100, Dmax=80, Db=0, D0=50, hmax=50, perfil="Convexo"
        )
        self.assertEqual(res.forma, "Globular")
        self.assertTrue(res.aproximacao)

    def test_ih_1_50_elipsoide_vertical_aproximado(self) -> None:
        res = classificarForma(
            H=150, Dmax=100, Db=20, D0=0, hmax=75, perfil="Convexo"
        )
        self.assertEqual(res.forma, "Elipsóide Vertical")
        self.assertTrue(res.aproximacao)

    def test_elipsoide_limpo_nao_e_aproximacao(self) -> None:
        res = classificarForma(
            H=150, Dmax=100, Db=40, D0=40, hmax=75, perfil="Convexo"
        )
        self.assertEqual(res.forma, "Elipsóide Vertical")
        self.assertFalse(res.aproximacao)


if __name__ == "__main__":
    unittest.main()

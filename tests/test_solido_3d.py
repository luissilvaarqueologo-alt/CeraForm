# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import unittest

import numpy as np

from ceraform.perfil import pontos_meridiano, perfil_raios
from ceraform.vista_solido import (
    _espessura_efetiva,
    _fator_zoom_roda,
    _importar_pyvista,
    _raios_casca_oca,
    peca_por_torno,
)


def _pts_tigela():
    z, r = perfil_raios(
        h=7.3,
        db=16.6,
        dmax=16.9,
        hmax=3.6,
        dbase=0.0,
        dmeio=0.0,
        perfil_geometrico="Convexo",
        tipo_base="Côncava",
    )
    return pontos_meridiano(z, r, "Côncava")


class TestSolido3dEspessura(unittest.TestCase):
    def test_casca_interna_menor_que_a_externa(self) -> None:
        r_med = np.linspace(0.05, 8.0, 40)
        t = 0.6
        r_ext, r_int = _raios_casca_oca(r_med, t, fecha_no_eixo=True)
        self.assertTrue(np.all(r_int < r_ext - 1e-9))
        meio = r_med.size // 2
        self.assertAlmostEqual(float(r_ext[meio] - r_int[meio]), t, delta=0.05)

    def test_espessura_vazia_usa_dois_milimetros(self) -> None:
        self.assertAlmostEqual(_espessura_efetiva(0.0), 0.2)
        self.assertAlmostEqual(_espessura_efetiva(0.5), 0.5)


class TestSolido3dCeramica(unittest.TestCase):
    def test_malha_traz_rgb_de_engobo(self) -> None:
        pv = _importar_pyvista()
        if pv is None:
            self.skipTest("PyVista não disponível")
        peca = peca_por_torno(pv, _pts_tigela(), 1.0, espessura=0.4)
        self.assertIsNotNone(peca)
        self.assertIn("RGB", peca.point_data)
        rgb = np.asarray(peca["RGB"])
        self.assertEqual(rgb.ndim, 2)
        self.assertEqual(rgb.shape[1], 3)
        self.assertGreater(float(np.ptp(rgb.astype(float))), 5.0)


class TestSolido3dZoom(unittest.TestCase):
    def test_mostrar_nao_zera_o_zoom(self) -> None:
        import tkinter as tk

        from ceraform.vista_solido import VistaSolido

        try:
            raiz = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk sem display")
        raiz.withdraw()
        vista = VistaSolido(raiz)
        vista.zoom = 2.4
        vista.azim = 80.0
        vista.mostrar(_pts_tigela(), 2.0, 1.0, espessura=0.4)
        self.assertAlmostEqual(vista.zoom, 2.4)
        self.assertAlmostEqual(vista.azim, 80.0)
        raiz.destroy()


class TestSolido3dRoda(unittest.TestCase):
    def test_fator_zoom_roda_windows_e_x11(self) -> None:
        self.assertGreater(_fator_zoom_roda(120, 0), 1.0)
        self.assertLess(_fator_zoom_roda(-120, 0), 1.0)
        self.assertGreater(_fator_zoom_roda(0, 4), 1.0)
        self.assertLess(_fator_zoom_roda(0, 5), 1.0)
        self.assertEqual(_fator_zoom_roda(0, 0), 1.0)
        # Wine às vezes entrega o HIWORD do wParam em vez de ±120.
        self.assertGreater(_fator_zoom_roda(120 << 16, 0), 1.0)
        self.assertLess(_fator_zoom_roda(((-120) & 0xFFFF) << 16, 0), 1.0)


class TestCabecalhoSobre(unittest.TestCase):
    def test_cabecalho_sem_bom_nem_iguais_soltos(self) -> None:
        from pathlib import Path

        from ceraform.ui_desktop import _blocos_autoria_sobre, _texto_cabecalho

        bruto = (Path(__file__).resolve().parent.parent / "CABECALHO.txt").read_bytes()
        self.assertFalse(bruto.startswith(b"\xef\xbb\xbf"), "BOM no início do arquivo")
        self.assertNotIn(b"\xef\xbb\xbf", bruto)
        texto = _texto_cabecalho()
        self.assertNotIn("\ufeff", texto)
        self.assertIn("CERAFORM", texto)
        partes = [b for b in _blocos_autoria_sobre() if isinstance(b, str)]
        self.assertGreaterEqual(len(partes), 2)
        self.assertTrue(any("CERAFORM" in p for p in partes))
        self.assertTrue(any("licença" in p.lower() for p in partes))
        from ceraform.ui_desktop import _linhas_cabecalho_windows

        limpo = _linhas_cabecalho_windows(
            ["\ufeff========", "", "", "CERAFORM", "========"]
        )
        self.assertEqual(limpo.count(""), 1)
        self.assertIn("CERAFORM", limpo)
        self.assertTrue(any(set(x.strip()) <= {"="} for x in limpo if x.strip()))


if __name__ == "__main__":
    unittest.main()

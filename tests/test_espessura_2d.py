# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ceraform.perfil import meridiano_com_base, perfil_raios
from ceraform.visual_2d import (
    desenhar_perfil_completo,
    offset_meridiano_normal,
    polilinha_perfil_interno,
)


def _tigela_base_zero():
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
    z_w, r_w, r_b, z_b = meridiano_com_base(z, r, "Côncava")
    r_in, z_in = polilinha_perfil_interno(z_w, r_w, r_b, z_b)
    return z, r, r_in, z_in


def _jarro_boca_estreita():
    z, r = perfil_raios(
        h=18.0,
        db=8.0,
        dmax=16.0,
        hmax=8.0,
        dbase=7.0,
        dmeio=0.0,
        perfil_geometrico="Convexo",
        tipo_base="Reta",
    )
    z_w, r_w, r_b, z_b = meridiano_com_base(z, r, "Reta")
    r_in, z_in = polilinha_perfil_interno(z_w, r_w, r_b, z_b)
    return z, r, r_in, z_in


class TestEspessuraCorte2d(unittest.TestCase):
    def test_offset_base_zero_fecha_no_eixo(self) -> None:
        _z, _r, r_in, z_in = _tigela_base_zero()
        t = 0.4
        r_out, z_out = offset_meridiano_normal(r_in, z_in, t)
        self.assertLess(float(r_out[0]), 0.05)
        self.assertLess(float(z_out[0]), float(z_in[0]) - 0.5 * t)

    def test_offset_distancia_na_parede_aproxima_a_espessura(self) -> None:
        _z, _r, r_in, z_in = _tigela_base_zero()
        t = 0.4
        r_out, z_out = offset_meridiano_normal(r_in, z_in, t)
        n = min(r_in.size, r_out.size)
        i = n // 2
        dist = float(
            np.hypot(r_out[i] - r_in[i], z_out[i] - z_in[i])
        )
        self.assertAlmostEqual(dist, t, delta=0.08)

    def test_tracejado_contorna_a_base_zero(self) -> None:
        z, r, _r_in, _z_in = _tigela_base_zero()
        dados = {
            "sitio": "Toca do Baixao da Pedra Furada",
            "numero": "ETIQ-67083",
            "h": 7.3,
            "db": 16.6,
            "dmax": 16.9,
            "hmax": 3.6,
            "dbase": 0.0,
            "espessura_parede": 0.4,
        }
        fig = Figure(figsize=(8, 6), dpi=120)
        ax = fig.add_subplot(111)
        desenhar_perfil_completo(
            ax,
            z,
            r,
            dados,
            forma="Elipsóide Vertical",
            volume_l=1.355,
            tipo_base="Côncava",
            espessura=0.4,
            modo="tela",
        )
        castanho = None
        for line in ax.get_lines():
            if line.get_color() != "#b45309":
                continue
            xs = np.asarray(line.get_xdata(), dtype=float)
            if castanho is None or xs.size > castanho.size:
                castanho = xs
        self.assertIsNotNone(castanho)
        assert castanho is not None
        self.assertGreater(castanho.size, 20)
        centro = 0.5 * (float(np.min(castanho)) + float(np.max(castanho)))
        self.assertLess(float(np.min(np.abs(castanho - centro))), 0.15)
        rotulos = [
            str(c.get_text()).lower()
            for c in ax.get_children()
            if hasattr(c, "get_text")
        ]
        self.assertTrue(any("espes. parede" in t for t in rotulos))
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "espessura.png"
            fig.savefig(str(dest), format="png", facecolor="white", dpi=140)
            self.assertTrue(dest.is_file() and dest.stat().st_size > 1000)

    def test_fechamento_na_borda_e_horizontal(self) -> None:
        t = 0.4
        casos = (
            _tigela_base_zero(),
            _jarro_boca_estreita(),
        )
        for _z, _r, r_in, z_in in casos:
            r_out, z_out = offset_meridiano_normal(r_in, z_in, t)
            self.assertAlmostEqual(float(z_out[-1]), float(z_in[-1]), places=6)
            self.assertAlmostEqual(float(r_out[-1]), float(r_in[-1]) + t, places=6)
            self.assertLessEqual(float(np.max(z_out)), float(z_in[-1]) + 1e-6)
            if z_out.size >= 2:
                self.assertAlmostEqual(float(z_out[-1]), float(z_out[-2]), places=5)


if __name__ == "__main__":
    unittest.main()

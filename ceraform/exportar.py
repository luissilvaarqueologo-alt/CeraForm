# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

from pathlib import Path

import numpy as np


def perfil_svg(
    caminho: Path,
    z: np.ndarray,
    r: np.ndarray,
    titulo: str,
    tipo_base: str = "Reta",
) -> None:
    from ceraform.perfil import meridiano_com_base
    z_w, r_w, r_b, z_b = meridiano_com_base(z, r, tipo_base)
    zmin = float(min(z_w.min(), z_b.min()))
    zmax = float(max(z_w.max(), z_b.max()))
    rm = float(max(r_w.max(), 1.0))
    h = max(zmax - zmin, 1.0)
    pad = 24
    escala = 4.84
    w = int(2 * rm * escala + 2 * pad + 8)
    ht = int(h * escala + 2 * pad)

    def px(rr: float, zz: float) -> tuple[float, float]:
        return pad + (rm + rr) * escala, pad + (zmax - zz) * escala

    pts_esq = " ".join(
        f"{px(-ri, zi)[0]:.2f},{px(-ri, zi)[1]:.2f}" for zi, ri in zip(z_w, r_w)
    )
    pts_base = " ".join(
        f"{px(-ri, zi)[0]:.2f},{px(-ri, zi)[1]:.2f}" for zi, ri in zip(z_b, r_b)
    )
    pts_dir = " ".join(
        f"{px(ri, zi)[0]:.2f},{px(ri, zi)[1]:.2f}" for zi, ri in zip(z_w, r_w)
    )
    pts_base_dir = " ".join(
        f"{px(ri, zi)[0]:.2f},{px(ri, zi)[1]:.2f}" for zi, ri in zip(z_b, r_b)
    )
    eixo = f"{px(0, zmin)[0]:.2f},{px(0, zmin)[1]:.2f} {px(0, zmax)[0]:.2f},{px(0, zmax)[1]:.2f}"
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{ht}" viewBox="0 0 {w} {ht}">
  <title>{titulo}</title>
  <rect width="100%" height="100%" fill="white"/>
  <polyline fill="none" stroke="#1a56db" stroke-width="1.6" points="{pts_esq}"/>
  <polyline fill="none" stroke="#1a56db" stroke-width="1.6" points="{pts_dir}"/>
  <polyline fill="none" stroke="#1a56db" stroke-width="1.6" points="{pts_base}"/>
  <polyline fill="none" stroke="#1a56db" stroke-width="1.6" points="{pts_base_dir}"/>
  <polyline fill="none" stroke="#888" stroke-dasharray="4 4" stroke-width="1" points="{eixo}"/>
  <text x="{pad}" y="16" font-family="Times New Roman, Times, Liberation Serif, serif" font-size="12">{titulo} — perfil completo — escala 1 cm = {escala} px</text>
</svg>
"""
    caminho.write_text(svg, encoding="utf-8")


def malha_stl(
    caminho: Path,
    malhas: list[tuple[np.ndarray, np.ndarray, np.ndarray]],
) -> None:
    """STL ASCII: parede de revolução e disco do fundo."""
    linhas = ["solid vaso"]
    for x, y, z in malhas:
        nt, nz = x.shape
        for i in range(nt - 1):
            for j in range(nz - 1):
                p00 = (x[i, j], y[i, j], z[i, j])
                p10 = (x[i + 1, j], y[i + 1, j], z[i + 1, j])
                p01 = (x[i, j + 1], y[i, j + 1], z[i + 1, j + 1])
                p11 = (x[i + 1, j + 1], y[i + 1, j + 1], z[i + 1, j + 1])
                for tri in ((p00, p10, p11), (p00, p11, p01)):
                    ax, ay, az = (
                        tri[1][0] - tri[0][0],
                        tri[1][1] - tri[0][1],
                        tri[1][2] - tri[0][2],
                    )
                    bx, by, bz = (
                        tri[2][0] - tri[0][0],
                        tri[2][1] - tri[0][1],
                        tri[2][2] - tri[0][2],
                    )
                    nx = ay * bz - az * by
                    ny = az * bx - ax * bz
                    nz_ = ax * by - ay * bx
                    linhas.append(f"  facet normal {nx:.6e} {ny:.6e} {nz_:.6e}")
                    linhas.append("    outer loop")
                    for p in tri:
                        linhas.append(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}")
                    linhas.append("    endloop")
                    linhas.append("  endfacet")
    linhas.append("endsolid vaso")
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def malha_obj(
    caminho: Path,
    malhas: list[tuple[np.ndarray, np.ndarray, np.ndarray]],
) -> None:
    linhas = ["# reconstituição geométrica de cerâmicas"]
    offset = 0
    for k, (x, y, z) in enumerate(malhas):
        nt, nz = x.shape
        linhas.append(f"o vaso_{k}")
        for i in range(nt):
            for j in range(nz):
                linhas.append(f"v {x[i, j]:.6f} {y[i, j]:.6f} {z[i, j]:.6f}")

        def vid(i: int, j: int) -> int:
            return offset + i * nz + j + 1

        for i in range(nt - 1):
            for j in range(nz - 1):
                a, b, c, d = vid(i, j), vid(i + 1, j), vid(i + 1, j + 1), vid(i, j + 1)
                linhas.append(f"f {a} {b} {c}")
                linhas.append(f"f {a} {c} {d}")
        offset += nt * nz
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")

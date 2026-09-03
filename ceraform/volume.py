# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ceraform.constantes import FAIXAS_VOLUME_L

CM3_POR_LITRO = 1_000.0
CM3_POR_ML = 1.0
MM3_POR_LITRO = CM3_POR_LITRO  # compatibilidade interna
MM3_POR_ML = CM3_POR_ML
FRACOES_CAPACIDADE_EFETIVA = (0.85, 0.90)


@dataclass
class ResultadoVolume:
    """Cubicagem da cavidade: centímetro cúbico (= mL) e litro."""

    mm3: float   # na verdade cm³; mantém o nome para compatibilidade interna
    ml: float
    litros: float


def _perfil_cubicagem(perfil: str) -> str:
    chave = (perfil or "Convexo").strip().lower()
    if chave in ("reto", "retilineo", "retilíneo", "linear"):
        return "Reto"
    if chave in ("concavo", "côncavo", "interna", "composto"):
        return "Concavo"
    return "Convexo"


def _volume_segmento_mm3(raio_a: float, raio_b: float, altura: float, modo: str) -> float:
    """Volume de revolução de um segmento em cm³ (base → maior diâmetro, ou maior → borda)."""
    h = float(altura)
    if h <= 1e-12:
        return 0.0
    a = max(float(raio_a), 0.0)
    b = max(float(raio_b), 0.0)
    if modo == "Reto":
        return math.pi * h / 3.0 * (a * a + a * b + b * b)
    if modo == "Convexo":
        return math.pi * h / 6.0 * (3.0 * a * a + 3.0 * b * b + h * h)
    v_concavo = math.pi * h / 6.0 * (3.0 * a * a + 3.0 * b * b - h * h)
    v_linear = math.pi * h / 3.0 * (a * a + a * b + b * b)
    return max(0.0, min(v_concavo, v_linear))


def calcular_volume(
    altura_total: float,
    diametro_maximo: float,
    diametro_borda: float,
    diametro_base: float,
    altura_diametro_max: float,
    perfil: str,
    espessura_parede: float = 0.0,
) -> ResultadoVolume:
    """Volume da cavidade por dois segmentos (inferior e superior).

    Perfis: Retilíneo (tronco de cone), Convexo (zona esférica) e
    Côncavo/Composto (zona reentrante, limitada pelo tronco linear).
    Com espessura da parede > 0, as medidas passam a ser as internas
    (diâmetros menos duas espessuras; altura total menos o fundo).
    """
    t = max(float(espessura_parede or 0.0), 0.0)
    h = max(float(altura_total) - t, 0.0)
    dmax = max(float(diametro_maximo) - 2.0 * t, 0.0)
    db = max(float(diametro_borda) - 2.0 * t, 0.0)
    d0 = max(float(diametro_base) - 2.0 * t, 0.0)
    hmax = min(max(float(altura_diametro_max) - t, 0.0), h)
    if h <= 0.0 or dmax <= 0.0:
        return ResultadoVolume(mm3=0.0, ml=0.0, litros=0.0)  # cm³=0

    modo = _perfil_cubicagem(perfil)
    r0 = d0 / 2.0
    rmax = dmax / 2.0
    rb = db / 2.0
    mm3 = _volume_segmento_mm3(r0, rmax, hmax, modo) + _volume_segmento_mm3(
        rmax, rb, h - hmax, modo
    )
    mm3 = max(mm3, 0.0)
    return ResultadoVolume(
        mm3=mm3,
        ml=mm3 / MM3_POR_ML,
        litros=mm3 / MM3_POR_LITRO,
    )


def _trapz(y: np.ndarray, x: np.ndarray) -> float:
    integrador = getattr(np, "trapezoid", np.trapz)
    return float(integrador(y, x))


def _planta_quadrangular(tipo_planta: str) -> bool:
    return str(tipo_planta or "").startswith("Quadr")


def area_secao_mm2(
    r_mm: np.ndarray | float,
    *,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
    tipo_planta: str = "Circular",
) -> np.ndarray:
    """Área da seção horizontal (cm²) à altura correspondente a cada raio."""
    r = np.asarray(r_mm, dtype=float)
    sx = float(rx_scale)
    sy = float(ry_scale)
    if _planta_quadrangular(tipo_planta):
        return 4.0 * sx * sy * np.square(r)
    return np.pi * (r * sx) * (r * sy)


def volume_litros(
    z_mm: np.ndarray,
    r_mm: np.ndarray,
    *,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
    tipo_planta: str = "Circular",
) -> float:
    """Volume da cavidade até o transbordamento (100 % da altura), em litros. Entrada em cm."""
    z = np.asarray(z_mm, dtype=float).ravel()
    r = np.asarray(r_mm, dtype=float).ravel()
    if z.size < 2:
        return 0.0
    area = area_secao_mm2(
        r, rx_scale=rx_scale, ry_scale=ry_scale, tipo_planta=tipo_planta
    )
    mm3 = _trapz(area, z)
    return max(mm3 / MM3_POR_LITRO, 0.0)


def volume_ate_altura_litros(
    z_mm: np.ndarray,
    r_mm: np.ndarray,
    z_corte_mm: float,
    *,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
    tipo_planta: str = "Circular",
) -> float:
    """Volume da cavidade até a altura de corte, em litros. Entrada em cm.

    A malha do perfil tem cerca de 240 passos: 0,85 H e 0,90 H podem cair entre
    dois nós. O raio em Z_corte é interpolado e entra sempre como limite
    superior do trapézio, para não truncar o último intervalo.
    """
    z = np.asarray(z_mm, dtype=float).ravel()
    r = np.asarray(r_mm, dtype=float).ravel()
    if z.size < 2:
        return 0.0
    ordem = np.argsort(z, kind="mergesort")
    z, r = z[ordem], r[ordem]
    z_lo = float(z[0])
    z_hi = float(z[-1])
    z_c = float(np.clip(z_corte_mm, z_lo, z_hi))
    if z_c <= z_lo:
        return 0.0
    abaixo = z < z_c - 1e-12
    z_sel = z[abaixo]
    r_sel = r[abaixo]
    r_c = float(np.interp(z_c, z, r))
    z_sel = np.append(z_sel, z_c)
    r_sel = np.append(r_sel, r_c)
    if z_sel.size < 2:
        return 0.0
    area = area_secao_mm2(
        r_sel, rx_scale=rx_scale, ry_scale=ry_scale, tipo_planta=tipo_planta
    )
    return max(_trapz(area, z_sel) / MM3_POR_LITRO, 0.0)


def capacidades_litros(
    z_mm: np.ndarray,
    r_mm: np.ndarray,
    h_mm: float,
    *,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
    tipo_planta: str = "Circular",
) -> dict[str, float]:
    """Capacidade efetiva (85 % e 90 % da altura total) e transbordamento (100 %). Entrada em cm."""
    z = np.asarray(z_mm, dtype=float).ravel()
    r = np.asarray(r_mm, dtype=float).ravel()
    z0 = float(z[0]) if z.size else 0.0
    h = float(h_mm) if h_mm and h_mm > 0 else (float(z[-1] - z0) if z.size else 0.0)
    kw = dict(rx_scale=rx_scale, ry_scale=ry_scale, tipo_planta=tipo_planta)
    v85 = volume_ate_altura_litros(z, r, z0 + 0.85 * h, **kw)
    v90 = volume_ate_altura_litros(z, r, z0 + 0.90 * h, **kw)
    v100 = volume_litros(z, r, **kw)
    return {
        "capacidade_efetiva_85": v85,
        "capacidade_efetiva_90": v90,
        "volume_transbordamento": v100,
    }


def observacao_volume(volume_l: float) -> str:
    if volume_l < 0.150:
        return "abaixo de 0,150 L"
    if volume_l >= 50.0:
        return "a partir de 50,0 L"
    return ""


def faixa_tamanho(volume_l: float) -> str:
    if volume_l < 0.150:
        return "Pequeno"
    if volume_l >= 50.0:
        return "Extra grande"
    for nome, a, b in FAIXAS_VOLUME_L:
        if a <= volume_l < b:
            return nome
    return "Extra grande"


def rotulo_tamanho(volume_l: float) -> str:
    faixa = faixa_tamanho(volume_l)
    obs = observacao_volume(volume_l)
    if obs:
        return f"{faixa} ({obs})"
    return faixa

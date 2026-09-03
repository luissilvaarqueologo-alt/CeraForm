# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Estacao:
    z: float
    r: float


FRACOES_MEDICAO = (0.25, 0.5, 0.75)


def _raio_de_diametro(diametro: float) -> float:
    """Diâmetro interno → raio. Nunca mistura D e R na interpolação."""
    d = max(float(diametro), 0.0)
    if d < 1e-9:
        return 0.0
    return d / 2.0


# Abaixo deste raio (cm) o diâmetro da base trata-se como 0 (sem anel).
_RAIO_BASE_ZERO = 0.05


def perfil_arco_borda_a_borda(
    *,
    h: float,
    db: float,
    n: int = 240,
) -> tuple[np.ndarray, np.ndarray]:
    """Tigela: círculo ou elipse da borda ao fundo (maior diâmetro = diâmetro da borda).

    Tangente horizontal no apoio (sem pontinha). Círculo se H ≤ R; senão elipse.
    """
    R = max(float(db), 0.05) / 2.0
    H = max(float(h), 1e-6)
    n_pts = max(int(n), 8)

    if H <= R + 1e-12:
        # Arco circular (φ de 0 no fundo até φ_max ≤ π/2 na borda).
        rho = (R * R + H * H) / (2.0 * H)
        phi_max = float(np.arctan2(R, rho - H))
        if phi_max < 1e-12:
            phi_max = 0.5 * float(np.pi)
        phi = np.linspace(0.0, phi_max, n_pts)
        r = rho * np.sin(phi)
        z = rho * (1.0 - np.cos(phi))
    else:
        # Semi-elipse: (r/R)² + ((H−z)/H)² = 1, ramo inferior.
        phi = np.linspace(0.0, 0.5 * float(np.pi), n_pts)
        r = R * np.sin(phi)
        z = H * (1.0 - np.cos(phi))

    r[0] = 0.0
    z[0] = 0.0
    r[-1] = R
    z[-1] = H
    return z, r


def perfil_circulo_elipse_fechado(
    *,
    h: float,
    db: float,
    dmax: float,
    hmax: float,
    n: int = 240,
) -> tuple[np.ndarray, np.ndarray]:
    """Fundo arredondado (diâmetro da base 0 cm): círculo ou elipse borda a borda.

    O meridiano apoia com tangente horizontal no eixo (calota, nunca cone).

    - Maior diâmetro igual ao da borda, ou na própria borda: um único arco/elipse.
    - Barriga mais larga: elipse inferior (polo no fundo, equador no maior
      diâmetro) + elipse superior (equador → borda), contínuas e com parede
      vertical no encontro. Círculo perfeito quando os semi-eixos coincidem.
    """
    H = max(float(h), 1e-6)
    R_borda = max(float(db), 0.05) / 2.0
    R_max = max(float(dmax), float(db), 0.05) / 2.0
    hmax_c = min(max(float(hmax), 1e-6), max(H - 1e-6, 1e-6))
    n_pts = max(int(n), 16)

    # Tigela só quando o maior diâmetro está na borda. Diferença de 2 cm
    # (QMN-0003: 23,5 vs 21) já exige a elipse da barriga — a tolerância
    # de classificação (12 %) não entra no desenho.
    if hmax_c >= 0.92 * H:
        return perfil_arco_borda_a_borda(h=H, db=2.0 * max(R_borda, R_max), n=n_pts)

    n_inf = max(n_pts // 2, 8)
    n_sup = max(n_pts - n_inf + 1, 8)
    phi = np.linspace(0.0, 0.5 * float(np.pi), n_inf)
    r_inf = R_max * np.sin(phi)
    z_inf = hmax_c * (1.0 - np.cos(phi))

    razao = float(min(max(R_borda / R_max, 0.0), 0.999999))
    psi_max = float(np.arccos(razao))
    if psi_max < 1e-9:
        z_sup = np.linspace(hmax_c, H, n_sup)
        r_sup = np.full_like(z_sup, R_max)
    else:
        b_sup = (H - hmax_c) / float(np.sin(psi_max))
        psi = np.linspace(0.0, psi_max, n_sup)
        r_sup = R_max * np.cos(psi)
        z_sup = hmax_c + b_sup * np.sin(psi)

    z = np.concatenate([z_inf, z_sup[1:]])
    r = np.concatenate([r_inf, r_sup[1:]])
    r[0] = 0.0
    z[0] = 0.0
    r[-1] = R_borda
    z[-1] = H
    return z, r


def pares_amostra(texto: str) -> list[tuple[float, float]]:
    """Lê pares altura, diâmetro (cm) gravados em texto, um por linha."""
    out: list[tuple[float, float]] = []
    for linha in (texto or "").splitlines():
        bruta = linha.strip().replace(";", ",")
        if not bruta:
            continue
        partes = [p.strip() for p in bruta.replace("\t", ",").split(",") if p.strip()]
        if len(partes) < 2:
            continue
        try:
            out.append(
                (
                    float(partes[0].replace(",", ".")),
                    float(partes[1].replace(",", ".")),
                )
            )
        except ValueError:
            continue
    return out


def _tolerancia_fracao(h: float) -> float:
    """Janela para reconhecer uma cota como 1/4, 1/2 ou 3/4 da altura total."""
    return max(0.02 * max(float(h), 0.0), 0.15)


def medicoes_fracao(
    h: float, d_14: float, d_12: float, d_34: float
) -> list[tuple[float, float]]:
    """Diâmetros internos a um quarto, à metade e a três quartos da altura total."""
    if h <= 0:
        return []
    pares: list[tuple[float, float]] = []
    for frac, diam in zip(FRACOES_MEDICAO, (d_14, d_12, d_34)):
        if diam > 0:
            pares.append((h * frac, diam))
    return pares


def texto_medicoes_fracao(h: float, d_14: float, d_12: float, d_34: float) -> str:
    return "\n".join(
        f"{alt:.1f}, {diam:.1f}" for alt, diam in medicoes_fracao(h, d_14, d_12, d_34)
    )


def amostras_exceto_fracoes(
    texto: str, h: float
) -> list[tuple[float, float]]:
    """Pares gravados que não são as cotas a 1/4, 1/2 e 3/4 da altura total."""
    pares = pares_amostra(texto)
    if float(h) <= 0:
        return pares
    alvos = [float(h) * f for f in FRACOES_MEDICAO]
    tol = _tolerancia_fracao(h)
    return [
        (alt, diam)
        for alt, diam in pares
        if all(abs(alt - alvo) > tol for alvo in alvos)
    ]


def texto_amostras_gravadas(
    h: float,
    d_14: float,
    d_12: float,
    d_34: float,
    outras: list[tuple[float, float]] | None = None,
) -> str:
    """Junta cotas livres (pescoço, etc.) com os diâmetros a 1/4, 1/2 e 3/4."""
    pares = list(outras or [])
    pares.extend(medicoes_fracao(h, d_14, d_12, d_34))
    pares.sort(key=lambda p: p[0])
    return "\n".join(f"{alt:.1f}, {diam:.1f}" for alt, diam in pares)


def diametros_fracao(texto: str, h: float) -> tuple[float, float, float]:
    """Recupera os três diâmetros a partir do texto gravado.

    Só associa um par à fração se a altura cair na janela dessa cota —
    uma junção bojo–pescoço a 8,0 cm não preenche o campo de três quartos.
    """
    pares = pares_amostra(texto)
    saida = [0.0, 0.0, 0.0]
    if not pares:
        return (0.0, 0.0, 0.0)
    if h > 0:
        alvos = [h * f for f in FRACOES_MEDICAO]
        tol = _tolerancia_fracao(h)
        ocupado: set[int] = set()
        for alt, diam in pares:
            i = min(range(3), key=lambda k: abs(alt - alvos[k]))
            if i in ocupado or abs(alt - alvos[i]) > tol:
                continue
            ocupado.add(i)
            saida[i] = diam
    else:
        for i, (_alt, diam) in enumerate(pares[:3]):
            saida[i] = diam
    return (saida[0], saida[1], saida[2])


def _ordenar_estacoes(z: np.ndarray, r: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ordena por Z crescente e funde alturas repetidas (fica o maior raio).

    Raio 0 cm é permitido (diâmetro da base 0). Não forçar piso artificial —
    isso distorcia o fecho no eixo e o volume de cones.
    """
    z = np.asarray(z, dtype=float).ravel()
    r = np.asarray(r, dtype=float).ravel()
    if z.size == 0:
        return z, r
    ordem = np.argsort(z, kind="mergesort")
    z, r = z[ordem], np.maximum(r[ordem], 0.0)
    z_out = [float(z[0])]
    r_out = [float(r[0])]
    for zi, ri in zip(z[1:], r[1:]):
        if abs(float(zi) - z_out[-1]) < 1e-9:
            r_out[-1] = max(r_out[-1], float(ri))
        else:
            z_out.append(float(zi))
            r_out.append(float(ri))
    return np.asarray(z_out, dtype=float), np.asarray(r_out, dtype=float)


def quebras_meridiano(
    z: np.ndarray,
    r: np.ndarray,
    graus_min: float = 18.0,
) -> list[tuple[float, float]]:
    """Vértices interiores em que a parede muda de direção o bastante para ser carena."""
    z = np.asarray(z, dtype=float).ravel()
    r = np.asarray(r, dtype=float).ravel()
    if z.size < 3:
        return []
    z, r = _ordenar_estacoes(z, r)
    quebras: list[tuple[float, float]] = []
    for i in range(1, z.size - 1):
        v1 = np.array([z[i] - z[i - 1], r[i] - r[i - 1]], dtype=float)
        v2 = np.array([z[i + 1] - z[i], r[i + 1] - r[i]], dtype=float)
        n1 = float(np.linalg.norm(v1))
        n2 = float(np.linalg.norm(v2))
        if n1 < 1e-9 or n2 < 1e-9:
            continue
        cosang = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
        ang = float(np.degrees(np.arccos(cosang)))
        if ang >= graus_min:
            quebras.append((float(z[i]), ang))
    return quebras


_EPS_PCHIP = 1e-12


def _proteger_div(numer: np.ndarray | float, denom: np.ndarray | float) -> np.ndarray | float:
    """Divisão com piso ε no denominador (mesmo sinal), evita ZeroDivision e inf."""
    d = np.asarray(denom, dtype=float)
    n = np.asarray(numer, dtype=float)
    sinal = np.where(d >= 0.0, 1.0, -1.0)
    d_ok = np.where(np.abs(d) < _EPS_PCHIP, sinal * _EPS_PCHIP, d)
    return n / d_ok


def _limitar_deriv_intervalo(d: float, delta: float) -> float:
    """Mantém d no cone de Fritsch–Carlson: mesmo sinal que δ e |d| ≤ 3|δ|."""
    if abs(delta) < _EPS_PCHIP:
        return 0.0
    if d * delta < 0.0:
        return 0.0
    lim = 3.0 * abs(delta)
    if abs(d) > lim:
        return float(np.copysign(lim, delta))
    return float(d)


def _forcar_pico_horizontal(
    deriv: np.ndarray, z_c: np.ndarray, r_c: np.ndarray, z_pico: float
) -> np.ndarray:
    """Anula dR/dZ no maior diâmetro sem violar a monotonicidade dos vizinhos."""
    d = np.array(deriv, dtype=float, copy=True)
    if z_c.size < 3:
        return d
    i = int(np.argmin(np.abs(z_c - float(z_pico))))
    d[i] = 0.0
    if i > 0:
        h_l = float(np.maximum(z_c[i] - z_c[i - 1], _EPS_PCHIP))
        delta_l = float(_proteger_div(r_c[i] - r_c[i - 1], h_l))
        d[i - 1] = _limitar_deriv_intervalo(float(d[i - 1]), delta_l)
    if i < z_c.size - 1:
        h_r = float(np.maximum(z_c[i + 1] - z_c[i], _EPS_PCHIP))
        delta_r = float(_proteger_div(r_c[i + 1] - r_c[i], h_r))
        d[i + 1] = _limitar_deriv_intervalo(float(d[i + 1]), delta_r)
    return d


def _pchip_derivadas(z: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Inclinações Fritsch–Carlson (PCHIP monótono por troços)."""
    h = np.maximum(np.diff(z), _EPS_PCHIP)
    delta = _proteger_div(np.diff(r), h)
    n = z.size
    d = np.zeros(n, dtype=float)
    if n == 2:
        d[0] = d[1] = float(delta[0])
        return d
    for i in range(1, n - 1):
        if delta[i - 1] * delta[i] <= 0.0:
            d[i] = 0.0
        else:
            w1 = 2.0 * h[i] + h[i - 1]
            w2 = h[i] + 2.0 * h[i - 1]
            inv = _proteger_div(w1, delta[i - 1]) + _proteger_div(w2, delta[i])
            d[i] = float(_proteger_div(w1 + w2, inv))

    def _extremo(h0: float, h1: float, m0: float, m1: float) -> float:
        s = float(_proteger_div((2.0 * h0 + h1) * m0 - h0 * m1, h0 + h1))
        if s * m0 <= 0.0:
            return 0.0
        if m0 * m1 < 0.0 and abs(s) > abs(3.0 * m0):
            return 3.0 * m0
        return s

    d[0] = _extremo(float(h[0]), float(h[1]), float(delta[0]), float(delta[1]))
    d[-1] = _extremo(float(h[-1]), float(h[-2]), float(delta[-1]), float(delta[-2]))
    return d


def _hermite_cubico(z_c: np.ndarray, r_c: np.ndarray, deriv: np.ndarray, z_out: np.ndarray) -> np.ndarray:
    """Spline de Hermite cúbica por troços (equivalente ao CubicHermiteSpline)."""
    h = np.maximum(np.diff(z_c), _EPS_PCHIP)
    idx = np.searchsorted(z_c, z_out, side="right") - 1
    idx = np.clip(idx, 0, z_c.size - 2)
    t = _proteger_div(z_out - z_c[idx], h[idx])
    t2 = t * t
    t3 = t2 * t
    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2
    return (
        h00 * r_c[idx]
        + h10 * h[idx] * deriv[idx]
        + h01 * r_c[idx + 1]
        + h11 * h[idx] * deriv[idx + 1]
    )


def _minimos_locais_raio(z_c: np.ndarray, r_c: np.ndarray) -> list[float]:
    """Alturas interiores de mínimo de raio (pescoço / cintura)."""
    z_c = np.asarray(z_c, dtype=float)
    r_c = np.asarray(r_c, dtype=float)
    out: list[float] = []
    if z_c.size < 3:
        return out
    for i in range(1, z_c.size - 1):
        ri = float(r_c[i])
        if ri <= float(r_c[i - 1]) and ri <= float(r_c[i + 1]):
            out.append(float(z_c[i]))
    return out


def _pchip_perfil(
    z_ctrl: np.ndarray,
    r_ctrl: np.ndarray,
    z_out: np.ndarray,
    *,
    z_pico: float | None = None,
    deriv_inicio: float | None = None,
    deriv_fim: float | None = None,
) -> np.ndarray:
    """PCHIP (Piecewise Cubic Hermite) entre estações de controlo.

    A distorção anterior vinha de dois arcos circulares independentes que se
    encontravam no maior diâmetro: mesmo com tangente horizontal (C¹), a
    curvatura saltava (descontinuidade C²). Isso lia-se como acinturamento
    no 2D e como degrau/sobreposição no 3D.

    O PCHIP (Fritsch–Carlson) é C¹, não oscila (sem Runge/overshoot) e, num
    máximo local, a derivada anula-se — o bojo fica no ponto medido, sem vale
    antes nem depois. Aqui ainda forçamos dr/dZ = 0 na estação do maior
    diâmetro, para a junta ser suave. Prefere SciPy (`PchipInterpolator`);
    se não estiver instalado, usa a mesma regra só com NumPy.
    """
    z_c, r_c = _ordenar_estacoes(z_ctrl, r_ctrl)
    z_out = np.asarray(z_out, dtype=float)
    if z_c.size == 0:
        return np.full_like(z_out, 0.002)
    if z_c.size == 1:
        return np.full_like(z_out, float(r_c[0]))
    deriv = None
    try:
        from scipy.interpolate import CubicHermiteSpline, PchipInterpolator

        pchip = PchipInterpolator(z_c, r_c, extrapolate=True)
        deriv = np.asarray(pchip.derivative()(z_c), dtype=float)
    except (ImportError, ValueError, TypeError):
        deriv = _pchip_derivadas(z_c, r_c)
    if deriv_inicio is not None:
        deriv[0] = float(deriv_inicio)
    if deriv_fim is not None:
        deriv[-1] = float(deriv_fim)
    if z_c.size >= 3:
        for zp in _minimos_locais_raio(z_c, r_c):
            deriv = _forcar_pico_horizontal(deriv, z_c, r_c, zp)
        if z_pico is not None:
            deriv = _forcar_pico_horizontal(deriv, z_c, r_c, float(z_pico))
    try:
        from scipy.interpolate import CubicHermiteSpline

        r = np.asarray(CubicHermiteSpline(z_c, r_c, deriv)(z_out), dtype=float)
    except (ImportError, ValueError, TypeError):
        r = _hermite_cubico(z_c, r_c, deriv, z_out)
    return np.maximum(np.asarray(r, dtype=float), 0.0)


def _interpolar_estacoes(
    z_ctrl: np.ndarray,
    r_ctrl: np.ndarray,
    z_out: np.ndarray,
    perfil: str,
    *,
    z_pico: float | None = None,
    deriv_inicio: float | None = None,
    deriv_fim: float | None = None,
) -> np.ndarray:
    p = (perfil or "Convexo").strip()
    z_c, r_c = _ordenar_estacoes(z_ctrl, r_ctrl)
    if z_out.size == 0:
        return z_out
    if p in ("Reto", "Carenado Simples", "Carenado Duplo"):
        return np.maximum(np.interp(z_out, z_c, r_c), 0.0)
    return _pchip_perfil(
        z_c,
        r_c,
        z_out,
        z_pico=z_pico,
        deriv_inicio=deriv_inicio,
        deriv_fim=deriv_fim,
    )


def _juntar_estacoes(
    *,
    h: float,
    db: float,
    dmax: float,
    hmax: float,
    dbase: float,
    dmeio: float,
    amostras: list[tuple[float, float]],
    altura_carena: float,
    diametro_carena: float,
    altura_carena2: float,
    diametro_carena2: float,
    altura_juncao: float,
    diametro_juncao: float,
) -> list[Estacao]:
    pts: dict[float, float] = {
        0.0: _raio_de_diametro(dbase),
        float(h): _raio_de_diametro(db),
    }
    hmax_c = min(max(float(hmax), 1e-6), max(h - 1e-6, 1e-6))
    pts[hmax_c] = _raio_de_diametro(dmax)
    if dmeio > 0:
        pts[h / 2.0] = _raio_de_diametro(dmeio)
    for alt, diam in amostras:
        if 0 < alt < h and diam > 0:
            pts[float(alt)] = _raio_de_diametro(diam)
    if 0 < altura_carena < h and diametro_carena > 0:
        pts[float(altura_carena)] = _raio_de_diametro(diametro_carena)
    if 0 < altura_carena2 < h and diametro_carena2 > 0:
        pts[float(altura_carena2)] = _raio_de_diametro(diametro_carena2)
    if 0 < altura_juncao < h and diametro_juncao > 0:
        pts[float(altura_juncao)] = _raio_de_diametro(diametro_juncao)
    z_c = np.array(list(pts.keys()), dtype=float)
    r_c = np.array(list(pts.values()), dtype=float)
    z_c, r_c = _ordenar_estacoes(z_c, r_c)
    return [Estacao(z=float(zi), r=float(ri)) for zi, ri in zip(z_c, r_c)]


def _reforcar_pescoco_piriforme(
    z_c: np.ndarray,
    r_c: np.ndarray,
    h: float,
    hmax: float,
    db: float,
    dmax: float,
    perfil: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Barriga baixa e borda estreita: estação extra no pescoço (silhueta de pêra)."""
    if perfil in ("Reto", "Carenado Simples", "Carenado Duplo"):
        return z_c, r_c
    if h <= 0 or dmax <= 0:
        return z_c, r_c
    im = hmax / h
    rb = db / dmax
    if im >= 0.40 or rb >= 0.55:
        return z_c, r_c
    z_lo = hmax + 0.10 * (h - hmax)
    z_hi = 0.90 * h
    if np.any((z_c > z_lo) & (z_c < z_hi)):
        return z_c, r_c
    z_p = hmax + 0.36 * (h - hmax)
    r_borda = _raio_de_diametro(db)
    r_max = _raio_de_diametro(dmax)
    r_p = r_borda + 0.18 * (r_max - r_borda)
    return _ordenar_estacoes(
        np.append(z_c, z_p),
        np.append(r_c, r_p),
    )


def _calota_circular_fundo(
    z1: float, r1: float, n: int = 48
) -> tuple[np.ndarray, np.ndarray]:
    """Arco circular no eixo, tangente horizontal no fundo, até (z1, r1)."""
    z1 = max(float(z1), 1e-6)
    r1 = max(float(r1), 0.0)
    n_pts = max(int(n), 4)
    if r1 < 1e-9:
        z = np.linspace(0.0, z1, n_pts)
        return z, np.zeros_like(z)
    rho = (r1 * r1 + z1 * z1) / (2.0 * z1)
    cos_phi = float(np.clip(1.0 - z1 / rho, -1.0, 1.0))
    phi_max = float(np.arccos(cos_phi))
    if phi_max < 1e-12:
        phi_max = 1e-6
    phi = np.linspace(0.0, phi_max, n_pts)
    r = rho * np.sin(phi)
    z = rho * (1.0 - np.cos(phi))
    r[0] = 0.0
    z[0] = 0.0
    r[-1] = r1
    z[-1] = z1
    return z, r


def _deriv_calota_circular(z1: float, r1: float) -> float:
    """dR/dZ no extremo da calota circular (continuidade C¹ com o PCHIP)."""
    z1 = max(float(z1), 1e-6)
    r1 = max(float(r1), 1e-9)
    rho = (r1 * r1 + z1 * z1) / (2.0 * z1)
    return (rho - z1) / r1


def _pares_cota_extra(
    *,
    h: float,
    dmeio: float,
    amostras: list[tuple[float, float]],
    altura_juncao: float,
    diametro_juncao: float,
    altura_carena: float,
    diametro_carena: float,
    altura_carena2: float,
    diametro_carena2: float,
) -> list[tuple[float, float]]:
    pares = list(amostras or [])
    if float(dmeio) > 0:
        pares.append((h / 2.0, float(dmeio)))
    if float(altura_juncao) > 0 and float(diametro_juncao) > 0:
        pares.append((float(altura_juncao), float(diametro_juncao)))
    if float(altura_carena) > 0 and float(diametro_carena) > 0:
        pares.append((float(altura_carena), float(diametro_carena)))
    if float(altura_carena2) > 0 and float(diametro_carena2) > 0:
        pares.append((float(altura_carena2), float(diametro_carena2)))
    return pares


def _ha_estacao_extra(
    *,
    h: float,
    hmax: float,
    dmeio: float,
    amostras: list[tuple[float, float]],
    altura_juncao: float,
    diametro_juncao: float,
    altura_carena: float,
    diametro_carena: float,
    altura_carena2: float,
    diametro_carena2: float,
) -> bool:
    """Há cota extra além do núcleo (1/4, 1/2, 3/4, pescoço, junta, carena).

    Qualquer altura estritamente entre a base e a borda, distinta da altura do
    maior diâmetro, conta — inclusive quando a barriga está perto da boca.
    """
    h = max(float(h), 1e-6)
    hmax_c = min(max(float(hmax), 1e-6), max(h - 1e-6, 1e-6))
    # 0,5 mm: mesma cota que o núcleo, não 3 % da altura (isso engolia a
    # junção bojo–pescoço quando H_max ficava perto da borda).
    tol_z = 0.05
    for alt, diam in _pares_cota_extra(
        h=h,
        dmeio=dmeio,
        amostras=amostras,
        altura_juncao=altura_juncao,
        diametro_juncao=diametro_juncao,
        altura_carena=altura_carena,
        diametro_carena=diametro_carena,
        altura_carena2=altura_carena2,
        diametro_carena2=diametro_carena2,
    ):
        if diam <= 0:
            continue
        if alt <= tol_z or alt >= h - tol_z:
            continue
        if abs(alt - hmax_c) <= tol_z:
            continue
        return True
    return False


def perfil_fundo_arredondado_com_estacoes(
    *,
    h: float,
    db: float,
    dmax: float,
    hmax: float,
    n: int = 240,
    dmeio: float = 0.0,
    amostras: list[tuple[float, float]] | None = None,
    perfil_geometrico: str = "Convexo",
    perfil_trecho_base: str = "",
    perfil_trecho_borda: str = "",
    altura_carena: float = 0.0,
    diametro_carena: float = 0.0,
    altura_carena2: float = 0.0,
    diametro_carena2: float = 0.0,
    altura_juncao: float = 0.0,
    diametro_juncao: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Fundo em calota até a primeira cota; acima, todas as estações medidas.

    Sem cotas entre o fundo e o maior diâmetro: elipse até a barriga (equador
    horizontal). Com diâmetro a um quarto da altura (ou outra cota abaixo da
    barriga): arco circular até essa cota, depois PCHIP pelo restante.
    """
    H = max(float(h), 1e-6)
    R_max = max(float(dmax), float(db), 0.05) / 2.0
    hmax_c = min(max(float(hmax), 1e-6), max(H - 1e-6, 1e-6))
    n_pts = max(int(n), 16)
    n_inf = max(n_pts // 2, 8)

    est = _juntar_estacoes(
        h=H,
        db=db,
        dmax=dmax,
        hmax=hmax_c,
        dbase=0.0,
        dmeio=dmeio,
        amostras=amostras or [],
        altura_carena=altura_carena,
        diametro_carena=diametro_carena,
        altura_carena2=altura_carena2,
        diametro_carena2=diametro_carena2,
        altura_juncao=altura_juncao,
        diametro_juncao=diametro_juncao,
    )
    abaixo = [e for e in est if 1e-6 < e.z < hmax_c - 0.02 * H]
    deriv0: float | None = None
    if abaixo:
        z0 = float(abaixo[0].z)
        r0 = float(abaixo[0].r)
        z_inf, r_inf = _calota_circular_fundo(z0, r0, n_inf)
        deriv0 = _deriv_calota_circular(z0, r0)
    else:
        z0 = hmax_c
        r0 = R_max
        phi = np.linspace(0.0, 0.5 * float(np.pi), n_inf)
        z_inf = hmax_c * (1.0 - np.cos(phi))
        r_inf = R_max * np.sin(phi)

    z_ctrl = np.array([e.z for e in est if e.z >= z0 - 1e-9], dtype=float)
    r_ctrl = np.array([e.r for e in est if e.z >= z0 - 1e-9], dtype=float)
    z_ctrl, r_ctrl = _ordenar_estacoes(z_ctrl, r_ctrl)
    if z_ctrl.size == 0 or abs(float(z_ctrl[0]) - z0) > 1e-6:
        z_ctrl = np.concatenate([[z0], z_ctrl])
        r_ctrl = np.concatenate([[r0], r_ctrl])
    z_lin = np.linspace(z0, H, max(n_pts - n_inf + 1, 8))
    z_sup = np.unique(np.concatenate([z_lin, z_ctrl]))
    z_sup.sort()
    perfil = perfil_geometrico or "Convexo"
    z_quebra = float(altura_juncao) if altura_juncao > 0 else hmax_c
    _linear = ("Reto", "Carenado Simples", "Carenado Duplo")
    trecho_b = (perfil_trecho_base or "Convexo").strip()
    trecho_p = (perfil_trecho_borda or "Convexo").strip()
    if (
        perfil == "Composto"
        and float(altura_juncao) > 0
        and trecho_b not in _linear
        and trecho_p not in _linear
    ):
        r_sup = _interpolar_estacoes(
            z_ctrl, r_ctrl, z_sup, "Convexo", z_pico=hmax_c, deriv_inicio=deriv0
        )
    elif perfil == "Composto":
        r_sup = np.empty_like(z_sup)
        inf = z_sup <= z_quebra + 1e-12
        sup = z_sup >= z_quebra - 1e-12
        r_sup[inf] = _interpolar_estacoes(
            z_ctrl,
            r_ctrl,
            z_sup[inf],
            trecho_b or "Convexo",
            z_pico=hmax_c,
            deriv_inicio=deriv0,
        )
        r_sup[sup] = _interpolar_estacoes(
            z_ctrl,
            r_ctrl,
            z_sup[sup],
            trecho_p or "Convexo",
            z_pico=hmax_c,
            deriv_inicio=deriv0,
        )
    else:
        r_sup = _interpolar_estacoes(
            z_ctrl, r_ctrl, z_sup, perfil, z_pico=hmax_c, deriv_inicio=deriv0
        )
    z = np.concatenate([z_inf[:-1], z_sup])
    r = np.concatenate([r_inf[:-1], r_sup])
    r[0] = 0.0
    z[0] = 0.0
    r[-1] = max(float(db), 0.05) / 2.0
    z[-1] = H
    return z, r


def perfil_raios(
    *,
    h: float,
    db: float,
    dmax: float,
    hmax: float,
    dbase: float,
    dmeio: float = 0.0,
    geratriz: str = "",
    perfil_geometrico: str = "Convexo",
    perfil_trecho_base: str = "",
    perfil_trecho_borda: str = "",
    amostras: list[tuple[float, float]] | None = None,
    altura_carena: float = 0.0,
    diametro_carena: float = 0.0,
    altura_carena2: float = 0.0,
    diametro_carena2: float = 0.0,
    altura_juncao: float = 0.0,
    diametro_juncao: float = 0.0,
    tipo_base: str = "Reta",
    n: int = 240,
) -> tuple[np.ndarray, np.ndarray]:
    """Perfil interno (z, r), z=0 na base, r = metade do diâmetro interno.

    Diâmetro da base 0 cm com parede curva: círculo/elipse da borda à borda
    (fundo arredondado). Cotas opcionais a um quarto, à metade e a três quartos
    da altura total (e demais amostras) deformam essa calota para passar pelos
    pontos medidos. Parede reta ou carenada com base 0 cm: fecha em ponta
    (cone). Com anel na base, interpola as estações medidas.
    """
    h = max(float(h), 1e-6)
    perfil = perfil_geometrico or "Convexo"
    if geratriz and perfil == "Convexo":
        mapa = {"externa": "Convexo", "linear": "Reto", "interna": "Côncavo"}
        perfil = mapa.get(geratriz.lower(), perfil)
    if float(dbase) < 0.1 and perfil not in (
        "Reto",
        "Carenado Simples",
        "Carenado Duplo",
    ):
        if not _ha_estacao_extra(
            h=h,
            hmax=float(hmax),
            dmeio=dmeio,
            amostras=amostras or [],
            altura_juncao=altura_juncao,
            diametro_juncao=diametro_juncao,
            altura_carena=altura_carena,
            diametro_carena=diametro_carena,
            altura_carena2=altura_carena2,
            diametro_carena2=diametro_carena2,
        ):
            return perfil_circulo_elipse_fechado(
                h=h, db=max(float(db), 0.05), dmax=float(dmax), hmax=float(hmax), n=n
            )
        return perfil_fundo_arredondado_com_estacoes(
            h=h,
            db=db,
            dmax=dmax,
            hmax=hmax,
            n=n,
            dmeio=dmeio,
            amostras=amostras or [],
            perfil_geometrico=perfil,
            perfil_trecho_base=perfil_trecho_base,
            perfil_trecho_borda=perfil_trecho_borda,
            altura_carena=altura_carena,
            diametro_carena=diametro_carena,
            altura_carena2=altura_carena2,
            diametro_carena2=diametro_carena2,
            altura_juncao=altura_juncao,
            diametro_juncao=diametro_juncao,
        )
    est = _juntar_estacoes(
        h=h,
        db=db,
        dmax=dmax,
        hmax=hmax,
        dbase=dbase,
        dmeio=dmeio,
        amostras=amostras or [],
        altura_carena=altura_carena,
        diametro_carena=diametro_carena,
        altura_carena2=altura_carena2,
        diametro_carena2=diametro_carena2,
        altura_juncao=altura_juncao,
        diametro_juncao=diametro_juncao,
    )
    z_ctrl = np.array([e.z for e in est], dtype=float)
    r_ctrl = np.array([e.r for e in est], dtype=float)
    hmax_c = min(max(float(hmax), 1e-6), max(h - 1e-6, 1e-6))
    z_ctrl, r_ctrl = _ordenar_estacoes(z_ctrl, r_ctrl)
    z_ctrl, r_ctrl = _reforcar_pescoco_piriforme(
        z_ctrl, r_ctrl, h, hmax_c, db, dmax, perfil
    )
    z_lin = np.linspace(0.0, h, n)
    z = np.unique(np.concatenate([z_lin, z_ctrl]))
    z.sort()
    z_quebra = float(altura_juncao) if altura_juncao > 0 else hmax_c
    _linear = ("Reto", "Carenado Simples", "Carenado Duplo")
    trecho_b = (perfil_trecho_base or "Convexo").strip()
    trecho_p = (perfil_trecho_borda or "Convexo").strip()
    if (
        perfil == "Composto"
        and float(altura_juncao) > 0
        and trecho_b not in _linear
        and trecho_p not in _linear
    ):
        # Pescoço: junta arredondada (um só PCHIP, mínimo horizontal).
        r = _interpolar_estacoes(z_ctrl, r_ctrl, z, "Convexo", z_pico=hmax_c)
    elif perfil == "Composto":
        r = np.empty_like(z)
        inf = z <= z_quebra + 1e-12
        sup = z >= z_quebra - 1e-12
        r[inf] = _interpolar_estacoes(
            z_ctrl, r_ctrl, z[inf], trecho_b or "Convexo", z_pico=hmax_c
        )
        r[sup] = _interpolar_estacoes(
            z_ctrl, r_ctrl, z[sup], trecho_p or "Convexo", z_pico=hmax_c
        )
    elif perfil == "Carenado Duplo":
        r = _interpolar_estacoes(z_ctrl, r_ctrl, z, "Reto")
    else:
        r = _interpolar_estacoes(z_ctrl, r_ctrl, z, perfil, z_pico=hmax_c)
    # Permite raio 0 na base (diâmetro da base 0 cm); piso só evita NaN.
    r = np.maximum(r, 0.0)
    return z, r


def estacoes_de_medidas(dados: dict) -> tuple[np.ndarray, np.ndarray]:
    """Pontos de controlo (Z, R) a partir das medidas, já em raio e ordenados."""
    amostras = dados.get("amostras") or []
    if isinstance(amostras, str):
        pares = pares_amostra(amostras)
    elif isinstance(amostras, list):
        pares = [(float(a), float(b)) for a, b in amostras]
    else:
        pares = []
    est = _juntar_estacoes(
        h=float(dados.get("h") or 0.0),
        db=float(dados.get("db") or 0.0),
        dmax=float(dados.get("dmax") or 0.0),
        hmax=float(dados.get("hmax") or 0.0),
        dbase=float(dados.get("dbase") or 0.0),
        dmeio=float(dados.get("dmeio") or 0.0),
        amostras=pares,
        altura_carena=float(dados.get("altura_carena") or 0.0),
        diametro_carena=float(dados.get("diametro_carena") or 0.0),
        altura_carena2=float(dados.get("altura_carena2") or 0.0),
        diametro_carena2=float(dados.get("diametro_carena2") or 0.0),
        altura_juncao=float(dados.get("altura_juncao") or 0.0),
        diametro_juncao=float(dados.get("diametro_juncao") or 0.0),
    )
    return (
        np.array([e.z for e in est], dtype=float),
        np.array([e.r for e in est], dtype=float),
    )


def curva_base(
    tipo: str, raio: float, n: int = 24
) -> tuple[np.ndarray, np.ndarray]:
    """Meridiano do fundo: r de 0 até o raio da base.

    Z = 0 é o ponto de contato com a mesa: centro (r = 0) na base convexa,
    anel (r = R_b) na base côncava, disco inteiro na base reta.
    """
    raio = max(float(raio), 0.002)
    tipo = (tipo or "Reta").strip()
    r = np.linspace(0.0, raio, n)
    if tipo == "Côncava":
        s = 0.20 * raio
        z = s * (1.0 - (r / raio) ** 2)
        return r, z
    if tipo == "Convexa":
        s = 0.20 * raio
        z = s * (r / raio) ** 2
        return r, z
    return r, np.zeros_like(r)


def _juntar_parede_ao_anel(
    z_parede: np.ndarray,
    r_parede: np.ndarray,
    r_anel: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Recorta a parede a partir do raio do anel (base côncava com anel)."""
    z_p = np.asarray(z_parede, dtype=float).ravel()
    r_p = np.asarray(r_parede, dtype=float).ravel()
    r_anel = float(r_anel)
    if z_p.size < 2:
        return z_p, r_p
    i_ok = int(np.argmax(r_p >= r_anel - 1e-9))
    if r_p[i_ok] < r_anel - 1e-9:
        return z_p, r_p
    if i_ok == 0:
        r_out = r_p.copy()
        r_out[0] = r_anel
        return z_p - float(z_p[0]), r_out
    z0 = float(z_p[i_ok - 1])
    z1 = float(z_p[i_ok])
    r0 = float(r_p[i_ok - 1])
    r1 = float(r_p[i_ok])
    if abs(r1 - r0) < 1e-12:
        z_cruz = z1
    else:
        t = (r_anel - r0) / (r1 - r0)
        z_cruz = z0 + t * (z1 - z0)
    z_tail = np.concatenate([[z_cruz], z_p[i_ok:]])
    r_tail = np.concatenate([[r_anel], r_p[i_ok:]])
    return z_tail - float(z_tail[0]), r_tail


def meridiano_com_base(
    z_parede: np.ndarray,
    r_parede: np.ndarray,
    tipo_base: str = "Reta",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parede deslocada + curva do fundo, no mesmo referencial (Z = 0 na mesa).

    Na base convexa o anel fica à altura da sagita s; a parede sobe de +s para
    o meridiano não descolar do fundo. Na côncava o anel já está em Z = 0 e a
    parede não sobe. A calota (r_b, z_b) permanece com Z = 0 no contato.

    Diâmetro da base 0 cm: a parede já fecha no eixo (círculo/elipse ou cone);
    não se acrescenta calota.
    """
    z_p = np.asarray(z_parede, dtype=float).ravel()
    r_p = np.asarray(r_parede, dtype=float).ravel()
    tipo = (tipo_base or "Reta").strip()
    r0 = float(r_p[0]) if r_p.size else 0.0

    if r0 < _RAIO_BASE_ZERO:
        z0 = float(z_p[0]) if z_p.size else 0.0
        return z_p - z0, r_p, np.array([0.0]), np.array([0.0])

    raio_anel = max(r0, 0.002)
    r_b, z_b = curva_base(tipo, raio_anel)
    if tipo == "Côncava" and r0 >= _RAIO_BASE_ZERO:
        z_w0, r_w = _juntar_parede_ao_anel(z_p, r_p, raio_anel)
        z_w = z_w0 + float(z_b[-1])
        return z_w, r_w, r_b, z_b
    z_w = z_p + float(z_b[-1])
    return z_w, r_p, r_b, z_b


def pontos_meridiano(
    z_parede: np.ndarray,
    r_parede: np.ndarray,
    tipo_base: str = "Reta",
    rx_scale: float = 1.0,
) -> np.ndarray:
    """Polilinha do torno (eixo Z): centro da base → fundo → parede → borda."""
    z_w, r_w, r_b, z_b = meridiano_com_base(z_parede, r_parede, tipo_base)
    pts: list[list[float]] = []

    def _add(x: float, z: float) -> None:
        if pts and abs(pts[-1][0] - x) < 1e-6 and abs(pts[-1][2] - z) < 1e-6:
            return
        pts.append([float(x) * rx_scale, 0.0, float(z)])

    for ri, zi in zip(r_b, z_b):
        _add(ri, zi)
    for ri, zi in zip(r_w, z_w):
        _add(ri, zi)
    return np.asarray(pts, dtype=float)


def centro_massa_casca(
    z_parede: np.ndarray,
    r_parede: np.ndarray,
    r_base: np.ndarray,
    z_base: np.ndarray,
    tipo_base: str = "Reta",
) -> tuple[float, str]:
    """Centro de massa de uma casca fina de revolução (eixo z).

    A parede usa área 2π R ds. O fundo entra de forma explícita: disco plano
    π R_b² (base reta) ou superfície da calota parabólica 2π R ds (côncava/convexa).

    As alturas Z̄ da calota e da parede estão no mesmo referencial: Z = 0 no
    ponto de contato com a mesa (centro na convexa, anel na côncava).
    """

    def _casca_revolucao(z: np.ndarray, r: np.ndarray) -> tuple[float, float]:
        if len(z) < 2:
            return 0.0, 0.0
        ds = np.hypot(np.diff(z), np.diff(r))
        zm = 0.5 * (z[1:] + z[:-1])
        rm = np.maximum(0.5 * (r[1:] + r[:-1]), 1e-9)
        w = 2.0 * np.pi * rm * ds
        return float(np.sum(zm * w)), float(np.sum(w))

    mz, m = _casca_revolucao(z_parede, r_parede)
    r_b = np.asarray(r_base, dtype=float).ravel()
    z_b = np.asarray(z_base, dtype=float).ravel()
    if z_b.size:
        z_b = z_b - float(np.min(z_b))
    raio_anel = float(r_b[-1]) if r_b.size else 0.0
    tipo = (tipo_base or "Reta").strip()
    if tipo == "Reta" or z_b.size < 2 or float(np.ptp(z_b)) < 1e-9:
        area_fundo = np.pi * max(raio_anel, 0.0) ** 2
        z_fundo = 0.0
        mz2, m2 = area_fundo * z_fundo, area_fundo
        tipo_nota = "casca de revolução com disco plano do fundo (π R²)"
    else:
        mz2, m2 = _casca_revolucao(z_b, r_b)
        tipo_nota = "casca de revolução com calota parabólica do fundo"
    tot = m + m2
    if tot <= 0:
        return 0.0, "ponto de equilíbrio indeterminado"
    z_cm = (mz + mz2) / tot
    return z_cm, tipo_nota


def raio_curvatura_base(tipo: str, raio: float) -> float | None:
    """Raio de curvatura no centro da base (parabólica)."""
    raio = max(float(raio), 0.002)
    tipo = (tipo or "Reta").strip()
    if tipo not in ("Côncava", "Convexa"):
        return None
    s = 0.20 * raio
    if s <= 1e-9:
        return None
    return (raio * raio) / (2.0 * s)


def superficie_base(
    r_lin: np.ndarray,
    z_lin: np.ndarray,
    n_theta: int = 48,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    th = np.linspace(0.0, 2.0 * np.pi, n_theta)
    rg, tg = np.meshgrid(r_lin, th)
    zg = np.tile(z_lin, (n_theta, 1))
    x = rg * rx_scale * np.cos(tg)
    y = rg * ry_scale * np.sin(tg)
    return x, y, zg


def malha_revolucao(
    z: np.ndarray,
    r: np.ndarray,
    *,
    n_theta: int = 250,
    n_z: int = 160,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Revolução do perfil r(Z) em grade (θ, Z), sem inversão de fatias.

    Cada altura tem um único raio (broadcasting por linha). O PCHIP no Z
    denso evita o acinturamento que a densificação linear da polilinha
    preservava ao revolucionar.
    """
    z, r = _ordenar_estacoes(z, r)
    if z.size < 2:
        z = np.array([0.0, 1.0])
        r = np.array([0.002, 0.002])
    z_denso = np.linspace(float(z[0]), float(z[-1]), int(n_z))
    r_denso = np.interp(z_denso, z, r)
    theta = np.linspace(0.0, 2.0 * np.pi, int(n_theta))
    theta_grid, z_grid = np.meshgrid(theta, z_denso)
    r_grid = np.repeat(r_denso[:, np.newaxis], theta.size, axis=1)
    x = r_grid * float(rx_scale) * np.cos(theta_grid)
    y = r_grid * float(ry_scale) * np.sin(theta_grid)
    return x, y, z_grid


def solido_revolucao(
    z: np.ndarray,
    r: np.ndarray,
    n_theta: int = 200,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return malha_revolucao(
        z, r, n_theta=n_theta, n_z=max(len(z), 160), rx_scale=rx_scale, ry_scale=ry_scale
    )


def disco_fundo(
    raio_x: float,
    raio_y: float,
    z0: float = 0.0,
    n_theta: int = 48,
    n_rad: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Disco que fecha o fundo do vaso (z = base)."""
    ri = np.linspace(0.0, 1.0, n_rad)
    th = np.linspace(0.0, 2.0 * np.pi, n_theta)
    rg, tg = np.meshgrid(ri, th)
    x = max(raio_x, 0.002) * rg * np.cos(tg)
    y = max(raio_y, 0.002) * rg * np.sin(tg)
    z = np.full_like(x, z0)
    return x, y, z


def malhas_vaso(
    z: np.ndarray,
    r_int: np.ndarray,
    *,
    espessura: float = 0.0,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
    n_theta: int = 48,
    tipo_base: str = "Reta",
) -> list[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Parede (e interior, se houver espessura) mais o fundo segundo o tipo de base."""
    z_w, r_w, r_b, z_b = meridiano_com_base(z, r_int, tipo_base)
    r_ext = r_w + max(float(espessura), 0.0)
    malhas = [solido_revolucao(z_w, r_ext, n_theta=n_theta, rx_scale=rx_scale, ry_scale=ry_scale)]
    if espessura > 0:
        malhas.append(
            solido_revolucao(z_w, r_w, n_theta=n_theta, rx_scale=rx_scale, ry_scale=ry_scale)
        )
    r_bf = r_b + max(float(espessura), 0.0)
    malhas.append(superficie_base(r_bf, z_b, n_theta=n_theta, rx_scale=rx_scale, ry_scale=ry_scale))
    return malhas


def solido_com_parede(
    z: np.ndarray,
    r_int: np.ndarray,
    espessura: float,
    n_theta: int = 48,
    rx_scale: float = 1.0,
    ry_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r_ext = r_int + max(float(espessura), 0.0)
    return solido_revolucao(z, r_ext, n_theta=n_theta, rx_scale=rx_scale, ry_scale=ry_scale)

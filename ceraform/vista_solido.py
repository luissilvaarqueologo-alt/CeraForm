# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import os
import sys
import tkinter as tk
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from ceraform.caminhos import congelado, pasta_dados

COR_CERAMICA = "#C47A52"
COR_FUNDO = "#2b2b2b"
N_THETA = 250
N_Z = 160
N_RAD_FUNDO = 56
ESPESSURA_PADRAO_MM = 0.2   # 0,2 cm (equivalente a 2 mm)
RAIO_INTERNO_MIN_MM = 0.05  # 0,05 cm (equivalente a 0,5 mm)


def _eh_wine() -> bool:
    """True quando o .exe Windows está rodando sob Wine (OpenGL costuma travar)."""
    if sys.platform != "win32":
        return False
    try:
        import winreg

        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Wine")
        return True
    except OSError:
        return bool(os.environ.get("WINELOADER") or os.environ.get("WINEPREFIX"))


def _gpu_leve() -> bool:
    """Windows (exe nativo ou Wine): sem cubemap IBL nem MSAA 8×.

    Esses dois passos prendem o OpenGL em muitos notebooks; as luzes de
    estúdio e o PBR da argila continuam.
    """
    return sys.platform == "win32"


def _anotar_3d(msg: str) -> None:
    """No .exe, deixa rastro das etapas do sólido (útil se o OpenGL travar)."""
    if not congelado():
        return
    try:
        dest = pasta_dados() / "ceraform_3d.txt"
        with dest.open("a", encoding="utf-8") as arq:
            arq.write(msg.rstrip() + "\n")
    except OSError:
        pass


def _anotar_falha_pyvista(exc: BaseException) -> None:
    """No .exe, grava o motivo se o VTK/PyVista não subir."""
    if not congelado():
        return
    texto = "Falha ao iniciar o PyVista/VTK:\n" + "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    _anotar_3d(texto)
    try:
        dest = pasta_dados() / "ceraform_erro.txt"
        dest.write_text(texto, encoding="utf-8")
    except OSError:
        pass


def _importar_pyvista():
    try:
        import pyvista as pv

        return pv
    except Exception as exc:
        _anotar_falha_pyvista(exc)
        return None


def densificar_meridiano(pts: np.ndarray, n: int = 400) -> np.ndarray:
    """Interpola o meridiano em comprimento de arco, conservando os cantos."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 2:
        return pts
    d = np.sqrt(np.sum(np.diff(pts, axis=0) ** 2, axis=1))
    s = np.concatenate([[0.0], np.cumsum(d)])
    if s[-1] < 1e-9:
        return pts
    t = np.unique(np.concatenate([np.linspace(0.0, s[-1], n), s]))
    return np.column_stack([np.interp(t, s, pts[:, i]) for i in range(pts.shape[1])])


def _z_com_estacoes(z_w: np.ndarray, n: int = N_Z) -> np.ndarray:
    """Grade em Z que inclui os nós do meridiano (carenas, junção, cotas)."""
    z_w = np.asarray(z_w, dtype=float).ravel()
    if z_w.size < 2:
        return z_w
    z_lin = np.linspace(float(z_w[0]), float(z_w[-1]), int(n))
    z = np.unique(np.concatenate([z_lin, z_w]))
    z.sort()
    return z


def _xy_secao(
    r: np.ndarray,
    theta: np.ndarray,
    sy_scale: float,
    planta: str = "Circular",
) -> tuple[np.ndarray, np.ndarray]:
    """Seção horizontal: círculo/elipse, ou retângulo se a planta for quadrangular."""
    c = np.cos(theta)
    s = np.sin(theta)
    if str(planta or "").startswith("Quadr"):
        a = np.maximum(np.abs(r), 1e-9)
        b = np.maximum(np.abs(r) * float(sy_scale), 1e-9)
        rho = np.minimum(
            a / np.maximum(np.abs(c), 1e-9),
            b / np.maximum(np.abs(s), 1e-9),
        )
        return rho * c, rho * s
    return r * c, r * float(sy_scale) * s


def superficie_numpy(
    pts: np.ndarray,
    n_theta: int = N_THETA,
    sy_scale: float = 1.0,
    planta: str = "Circular",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    z_w, r_w = _extrair_parede(pts)
    z_d = _z_com_estacoes(z_w, N_Z)
    r_d = np.interp(z_d, z_w, r_w)
    theta = np.linspace(0.0, 2.0 * np.pi, n_theta)
    th, zz = np.meshgrid(theta, z_d)
    rr = np.repeat(r_d[:, np.newaxis], theta.size, axis=1)
    x, y = _xy_secao(rr, th, sy_scale, planta)
    return x, y, zz


def _extrair_parede(pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    z = np.asarray(pts[:, 2], dtype=float)
    r = np.abs(np.asarray(pts[:, 0], dtype=float))
    dz = np.diff(z)
    i0 = 0
    for i, dzi in enumerate(dz):
        if dzi > 1e-8:
            i0 = i
            break
    return z[i0:], r[i0:]


def _fator_zoom_roda(delta: int, num: int) -> float:
    """Fator da roda: >1 amplia, <1 reduz, 1.0 ignora o evento.

    Windows e Wine enviam MouseWheel (delta ±120, ±1, ou o HIWORD do
    wParam); o X11 nativo usa Button-4 (ampliar) e Button-5 (reduzir).
    """
    n = int(num)
    if n == 4:
        return 1.12
    if n == 5:
        return 1.0 / 1.12
    d = int(delta)
    if abs(d) > 10000:
        d = (d >> 16) & 0xFFFF
        if d >= 0x8000:
            d -= 0x10000
    if d > 0:
        return 1.12
    if d < 0:
        return 1.0 / 1.12
    return 1.0


def _ruido_engobo(pontos: np.ndarray) -> np.ndarray:
    """Variação suave de queima/engobo (UV cilíndrico + ruído senoidal)."""
    x, y, z = pontos[:, 0], pontos[:, 1], pontos[:, 2]
    theta = np.arctan2(y, x)
    rho = np.hypot(x, y)
    n = (
        0.50 * np.sin(3.0 * theta + 0.035 * z)
        + 0.28 * np.sin(8.0 * theta - 0.055 * z + 0.035 * rho)
        + 0.22 * np.sin(0.09 * z + 1.7 * theta)
    )
    t = 0.5 + 0.5 * np.tanh(1.35 * n)
    argila = np.array([0.46, 0.26, 0.15])
    engobo = np.array([0.84, 0.60, 0.40])
    rgb = argila[None, :] * (1.0 - t[:, None]) + engobo[None, :] * t[:, None]
    return np.clip(rgb, 0.0, 1.0)


def _uv_cilindrico(pontos: np.ndarray) -> np.ndarray:
    x, y, z = pontos[:, 0], pontos[:, 1], pontos[:, 2]
    u = (np.arctan2(y, x) + np.pi) / (2.0 * np.pi)
    zmin, zmax = float(z.min()), float(z.max())
    v = (z - zmin) / max(zmax - zmin, 1e-9)
    return np.column_stack([u, v])


def _extrair_superficie(grid: Any):
    """Superfície da malha estruturada.

    PyVista 0.45+ aceita ``algorithm=None`` (sem suavizar carenas). O 0.44
    embarcado no exe Windows não tem esse argumento.
    """
    try:
        return grid.extract_surface(algorithm=None)
    except TypeError:
        return grid.extract_surface()


def _revolucao_polilinha(
    pv: Any,
    r: np.ndarray,
    z: np.ndarray,
    *,
    sy_scale: float,
    planta: str = "Circular",
):
    """Revolve um meridiano (r, z) em torno do eixo Z, sem interpolar r(Z).

    O perfil oco tem dois raios na mesma altura (parede externa e interna);
    tratar como função r(Z) taparia a boca.
    """
    r = np.asarray(r, dtype=float).ravel()
    z = np.asarray(z, dtype=float).ravel()
    if r.size < 2:
        return None
    theta = np.linspace(0.0, 2.0 * np.pi, N_THETA)
    th, idx = np.meshgrid(theta, np.arange(r.size), indexing="xy")
    rr = r[idx]
    zz = z[idx]
    x, y = _xy_secao(rr, th, sy_scale, planta)
    grid = pv.StructuredGrid(x, y, zz)
    peca = _extrair_superficie(grid).triangulate()
    peca = peca.clean()
    peca = _orientar_normais_para_fora(peca)
    return peca


def _espessura_efetiva(espessura: float) -> float:
    """Espessura da parede em centímetro; 0,2 cm se o campo estiver vazio."""
    e = float(espessura or 0.0)
    if e < 0.002:
        return ESPESSURA_PADRAO_MM
    return e


def _meridiano_vaso_oco(
    z_denso: np.ndarray,
    r_ext: np.ndarray,
    r_int: np.ndarray,
    z_piso: float,
    *,
    fundo_plano: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Polilinha da argila: fundo externo → parede → lábio → interior → fundo interno.

    Com fundo_plano=False (diâmetro da base 0 cm em arco), o interior segue o
    perfil até o eixo — sem disco plano a meia altura (sombra de base falsa).
    """
    z_denso = np.asarray(z_denso, dtype=float)
    r_ext = np.asarray(r_ext, dtype=float)
    r_int = np.asarray(r_int, dtype=float)
    z0 = float(z_denso[0])
    zH = float(z_denso[-1])
    n_rad = N_RAD_FUNDO

    if not fundo_plano:
        r_labio = np.linspace(float(r_ext[-1]), float(r_int[-1]), 8)
        z_labio = np.full(r_labio.size, zH)
        r_parede_in = r_int[-2::-1]
        z_parede_in = z_denso[-2::-1]
        r_fecho = np.array([0.0])
        z_fecho = np.array([float(z_denso[0])])
        if float(r_ext[0]) < 1e-4:
            r = np.concatenate([r_ext, r_labio[1:], r_parede_in, r_fecho])
            z = np.concatenate([z_denso, z_labio[1:], z_parede_in, z_fecho])
        else:
            r_fundo_ext = np.linspace(0.0, float(r_ext[0]), n_rad, endpoint=False)
            z_fundo_ext = np.full(r_fundo_ext.size, z0)
            r = np.concatenate(
                [r_fundo_ext, r_ext, r_labio[1:], r_parede_in, r_fecho]
            )
            z = np.concatenate(
                [z_fundo_ext, z_denso, z_labio[1:], z_parede_in, z_fecho]
            )
        return r, z

    dentro = z_denso >= (float(z_piso) - 1e-9)
    if int(np.count_nonzero(dentro)) < 2:
        dentro = np.ones(z_denso.size, dtype=bool)
        z_piso = z0
    r_in = r_int[dentro]
    z_in = z_denso[dentro]
    r_fundo_ext = np.linspace(0.0, float(r_ext[0]), n_rad, endpoint=False)
    z_fundo_ext = np.full(r_fundo_ext.size, z0)
    r_labio = np.linspace(float(r_ext[-1]), float(r_in[-1]), 8)
    z_labio = np.full(r_labio.size, zH)
    r_parede_in = r_in[-2:0:-1]
    z_parede_in = z_in[-2:0:-1]
    r_fundo_in = np.linspace(float(r_in[0]), 0.0, n_rad)
    z_fundo_in = np.full(r_fundo_in.size, float(z_piso))
    r = np.concatenate([r_fundo_ext, r_ext, r_labio[1:], r_parede_in, r_fundo_in])
    z = np.concatenate([z_fundo_ext, z_denso, z_labio[1:], z_parede_in, z_fundo_in])
    return r, z


def _raios_casca_oca(
    r_meridiano: np.ndarray,
    espessura: float,
    *,
    fecha_no_eixo: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Parede externa e interna; interior estritamente menor que o exterior."""
    r_ext = np.maximum(np.asarray(r_meridiano, dtype=float), 1e-6)
    esp = max(float(espessura), 0.0)
    if fecha_no_eixo:
        r_int = np.maximum(r_ext - esp, 1e-6)
        estreito = r_ext < (esp + 1e-9)
        r_int = np.where(estreito, np.maximum(0.40 * r_ext, 1e-6), r_int)
        r_int = np.minimum(r_int, r_ext - 1e-6)
        r_int = np.maximum(r_int, 1e-6)
        r_ext = np.maximum(r_ext, r_int + 1e-6)
        return r_ext, r_int
    r_ext = np.maximum(r_ext, RAIO_INTERNO_MIN_MM)
    folga = np.maximum(r_ext - RAIO_INTERNO_MIN_MM, 0.0)
    r_int = np.maximum(r_ext - np.minimum(esp, folga), RAIO_INTERNO_MIN_MM)
    coincidem = r_int >= (r_ext - 1e-9)
    if np.any(coincidem):
        r_int = np.where(
            coincidem,
            np.maximum(0.5 * r_ext, 0.5 * RAIO_INTERNO_MIN_MM),
            r_int,
        )
        r_int = np.minimum(r_int, r_ext - 1e-6)
        r_int = np.maximum(r_int, 1e-6)
    return r_ext, r_int


def _orientar_normais_para_fora(peca):
    """Normais consistentes, apontando para fora da argila (evita inversão na base)."""
    if peca is None:
        return peca
    try:
        peca.compute_normals(
            inplace=True,
            point_normals=True,
            cell_normals=True,
            consistent=True,
            auto_orient_normals=True,
            flip_normals=False,
        )
    except TypeError:
        peca.compute_normals(
            inplace=True,
            point_normals=True,
            cell_normals=True,
            auto_orient_normals=True,
        )
    pts = np.asarray(peca.points, dtype=float)
    if "Normals" not in peca.point_data or pts.size == 0:
        return peca
    nrm = np.asarray(peca.point_data["Normals"], dtype=float)
    xy = pts[:, :2]
    rho = np.linalg.norm(xy, axis=1)
    if rho.size == 0:
        return peca
    limiar = float(np.quantile(rho, 0.75))
    mask = rho >= limiar
    if int(np.count_nonzero(mask)) < 8:
        mask = rho > 1e-6
    radial = xy / np.maximum(rho[:, None], 1e-9)
    proj = np.sum(nrm[mask, :2] * radial[mask], axis=1)
    if proj.size and float(np.mean(proj)) < 0.0:
        try:
            peca.flip_normals()
        except Exception:
            peca.point_data["Normals"] = (-nrm).astype(np.float32)
            try:
                peca.compute_normals(
                    inplace=True,
                    point_normals=True,
                    cell_normals=True,
                    auto_orient_normals=True,
                    flip_normals=True,
                )
            except TypeError:
                pass
    if "Normals" in peca.point_data:
        peca.point_data["Normals"] = np.asarray(
            peca.point_data["Normals"], dtype=np.float32
        )
    return peca


def peca_por_torno(
    pv: Any,
    pts: np.ndarray,
    sy_scale: float = 1.0,
    espessura: float = 0.0,
    planta: str = "Circular",
):
    """Vaso oco: boca aberta, parede com espessura. Preserva quebras do perfil."""
    if len(pts) < 3:
        return None
    z_w, r_w = _extrair_parede(pts)
    if z_w.size < 2:
        return None
    esp = _espessura_efetiva(espessura)
    z_denso = _z_com_estacoes(z_w, N_Z)
    r_med = np.interp(z_denso, z_w, r_w)
    fecha_no_eixo = float(r_med[0]) < 0.08
    r_ext, r_int = _raios_casca_oca(
        r_med, esp, fecha_no_eixo=fecha_no_eixo
    )
    z0 = float(z_denso[0])
    h = max(float(z_denso[-1]) - z0, 1e-6)
    z_piso = z0 if fecha_no_eixo else z0 + min(esp, 0.35 * h)
    r_m, z_m = _meridiano_vaso_oco(
        z_denso, r_ext, r_int, z_piso, fundo_plano=not fecha_no_eixo
    )
    peca = _revolucao_polilinha(pv, r_m, z_m, sy_scale=sy_scale, planta=planta)
    if peca is None:
        return None
    peca = peca.clean()
    peca = _orientar_normais_para_fora(peca)
    pontos = np.asarray(peca.points)
    peca["RGB"] = (np.clip(_ruido_engobo(pontos), 0.0, 1.0) * 255.0).astype(np.uint8)
    peca.active_texture_coordinates = _uv_cilindrico(pontos).astype(np.float32)
    if "Normals" in peca.point_data:
        peca.point_data["Normals"] = np.asarray(
            peca.point_data["Normals"], dtype=np.float32
        )
    return peca


def _face_estudio(pv: Any, rgb: tuple[float, float, float], n: int = 64):
    arr = np.empty((n, n, 3), dtype=np.uint8)
    arr[:] = np.clip(np.array(rgb, dtype=float) * 255.0, 0, 255).astype(np.uint8)
    return pv.Texture(arr).to_image()


def _cubemap_estudio(pv: Any):
    """Ambiente de estúdio para IBL (necessário ao PBR no VTK)."""
    return pv.Texture(
        [
            _face_estudio(pv, (0.42, 0.40, 0.36)),
            _face_estudio(pv, (0.28, 0.30, 0.34)),
            _face_estudio(pv, (0.50, 0.49, 0.46)),
            _face_estudio(pv, (0.16, 0.15, 0.14)),
            _face_estudio(pv, (0.34, 0.33, 0.32)),
            _face_estudio(pv, (0.34, 0.33, 0.32)),
        ]
    )


def _iluminacao_estudio(plotter: Any, pv: Any, peca: Any) -> None:
    """Key + fill de estúdio, focados a meia altura da peça."""
    plotter.remove_all_lights()
    b = peca.bounds
    z_meio = 0.5 * (b[4] + b[5])
    key = pv.Light(
        position=(250.0, 250.0, 300.0),
        focal_point=(0.0, 0.0, z_meio),
        intensity=1.2,
    )
    fill = pv.Light(
        position=(-200.0, -150.0, 150.0),
        focal_point=(0.0, 0.0, z_meio),
        intensity=0.6,
        color="#ffcc99",
    )
    plotter.add_light(key)
    plotter.add_light(fill)
    if _gpu_leve():
        return
    try:
        env = _cubemap_estudio(pv)
        plotter.set_environment_texture(env, is_srgb=True, show_background=False)
    except (TypeError, ValueError, RuntimeError, AttributeError):
        pass


def _enquadrar_peca(
    plotter: Any, peca: Any, azim: float, elev: float, zoom: float = 1.0
) -> None:
    """Posiciona a câmera em órbita (azimute + elevação) sem cruzar os polos.

    Elevação perto de ±90° deixa a normal do plano de vista paralela ao
    view-up: o VTK reinicia o up e o giro horizontal (azimute) deixa de
    parecer funcionar. Mantemos |elev| ≤ 75° e não chamamos reset_camera
    a cada frame.
    """
    b = peca.bounds
    cx = 0.5 * (b[0] + b[1])
    cy = 0.5 * (b[2] + b[3])
    cz = 0.5 * (b[4] + b[5])
    diag = max(b[1] - b[0], b[3] - b[2], b[5] - b[4], 40.0)
    az = np.radians(float(azim))
    el = np.radians(float(np.clip(elev, -75.0, 75.0)))
    zf = float(np.clip(zoom, 0.25, 8.0))
    dist = 2.14 * diag / zf
    cam = plotter.camera
    cam.position = (
        cx + dist * np.cos(el) * np.sin(az),
        cy - dist * np.cos(el) * np.cos(az),
        cz + dist * np.sin(el),
    )
    cam.focal_point = (cx, cy, cz)
    cam.up = (0.0, 0.0, 1.0)
    try:
        cam.orthogonalize_view_up()
    except (TypeError, ValueError, AttributeError, RuntimeError):
        pass
    plotter.reset_camera_clipping_range()


def _pintar_peca(
    plotter: Any,
    pv: Any,
    pts: np.ndarray,
    z_cm: float,
    sy_scale: float,
    espessura: float = 0.0,
    planta: str = "Circular",
):
    peca = peca_por_torno(pv, pts, sy_scale, espessura=espessura, planta=planta)
    if peca is None:
        return None
    _iluminacao_estudio(plotter, pv, peca)
    if not _gpu_leve():
        try:
            plotter.enable_anti_aliasing("msaa", multi_samples=8)
        except Exception:
            pass
    comum = dict(
        color=COR_CERAMICA,
        smooth_shading=True,
        show_edges=False,
        lighting=True,
        pbr=True,
        roughness=0.35,
        metallic=0.02,
        specular=0.6,
        ambient=0.25,
        opacity=1.0,
        show_scalar_bar=False,
    )
    tentativas = [
        dict(**comum, edge_color=None),
        dict(**comum),
        dict(
            color=COR_CERAMICA,
            smooth_shading=True,
            show_edges=False,
            lighting=True,
            pbr=True,
            roughness=0.35,
            metallic=0.02,
            opacity=1.0,
        ),
    ]
    for kw in tentativas:
        try:
            plotter.add_mesh(peca, **kw)
            break
        except (TypeError, ValueError, RuntimeError):
            continue
    return peca


def _triangulos(peca) -> np.ndarray:
    if hasattr(peca, "regular_faces"):
        return np.asarray(peca.regular_faces, dtype=int)
    faces = np.asarray(peca.faces)
    return faces.reshape(-1, 4)[:, 1:]


def _gravar_obj_com_normais(peca, caminho: str) -> None:
    from pathlib import Path

    pts = np.asarray(peca.points, dtype=float)
    if "Normals" in peca.point_data:
        nrm = np.asarray(peca.point_data["Normals"], dtype=float)
    else:
        peca.compute_normals(inplace=True, point_normals=True, cell_normals=False)
        nrm = np.asarray(peca.point_data["Normals"], dtype=float)
    uv = peca.active_texture_coordinates
    uv = _uv_cilindrico(pts) if uv is None else np.asarray(uv, dtype=float)
    tri = _triangulos(peca)
    linhas = ["# reconstituição geométrica de cerâmicas — malha com normais por vértice"]
    for p in pts:
        linhas.append(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}")
    for n in nrm:
        linhas.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
    for t in uv:
        linhas.append(f"vt {float(t[0]):.6f} {float(t[1]):.6f}")
    linhas.append("o vaso")
    for a, b, c in tri + 1:
        linhas.append(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}")
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _exportar_malha(peca, caminho: str) -> None:
    dest = str(caminho).lower()
    if dest.endswith(".obj"):
        _gravar_obj_com_normais(peca, caminho)
        return
    if dest.endswith(".ply"):
        rgb = peca.point_data.get("RGB")
        if rgb is not None and np.asarray(rgb).dtype != np.uint8:
            peca.point_data["RGB"] = np.clip(np.asarray(rgb) * 255.0, 0, 255).astype(np.uint8)
    if "Normals" in peca.point_data:
        peca.point_data["Normals"] = np.asarray(peca.point_data["Normals"], dtype=np.float32)
    tcoord = peca.active_texture_coordinates
    if tcoord is not None:
        peca.active_texture_coordinates = np.asarray(tcoord, dtype=np.float32)
    peca.save(caminho)


def exportar_stl(
    caminho_arquivo: str,
    peca=None,
    *,
    pts: np.ndarray | None = None,
    sy_scale: float = 1.0,
    espessura: float = 0.0,
    planta: str = "Circular",
) -> bool:
    """Grava a malha em STL (PyVista ou exportador poligonal)."""
    dest = str(caminho_arquivo)
    if not dest.lower().endswith(".stl"):
        dest = dest + ".stl"
    if peca is not None:
        _exportar_malha(peca, dest)
        return True
    if pts is None:
        return False
    return gravar_malha_solido(
        dest, pts, sy_scale=sy_scale, espessura=espessura, planta=planta
    )


def exportar_obj(
    caminho_arquivo: str,
    peca=None,
    *,
    pts: np.ndarray | None = None,
    sy_scale: float = 1.0,
    espessura: float = 0.0,
    planta: str = "Circular",
) -> bool:
    """Grava a malha em OBJ (PyVista ou exportador poligonal)."""
    dest = str(caminho_arquivo)
    if not dest.lower().endswith(".obj"):
        dest = dest + ".obj"
    if peca is not None:
        _exportar_malha(peca, dest)
        return True
    if pts is None:
        return False
    return gravar_malha_solido(
        dest, pts, sy_scale=sy_scale, espessura=espessura, planta=planta
    )


def gravar_png_solido(
    caminho: str,
    pts: np.ndarray,
    z_cm: float,
    sy_scale: float = 1.0,
    tamanho: tuple[int, int] = (1100, 820),
    espessura: float = 0.0,
    planta: str = "Circular",
) -> None:
    pv = _importar_pyvista()
    if pv is not None:
        pl = pv.Plotter(off_screen=True, window_size=list(tamanho), lighting="none")
        pl.set_background(COR_FUNDO)
        peca = _pintar_peca(
            pl, pv, pts, z_cm, sy_scale, espessura=espessura, planta=planta
        )
        if peca is not None:
            _enquadrar_peca(pl, peca, 45.0, 20.0)
        pl.screenshot(caminho)
        pl.close()
        return
    from matplotlib.colors import LightSource
    from matplotlib.figure import Figure

    fig = Figure(figsize=(tamanho[0] / 100, tamanho[1] / 100), dpi=100, facecolor=COR_FUNDO)
    ax = fig.add_subplot(111, projection="3d")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    x, y, zz = superficie_numpy(pts, n_theta=180, sy_scale=sy_scale, planta=planta)
    ls = LightSource(azdeg=315, altdeg=45)
    ax.plot_surface(
        x, y, zz, color=COR_CERAMICA, shade=True, lightsource=ls,
        linewidth=0, antialiased=True, alpha=1.0, rstride=1, cstride=1,
    )
    ax.set_axis_off()
    ax.view_init(elev=20.0, azim=45.0)
    ax.set_facecolor(COR_FUNDO)
    fig.savefig(caminho, facecolor=COR_FUNDO)


def gravar_malha_solido(
    caminho: str,
    pts: np.ndarray,
    sy_scale: float = 1.0,
    espessura: float = 0.0,
    planta: str = "Circular",
) -> bool:
    pv = _importar_pyvista()
    if pv is not None:
        peca = peca_por_torno(pv, pts, sy_scale, espessura=espessura, planta=planta)
        if peca is None:
            return False
        _exportar_malha(peca, caminho)
        return True
    from pathlib import Path

    from ceraform.exportar import malha_obj, malha_stl

    malhas = [superficie_numpy(pts, n_theta=180, sy_scale=sy_scale, planta=planta)]
    dest = str(caminho).lower()
    p = Path(caminho)
    if dest.endswith(".obj"):
        malha_obj(p, malhas)
    else:
        malha_stl(p, malhas)
    return True


class VistaSolido(tk.Frame):
    """Peça cerâmica opaca gerada por revolução, com órbita e zoom."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=COR_FUNDO)
        self.pv = None
        self.plotter = None
        self.ativa = False
        self.azim = 45.0
        self.elev = 20.0
        self.zoom = 1.0
        self._xy: tuple[int, int] | None = None
        self._foto = None
        self._pts: np.ndarray | None = None
        self._sy = 1.0
        self._z_cm = 0.0
        self._espessura = 0.0
        self._planta = "Circular"
        self._peca = None
        self.rotulo = tk.Text(
            self,
            bg=COR_FUNDO,
            fg=COR_FUNDO,
            bd=0,
            highlightthickness=0,
            wrap=tk.NONE,
            cursor="fleur",
            takefocus=True,
            insertwidth=0,
            padx=0,
            pady=0,
            relief=tk.FLAT,
        )
        self.rotulo.pack(fill=tk.BOTH, expand=True)
        self.rotulo.bind("<ButtonPress-1>", self._pressionar)
        self.rotulo.bind("<B1-Motion>", self._arrastar)
        self.rotulo.bind("<Enter>", self._foco_roda)
        self.bind("<Enter>", self._foco_roda)
        for ev in (
            "<MouseWheel>",
            "<Button-4>",
            "<Button-5>",
            "<ButtonPress-4>",
            "<ButtonPress-5>",
        ):
            self.rotulo.bind(ev, self._roda)
            self.bind(ev, self._roda)
        self.rotulo.bind("<Configure>", self._ao_redimensionar)
        self.rotulo.bind("<Key>", self._tecla_zoom)
        self._job_resize: str | None = None
        self._job_zoom: str | None = None
        self._ids_scroll: list[tuple[tk.Misc, str, str]] = []
        self._evs_all: list[str] = []

    def _garantir_plotter(self) -> None:
        if self.plotter is not None:
            return
        _anotar_3d("1 importando PyVista")
        self.pv = _importar_pyvista()
        if self.pv is None:
            _anotar_3d("1b PyVista indisponível; 3D em Matplotlib")
            return
        try:
            self.pv.OFF_SCREEN = True
            try:
                self.pv.global_theme.anti_aliasing = None
            except Exception:
                pass
            if _gpu_leve():
                try:
                    from vtkmodules.vtkRenderingCore import vtkRenderWindow

                    vtkRenderWindow.SetGlobalMaximumNumberOfMultiSamples(0)
                except Exception:
                    pass
            _anotar_3d("2 criando janela off-screen do VTK")
            self.plotter = self.pv.Plotter(
                off_screen=True,
                window_size=(640, 480),
                lighting="none",
            )
            try:
                rw = getattr(self.plotter, "render_window", None) or getattr(
                    self.plotter, "ren_win", None
                )
                if rw is not None:
                    rw.SetMultiSamples(0)
            except Exception:
                pass
            self.plotter.set_background(COR_FUNDO)
            _anotar_3d("3 plotter pronto")
        except Exception as exc:
            _anotar_falha_pyvista(exc)
            self.plotter = None

    def fechar(self) -> None:
        """Encerra o plotter off-screen antes do coletor destruir o objeto."""
        self._desligar_scroll_janela()
        pl = self.plotter
        self.plotter = None
        self._peca = None
        if pl is None:
            return
        try:
            pl.close()
        except Exception:
            pass

    def destroy(self) -> None:
        self.fechar()
        super().destroy()

    def mostrar(
        self,
        pts: np.ndarray,
        z_cm: float,
        sy_scale: float = 1.0,
        espessura: float = 0.0,
        planta: str = "Circular",
    ) -> None:
        self._pts = np.asarray(pts, dtype=float)
        self._z_cm = float(z_cm)
        self._sy = float(sy_scale)
        self._espessura = float(espessura or 0.0)
        self._planta = planta or "Circular"
        try:
            self.update_idletasks()
        except tk.TclError:
            pass
        self._reconstruir()
        try:
            self.rotulo.focus_set()
        except tk.TclError:
            pass

    def salvar_png(self, caminho: str) -> None:
        if self.plotter is not None:
            self.plotter.screenshot(caminho)

    def salvar_malha(self, caminho: str) -> bool:
        if self.pv is None or self._pts is None:
            return False
        peca = self._peca
        if peca is None:
            peca = peca_por_torno(
                self.pv,
                self._pts,
                self._sy,
                espessura=self._espessura,
                planta=self._planta,
            )
        if peca is None:
            return False
        _exportar_malha(peca, caminho)
        return True

    def exportar_stl(self, caminho_arquivo: str) -> bool:
        dest = str(caminho_arquivo)
        if not dest.lower().endswith(".stl"):
            dest = dest + ".stl"
        return self.salvar_malha(dest)

    def exportar_obj(self, caminho_arquivo: str) -> bool:
        dest = str(caminho_arquivo)
        if not dest.lower().endswith(".obj"):
            dest = dest + ".obj"
        return self.salvar_malha(dest)

    def _reconstruir(self) -> None:
        if self._pts is None:
            return
        self._garantir_plotter()
        if self.plotter is not None and self.pv is not None:
            try:
                self._desenhar_pyvista()
                return
            except Exception as exc:
                _anotar_falha_pyvista(exc)
                try:
                    self.plotter.close()
                except Exception:
                    pass
                self.plotter = None
        _anotar_3d("3D em Matplotlib")
        self._desenhar_matplotlib()

    def _desenhar_pyvista(self) -> None:
        _anotar_3d("4 montando a malha PBR")
        self.plotter.clear()
        self._peca = _pintar_peca(
            self.plotter,
            self.pv,
            self._pts,
            self._z_cm,
            self._sy,
            espessura=self._espessura,
            planta=self._planta,
        )
        if self._peca is not None:
            _enquadrar_peca(self.plotter, self._peca, self.azim, self.elev, self.zoom)
        _anotar_3d("5 screenshot")
        self._blit()
        _anotar_3d("6 sólido na tela")

    def _blit(self) -> None:
        w = max(int(self.rotulo.winfo_width()), 400)
        h = max(int(self.rotulo.winfo_height()), 300)
        self.plotter.window_size = [w, h]
        img = self.plotter.screenshot(return_img=True)
        from PIL import Image, ImageTk

        im = Image.fromarray(img)
        if im.size != (w, h):
            im = im.resize((w, h), Image.Resampling.BILINEAR)
        self._foto = ImageTk.PhotoImage(im)
        self._mostrar_foto()

    def _mostrar_foto(self) -> None:
        try:
            self.rotulo.configure(state=tk.NORMAL)
            self.rotulo.delete("1.0", "end")
            self.rotulo.image_create("1.0", image=self._foto)
        except tk.TclError:
            pass

    def _desenhar_matplotlib(self) -> None:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.colors import LightSource
        from matplotlib.figure import Figure
        if self._pts is None:
            return
        w = max(int(self.rotulo.winfo_width()), 400)
        h = max(int(self.rotulo.winfo_height()), 300)
        fig = Figure(figsize=(w / 100, h / 100), dpi=100, facecolor=COR_FUNDO)
        ax = fig.add_subplot(111, projection="3d")
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        x, y, zz = superficie_numpy(
            self._pts, n_theta=180, sy_scale=self._sy, planta=self._planta
        )
        ls = LightSource(azdeg=315, altdeg=45)
        ax.plot_surface(
            x, y, zz, color=COR_CERAMICA, shade=True, lightsource=ls,
            linewidth=0, antialiased=True, alpha=1.0, rstride=1, cstride=1,
        )
        ax.set_axis_off()
        ax.view_init(elev=self.elev, azim=self.azim)
        zf = float(np.clip(self.zoom, 0.25, 8.0))
        xmin, xmax = float(np.min(x)), float(np.max(x))
        ymin, ymax = float(np.min(y)), float(np.max(y))
        zmin, zmax = float(np.min(zz)), float(np.max(zz))
        cx = 0.5 * (xmin + xmax)
        cy = 0.5 * (ymin + ymax)
        cz = 0.5 * (zmin + zmax)
        half = max(xmax - xmin, ymax - ymin, zmax - zmin, 1.0) * 0.55 / zf
        ax.set_xlim(cx - half, cx + half)
        ax.set_ylim(cy - half, cy + half)
        ax.set_zlim(cz - half, cz + half)
        try:
            ax.set_box_aspect((1, 1, 1))
        except Exception:
            pass
        ax.set_facecolor(COR_FUNDO)
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        from PIL import Image, ImageTk

        buf = np.asarray(canvas.buffer_rgba())
        self._foto = ImageTk.PhotoImage(Image.fromarray(buf))
        self._mostrar_foto()

    def _pressionar(self, evt: tk.Event) -> None:
        self._xy = (evt.x, evt.y)
        try:
            self.rotulo.focus_set()
        except tk.TclError:
            pass

    def _arrastar(self, evt: tk.Event) -> None:
        if self._xy is None:
            return
        dx = evt.x - self._xy[0]
        dy = evt.y - self._xy[1]
        self._xy = (evt.x, evt.y)
        # Horizontal → azimute (volta completa); vertical → elevação (sem polos).
        self.azim = (self.azim - dx * 0.55) % 360.0
        self.elev = float(np.clip(self.elev + dy * 0.40, -75.0, 75.0))
        if self._job_zoom is not None:
            self.after_cancel(self._job_zoom)
        self._job_zoom = self.after(16, self._atualizar_vista)

    def definir_ativa(self, ativa: bool) -> None:
        """Liga o scroll da janela só enquanto a tela 3D está na frente."""
        self.ativa = bool(ativa)
        if self.ativa:
            self._ligar_scroll_janela()
        else:
            self._desligar_scroll_janela()

    def _ligar_scroll_janela(self) -> None:
        self._desligar_scroll_janela()
        try:
            top = self.winfo_toplevel()
        except tk.TclError:
            return
        teclas = (
            "<KeyPress-plus>",
            "<KeyPress-equal>",
            "<KeyPress-minus>",
            "<KeyPress-KP_Add>",
            "<KeyPress-KP_Subtract>",
        )
        roda = (
            "<MouseWheel>",
            "<Button-4>",
            "<Button-5>",
            "<ButtonPress-4>",
            "<ButtonPress-5>",
        )
        for ev in teclas:
            ident = top.bind(ev, self._tecla_zoom, add="+")
            self._ids_scroll.append((top, ev, ident))
            top.bind_all(ev, self._tecla_zoom, add="+")
            self._evs_all.append(ev)
        # No Windows a roda chega no widget com foco, não no desenho.
        # Enquanto o 3D está na frente, o mesmo caminho das teclas +/−.
        for ev in roda:
            ident = top.bind(ev, self._roda, add="+")
            self._ids_scroll.append((top, ev, ident))
            top.bind_all(ev, self._roda, add="+")
            self._evs_all.append(ev)
        self._foco_roda()

    def _desligar_scroll_janela(self) -> None:
        for top, ev, ident in self._ids_scroll:
            try:
                top.unbind(ev, ident)
            except tk.TclError:
                pass
        self._ids_scroll = []
        for ev in self._evs_all:
            try:
                self.unbind_all(ev)
            except tk.TclError:
                pass
        self._evs_all = []

    def _foco_roda(self, _evt: tk.Event | None = None) -> None:
        try:
            self.rotulo.focus_set()
        except tk.TclError:
            pass

    def _tecla_zoom(self, evt: tk.Event):
        if not self.ativa:
            return
        k = str(getattr(evt, "keysym", "") or "")
        if k in ("plus", "equal", "KP_Add"):
            fator = 1.12
        elif k in ("minus", "KP_Subtract"):
            fator = 1.0 / 1.12
        else:
            return
        self.zoom = float(np.clip(self.zoom * fator, 0.25, 8.0))
        if self._job_zoom is not None:
            self.after_cancel(self._job_zoom)
        self._job_zoom = self.after(40, self._atualizar_vista)
        return "break"

    def aplicar_delta_roda(self, delta: int) -> None:
        """Zoom pela roda (mensagem nativa do Windows/Wine)."""
        if not self.ativa:
            return
        fator = _fator_zoom_roda(int(delta), 0)
        if fator == 1.0:
            return
        self.zoom = float(np.clip(self.zoom * fator, 0.25, 8.0))
        if self._job_zoom is not None:
            self.after_cancel(self._job_zoom)
        self._job_zoom = self.after(40, self._atualizar_vista)

    def _roda(self, evt: tk.Event):
        """Scroll do mouse ou gesto de pinça do touchpad (via eventos de roda)."""
        if not self.ativa:
            return
        fator = _fator_zoom_roda(
            int(getattr(evt, "delta", 0) or 0),
            int(getattr(evt, "num", 0) or 0),
        )
        if fator != 1.0:
            self.zoom = float(np.clip(self.zoom * fator, 0.25, 8.0))
            if self._job_zoom is not None:
                self.after_cancel(self._job_zoom)
            self._job_zoom = self.after(40, self._atualizar_vista)
        return "break"

    def _atualizar_vista(self) -> None:
        self._job_zoom = None
        if self.plotter is not None and self._peca is not None:
            _enquadrar_peca(
                self.plotter, self._peca, self.azim, self.elev, self.zoom
            )
            self._blit()
        else:
            self._desenhar_matplotlib()

    def _ao_redimensionar(self, _evt: tk.Event) -> None:
        if not self.ativa:
            return
        if self._job_resize is not None:
            self.after_cancel(self._job_resize)
        self._job_resize = self.after(200, self._reconstruir)

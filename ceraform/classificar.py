# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

from dataclasses import dataclass

from ceraform.constantes import FORMAS
from ceraform.perfil import perfil_raios, quebras_meridiano


@dataclass
class ResultadoForma:
    forma: str
    forma_secundaria: str = ""
    aproximacao: bool = False
    observacao: str = ""
    valido: bool = True


def _perto(a: float, b: float, rel: float = 0.12, abs_tol: float = 0.015) -> bool:
    escala = max(abs(a), abs(b), 1e-9)
    return abs(a - b) <= max(rel * escala, abs_tol)


def _normalizar_perfil(perfil: str) -> str:
    """Aceita os nomes da tela e os sinônimos do enunciado analítico."""
    chave = (perfil or "Convexo").strip().lower()
    mapa = {
        "convexo": "Convexo",
        "externa": "Convexo",
        "reto": "Reto",
        "retilineo": "Reto",
        "retilíneo": "Reto",
        "linear": "Reto",
        "concavo": "Côncavo",
        "côncavo": "Côncavo",
        "interna": "Côncavo",
        "composto": "Composto",
        "carenado simples": "Carenado Simples",
        "carenado duplo": "Carenado Duplo",
        "sigmoide": "Sigmoide",
    }
    return mapa.get(chave, perfil or "Convexo")


def razoes_adimensionais(
    *,
    H: float,
    Dmax: float,
    Db: float,
    D0: float,
    hmax: float,
) -> dict[str, float]:
    """Índices usados pela inferência: H/Dmax, hmax/H, Db/D0, Db/Dmax.

    D0 = 0 ou Db = 0 não geram divisão por zero: a razão ausente fica 0 ou
    um sentinela finito (não se usa infinito nas comparações seguintes).
    """
    eps = 1e-12
    h = float(H)
    dmax = float(Dmax)
    db = float(Db)
    d0 = float(D0)
    hm = float(hmax)
    h_sobre_dmax = h / dmax if abs(dmax) > eps else 0.0
    hmax_sobre_h = min(max(hm / h, 0.0), 1.0) if abs(h) > eps else 0.0
    if abs(d0) > eps:
        db_sobre_d0 = db / d0
    elif abs(db) > eps:
        db_sobre_d0 = 0.0
    else:
        db_sobre_d0 = 0.0
    db_sobre_dmax = db / dmax if abs(dmax) > eps else 0.0
    return {
        "H_sobre_Dmax": h_sobre_dmax,
        "hmax_sobre_H": hmax_sobre_h,
        "Db_sobre_D0": db_sobre_d0,
        "Db_sobre_Dmax": db_sobre_dmax,
    }


# Centros das faixas de i_H (H/Dmax) para o vizinho mais próximo.
_CENTRO_LENTICULAR = 0.32  # (0,22 + 0,42) / 2
_CENTRO_ELIPSOIDE_H = 0.50  # caso-teste da seção 18.1 (tigela)
_CENTRO_SUBGLOBULAR = 0.79  # (0,70 + 0,88) / 2
_CENTRO_GLOBULAR = 1.03  # (0,88 + 1,18) / 2
_CENTRO_ELIPSOIDE_V = 1.50  # caso-teste da seção 18.1


def _forma_por_ih_restante(i_h: float, r_bmax: float, r_0max: float) -> tuple[str, bool]:
    """Barriga a meio e boca ≉ base: o nome sai de i_H, sem classe lixeira.

    Faixa com nome no catálogo → esse nome. Boca ou base quase iguais ao
    bojo (razão ≥ 0,92) em globular/subglobular → aproximação. Fora das
    faixas → o centro mais próximo, sempre aproximação.
    """
    boca_ou_base_aberta = r_bmax >= 0.92 or r_0max >= 0.92
    if 0.22 <= i_h < 0.42:
        return "Lenticular", False
    if 0.88 <= i_h <= 1.18:
        return "Globular", boca_ou_base_aberta
    if 0.70 <= i_h < 0.88:
        return "Subglobular", boca_ou_base_aberta
    alvos = (
        ("Lenticular", _CENTRO_LENTICULAR),
        ("Elipsóide Horizontal", _CENTRO_ELIPSOIDE_H),
        ("Subglobular", _CENTRO_SUBGLOBULAR),
        ("Globular", _CENTRO_GLOBULAR),
        ("Elipsóide Vertical", _CENTRO_ELIPSOIDE_V),
    )
    forma = min(alvos, key=lambda par: abs(i_h - par[1]))[0]
    return forma, True


def _mais_proximo_reto(db: float, d0: float, dmax: float, i_m: float) -> tuple[str, bool]:
    """Parede reta que não casou cone/cilindro/tronco/bicone: vizinho por diâmetros."""
    escala = max(abs(dmax), 1e-9)
    dist = {
        "Cilíndrico": abs(db - dmax) / escala + abs(d0 - dmax) / escala,
        "Cônico": (abs(d0) / escala) + abs(db - dmax) / escala,
        "Tronco-Cônico": min(abs(db - dmax), abs(d0 - dmax)) / escala
        + (0.0 if not _perto(db, d0) else 0.5),
        "Bicônico (Cone Duplo)": (
            max(0.0, 1.12 - dmax / max(abs(db), 1e-9))
            + max(0.0, 1.12 - dmax / max(abs(d0), 1e-9))
            + abs(i_m - 0.5)
        ),
    }
    return min(dist, key=lambda nome: dist[nome]), True


def _medidas_validas(H: float, Dmax: float, Db: float, D0: float, hmax: float) -> bool:
    try:
        nums = (float(H), float(Dmax), float(Db), float(D0), float(hmax))
    except (TypeError, ValueError):
        return False
    if any(n < 0 for n in nums):
        return False
    if nums[0] <= 0 or nums[1] <= 0:
        return False
    if nums[4] > nums[0]:
        return False
    return True


def classificarForma(
    H: float,
    Dmax: float,
    Db: float,
    D0: float,
    hmax: float,
    perfil: str = "Convexo",
    *,
    perfil_trecho_base: str = "",
    perfil_trecho_borda: str = "",
    altura_juncao: float = 0.0,
    diametro_juncao: float = 0.0,
    altura_carena: float = 0.0,
    diametro_carena: float = 0.0,
    altura_carena2: float = 0.0,
    diametro_carena2: float = 0.0,
    dmeio: float = 0.0,
) -> ResultadoForma:
    """Forma geométrica a partir do meridiano e das razões adimensionais.

    A quebra de tangente (carena, θ ≥ 18°) decide antes das silhuetas lisas:
    pera, ovo e elipsóide exigem parede contínua. Parede reta (cone, cilindro,
    bicone) continua a ter nome próprio. A junta do perfil composto não conta
    como segunda carena. Não há classe lixeira: ou a faixa casa, ou o
    vizinho mais próximo vem com aproximacao=True.

    Entradas inválidas não levantam exceção: devolvem uma forma do catálogo
    com valido=False.
    """
    perfil_n = _normalizar_perfil(perfil)
    valido = _medidas_validas(H, Dmax, Db, D0, hmax)
    aproximacao = not valido
    observacao = "" if valido else "Medidas inválidas; forma mais próxima (aproximação)."

    try:
        h = float(H)
        dmax = float(Dmax)
        db = float(Db)
        d0 = float(D0)
        hm = float(hmax)
    except (TypeError, ValueError):
        return ResultadoForma(
            forma="Elipsóide Vertical",
            aproximacao=True,
            observacao=observacao or "Medidas inválidas; forma mais próxima (aproximação).",
            valido=False,
        )

    if h <= 0 or dmax <= 0:
        return ResultadoForma(
            forma="Elipsóide Vertical",
            aproximacao=True,
            observacao=observacao,
            valido=False,
        )

    r = razoes_adimensionais(H=h, Dmax=dmax, Db=db, D0=d0, hmax=hm)
    i_h = r["H_sobre_Dmax"]
    i_m = r["hmax_sobre_H"]
    r_bmax = r["Db_sobre_Dmax"]
    r_0max = d0 / dmax if dmax > 0 else 0.0
    simetrico = _perto(db, d0)
    base_n = _normalizar_perfil(perfil_trecho_base) if perfil_trecho_base else perfil_n
    borda_n = _normalizar_perfil(perfil_trecho_borda) if perfil_trecho_borda else perfil_n
    reto = perfil_n == "Reto" or (
        perfil_n == "Composto" and base_n == "Reto" and borda_n == "Reto"
    )
    barriga_meio = 0.42 <= i_m <= 0.58
    medidas_carena = {
        "h": h,
        "db": db,
        "dmax": dmax,
        "hmax": hm,
        "dbase": d0,
        "dmeio": float(dmeio or 0.0),
        "perfil": perfil_n,
        "perfil_base": perfil_trecho_base,
        "perfil_borda": perfil_trecho_borda,
        "altura_carena": float(altura_carena or 0.0),
        "diametro_carena": float(diametro_carena or 0.0),
        "altura_carena2": float(altura_carena2 or 0.0),
        "diametro_carena2": float(diametro_carena2 or 0.0),
        "altura_juncao": float(altura_juncao or 0.0),
        "diametro_juncao": float(diametro_juncao or 0.0),
    }

    if i_h < 0.28:
        forma = "Discoide"
    elif reto:
        ponta = d0 <= max(0.08 * max(db, dmax, 0.0), 0.015)
        if ponta and _perto(db, dmax):
            forma = "Cônico"
        elif _perto(db, dmax) and _perto(d0, dmax):
            forma = "Cilíndrico"
        else:
            dmax_na_borda = _perto(hm, h) or _perto(db, dmax)
            dmax_na_base = _perto(hm, 0.0) or _perto(d0, dmax)
            if dmax_na_borda and not ponta and not _perto(db, d0):
                forma = "Tronco-Cônico"
            elif dmax_na_base and not ponta and not _perto(db, d0):
                forma = "Tronco-Cônico"
            elif dmax > db * 1.12 and dmax > d0 * 1.12 and 0.38 <= i_m <= 0.62:
                forma = "Bicônico (Cone Duplo)"
            else:
                forma, so_aprox = _mais_proximo_reto(db, d0, dmax, i_m)
                if so_aprox:
                    aproximacao = True
                    observacao = observacao or "Forma mais próxima (aproximação)."
    else:
        primeira, segunda, n_quebras = _carenas_no_meridiano(medidas_carena)
        if segunda or perfil_n == "Carenado Duplo":
            forma = "Carenado Duplo"
        elif n_quebras > 0 or primeira or perfil_n == "Carenado Simples":
            forma = "Carenado"
        elif barriga_meio and simetrico:
            if 0.88 <= i_h <= 1.18:
                forma = "Esférico"
            elif i_h > 1.18:
                forma = "Elipsóide Vertical"
            else:
                forma = "Elipsóide Horizontal"
        elif i_m < 0.42:
            if i_m < 0.30 and r_bmax < 0.40:
                forma = "Piriforme"
            else:
                forma = "Ovoide"
        elif i_m > 0.58:
            forma = "Ovoide Invertido"
        else:
            forma, so_aprox = _forma_por_ih_restante(i_h, r_bmax, r_0max)
            if so_aprox:
                aproximacao = True
                observacao = observacao or "Forma mais próxima (aproximação)."

    return ResultadoForma(
        forma=forma,
        aproximacao=aproximacao,
        observacao=observacao,
        valido=valido,
    )


def _carenas_no_meridiano(valores: dict) -> tuple[bool, bool, int]:
    """Quebras no meridiano interpolado (θ ≥ 18°).

    A junta do perfil composto não conta como segunda carena. Qualquer quebra
    visível (incluindo a junta) conta para *haver* carena.
    """
    h = float(valores.get("h") or 0.0)
    hmax = float(valores.get("hmax") or 0.0)
    if h <= 0:
        return False, False, 0
    z, r = perfil_raios(
        h=h,
        db=float(valores.get("db") or 0.0),
        dmax=float(valores.get("dmax") or 0.0),
        hmax=hmax,
        dbase=float(valores.get("dbase") or 0.0),
        dmeio=float(valores.get("dmeio") or 0.0),
        perfil_geometrico=str(valores.get("perfil") or "Convexo"),
        perfil_trecho_base=str(valores.get("perfil_base") or ""),
        perfil_trecho_borda=str(valores.get("perfil_borda") or ""),
        altura_carena=float(valores.get("altura_carena") or 0.0),
        diametro_carena=float(valores.get("diametro_carena") or 0.0),
        altura_carena2=float(valores.get("altura_carena2") or 0.0),
        diametro_carena2=float(valores.get("diametro_carena2") or 0.0),
        altura_juncao=float(valores.get("altura_juncao") or 0.0),
        diametro_juncao=float(valores.get("diametro_juncao") or 0.0),
    )
    quebras = quebras_meridiano(z, r)
    # Quebra nos extremos (base/borda) é artefato de Hmax colado ao fim, não carena.
    margem = max(0.03 * h, 0.15)
    quebras = [(zi, ang) for zi, ang in quebras if margem < zi < h - margem]
    n_visiveis = len(quebras)
    if n_visiveis == 0:
        return False, False, 0
    tol = max(0.08 * h, 0.2)
    junta = float(valores.get("altura_juncao") or 0.0)
    sem_junta = [
        (zi, ang)
        for zi, ang in quebras
        if junta <= 0.0 or abs(zi - junta) > tol
    ]
    primeira = any(abs(zi - hmax) <= tol for zi, _ang in sem_junta)
    segunda = any(abs(zi - hmax) > tol for zi, _ang in sem_junta)
    return primeira, segunda, len(sem_junta)


def _carenas_distintas(valores: dict) -> tuple[bool, bool]:
    """Primeira quebra (junto do maior diâmetro) e segunda, sem a junta."""
    primeira, segunda, _n = _carenas_no_meridiano(valores)
    return primeira, segunda


def _score_par(valores: dict[str, float]) -> list[tuple[float, str]]:
    h = valores["h"]
    db = valores["db"]
    dmax = valores["dmax"]
    hmax = valores["hmax"]
    dbase = valores["dbase"]
    dmeio = valores["dmeio"]
    perfil = valores.get("perfil", "Convexo")
    perfil_base = valores.get("perfil_base", "") or perfil
    perfil_borda = valores.get("perfil_borda", "") or perfil
    contorno = valores.get("contorno", "Circular")
    n_amostras = int(valores.get("n_amostras", 0))

    if h <= 0 or dmax <= 0:
        return [(0.2, "Elipsóide Vertical")]

    ih = h / dmax
    im = min(max(hmax / h, 0.0), 1.0)
    rb = db / dmax
    scores: dict[str, float] = {nome: 0.0 for nome in FORMAS}

    if contorno == "Quadrangular":
        scores["Quadrangular"] += 8.0

    if dmeio > 0 and dmeio < min(db, dbase, dmax) * 0.92:
        scores["Hiperboloide"] += 6.0

    _, segunda, n_quebras = _carenas_no_meridiano(valores)
    if segunda:
        scores["Carenado Duplo"] += 7.2
    elif n_quebras > 0 or perfil in ("Carenado Simples", "Carenado Duplo") or (
        valores["altura_carena"] > 0 and valores["diametro_carena"] > 0
    ):
        scores["Carenado"] += 6.5

    if n_amostras >= 3:
        scores["Escalonado"] += 1.5

    if ih < 0.22:
        scores["Discoide"] += 6.0
    elif ih < 0.42:
        scores["Lenticular"] += 4.5 if perfil in ("Convexo", "Côncavo", "Sigmoide") else 3.0
        scores["Discoide"] += 2.0

    if _perto(h, dmax) and _perto(db, dmax) and _perto(dbase, dmax):
        scores["Esférico"] += 7.0

    reto = perfil == "Reto" or (
        perfil == "Composto" and perfil_base == "Reto" and perfil_borda == "Reto"
    )
    menor = min(db, dbase)
    maior = max(db, dbase)

    if reto:
        if menor <= max(0.08 * maior, 0.015) and maior > 0:
            scores["Cônico"] += 6.5
        if _perto(db, dmax) and _perto(dbase, dmax):
            scores["Cilíndrico"] += 6.5
        if _perto(dmax, maior) and not _perto(db, dbase):
            scores["Tronco-Cônico"] += 6.0
        if dmax > db * 1.12 and dmax > dbase * 1.12 and 0.38 <= im <= 0.62:
            scores["Bicônico (Cone Duplo)"] += 6.0

    if im < 0.36 and rb < 0.50:
        scores["Piriforme"] += 6.8
    if im < 0.42:
        scores["Ovoide"] += 3.2 if rb < 0.50 else 5.0
    if im > 0.58:
        scores["Ovoide Invertido"] += 5.2

    if 0.42 <= im <= 0.58:
        if ih > 1.18:
            scores["Elipsóide Vertical"] += 5.8
        elif ih < 0.88:
            scores["Elipsóide Horizontal"] += 5.8

    if db < dmax * 0.92 and dbase < dmax * 0.92:
        if 0.88 <= ih <= 1.18:
            scores["Globular"] += 5.5
            scores["Subglobular"] += 3.2
        elif 0.70 <= ih < 0.88:
            scores["Subglobular"] += 5.0
            scores["Elipsóide Horizontal"] += 3.0

    if perfil == "Composto":
        if perfil_base == "Convexo" and perfil_borda == "Reto":
            scores["Globular"] += 2.0
            scores["Cilíndrico"] += 2.5
        if perfil_base == "Reto" and perfil_borda == "Convexo":
            scores["Cilíndrico"] += 2.0

    ranked = sorted(((s, nome) for nome, s in scores.items()), reverse=True)
    return ranked


def classificar(
    *,
    h: float,
    db: float,
    dmax: float,
    hmax: float,
    dbase: float,
    dmeio: float = 0.0,
    largura: float = 0.0,
    profundidade: float = 0.0,
    geratriz: str = "",
    perfil_geometrico: str = "Convexo",
    perfil_trecho_base: str = "",
    perfil_trecho_borda: str = "",
    contorno_planta: str = "Circular",
    altura_carena: float = 0.0,
    diametro_carena: float = 0.0,
    altura_carena2: float = 0.0,
    diametro_carena2: float = 0.0,
    altura_juncao: float = 0.0,
    diametro_juncao: float = 0.0,
    n_amostras: int = 0,
) -> ResultadoForma:
    """Heurística da 1ª versão — a pesquisadora confirma ou corrige."""
    perfil = perfil_geometrico or "Convexo"
    if geratriz and perfil == "Convexo":
        mapa = {"externa": "Convexo", "linear": "Reto", "interna": "Côncavo"}
        perfil = mapa.get(geratriz.lower(), perfil)

    contorno = contorno_planta or "Circular"

    ranked = _score_par(
        {
            "h": h,
            "db": db,
            "dmax": dmax,
            "hmax": hmax,
            "dbase": dbase,
            "dmeio": dmeio,
            "perfil": perfil,
            "perfil_base": perfil_trecho_base,
            "perfil_borda": perfil_trecho_borda,
            "contorno": contorno,
            "altura_carena": altura_carena,
            "diametro_carena": diametro_carena,
            "altura_carena2": altura_carena2,
            "diametro_carena2": diametro_carena2,
            "altura_juncao": altura_juncao,
            "diametro_juncao": diametro_juncao,
            "n_amostras": n_amostras,
        }
    )
    sugerida = classificarForma(
        H=h,
        Dmax=dmax,
        Db=db,
        D0=dbase,
        hmax=hmax,
        perfil=perfil,
        perfil_trecho_base=perfil_trecho_base,
        perfil_trecho_borda=perfil_trecho_borda,
        altura_juncao=altura_juncao,
        diametro_juncao=diametro_juncao,
        altura_carena=altura_carena,
        diametro_carena=diametro_carena,
        altura_carena2=altura_carena2,
        diametro_carena2=diametro_carena2,
        dmeio=dmeio,
    )
    melhor = sugerida.forma
    if contorno == "Quadrangular":
        melhor = "Quadrangular"
    melhor_s = next((s for s, nome in ranked if nome == melhor), ranked[0][0] if ranked else 0.0)
    segundo_s, segundo = 0.0, ""
    for s, nome in ranked:
        if nome != melhor:
            segundo_s, segundo = s, nome
            break
    aproximacao = sugerida.aproximacao or melhor_s < 4.5 or not sugerida.valido
    secundaria = ""
    if segundo and segundo_s >= melhor_s * 0.72 and segundo_s >= 3.5:
        secundaria = segundo
    observacao = sugerida.observacao
    if aproximacao and not observacao:
        observacao = "Forma mais próxima (aproximação)."
    return ResultadoForma(
        forma=melhor,
        forma_secundaria=secundaria,
        aproximacao=aproximacao,
        observacao=observacao,
        valido=sugerida.valido,
    )

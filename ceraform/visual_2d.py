# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

from typing import Any

import numpy as np
from matplotlib.patches import Rectangle

from ceraform.perfil import (
    centro_massa_casca,
    diametros_fracao,
    meridiano_com_base,
    raio_curvatura_base,
)
from ceraform.volume import rotulo_tamanho

# Folha A4 em centímetro (largura × altura).
_FOLHA_RETRATO = (21.0, 29.7)
_FOLHA_PAISAGEM = (29.7, 21.0)
_MARGEM_FOLHA = 1.0
# Campo do desenho no PDF (cm a partir das bordas da folha).
_MARGEM_DESENHO_PDF = 2.5  # esquerda, direita e inferior
_FOLGA_ABAIXO_CABECALHO_PDF = 1.0  # entre o fim do cabeçalho e o desenho
# Barra de escala: 0,5 cm acima da borda inferior do milimetrado.
_Y_BARRA_ESCALA_PDF = _MARGEM_FOLHA + 0.5
_ESCALA_MAX_AMPLIACAO = 5.0
_MARGEM_FIGURA = dict(left=0.0, right=1.0, top=1.0, bottom=0.0)
_MARGEM_FIGURA_TELA = dict(left=0.03, right=0.97, top=0.86, bottom=0.06)
_ALTURA_CABECALHO_PDF = 1.65
_FATOR_AREA_UTIL = 0.98
_MARGEM_COTA_X = 2.4
_MARGEM_COTA_Y = 1.8
_COR_FUNDO_JANELA = "#e8e4df"
_COR_FUNDO_TELA = "#ffffff"
_COR_COTA = "#111111"

_LW_PERFIL = 1.35
_LW_COTA = 0.95
_LW_EIXO = 0.75
_LW_BORDA_FOLHA = 1.0
_LW_MARGEM_UTIL = 0.65
_LW_GRADE_1CM = 0.75
_LW_GRADE_5MM = 0.45
_LW_GRADE_1MM = 0.25
_LW_PUB_PERFIL = 1.55
_LW_PUB_TRACEJADO = 1.05
_COR_PUBLICACAO = "#111111"
# Encurtamento da elipse da borda (vista ligeiramente de cima).
# Valores altos fazem o arco frontal cruzar o corpo em tigelas abertas.
_FATOR_ELIPSE_BORDA = 0.20
# Barra de escala na tela Publicação: tamanho visual fixo (fração da figura).
_L_FIG_BARRA_PUB = 0.18
_N_SEG_BARRA_PUB = 4
_H_FIG_BARRA_PUB = 0.012
_TICK_FIG_BARRA_PUB = 0.008
_FS_COTA = 8.5
_FS_ESCALA = 10.0
_FS_TITULO = 11.0
_FOLHA_DPI_TELA = 150


def ficha_objeto(
    dados: dict[str, Any], z_cm: float, nota_eq: str, titulo: str
) -> dict[str, Any]:
    """Campos da ficha do corte 2D, em pares (rótulo, valor) para grade de três colunas."""
    vol = float(dados.get("volume_l") or 0.0)
    celulas: list[tuple[str, str]] = [
        ("Nome do sítio", str(dados.get("sitio") or "—")),
        ("Número do desenho", str(dados.get("numero") or "—")),
        ("Forma geométrica", titulo or "—"),
        (
            "Volume do objeto",
            f"{vol:.3f} L ({rotulo_tamanho(vol)})",
        ),
        (
            "Capacidade efetiva a 90 % da altura total",
            f"{float(dados.get('volume_90_l') or 0):.3f} L"
            if dados.get("volume_90_l") is not None
            else "—",
        ),
        (
            "Capacidade efetiva a 85 % da altura total",
            f"{float(dados.get('volume_85_l') or 0):.3f} L"
            if dados.get("volume_85_l") is not None
            else "—",
        ),
        ("Tipo de base", str(dados.get("tipo_base") or "Reta")),
        (
            "Ponto de equilíbrio",
            f"{z_cm:.2f} cm acima do apoio",
        ),
        ("Altura total", f"{float(dados.get('h') or 0):.1f} cm"),
        ("Diâmetro da borda", f"{float(dados.get('db') or 0):.1f} cm"),
        ("Diâmetro da base", f"{float(dados.get('dbase') or 0):.1f} cm"),
        ("Maior diâmetro da peça", f"{float(dados.get('dmax') or 0):.1f} cm"),
        (
            "Altura da base até o maior diâmetro",
            f"{float(dados.get('hmax') or 0):.1f} cm",
        ),
    ]
    if dados.get("dmeio"):
        celulas.append(("Diâmetro da cintura", f"{dados['dmeio']:.1f} cm"))
    d_14 = dados.get("d_14")
    d_12 = dados.get("d_12")
    d_34 = dados.get("d_34")
    if d_14 is None and d_12 is None and d_34 is None:
        d_14, d_12, d_34 = diametros_fracao(
            str(dados.get("amostras") or ""), float(dados.get("h") or 0)
        )
    if d_14:
        celulas.append(("1/4 da altura", f"{float(d_14):.1f} cm"))
    if d_12:
        celulas.append(("1/2 da altura", f"{float(d_12):.1f} cm"))
    if d_34:
        celulas.append(("3/4 da altura", f"{float(d_34):.1f} cm"))
    if dados.get("espessura_parede"):
        celulas.append(("Espessura da parede", f"{dados['espessura_parede']:.1f} cm"))
    if dados.get("diametro_carena") and dados.get("altura_carena"):
        celulas.append(
            (
                "Carena",
                f"altura {dados['altura_carena']:.1f} cm, "
                f"diâmetro {dados['diametro_carena']:.1f} cm",
            )
        )
    if dados.get("diametro_carena2") and dados.get("altura_carena2"):
        celulas.append(
            (
                "Segunda quebra",
                f"altura {dados['altura_carena2']:.1f} cm, "
                f"diâmetro {dados['diametro_carena2']:.1f} cm",
            )
        )
    if dados.get("diametro_juncao") and dados.get("altura_juncao"):
        celulas.append(
            (
                "Junção bojo–pescoço",
                f"altura {dados['altura_juncao']:.1f} cm, "
                f"diâmetro {dados['diametro_juncao']:.1f} cm",
            )
        )
    return {"celulas": celulas, "nota": nota_eq}


def texto_dados(dados: dict[str, Any], z_cm: float, nota_eq: str, titulo: str) -> str:
    ficha = ficha_objeto(dados, z_cm, nota_eq, titulo)
    linhas = [f"{rotulo}: {valor}" for rotulo, valor in ficha["celulas"]]
    if ficha["nota"]:
        linhas.append(str(ficha["nota"]))
    return "\n".join(linhas)


def _nota_equilibrio(tipo_base: str, raio_base: float, z_cm: float, *, dbase: float = -1.0) -> str:
    tipo = (tipo_base or "Reta").strip()
    diam_base = float(dbase) if dbase >= 0.0 else 2.0 * float(raio_base)
    if tipo == "Reta":
        return "Apoio plano no anel da base; centro de massa no eixo."
    if tipo == "Côncava":
        return "Apoio no anel da base (fundo reentrante); centro de massa no eixo."
    if diam_base < 0.1:
        return (
            "Fundo convexo (diâmetro da base = 0 cm); "
            "centro de massa no eixo."
        )
    rho = raio_curvatura_base(tipo, raio_base)
    if rho is None:
        return "Base convexa; centro de massa no eixo."
    if z_cm < rho:
        return (
            f"Base convexa: centro de massa abaixo do centro de curvatura "
            f"({rho:.2f} cm) — tendência a recuperar a vertical."
        )
    return (
        f"Base convexa: centro de massa acima do centro de curvatura "
        f"({rho:.2f} cm) — equilíbrio mais instável ao inclinar."
    )


def resumo_peca(
    z: np.ndarray,
    r: np.ndarray,
    dados: dict[str, Any],
    titulo: str,
) -> tuple[float, dict[str, Any]]:
    tipo_base = dados.get("tipo_base") or "Reta"
    z_w, r_w, r_b, z_b = meridiano_com_base(z, r, tipo_base)
    z_cm, _ = centro_massa_casca(z_w, r_w, r_b, z_b, tipo_base=tipo_base)
    nota = _nota_equilibrio(
        tipo_base,
        float(r_w[0]),
        z_cm,
        dbase=float(dados.get("dbase") or 0.0),
    )
    return z_cm, ficha_objeto(dados, z_cm, nota, titulo)


def _rotulo_cota(texto: str, largura: int = 28) -> str:
    """Nome por extenso numa ou duas linhas; valor com vírgula decimal na última."""
    t = (texto or "").strip()
    if not t.endswith(" cm"):
        return t
    corpo = t[: -len(" cm")].rstrip()
    i = corpo.rfind(" ")
    if i <= 0:
        return t.replace(".", ",")
    nome = corpo[:i].strip()
    valor = corpo[i + 1 :].replace(".", ",") + " cm"
    # Quebra fixa do rótulo longo (cabe no campo do PDF).
    if nome == "altura da base até o maior diâmetro":
        return f"altura da base até\no maior diâmetro\n{valor}"
    largura = max(int(largura), 8)
    if len(nome) <= largura:
        return f"{nome}\n{valor}"
    corte = nome[:largura].rfind(" ")
    if corte < max(largura // 2, 8):
        corte = largura
    return f"{nome[:corte].strip()}\n{nome[corte:].strip()}\n{valor}"


def _x_trilho(r_max: float, i: int, *, compacto: bool = False) -> float:
    """Posição do trilho i à direita do eixo, em centímetro real."""
    if compacto:
        # PDF: trilhos junto à peça para a escala poder preencher a folha.
        return float(r_max) + 1.35 + float(i) * 1.05
    return float(r_max) * (1.15 + int(i) * 0.18)


def _fator_escala_pdf(fator_bruto: float) -> tuple[float, int, int]:
    """Maior escala discreta que ainda cabe na folha.

    Retorna ``(fator, a, b)`` com razão gráfica **a:b** (papel:objeto):
    ampliação 5:1 … 2:1, razões intermediárias (3:2, 4:5, …), natural 1:1,
    redução 1:2 … 1:100. ``fator`` = cm no papel / cm do objeto (= a/b).
    """
    bruto = max(float(fator_bruto), 1e-9)
    # Ordenados do maior para o menor fator.
    candidatos: list[tuple[float, int, int]] = [
        (5.0, 5, 1),
        (4.0, 4, 1),
        (3.0, 3, 1),
        (2.5, 5, 2),
        (2.0, 2, 1),
        (5.0 / 3.0, 5, 3),
        (1.5, 3, 2),
        (4.0 / 3.0, 4, 3),
        (1.25, 5, 4),
        (1.0, 1, 1),
        (5.0 / 6.0, 5, 6),
        (0.8, 4, 5),
        (0.75, 3, 4),
        (2.0 / 3.0, 2, 3),
        (0.6, 3, 5),
    ]
    for n in (2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100):
        candidatos.append((1.0 / float(n), 1, n))
    for fator, a, b in candidatos:
        if fator <= bruto + 1e-12:
            return fator, int(a), int(b)
    return candidatos[-1]


def _parametros_barra_escala_pdf(fator: float) -> tuple[float, int, float]:
    """Barra com comprimento exato em cm do papel e rótulos em cm do objeto.

    Retorna (comprimento_real_cm, n_segmentos, comprimento_papel_cm).
    Prefere totais e passos redondos no objeto (1 cm, 2 cm, …).
    """
    fator = max(float(fator), 1e-9)
    opcoes: list[tuple[float, float, int, float]] = []
    for L_real in (1.0, 2.0, 2.5, 4.0, 5.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0):
        L_papel = L_real * fator
        if L_papel < 2.0 or L_papel > 6.5:
            continue
        for n_seg in (5, 4, 2):
            passo_real = L_real / float(n_seg)
            passo_papel = L_papel / float(n_seg)
            # Preferir passos inteiros (ou meios) no objeto e barra ~4–5 cm.
            nota = abs(L_papel - 4.5)
            if abs(passo_real - round(passo_real)) < 1e-6:
                nota -= 0.6
            elif abs(passo_real * 2.0 - round(passo_real * 2.0)) < 1e-6:
                nota -= 0.25
            else:
                nota += 0.8
            if abs(passo_papel - 1.0) < 0.2 or abs(passo_papel - 0.5) < 0.15:
                nota -= 0.2
            opcoes.append((nota, float(L_real), int(n_seg), float(L_papel)))
    if not opcoes:
        # Reserva: 4 cm no papel, 4 segmentos.
        return 4.0 / fator, 4, 4.0
    opcoes.sort()
    _, L_real, n_seg, L_papel = opcoes[0]
    return float(L_real), int(n_seg), float(L_papel)


def _barra_escala_igual_ao_pdf_tecnico(
    z,
    r,
    dados: dict[str, Any],
    *,
    tipo_base: str = "Reta",
    espessura: float = 0.0,
) -> tuple[float, int, float]:
    """Mesmos (L_real, n_segmentos, fator) que o PDF do corte técnico usaria nesta peça."""
    z_w, r_w, r_b, z_b = meridiano_com_base(z, r, tipo_base)
    z0 = float(min(z_w.min(), z_b.min()))
    z1 = float(max(z_w.max(), z_b.max()))
    h = float(dados.get("h") or 0.0)
    db = float(dados.get("db") or 0.0)
    dmax = float(dados.get("dmax") or 0.0)
    hmax = float(dados.get("hmax") or 0.0)
    dbase = float(dados.get("dbase") or 0.0)
    offset = float(z_b[-1])
    r_max = float(max(np.max(r_w), db / 2.0, dmax / 2.0, dbase / 2.0, 1.0))
    if espessura > 0:
        r_max += float(espessura)
    h_c2 = float(dados.get("altura_carena2") or 0.0)
    d_c2 = float(dados.get("diametro_carena2") or 0.0)
    tem_c2 = h_c2 > 0.0 and d_c2 > 0.0 and abs(h_c2 - hmax) > 0.2
    mesma_borda_dmax = round(db, 1) == round(dmax, 1)
    base_nula = round(dbase, 1) == 0.0
    mesma_altura_dmax = round(h, 1) == round(hmax, 1)
    # Se altura total == hmax, só uma cota de altura; senão hmax + total (+ carena).
    if mesma_altura_dmax:
        n_trilhos = 1 + (1 if tem_c2 else 0)
    else:
        n_trilhos = 2 + (1 if tem_c2 else 0)
    cont_w, cont_h, _pad_sup, _pad_inf = _tamanho_ajuste_pdf(
        r_max=r_max,
        altura_peca=max(float(z1 - z0), h, 1.0),
        n_trilhos_altura=n_trilhos,
        com_cota_base=not base_nula,
        com_cota_dmax=not mesma_borda_dmax,
    )
    _folha, fator, _a, _b = _folha_e_escala_para_conteudo(cont_w, cont_h)
    L_real, n_seg, _L_papel = _parametros_barra_escala_pdf(fator)
    return float(L_real), int(n_seg), float(fator)


def _tamanho_ajuste_pdf(
    *,
    r_max: float,
    altura_peca: float,
    n_trilhos_altura: int,
    com_cota_base: bool,
    com_cota_dmax: bool,
) -> tuple[float, float, float, float]:
    """Envelope da peça + cotas (cm do objeto).

    Retorna ``(cont_w, cont_h, pad_sup, pad_inf)`` para encaixe e centragem
    no campo do PDF.
    """
    r_max = max(float(r_max), 0.5)
    altura_peca = max(float(altura_peca), 0.5)
    n_tr = max(int(n_trilhos_altura), 1)
    # Trilho compacto + folga curta para o texto (não inflar e forçar 1:2).
    folga_dir = 1.55 + 1.0 * float(n_tr - 1)
    half_x = r_max + max(folga_dir, 1.55)
    afast_borda = 0.10 * r_max
    # Borda: rótulo acima; altura total: rótulo na extremidade superior.
    pad_sup = max(2.35, afast_borda + 1.55)
    pad_inf = 2.0 if com_cota_base else 0.55
    if com_cota_dmax:
        pad_sup = max(pad_sup, 1.15)
        pad_inf = max(pad_inf, 1.15)
    cont_w = 2.0 * half_x
    cont_h = altura_peca + pad_sup + pad_inf
    return cont_w, cont_h, pad_sup, pad_inf


def _folha_e_escala_para_conteudo(
    cont_w: float, cont_h: float
) -> tuple[tuple[float, float], float, int, int]:
    """Escolhe orientação A4 e a maior escala discreta que cabe no campo.

    Campo: 2,5 cm (E/D/inferior) e 1 cm abaixo do cabeçalho. Só a escala
    muda para encaixar peça + cotas nesse retângulo.
    """
    cont_w = max(float(cont_w), 1.0)
    cont_h = max(float(cont_h), 1.0)
    melhor: tuple[float, float, tuple[float, float], float, int, int] | None = None
    for folha in (_FOLHA_PAISAGEM, _FOLHA_RETRATO):
        ax_x0, ax_x1, ax_y0, ax_y1 = _area_desenho_pdf(folha[0], folha[1])
        util_w = max(ax_x1 - ax_x0, 1.0)
        util_h = max(ax_y1 - ax_y0, 1.0)
        bruto = min(
            util_w * _FATOR_AREA_UTIL / cont_w,
            util_h * _FATOR_AREA_UTIL / cont_h,
        )
        bruto = min(bruto, _ESCALA_MAX_AMPLIACAO)
        fator, a_esc, b_esc = _fator_escala_pdf(bruto)
        ocup = (fator * cont_w / util_w) * (fator * cont_h / util_h)
        cand = (fator, ocup, folha, fator, a_esc, b_esc)
        if melhor is None or cand[0] > melhor[0] or (
            abs(cand[0] - melhor[0]) < 1e-12 and cand[1] > melhor[1]
        ):
            melhor = cand
    assert melhor is not None
    _f, _o, folha, fator, a_esc, b_esc = melhor
    return folha, float(fator), int(a_esc), int(b_esc)


def _fmt_marca_escala(valor_cm: float) -> str:
    v = float(valor_cm)
    if abs(v - round(v)) < 1e-6:
        return str(int(round(v)))
    return f"{v:.1f}".replace(".", ",")


def _desenhar_barra_escala(
    ax,
    *,
    x_direita: float,
    y_base: float,
    comprimento_eixos: float,
    comprimento_real_cm: float,
    n_segmentos: int,
    fontweight: str = "normal",
    razao_escala: int | None = None,
) -> None:
    """Escala gráfica: segmentos preto/branco e marcas em cm (sem rótulo de razão)."""
    del razao_escala  # mantido na assinatura por chamadas existentes
    L = max(float(comprimento_eixos), 1e-6)
    n_seg = max(int(n_segmentos), 2)
    total = max(float(comprimento_real_cm), 1e-6)
    passo = total / float(n_seg)
    x1 = float(x_direita)
    x0 = x1 - L
    seg_w = L / float(n_seg)
    h, tick, _folga = _medidas_barra_escala(L)
    y_barra = float(y_base)
    y_topo = y_barra + h
    z = 10

    for i in range(n_seg):
        xi = x0 + i * seg_w
        face = "#ffffff" if i % 2 == 0 else "#111111"
        ax.add_patch(
            Rectangle(
                (xi, y_barra),
                seg_w,
                h,
                facecolor=face,
                edgecolor="none",
                linewidth=0.0,
                clip_on=False,
                zorder=z,
            )
        )
    ax.add_patch(
        Rectangle(
            (x0, y_barra),
            L,
            h,
            facecolor="none",
            edgecolor=_COR_COTA,
            linewidth=_LW_COTA * 1.15,
            clip_on=False,
            zorder=z + 1,
        )
    )

    for i in range(n_seg + 1):
        xi = x0 + i * seg_w
        ax.plot(
            [xi, xi],
            [y_topo, y_topo + tick],
            color=_COR_COTA,
            lw=_LW_COTA,
            clip_on=False,
            zorder=z + 2,
        )
        ax.text(
            xi,
            y_topo + tick + 0.04 * h,
            _fmt_marca_escala(i * passo),
            ha="center",
            va="bottom",
            fontsize=_FS_ESCALA * 0.92,
            fontweight=fontweight,
            color=_COR_COTA,
            clip_on=False,
            zorder=z + 3,
        )
        if i == n_seg:
            ax.text(
                xi + max(0.12, 0.04 * L),
                y_topo + tick + 0.04 * h,
                "cm",
                ha="left",
                va="bottom",
                fontsize=_FS_ESCALA * 0.92,
                fontweight=fontweight,
                color=_COR_COTA,
                clip_on=False,
                zorder=z + 3,
            )


def _remover_barra_escala_pub(ax) -> None:
    """Remove artistas da barra de escala da publicação (para redesenhar)."""
    arts = getattr(ax, "_pub_barra_artistas", None)
    if not arts:
        return
    for art in arts:
        try:
            art.remove()
        except Exception:
            pass
    ax._pub_barra_artistas = []  # type: ignore[attr-defined]


def _desenhar_barra_escala_canto_eixos(
    ax,
    *,
    fontweight: str = "normal",
    x_direita: float | None = None,
    y_base: float | None = None,
) -> None:
    """Barra padronizada no canto inferior direito da janela (Publicação / tela).

    Tamanho visual **fixo** na figura (não depende da peça). Os números são
    cm do objeto segundo a escala atual dos eixos — assim a régua parece
    sempre igual e continua metrologicamente correcta.
    """
    fig = ax.figure
    if fig is None:
        return
    _remover_barra_escala_pub(ax)
    ax._pub_barra_escala = {"fontweight": fontweight}  # type: ignore[attr-defined]

    x0, x1 = ax.get_xlim()
    span_x = max(float(x1 - x0), 1e-9)
    try:
        ax.apply_aspect()
    except Exception:
        pass
    pos = ax.get_position()
    pos_w = max(float(pos.width), 1e-9)

    L_fig = float(_L_FIG_BARRA_PUB)
    n_seg = int(_N_SEG_BARRA_PUB)
    h_fig = float(_H_FIG_BARRA_PUB)
    tick_fig = float(_TICK_FIG_BARRA_PUB)
    L_real = L_fig / pos_w * span_x
    passo = L_real / float(n_seg)

    m = _MARGEM_FIGURA_TELA
    x1a = float(x_direita) if x_direita is not None else float(m["right"]) - 0.02
    y_barra = float(y_base) if y_base is not None else float(m["bottom"]) + 0.015
    x0a = x1a - L_fig
    seg_w = L_fig / float(n_seg)
    y_topo = y_barra + h_fig
    z = 10
    tr = fig.transFigure
    arts: list = []

    for i in range(n_seg):
        xi = x0a + i * seg_w
        face = "#ffffff" if i % 2 == 0 else "#111111"
        patch = ax.add_patch(
            Rectangle(
                (xi, y_barra),
                seg_w,
                h_fig,
                facecolor=face,
                edgecolor="none",
                linewidth=0.0,
                transform=tr,
                clip_on=False,
                zorder=z,
            )
        )
        arts.append(patch)
    contorno = ax.add_patch(
        Rectangle(
            (x0a, y_barra),
            L_fig,
            h_fig,
            facecolor="none",
            edgecolor=_COR_COTA,
            linewidth=_LW_COTA * 1.15,
            transform=tr,
            clip_on=False,
            zorder=z + 1,
        )
    )
    arts.append(contorno)

    for i in range(n_seg + 1):
        xi = x0a + i * seg_w
        (ln,) = ax.plot(
            [xi, xi],
            [y_topo, y_topo + tick_fig],
            color=_COR_COTA,
            lw=_LW_COTA,
            transform=tr,
            clip_on=False,
            zorder=z + 2,
        )
        arts.append(ln)
        txt = ax.text(
            xi,
            y_topo + tick_fig + 0.004,
            _fmt_marca_escala(i * passo),
            ha="center",
            va="bottom",
            fontsize=_FS_ESCALA * 0.92,
            fontweight=fontweight,
            color=_COR_COTA,
            transform=tr,
            clip_on=False,
            zorder=z + 3,
        )
        arts.append(txt)

    # «cm» centrado abaixo da barra.
    txt_cm = ax.text(
        0.5 * (x0a + x1a),
        y_barra - 0.004,
        "cm",
        ha="center",
        va="top",
        fontsize=_FS_ESCALA * 0.92,
        fontweight=fontweight,
        color=_COR_COTA,
        transform=tr,
        clip_on=False,
        zorder=z + 3,
    )
    arts.append(txt_cm)

    ax._pub_barra_artistas = arts  # type: ignore[attr-defined]


def _medidas_barra_escala(comprimento_eixos: float) -> tuple[float, float, float]:
    """Altura da barra, comprimento do traço e folga inferior (reservada, sem texto)."""
    L = max(float(comprimento_eixos), 1e-6)
    h = max(0.22, min(0.55, 0.09 * L))
    tick = max(0.10, 0.045 * L)
    return h, tick, 0.0


def _posicao_escala_canto_folha(
    folha_w: float, comprimento_eixos: float
) -> tuple[float, float]:
    """Canto inferior direito do milimetrado (mesmo padrão do PDF técnico)."""
    del comprimento_eixos  # reservado para chamadas existentes
    x_direita = float(folha_w) - _MARGEM_DESENHO_PDF
    return x_direita, float(_Y_BARRA_ESCALA_PDF)


def ajustar_figura_tela(fig, ax) -> None:
    """Preenche a área disponível na janela (pré-visualização em fundo branco)."""
    if fig is None or ax is None:
        return
    canvas = fig.canvas
    if canvas is None:
        return
    # Repõe a área do eixo (publicação chegou a forçar [0,0,1,1]).
    m = _MARGEM_FIGURA_TELA
    fig.subplots_adjust(**m)
    ax.set_position(
        [
            float(m["left"]),
            float(m["bottom"]),
            float(m["right"]) - float(m["left"]),
            float(m["top"]) - float(m["bottom"]),
        ]
    )
    ax.set_aspect("equal", adjustable="box", anchor="C")
    # Publicação: redesenha a barra no canto da figura (após o eixo encolher).
    modo = str(getattr(ax, "_perfil_modo", "") or "")
    params = getattr(ax, "_pub_barra_escala", None)
    if modo.startswith("publicacao") and isinstance(params, dict):
        _desenhar_barra_escala_canto_eixos(
            ax, fontweight=str(params.get("fontweight") or "normal")
        )
    elif params is not None:
        _remover_barra_escala_pub(ax)
        ax._pub_barra_escala = None  # type: ignore[attr-defined]
    get_tk = getattr(canvas, "get_tk_widget", None)
    if get_tk is None:
        return
    try:
        widget = get_tk()
        widget.update_idletasks()
        px_w = max(int(widget.winfo_width()), 120)
        px_h = max(int(widget.winfo_height()), 120)
    except Exception:
        return
    dpi = float(fig.get_dpi() or _FOLHA_DPI_TELA)
    fig.set_size_inches(px_w / dpi, px_h / dpi, forward=True)


def preparar_folha_exportacao(fig, ax, folha: tuple[float, float]) -> None:
    """Prepara figura em tamanho físico A4 para exportação PDF."""
    folha_w, folha_h = folha
    fig.set_size_inches(folha_w / 2.54, folha_h / 2.54)
    fig.subplots_adjust(**_MARGEM_FIGURA)
    ax.set_position([0.0, 0.0, 1.0, 1.0])
    ax.set_aspect("equal", adjustable="box", anchor="C")


def _area_desenho_pdf(folha_w: float, folha_h: float) -> tuple[float, float, float, float]:
    """Campo do desenho no quadriculado (cm do papel).

    — 2,5 cm das bordas esquerda, direita e inferior da folha;
    — 1 cm abaixo do bloco do cabeçalho.
    A barra de escala fica na faixa inferior (fora deste retângulo).
    """
    x0 = _MARGEM_DESENHO_PDF
    x1 = float(folha_w) - _MARGEM_DESENHO_PDF
    y0 = _MARGEM_DESENHO_PDF
    y1 = (
        float(folha_h)
        - _MARGEM_FOLHA
        - _ALTURA_CABECALHO_PDF
        - _FOLGA_ABAIXO_CABECALHO_PDF
    )
    return x0, x1, y0, y1


def _desenhar_cabecalho_pdf(ax, folha_w: float, folha_h: float, titulo: str) -> None:
    partes = [p.strip() for p in titulo.split("\n\n") if p.strip()]
    y_linha1 = folha_h - _MARGEM_FOLHA - 0.2
    y_linha2 = y_linha1 - 0.55
    if partes:
        ax.text(
            folha_w / 2.0,
            y_linha1,
            partes[0],
            ha="center",
            va="top",
            fontsize=_FS_TITULO,
            fontweight="bold",
            color="#111111",
            clip_on=False,
            zorder=8,
        )
    if len(partes) > 1:
        ax.text(
            folha_w / 2.0,
            y_linha2,
            partes[1],
            ha="center",
            va="top",
            fontsize=_FS_TITULO * 0.95,
            fontweight="bold",
            color="#111111",
            clip_on=False,
            zorder=8,
        )


def limpar_decoracao_figura(fig) -> None:
    """Remove cabeçalho da figura da tela."""
    if fig is None:
        return
    fig.suptitle("")
    antigo = getattr(fig, "_texto_escala_tela", None)
    if antigo is not None:
        try:
            antigo.remove()
        except Exception:
            pass
        fig._texto_escala_tela = None  # type: ignore[attr-defined]


def _texto_cabecalho_perfil(
    dados: dict[str, Any], forma: str, volume_l: float
) -> str:
    sitio = (dados.get("sitio") or "").strip() or "—"
    numero = (dados.get("numero") or "").strip() or "—"
    return (
        f"Nome do sítio: {sitio}    Número do desenho: {numero}\n\n"
        f"Forma geométrica: {forma or '—'}    "
        f"Volume do objeto: {volume_l:.3f} L    "
        f"Tamanho: {rotulo_tamanho(volume_l)}"
    )


def _aplicar_cabecalho(fig, titulo: str, *, em_pdf: bool) -> None:
    if fig is None:
        return
    y = 0.925 if em_pdf else 0.965
    margem = _MARGEM_FIGURA if em_pdf else _MARGEM_FIGURA_TELA
    fig.suptitle(
        titulo,
        fontsize=_FS_TITULO,
        y=y,
        va="top",
        linespacing=1.35,
        color="#111111",
    )
    fig.subplots_adjust(**margem)


def _folha_orientacao(largura: float, altura: float) -> tuple[float, float]:
    if float(largura) >= float(altura):
        return _FOLHA_PAISAGEM
    return _FOLHA_RETRATO


def _transformar_papel(
    x: float | np.ndarray,
    y: float | np.ndarray,
    *,
    cx_papel: float,
    cy_papel: float,
    cx_real: float,
    cy_real: float,
    fator: float,
) -> tuple[np.ndarray, np.ndarray]:
    xa = np.asarray(x, dtype=float)
    ya = np.asarray(y, dtype=float)
    return (
        cx_papel + (xa - cx_real) * fator,
        cy_papel + (ya - cy_real) * fator,
    )


def _grade_folha(ax, lo: float, hi: float, orientacao: str) -> None:
    lo = float(lo)
    hi = float(hi)
    if hi <= lo:
        return

    def _linhas(
        passo: float,
        cor: str,
        lw: float,
        *,
        zorder: float = 1.0,
        omitir_multiplos_de: float | None = None,
    ) -> None:
        if passo <= 0.0:
            return
        t0 = np.floor(lo / passo) * passo
        for t in np.arange(t0, hi + 1e-9, passo):
            if t < lo - 1e-9 or t > hi + 1e-9:
                continue
            if omitir_multiplos_de is not None and np.isclose(
                t % omitir_multiplos_de, 0.0
            ):
                continue
            if orientacao == "x":
                ax.axvline(t, color=cor, linewidth=lw, linestyle="-", zorder=zorder)
            else:
                ax.axhline(t, color=cor, linewidth=lw, linestyle="-", zorder=zorder)

    _linhas(1.0, "#D0D0D0", _LW_GRADE_1CM, zorder=2.0)
    _linhas(0.1, "#ECECEC", _LW_GRADE_1MM, zorder=1.0, omitir_multiplos_de=1.0)
    _linhas(0.5, "#E2E2E2", _LW_GRADE_5MM, zorder=1.5, omitir_multiplos_de=1.0)


def _grade_folha_util(
    ax, x0: float, y0: float, x1: float, y1: float
) -> None:
    """Milimetrado só na área útil (margem de 1 cm permanece branca)."""
    x0, y0, x1, y1 = float(x0), float(y0), float(x1), float(y1)

    def _horiz(
        passo: float,
        cor: str,
        lw: float,
        *,
        zorder: float = 1.0,
        omitir_multiplos_de: float | None = None,
    ) -> None:
        if passo <= 0.0:
            return
        t0 = np.floor(y0 / passo) * passo
        for t in np.arange(t0, y1 + 1e-9, passo):
            if t < y0 - 1e-9 or t > y1 + 1e-9:
                continue
            if omitir_multiplos_de is not None and np.isclose(
                t % omitir_multiplos_de, 0.0
            ):
                continue
            ax.plot([x0, x1], [t, t], color=cor, linewidth=lw, zorder=zorder)

    def _vert(
        passo: float,
        cor: str,
        lw: float,
        *,
        zorder: float = 1.0,
        omitir_multiplos_de: float | None = None,
    ) -> None:
        if passo <= 0.0:
            return
        t0 = np.floor(x0 / passo) * passo
        for t in np.arange(t0, x1 + 1e-9, passo):
            if t < x0 - 1e-9 or t > x1 + 1e-9:
                continue
            if omitir_multiplos_de is not None and np.isclose(
                t % omitir_multiplos_de, 0.0
            ):
                continue
            ax.plot([t, t], [y0, y1], color=cor, linewidth=lw, zorder=zorder)

    _horiz(0.1, "#ECECEC", _LW_GRADE_1MM, zorder=1.0, omitir_multiplos_de=1.0)
    _horiz(0.5, "#E2E2E2", _LW_GRADE_5MM, zorder=1.5, omitir_multiplos_de=1.0)
    _horiz(1.0, "#D0D0D0", _LW_GRADE_1CM, zorder=2.0)
    _vert(0.1, "#ECECEC", _LW_GRADE_1MM, zorder=1.0, omitir_multiplos_de=1.0)
    _vert(0.5, "#E2E2E2", _LW_GRADE_5MM, zorder=1.5, omitir_multiplos_de=1.0)
    _vert(1.0, "#D0D0D0", _LW_GRADE_1CM, zorder=2.0)


def _contorno_folha(ax, largura: float, altura: float) -> None:
    from matplotlib.patches import Rectangle

    util_w = largura - 2.0 * _MARGEM_FOLHA
    util_h = altura - 2.0 * _MARGEM_FOLHA
    ax.add_patch(
        Rectangle(
            (0.0, 0.0),
            largura,
            altura,
            fill=False,
            edgecolor="#666666",
            linewidth=_LW_BORDA_FOLHA,
            zorder=3,
        )
    )
    ax.add_patch(
        Rectangle(
            (_MARGEM_FOLHA, _MARGEM_FOLHA),
            util_w,
            util_h,
            fill=False,
            edgecolor="#AAAAAA",
            linewidth=_LW_MARGEM_UTIL,
            linestyle=(0, (4, 3)),
            zorder=3,
        )
    )


def _desenhar_folha_a4(ax, largura: float, altura: float) -> None:
    """Papel milimetrado A4 fixo, sem eixos numéricos."""
    ax.set_facecolor("white")
    ax.set_axisbelow(True)
    ax.set_xlim(0.0, largura)
    ax.set_ylim(0.0, altura)
    m = _MARGEM_FOLHA
    _grade_folha_util(ax, m, m, largura - m, altura - m)
    _contorno_folha(ax, largura, altura)
    ax.set_aspect("equal", adjustable="box", anchor="C")
    ax.autoscale(enable=False)
    ax.set_xlim(0.0, largura)
    ax.set_ylim(0.0, altura)
    ax.axis("off")


def _cota_horizontal(
    ax,
    y: float,
    x0: float,
    x1: float,
    texto: str,
    afast: float,
    *,
    marca: float,
    pos_rotulo: str = "acima",
    fontweight: str = "normal",
) -> None:
    rotulo = _rotulo_cota(texto)

    def _anotar(y_linha: float) -> None:
        if pos_rotulo == "abaixo":
            dy, va = -8.0, "top"
        else:
            dy, va = 8.0, "bottom"
        ax.annotate(
            rotulo,
            xy=(0.5 * (x0 + x1), y_linha),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=_FS_COTA,
            fontweight=fontweight,
            color=_COR_COTA,
            linespacing=1.12,
            clip_on=False,
            annotation_clip=False,
            zorder=6,
        )

    if abs(afast) < 1e-9:
        if abs(x1 - x0) >= 1e-9:
            ax.plot([x0, x1], [y, y], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
            if marca > 1e-9:
                ax.plot([x0, x0], [y - marca, y + marca], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
                ax.plot([x1, x1], [y - marca, y + marca], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
        _anotar(y)
        return
    yy = y + afast
    if abs(x1 - x0) < 1e-9:
        # Diâmetro nulo: só o texto (sem traço no eixo / pontinha).
        _anotar(yy)
        return
    ax.plot([x0, x0], [y, yy], color=_COR_COTA, lw=_LW_COTA * 0.85, clip_on=False)
    ax.plot([x1, x1], [y, yy], color=_COR_COTA, lw=_LW_COTA * 0.85, clip_on=False)
    ax.plot([x0, x1], [yy, yy], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
    if marca > 1e-9:
        ax.plot([x0, x0], [yy - marca, yy + marca], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
        ax.plot([x1, x1], [yy - marca, yy + marca], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
    _anotar(yy)


def _cota_vertical(
    ax,
    x: float,
    y0: float,
    y1: float,
    texto: str,
    *,
    marca: float,
    lado: str = "dir",
    ancoragem: str = "meio",
    y_rotulo: float | None = None,
    dx_pts: float = 3.0,
    dy_pts: float = 0.0,
    fontweight: str = "normal",
) -> None:
    """Cota vertical.

    ``ancoragem``:
    - ``topo`` — rótulo na extremidade superior, acima da linha;
    - ``base`` — rótulo na extremidade inferior, abaixo da linha;
    - ``meio`` — a meio do segmento (predefinição).
    """
    ax.plot([x, x], [y0, y1], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
    ax.plot([x - marca, x + marca], [y0, y0], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
    ax.plot([x - marca, x + marca], [y1, y1], color=_COR_COTA, lw=_LW_COTA, clip_on=False)
    dx = float(dx_pts) if lado == "dir" else -float(dx_pts)
    y_lo, y_hi = (float(y0), float(y1)) if y0 <= y1 else (float(y1), float(y0))
    if y_rotulo is not None:
        y_txt = float(y_rotulo)
        va = "center"
        dy = float(dy_pts)
    elif ancoragem == "topo":
        y_txt = y_hi
        va = "bottom"
        dy = 2.0 + float(dy_pts)
    elif ancoragem == "base":
        y_txt = y_lo
        va = "top"
        dy = -2.0 + float(dy_pts)
    else:
        y_txt = 0.5 * (y_lo + y_hi)
        va = "center"
        dy = float(dy_pts)
    ax.annotate(
        _rotulo_cota(texto),
        xy=(x, y_txt),
        xytext=(dx, dy),
        textcoords="offset points",
        ha="left" if lado == "dir" else "right",
        va=va,
        fontsize=_FS_COTA,
        fontweight=fontweight,
        color=_COR_COTA,
        linespacing=1.12,
        clip_on=False,
        annotation_clip=False,
        zorder=6,
    )


def _caixa_conteudo_real(
    *,
    ox: float,
    oy: float,
    r_max: float,
    r_w: np.ndarray,
    y0: float,
    y1: float,
    y_dmax: float,
    h: float,
    db: float,
    dmax: float,
    dbase: float,
    i_ultimo: int,
    afast_diam: float,
    margem_x: float,
    margem_y: float,
    tem_c2: bool,
    h_c2: float,
    d_c2: float,
    offset: float,
    z0: float,
) -> tuple[float, float, float, float]:
    x_hi = ox + _x_trilho(r_max, i_ultimo) + 0.35 * r_max
    x_lo = ox - max(float(np.max(r_w)), db / 2.0, dmax / 2.0, dbase / 2.0) - margem_x
    x_lo = min(x_lo, ox - dmax / 2.0 - 3.5)
    y_lo = y0 - afast_diam - margem_y - 2.0
    y_hi = y1 + afast_diam + margem_y + 1.6
    if tem_c2:
        y_c2 = offset + h_c2 - z0 + oy
        y_hi = max(y_hi, y_c2 + 0.8)
        x_hi = max(x_hi, ox + d_c2 / 2.0 + 0.6)
    y_hi = max(y_hi, y0 + h + afast_diam + 0.8)
    x_lo -= _MARGEM_COTA_X
    x_hi += _MARGEM_COTA_X
    y_lo -= _MARGEM_COTA_Y
    y_hi += _MARGEM_COTA_Y
    # Equilibra esquerda/direita em torno do eixo da peça (as cotas à direita
    # não devem empurrar o vaso para a esquerda na vista).
    margem_h = max(ox - x_lo, x_hi - ox)
    x_lo = ox - margem_h
    x_hi = ox + margem_h
    return x_lo, x_hi, y_lo, y_hi


def polilinha_perfil_interno(
    z_w: np.ndarray,
    r_w: np.ndarray,
    r_b: np.ndarray,
    z_b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Meridiano interno contínuo: fundo (se houver anel) e parede até a borda."""
    r_w = np.asarray(r_w, dtype=float).ravel()
    z_w = np.asarray(z_w, dtype=float).ravel()
    r_b = np.asarray(r_b, dtype=float).ravel()
    z_b = np.asarray(z_b, dtype=float).ravel()
    if r_b.size > 1 and float(np.max(r_b)) > 0.02:
        r = np.concatenate([r_b, r_w])
        z = np.concatenate([z_b, z_w])
    else:
        r, z = r_w, z_w
    if r.size < 2:
        return r, z
    ds = np.hypot(np.diff(r), np.diff(z))
    keep = np.ones(r.size, dtype=bool)
    keep[1:] = ds > 1e-9
    return r[keep], z[keep]


def offset_meridiano_normal(
    r: np.ndarray, z: np.ndarray, espessura: float
) -> tuple[np.ndarray, np.ndarray]:
    """Paralela do meridiano a ``espessura`` na normal exterior (plano R×Z).

    Percurso do eixo/fundo até a borda. No fundo arredondado (diâmetro da base
    0 cm) a normal aponta para baixo no eixo: o tracejado fecha no centro,
    abaixo do contato interno, em vez de parar a uma distância horizontal.
    """
    r = np.asarray(r, dtype=float).ravel()
    z = np.asarray(z, dtype=float).ravel()
    t = float(espessura)
    if r.size < 2 or t <= 0.0:
        return r.copy(), z.copy()
    dr = np.diff(r)
    dz = np.diff(z)
    hyp = np.maximum(np.hypot(dr, dz), 1e-12)
    nsr = dz / hyp
    nsz = -dr / hyp
    nr = np.zeros(r.size)
    nz = np.zeros(z.size)
    nr[0], nz[0] = nsr[0], nsz[0]
    nr[-1], nz[-1] = nsr[-1], nsz[-1]
    if r.size > 2:
        nr[1:-1] = nsr[:-1] + nsr[1:]
        nz[1:-1] = nsz[:-1] + nsz[1:]
        hn = np.maximum(np.hypot(nr, nz), 1e-12)
        nr /= hn
        nz /= hn
    r_out = np.maximum(r + t * nr, 0.0)
    z_out = z + t * nz
    if float(r[0]) <= 1e-4:
        nr[0], nz[0] = 0.0, -1.0
        r_out[0] = 0.0
        z_out[0] = float(z[0]) - t
    return _fechar_offset_na_borda(r, z, r_out, z_out, t)


def _fechar_offset_na_borda(
    r: np.ndarray,
    z: np.ndarray,
    r_out: np.ndarray,
    z_out: np.ndarray,
    t: float,
) -> tuple[np.ndarray, np.ndarray]:
    """O lábio fica na horizontal, na mesma altura da borda interna."""
    z_rim = float(z[-1])
    r_lip = float(r[-1]) + float(t)
    r_out = np.asarray(r_out, dtype=float).copy()
    z_out = np.asarray(z_out, dtype=float).copy()
    acima = z_out > z_rim + 1e-9
    if np.any(acima):
        i_ac = int(np.argmax(acima))
        if i_ac > 0:
            z0, z1 = float(z_out[i_ac - 1]), float(z_out[i_ac])
            r0, r1 = float(r_out[i_ac - 1]), float(r_out[i_ac])
            if abs(z1 - z0) > 1e-12:
                a = (z_rim - z0) / (z1 - z0)
                r_cruz = r0 + a * (r1 - r0)
            else:
                r_cruz = r0
            r_out = np.concatenate([r_out[:i_ac], [r_cruz]])
            z_out = np.concatenate([z_out[:i_ac], [z_rim]])
        else:
            r_out = np.array([r_lip], dtype=float)
            z_out = np.array([z_rim], dtype=float)
    r_ult = float(r_out[-1])
    z_ult = float(z_out[-1])
    extra_r: list[float] = []
    extra_z: list[float] = []
    if z_ult < z_rim - 1e-6:
        extra_r.append(r_ult)
        extra_z.append(z_rim)
        r_ult, z_ult = r_ult, z_rim
    if abs(r_ult - r_lip) > 1e-6 or abs(z_ult - z_rim) > 1e-6:
        extra_r.append(r_lip)
        extra_z.append(z_rim)
    else:
        r_out[-1] = r_lip
        z_out[-1] = z_rim
    if extra_r:
        r_out = np.concatenate([r_out, extra_r])
        z_out = np.concatenate([z_out, extra_z])
    return r_out, z_out


def _cota_espessura_parede(
    ax,
    T,
    *,
    ox: float,
    r_in: np.ndarray,
    y_in: np.ndarray,
    r_out: np.ndarray,
    y_out: np.ndarray,
    espessura: float,
    marca: float,
    fontweight: str,
) -> None:
    """Cota da espessura da parede no flanco esquerdo, junto à borda."""
    if r_in.size < 2 or r_out.size < 2:
        return
    i = int(round(0.82 * (r_in.size - 1)))
    i = min(i, r_out.size - 1)
    xa, ya = T(
        [ox - float(r_in[i]), ox - float(r_out[i])],
        [float(y_in[i]), float(y_out[i])],
    )
    x0, x1 = float(xa[0]), float(xa[1])
    y0, y1 = float(ya[0]), float(ya[1])
    ax.plot([x0, x1], [y0, y1], color=_COR_COTA, lw=_LW_COTA, zorder=6, clip_on=False)
    dx, dy = x1 - x0, y1 - y0
    L = max(float(np.hypot(dx, dy)), 1e-9)
    px, py = -dy / L * marca, dx / L * marca
    ax.plot(
        [x0 - px, x0 + px],
        [y0 - py, y0 + py],
        color=_COR_COTA,
        lw=_LW_COTA,
        zorder=6,
        clip_on=False,
    )
    ax.plot(
        [x1 - px, x1 + px],
        [y1 - py, y1 + py],
        color=_COR_COTA,
        lw=_LW_COTA,
        zorder=6,
        clip_on=False,
    )
    ax.annotate(
        _rotulo_cota(f"espes. parede {espessura:.1f} cm"),
        xy=(x1, y1),
        xytext=(-8, 0),
        textcoords="offset points",
        ha="right",
        va="center",
        fontsize=_FS_COTA,
        fontweight=fontweight,
        color=_COR_COTA,
        clip_on=False,
        annotation_clip=False,
        zorder=6,
    )


def desenhar_perfil_completo(
    ax,
    z,
    r,
    dados: dict[str, Any],
    *,
    forma: str = "",
    volume_l: float = 0.0,
    tipo_base: str = "Reta",
    espessura: float = 0.0,
    modo: str = "tela",
) -> None:
    """Desenha o perfil 2D. Modo «tela»: fundo branco, sem milimetrado; «pdf»: folha A4."""
    from ceraform.perfil import meridiano_com_base

    z_w, r_w, r_b, z_b = meridiano_com_base(z, r, tipo_base)
    r_in, z_in = polilinha_perfil_interno(z_w, r_w, r_b, z_b)
    r_out = z_out = None
    if espessura > 0:
        r_out, z_out = offset_meridiano_normal(r_in, z_in, float(espessura))
    ax.clear()
    fig = ax.figure
    if fig is not None:
        limpar_decoracao_figura(fig)
    em_pdf = modo == "pdf"
    peso_fonte = "bold" if em_pdf else "normal"

    cor = "#1a56db"
    z0 = float(min(z_w.min(), z_b.min(), z_in.min()))
    z1 = float(max(z_w.max(), z_b.max(), z_in.max()))
    if z_out is not None:
        z0 = min(z0, float(z_out.min()))
        z1 = max(z1, float(z_out.max()))
    h = float(dados.get("h") or 0.0)
    db = float(dados.get("db") or 0.0)
    dmax = float(dados.get("dmax") or 0.0)
    hmax = float(dados.get("hmax") or 0.0)
    dbase = float(dados.get("dbase") or 0.0)
    offset = float(z_b[-1])
    # Posição do maior diâmetro nunca sai da peça (evita cota a flutuar no cabeçalho).
    hmax_pos = min(max(hmax, 0.0), h) if h > 0.0 else max(hmax, 0.0)
    z_dmax = offset + hmax_pos
    r_max = float(max(np.max(r_w), db / 2.0, dmax / 2.0, dbase / 2.0, 1.0))
    if r_out is not None:
        r_max = max(r_max, float(np.max(r_out)))
    h_c2 = float(dados.get("altura_carena2") or 0.0)
    d_c2 = float(dados.get("diametro_carena2") or 0.0)
    tem_c2 = h_c2 > 0.0 and d_c2 > 0.0 and abs(h_c2 - hmax) > 0.2
    i_ultimo = 2 if tem_c2 else 1

    folga = 0.12
    largura_peca = 2.0 * r_max
    altura_peca = max(float(z1 - z0), h, 1.0)
    margem_x = folga * largura_peca
    margem_y = folga * altura_peca
    afast_diam = 0.10 * r_max
    marca = 0.04 * r_max

    ox = margem_x + r_max
    oy = margem_y + afast_diam + max(0.0, -z0)
    y_w = z_w - z0 + oy
    y_b = z_b - z0 + oy
    y0 = oy
    y1 = z1 - z0 + oy
    y_dmax = z_dmax - z0 + oy

    x_lo, x_hi, y_lo, y_hi = _caixa_conteudo_real(
        ox=ox,
        oy=oy,
        r_max=r_max,
        r_w=r_w,
        y0=y0,
        y1=y1,
        y_dmax=y_dmax,
        h=h,
        db=db,
        dmax=dmax,
        dbase=dbase,
        i_ultimo=i_ultimo,
        afast_diam=afast_diam,
        margem_x=margem_x,
        margem_y=margem_y,
        tem_c2=tem_c2,
        h_c2=h_c2,
        d_c2=d_c2,
        offset=offset,
        z0=z0,
    )
    # Cotas redundantes (comparação a 1 casa, como no rótulo).
    mesma_borda_dmax = round(db, 1) == round(dmax, 1)
    base_nula = round(dbase, 1) == 0.0
    # Se hmax ≥ altura total, o maior diâmetro está na borda: só a cota de altura total.
    mesma_altura_dmax = round(h, 1) == round(hmax_pos, 1)
    if mesma_altura_dmax:
        n_trilhos = 1 + (1 if tem_c2 else 0)
    else:
        n_trilhos = 2 + (1 if tem_c2 else 0)

    if em_pdf:
        # Escala: peça + cotas encaixadas no campo 2,5 cm / 1 cm sob o cabeçalho.
        cont_w, cont_h, pad_sup, pad_inf = _tamanho_ajuste_pdf(
            r_max=r_max,
            altura_peca=max(float(z1 - z0), h, 1.0),
            n_trilhos_altura=n_trilhos,
            com_cota_base=not base_nula,
            com_cota_dmax=not mesma_borda_dmax,
        )
        (folha_w, folha_h), fator, a_esc, b_esc = _folha_e_escala_para_conteudo(
            cont_w, cont_h
        )
        ax_x0, ax_x1, ax_y0, ax_y1 = _area_desenho_pdf(folha_w, folha_h)
    else:
        cont_w = max(x_hi - x_lo, 1.0)
        cont_h = max(y_hi - y_lo, 1.0)
        pad_sup = 0.0
        pad_inf = 0.0
        folha_w, folha_h = _folha_orientacao(cont_w, cont_h)
        util_w = folha_w - 2.0 * _MARGEM_FOLHA
        util_h = folha_h - 2.0 * _MARGEM_FOLHA
        fator = min(
            util_w * _FATOR_AREA_UTIL / cont_w,
            util_h * _FATOR_AREA_UTIL / cont_h,
        )
        fator = min(fator, _ESCALA_MAX_AMPLIACAO)
        a_esc = None
        b_esc = None

    if em_pdf:
        # Centra o envelope (peça + cotas) no campo do quadriculado.
        cx_real = ox
        cy_real = 0.5 * ((y0 - pad_inf) + (y1 + pad_sup))
        cx_papel = 0.5 * (ax_x0 + ax_x1)
        cy_papel = 0.5 * (ax_y0 + ax_y1)

        def T(x, y):
            xa = np.atleast_1d(np.asarray(x, dtype=float))
            ya = np.atleast_1d(np.asarray(y, dtype=float))
            if xa.size == 1 and ya.size > 1:
                xa = np.full_like(ya, xa[0])
            elif ya.size == 1 and xa.size > 1:
                ya = np.full_like(xa, ya[0])
            return _transformar_papel(
                xa,
                ya,
                cx_papel=cx_papel,
                cy_papel=cy_papel,
                cx_real=cx_real,
                cy_real=cy_real,
                fator=fator,
            )

        if fig is not None:
            fig.patch.set_facecolor("white")
            fig.subplots_adjust(**_MARGEM_FIGURA)
        _desenhar_folha_a4(ax, folha_w, folha_h)
        _desenhar_cabecalho_pdf(ax, folha_w, folha_h, _texto_cabecalho_perfil(dados, forma, volume_l))
        marca_u = marca * fator
        afast_u = afast_diam * fator
    else:
        pad = 0.6
        if fig is not None:
            fig.patch.set_facecolor(_COR_FUNDO_TELA)
            fig.subplots_adjust(**_MARGEM_FIGURA_TELA)
        ax.set_facecolor(_COR_FUNDO_TELA)
        ax.set_xlim(x_lo - pad, x_hi + pad)
        ax.set_ylim(y_lo - pad, y_hi + pad)
        ax.set_aspect("equal", adjustable="box", anchor="C")
        ax.autoscale(enable=False)
        ax.axis("off")

        def T(x, y):
            xa = np.atleast_1d(np.asarray(x, dtype=float))
            ya = np.atleast_1d(np.asarray(y, dtype=float))
            if xa.size == 1 and ya.size > 1:
                xa = np.full_like(ya, xa[0])
            elif ya.size == 1 and xa.size > 1:
                ya = np.full_like(xa, ya[0])
            return xa, ya

        marca_u = marca
        afast_u = afast_diam

    x_esq, y_esq = T(ox - r_w, y_w)
    x_dir, y_dir = T(ox + r_w, y_w)
    ax.plot(x_esq, y_esq, color=cor, lw=_LW_PERFIL, zorder=5)
    ax.plot(x_dir, y_dir, color=cor, lw=_LW_PERFIL, zorder=5)
    x_esq_b, y_esq_b = T(ox - r_b, y_b)
    x_dir_b, y_dir_b = T(ox + r_b, y_b)
    ax.plot(x_esq_b, y_esq_b, color=cor, lw=_LW_PERFIL, zorder=5)
    ax.plot(x_dir_b, y_dir_b, color=cor, lw=_LW_PERFIL, zorder=5)
    xa, ya = T([ox - r_w[-1], ox + r_w[-1]], [y_w[-1], y_w[-1]])
    ax.plot(xa, ya, color=cor, lw=_LW_PERFIL, zorder=5)

    if r_out is not None and z_out is not None:
        y_ext = z_out - z0 + oy
        y_int = z_in - z0 + oy
        xs = np.concatenate([ox - r_out[::-1], ox + r_out])
        ys = np.concatenate([y_ext[::-1], y_ext])
        xt, yt = T(xs, ys)
        ax.plot(
            xt,
            yt,
            color="#b45309",
            lw=_LW_PERFIL * 0.8,
            ls=(0, (3.2, 1.6)),
            zorder=4,
            solid_capstyle="round",
            solid_joinstyle="round",
        )
        r_labio = float(r_in[-1]) + float(espessura)
        y_borda = float(y_int[-1])
        for sinal in (-1.0, 1.0):
            xa, ya = T(
                [ox + sinal * float(r_in[-1]), ox + sinal * r_labio],
                [y_borda, y_borda],
            )
            ax.plot(
                xa,
                ya,
                color="#b45309",
                lw=_LW_PERFIL * 0.8,
                ls="-",
                solid_capstyle="butt",
                zorder=4,
            )
        _cota_espessura_parede(
            ax,
            T,
            ox=ox,
            r_in=r_in,
            y_in=y_int,
            r_out=r_out,
            y_out=y_ext,
            espessura=float(espessura),
            marca=marca_u,
            fontweight=peso_fonte,
        )

    xl, yl = T([ox, ox], [y0, y1])
    ax.plot(xl, yl, color="#888888", lw=_LW_EIXO, ls="--", zorder=4)

    # Cotas redundantes omitidas: valores iguais ao que já se lê noutra cota
    # (ou diâmetro da base 0) não se repetem no desenho técnico.
    xp, yp = T([ox - db / 2.0, ox + db / 2.0], y1)
    _cota_horizontal(
        ax, float(yp[0]), float(xp[0]), float(xp[1]),
        f"diâmetro da borda {db:.1f} cm",
        afast_u,
        marca=marca_u,
        fontweight=peso_fonte,
        pos_rotulo="acima",
    )
    if not mesma_borda_dmax:
        xp, yp = T([ox - dmax / 2.0, ox + dmax / 2.0], y_dmax)
        _cota_horizontal(
            ax, float(yp[0]), float(xp[0]), float(xp[1]),
            f"maior diâmetro da peça {dmax:.1f} cm",
            0.0,
            marca=marca_u,
            fontweight=peso_fonte,
            pos_rotulo="abaixo",
        )
    if not base_nula:
        xp, yp = T([ox - dbase / 2.0, ox + dbase / 2.0], y0)
        _cota_horizontal(
            ax, float(yp[0]), float(xp[0]), float(xp[1]),
            f"diâmetro da base {dbase:.1f} cm",
            -afast_u,
            marca=marca_u,
            fontweight=peso_fonte,
            pos_rotulo="abaixo",
        )

    i_trilho = 0
    y_htot = y0 + h if h > 0 else y1
    _, y0p = T(ox, y0)
    _, y_dmax_p = T(ox, y_dmax)
    if not mesma_altura_dmax:
        xh, _ = T(ox + _x_trilho(r_max, i_trilho, compacto=em_pdf), y0)
        i_trilho += 1
        _cota_vertical(
            ax,
            float(xh[0]),
            float(y0p[0]),
            float(y_dmax_p[0]),
            f"altura da base até o maior diâmetro {hmax:.1f} cm",
            marca=marca_u,
            fontweight=peso_fonte,
            ancoragem="base",
        )

    if tem_c2:
        h_c2_pos = min(max(h_c2, 0.0), h) if h > 0.0 else max(h_c2, 0.0)
        y_c2 = offset + h_c2_pos - z0 + oy
        xp, yp = T([ox - d_c2 / 2.0, ox + d_c2 / 2.0], y_c2)
        _cota_horizontal(
            ax,
            float(yp[0]),
            float(xp[0]),
            float(xp[1]),
            f"diâmetro da segunda quebra {d_c2:.1f} cm",
            0.0,
            marca=marca_u,
            fontweight=peso_fonte,
            pos_rotulo="abaixo",
        )
        xc, _ = T(ox + _x_trilho(r_max, i_trilho, compacto=em_pdf), y0)
        i_trilho += 1
        _, y_c2p = T(ox, y_c2)
        _, y0p2 = T(ox, y0)
        _cota_vertical(
            ax,
            float(xc[0]),
            float(y0p2[0]),
            float(y_c2p[0]),
            f"altura da segunda quebra {h_c2:.1f} cm",
            marca=marca_u,
            fontweight=peso_fonte,
            ancoragem="meio",
        )

    xht, _ = T(ox + _x_trilho(r_max, i_trilho, compacto=em_pdf), y0)
    _, y_htot_p = T(ox, y_htot)
    _, y0p3 = T(ox, y0)
    _cota_vertical(
        ax,
        float(xht[0]),
        float(y0p3[0]),
        float(y_htot_p[0]),
        f"altura total {h:.1f} cm",
        marca=marca_u,
        fontweight=peso_fonte,
        ancoragem="topo",
    )

    titulo = _texto_cabecalho_perfil(dados, forma, volume_l)

    if em_pdf:
        # Barra alinhada ao milimetrado; rótulos em cm do objeto.
        assert a_esc is not None and b_esc is not None
        L_real, n_seg, L_papel = _parametros_barra_escala_pdf(fator)
        # Barra na faixa inferior do milimetrado (padrão único de todos os PDF 2D).
        x_esc, y_esc = _posicao_escala_canto_folha(folha_w, L_papel)
        _desenhar_barra_escala(
            ax,
            x_direita=x_esc,
            y_base=y_esc,
            comprimento_eixos=L_papel,
            comprimento_real_cm=L_real,
            n_segmentos=n_seg,
            fontweight="bold",
            razao_escala=b_esc,
        )
        ax._folha_escala = (  # type: ignore[attr-defined]
            f"{a_esc}:{b_esc} ({_fmt_marca_escala(L_real)} cm)"
        )
    else:
        # Tela / PNG: só cotas (sem barra de escala — o tamanho na tela não é físico).
        _aplicar_cabecalho(fig, titulo, em_pdf=False)

    ax._folha_tamanho = (folha_w, folha_h)  # type: ignore[attr-defined]
    ax._perfil_modo = modo  # type: ignore[attr-defined]
    ax._perfil_titulo = titulo  # type: ignore[attr-defined]


def _desenhar_folha_publicacao(ax, largura: float, altura: float) -> None:
    """Folha A4 branca para figura de publicação (sem milimetrado)."""
    ax.set_facecolor("white")
    ax.set_xlim(0.0, largura)
    ax.set_ylim(0.0, altura)
    ax.set_aspect("equal", adjustable="box", anchor="C")
    ax.autoscale(enable=False)
    ax.axis("off")
    # Contorno ligeiramente para dentro para não ser cortado na exportação.
    m = 0.04
    ax.add_patch(
        Rectangle(
            (m, m),
            largura - 2.0 * m,
            altura - 2.0 * m,
            fill=False,
            edgecolor="#888888",
            linewidth=_LW_BORDA_FOLHA * 0.7,
            zorder=1,
        )
    )


def _pontilhado_exterior(
    ax,
    T,
    *,
    ox: float,
    y_perfil: np.ndarray,
    r_perfil: np.ndarray,
    y_borda: float,
    r_borda: float,
    b_elipse: float,
    semente: int,
    n_pontos: int = 900,
) -> None:
    """Pontilhado leve no flanco direito, sugerindo volume (estilo publicação)."""
    if y_perfil.size < 2:
        return
    rng = np.random.default_rng(int(semente) & 0xFFFFFFFF)
    y0 = float(y_perfil.min())
    y1 = float(y_perfil.max())
    if y1 - y0 < 1e-6:
        return
    ys = rng.uniform(y0, y1, size=n_pontos)
    rs = np.interp(ys, y_perfil, r_perfil)
    frac = rng.beta(2.2, 1.15, size=n_pontos)
    xs = ox + rs * frac
    peso_y = 0.35 + 0.65 * (1.0 - (ys - y0) / (y1 - y0))
    manter = rng.random(n_pontos) < (0.55 * peso_y * (0.4 + 0.6 * frac))
    xs, ys = xs[manter], ys[manter]
    if xs.size == 0:
        return
    # Não pontilhar dentro da elipse da borda.
    if r_borda > 1e-9 and b_elipse > 1e-9:
        fora = ((xs - ox) / r_borda) ** 2 + ((ys - y_borda) / b_elipse) ** 2 >= 0.98
        xs, ys = xs[fora], ys[fora]
    if xs.size == 0:
        return
    xp, yp = T(xs, ys)
    ax.plot(
        xp,
        yp,
        ",",
        color=_COR_PUBLICACAO,
        markersize=1.1,
        alpha=0.55,
        zorder=3,
    )


def _ponto_dentro_elipse_borda(
    x: float,
    y: float,
    *,
    ox: float,
    y_borda: float,
    r_borda: float,
    b_elipse: float,
    folga: float = 0.02,
) -> bool:
    if r_borda < 1e-9 or b_elipse < 1e-9:
        return False
    return ((x - ox) / r_borda) ** 2 + ((y - y_borda) / b_elipse) ** 2 < (1.0 - folga)


def _silhueta_fora_da_elipse(
    ox: float,
    y_perfil: np.ndarray,
    r_perfil: np.ndarray,
    *,
    y_borda: float,
    r_borda: float,
    b_elipse: float,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Contorno exterior da esquerda → base → direita, sem cruzar a elipse da borda.

    Em tigelas abertas o arco frontal da elipse desce pelo centro; o meridiano
    largo nessa faixa ficaria por cima da borda — daí o recorte. O corpo encontra
    a borda na interseção com o arco frontal e fecha nos extremos pelo arco da
    elipse. Devolve também os ângulos das junturas (para o arco frontal central).
    """
    y = np.asarray(y_perfil, dtype=float).ravel()
    r = np.asarray(r_perfil, dtype=float).ravel()
    if y.size < 2:
        return (
            np.array([ox - r_borda, ox + r_borda], dtype=float),
            np.array([y_borda, y_borda], dtype=float),
            float(np.pi),
            0.0,
        )

    def _cruzamento(sinal: float) -> tuple[float, float] | None:
        prev: tuple[float, float] | None = None
        for yi, ri in zip(y, r):
            xi = ox + sinal * float(ri)
            pt = (xi, float(yi))
            dentro = _ponto_dentro_elipse_borda(
                xi,
                float(yi),
                ox=ox,
                y_borda=y_borda,
                r_borda=r_borda,
                b_elipse=b_elipse,
                folga=0.0,
            )
            if dentro:
                if prev is None:
                    return None
                x0, y0 = prev
                x1, y1 = pt
                for _ in range(16):
                    xm, ym = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
                    if _ponto_dentro_elipse_borda(
                        xm,
                        ym,
                        ox=ox,
                        y_borda=y_borda,
                        r_borda=r_borda,
                        b_elipse=b_elipse,
                        folga=0.0,
                    ):
                        x1, y1 = xm, ym
                    else:
                        x0, y0 = xm, ym
                return (x0, y0)
            prev = pt
        return prev

    def _subir_ate_elipse(sinal: float) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for yi, ri in zip(y, r):
            xi = ox + sinal * float(ri)
            if _ponto_dentro_elipse_borda(
                xi,
                float(yi),
                ox=ox,
                y_borda=y_borda,
                r_borda=r_borda,
                b_elipse=b_elipse,
                folga=0.0,
            ):
                break
            pts.append((xi, float(yi)))
        cruz = _cruzamento(sinal)
        if cruz is not None:
            if not pts:
                pts.append(cruz)
            else:
                pts[-1] = cruz
        return pts

    esq = _subir_ate_elipse(-1.0)
    dir_ = _subir_ate_elipse(1.0)
    if not esq and not dir_:
        return (
            np.array([ox - r_borda, ox + r_borda], dtype=float),
            np.array([y_borda, y_borda], dtype=float),
            float(np.pi),
            0.0,
        )

    def _ang(p: tuple[float, float]) -> float:
        return float(
            np.arctan2(
                (p[1] - y_borda) / max(b_elipse, 1e-9),
                (p[0] - ox) / max(r_borda, 1e-9),
            )
        )

    def _arco(t0: float, t1: float, n: int = 12) -> list[tuple[float, float]]:
        dt = (t1 - t0 + np.pi) % (2.0 * np.pi) - np.pi
        if abs(dt) < 1e-9:
            return []
        ts = t0 + np.linspace(0.0, dt, max(n, 2))
        return [
            (
                ox + r_borda * float(np.cos(t)),
                y_borda + b_elipse * float(np.sin(t)),
            )
            for t in ts
        ]

    canto_e = (ox - r_borda, y_borda)
    canto_d = (ox + r_borda, y_borda)
    t_junc_e = _ang(esq[-1]) if esq else np.pi
    t_junc_d = _ang(dir_[-1]) if dir_ else 0.0
    # Fecha nos extremos pelo arco da elipse (sem cordão interior).
    if esq:
        arco_e = _arco(t_junc_e, np.pi)
        if arco_e:
            esq = esq + arco_e[1:]
            esq[-1] = canto_e
        else:
            esq[-1] = canto_e
    else:
        esq = [canto_e]
    if dir_:
        arco_d = _arco(t_junc_d, 0.0)
        if arco_d:
            dir_ = dir_ + arco_d[1:]
            dir_[-1] = canto_d
        else:
            dir_[-1] = canto_d
    else:
        dir_ = [canto_d]

    caminho: list[tuple[float, float]] = []
    caminho.extend(reversed(esq))
    if caminho and abs(caminho[-1][0] - dir_[0][0]) < 1e-9 and abs(
        caminho[-1][1] - dir_[0][1]
    ) < 1e-9:
        caminho.extend(dir_[1:])
    else:
        caminho.extend(dir_)
    xs = np.array([p[0] for p in caminho], dtype=float)
    ys = np.array([p[1] for p in caminho], dtype=float)
    return xs, ys, float(t_junc_e), float(t_junc_d)


def desenhar_elevacao_publicacao(
    ax,
    z,
    r,
    dados: dict[str, Any],
    *,
    forma: str = "",
    volume_l: float = 0.0,
    tipo_base: str = "Reta",
    modo: str = "tela",
) -> None:
    """Elevação ortográfica com elipse da borda (figura de publicação).

    Sem cotas numéricas: silhueta, borda (frente cheia / fundo tracejado),
    pontilhado suave e escala gráfica.
    — modo «tela»: coordenadas da peça; escala a 1 cm das bordas da vista.
    — modo «pdf»: folha A4 (inalterado face ao exporto já validado).
    """
    z_w, r_w, r_b, z_b = meridiano_com_base(z, r, tipo_base)
    ax.clear()
    fig = ax.figure
    if fig is not None:
        limpar_decoracao_figura(fig)
    em_pdf = modo == "pdf"
    titulo = _texto_cabecalho_perfil(dados, forma, volume_l)

    z0 = float(min(z_w.min(), z_b.min()))
    z1 = float(max(z_w.max(), z_b.max()))
    db = float(dados.get("db") or 0.0)
    dmax = float(dados.get("dmax") or 0.0)
    dbase = float(dados.get("dbase") or 0.0)
    r_borda = max(db / 2.0, float(r_w[-1]) if r_w.size else 0.0, 0.05)
    r_max = float(max(np.max(r_w), np.max(r_b), r_borda, dmax / 2.0, dbase / 2.0, 1.0))
    b_elipse = r_borda * _FATOR_ELIPSE_BORDA

    folga = 0.12
    margem_x = folga * (2.0 * r_max)
    margem_y = folga * max(float(z1 - z0) + 2.0 * b_elipse, 1.0)

    ox = margem_x + r_max
    oy = margem_y + max(0.0, -z0) + b_elipse * 0.15
    y_w = z_w - z0 + oy
    y_b = z_b - z0 + oy
    y_borda = float(y_w[-1]) if y_w.size else oy + float(z1 - z0)

    if r_b.size > 1 and float(np.max(r_b)) > 0.05:
        y_perfil = np.concatenate([y_b, y_w])
        r_perfil = np.concatenate([r_b, r_w])
    else:
        y_perfil = y_w
        r_perfil = np.asarray(r_w, dtype=float)

    x_lo = ox - r_max - margem_x
    x_hi = ox + r_max + margem_x
    y_lo = min(float(y_perfil.min()), float(y_b.min())) - margem_y * 0.25
    y_hi = y_borda + b_elipse + margem_y * 0.45
    cont_w = max(x_hi - x_lo, 1.0)
    cont_h = max(y_hi - y_lo, 1.0)
    folha_w, folha_h = _folha_orientacao(cont_w, cont_h)

    if em_pdf:
        ax_x0, ax_x1, ax_y0, ax_y1 = _area_desenho_pdf(folha_w, folha_h)
        util_w = max(ax_x1 - ax_x0, 1.0)
        util_h = max(ax_y1 - ax_y0, 1.0)
        fator = min(
            util_w * _FATOR_AREA_UTIL / cont_w,
            util_h * _FATOR_AREA_UTIL / cont_h,
        )
        fator = min(fator, _ESCALA_MAX_AMPLIACAO)
        fator, a_esc, b_esc = _fator_escala_pdf(fator)
        cx_real = 0.5 * (x_lo + x_hi)
        cy_real = 0.5 * (y_lo + y_hi)
        cx_papel = 0.5 * (ax_x0 + ax_x1)
        cy_papel = 0.5 * (ax_y0 + ax_y1)

        def T(x, y):
            xa = np.atleast_1d(np.asarray(x, dtype=float))
            ya = np.atleast_1d(np.asarray(y, dtype=float))
            if xa.size == 1 and ya.size > 1:
                xa = np.full_like(ya, xa[0])
            elif ya.size == 1 and xa.size > 1:
                ya = np.full_like(xa, ya[0])
            return _transformar_papel(
                xa,
                ya,
                cx_papel=cx_papel,
                cy_papel=cy_papel,
                cx_real=cx_real,
                cy_real=cy_real,
                fator=fator,
            )

        if fig is not None:
            fig.patch.set_facecolor("white")
            fig.subplots_adjust(**_MARGEM_FIGURA)
        _desenhar_folha_publicacao(ax, folha_w, folha_h)
        _desenhar_cabecalho_pdf(ax, folha_w, folha_h, titulo)
    else:
        # Tela Publicação: barra com tamanho visual fixo (padrão); números = cm do objeto.
        pad_x = max(0.55, 0.18 * r_max)
        pad_y = max(0.55, 0.12 * max(y_hi - y_lo, 1.0))
        meio = max(ox - x_lo, x_hi - ox) + pad_x
        if fig is not None:
            fig.patch.set_facecolor(_COR_FUNDO_TELA)
            fig.subplots_adjust(**_MARGEM_FIGURA_TELA)
        ax.set_facecolor(_COR_FUNDO_TELA)
        ax.set_xlim(ox - meio, ox + meio)
        ax.set_ylim(y_lo - pad_y, y_hi + pad_y)
        ax.set_aspect("equal", adjustable="box", anchor="C")
        ax.autoscale(enable=False)
        ax.axis("off")

        def T(x, y):
            xa = np.atleast_1d(np.asarray(x, dtype=float))
            ya = np.atleast_1d(np.asarray(y, dtype=float))
            if xa.size == 1 and ya.size > 1:
                xa = np.full_like(ya, xa[0])
            elif ya.size == 1 and xa.size > 1:
                ya = np.full_like(xa, ya[0])
            return xa, ya

    x_sil, y_sil, t_junc_e, t_junc_d = _silhueta_fora_da_elipse(
        ox,
        y_perfil,
        r_perfil,
        y_borda=y_borda,
        r_borda=r_borda,
        b_elipse=b_elipse,
    )
    xs, ys = T(x_sil, y_sil)
    ax.plot(
        xs,
        ys,
        color=_COR_PUBLICACAO,
        lw=_LW_PUB_PERFIL,
        solid_capstyle="butt",
        solid_joinstyle="miter",
        zorder=5,
    )

    t_fundo = np.linspace(0.0, np.pi, 91)
    xb, yb = T(
        ox + r_borda * np.cos(t_fundo),
        y_borda + b_elipse * np.sin(t_fundo),
    )
    ax.plot(
        xb,
        yb,
        color=_COR_PUBLICACAO,
        lw=_LW_PUB_TRACEJADO,
        ls=(0, (2.5, 2.0)),
        solid_capstyle="butt",
        zorder=4,
    )
    t0 = float(t_junc_e)
    t1 = float(t_junc_d)
    if t0 < 0:
        t0 += 2.0 * np.pi
    if t1 < 0:
        t1 += 2.0 * np.pi
    if t1 < t0:
        t1 += 2.0 * np.pi
    if not (t0 - 1e-6 <= 1.5 * np.pi <= t1 + 1e-6):
        t0, t1 = float(np.pi), 2.0 * np.pi
    t_frente = np.linspace(t0, t1, max(24, int(40 * (t1 - t0) / np.pi)))
    xf, yf = T(
        ox + r_borda * np.cos(t_frente),
        y_borda + b_elipse * np.sin(t_frente),
    )
    ax.plot(
        xf,
        yf,
        color=_COR_PUBLICACAO,
        lw=_LW_PUB_PERFIL,
        solid_capstyle="butt",
        zorder=6,
    )

    semente = (
        sum(ord(c) for c in str(dados.get("numero") or "x")) * 131
        + sum(ord(c) for c in str(dados.get("sitio") or "y")) * 17
        + 42
    )
    _pontilhado_exterior(
        ax,
        T,
        ox=ox,
        y_perfil=y_w,
        r_perfil=np.asarray(r_w, dtype=float),
        y_borda=y_borda,
        r_borda=r_borda,
        b_elipse=b_elipse,
        semente=semente,
    )

    if em_pdf:
        L_real, n_seg, L_papel = _parametros_barra_escala_pdf(fator)
        # PDF de publicação: posição já usada na folha (não misturar com o ajuste da tela).
        x_esc, y_esc = _posicao_escala_canto_folha(folha_w, L_papel)
        _desenhar_barra_escala(
            ax,
            x_direita=x_esc,
            y_base=y_esc,
            comprimento_eixos=L_papel,
            comprimento_real_cm=L_real,
            n_segmentos=n_seg,
            fontweight="bold",
            razao_escala=b_esc,
        )
        ax._folha_escala = (  # type: ignore[attr-defined]
            f"{a_esc}:{b_esc} ({_fmt_marca_escala(L_real)} cm)"
        )
    else:
        # Sempre no canto inferior direito da janela; tamanho visual fixo.
        _desenhar_barra_escala_canto_eixos(ax, fontweight="normal")
        _aplicar_cabecalho(fig, titulo, em_pdf=False)

    ax._folha_tamanho = (folha_w, folha_h)  # type: ignore[attr-defined]
    ax._perfil_modo = f"publicacao-{modo}"  # type: ignore[attr-defined]
    ax._perfil_titulo = titulo  # type: ignore[attr-defined]


def exportar_stl(caminho_arquivo: str, *args, **kwargs) -> bool:
    """Reexporta a malha 3D em STL (delega a vista_solido)."""
    from ceraform.vista_solido import exportar_stl as _exp

    return _exp(caminho_arquivo, *args, **kwargs)


def exportar_obj(caminho_arquivo: str, *args, **kwargs) -> bool:
    """Reexporta a malha 3D em OBJ (delega a vista_solido)."""
    from ceraform.vista_solido import exportar_obj as _exp

    return _exp(caminho_arquivo, *args, **kwargs)

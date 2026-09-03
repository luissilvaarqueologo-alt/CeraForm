# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import webbrowser
from pathlib import Path
from tkinter import filedialog, ttk
import tkinter as tk

from ceraform.classificar import classificar
from ceraform.constantes import (
    CONTORNOS_PLANTA,
    FORMAS,
    PERFIS_GEOMETRICOS,
    PERFIS_TRECHO,
    TIPOS_BASE,
)
from ceraform.db import BancoVasos, garantir_banco
from ceraform.caminhos import anotar_inicio, congelado, pasta_dados, pasta_recursos
from ceraform.perfil import (
    amostras_exceto_fracoes,
    diametros_fracao,
    pares_amostra,
    perfil_raios,
    pontos_meridiano,
    texto_amostras_gravadas,
)
from ceraform.relatorio import gravar_relatorio_html
from ceraform.ui_listas import montar_consulta, montar_relatorio
from ceraform import fonte
from ceraform.janela import aplicar_geometria, aviso, erro, mostrar_quando_pronta, sim_nao, centrar_janela
from ceraform.volume import capacidades_litros, rotulo_tamanho

RAIZ = pasta_recursos()
PASTA_DADOS = pasta_dados()
DOCUMENTACAO = RAIZ / "documentacao"
PDF_COMO_FUNCIONA = DOCUMENTACAO / "como_o_sistema_funciona.pdf"
SVG_ARQUITETURA = DOCUMENTACAO / "arquitetura_e_fluxo.svg"
HTML_ARQUITETURA = DOCUMENTACAO / "arquitetura_e_fluxo.html"
DRAWIO_ARQUITETURA = DOCUMENTACAO / "arquitetura_e_fluxo.drawio"
MD_HISTORICO = DOCUMENTACAO / "historico.md"
DB_PATH = garantir_banco(PASTA_DADOS, RAIZ)
_ALTURA_LOGO = 54
_TEXTO_RODAPE = (
    "Copyright (c) 2026 Cláudia Alves de Oliveira "
    "(Idealização e Metodologia Arqueológica) & "
    "Luís Antônio da Silva (Arquitetura e Desenvolvimento de Software)"
)
_CITACAO_ANTES = "OLIVEIRA, Cláudia Alves de; SILVA, Luís Antônio da. "
_CITACAO_NEGRITO = "CERAFORM"
_CITACAO_DEPOIS = (
    ": sistema computacional para reconstituição geométrica, "
    "modelagem morfológica e cálculo volumétrico de cerâmicas "
    "arqueológicas. Versão 1.0. Recife: [s. n.], 2026. "
    "Programa de computador. Python 3.11+, NumPy, SQLite, "
    "Matplotlib, PyVista/Plotly."
)
_CITACAO_SOFTWARE = _CITACAO_ANTES + _CITACAO_NEGRITO + _CITACAO_DEPOIS


def _v2d():
    """Matplotlib só entra quando o perfil 2D/PDF precisa — não na abertura."""
    from ceraform import visual_2d as m

    return m


def _caminho_logo_ceraform() -> Path | None:
    """Arquivo «Logo CeraForm.png» em Imagens/; fallback para o JPEG sem fundo."""
    pasta = RAIZ / "Imagens"
    for nome in (
        "Logo CeraForm.png",
        "Logo CeraForm sem fundo.png",
        "Logo CeraForm sem fundo.jpeg",
        "Logo CeraForm sem fundo.jpg",
    ):
        caminho = pasta / nome
        if caminho.is_file():
            return caminho
    if not pasta.is_dir():
        return None
    for arq in pasta.iterdir():
        if arq.suffix.lower() not in {".jpeg", ".jpg", ".png"}:
            continue
        stem = arq.stem.casefold()
        if "ceraform" in stem and "logo" in stem:
            return arq
    return None


def _rgba_sem_fundo_claro(im):
    """JPEG não tem transparência: o cinza-claro do fundo vira alfa 0."""
    rgba = im.convert("RGBA")
    pix = list(rgba.getdata())
    limpo = []
    for r, g, b, a in pix:
        if r >= 198 and g >= 198 and b >= 190 and abs(r - g) < 22 and abs(g - b) < 22:
            limpo.append((r, g, b, 0))
        else:
            limpo.append((r, g, b, a))
    rgba.putdata(limpo)
    return rgba


def _aparar_transparente(im, margem: int = 2):
    caixa = im.getbbox()
    if caixa is None:
        return im
    esq, topo, dir_, base = caixa
    esq = max(0, esq - margem)
    topo = max(0, topo - margem)
    dir_ = min(im.width, dir_ + margem)
    base = min(im.height, base + margem)
    return im.crop((esq, topo, dir_, base))


def _imagem_logo_cabecalho(caminho: Path, altura: int):
    """Vaso à esquerda e a palavra CeraForm à direita (mesma disposição do ARCHFORM)."""
    from PIL import Image

    with Image.open(caminho) as orig:
        rgb = orig.convert("RGB")
        lar, alt = rgb.size
        vaso = rgb.crop(
            (int(0.277 * lar), int(0.124 * alt), int(0.725 * lar), int(0.730 * alt))
        )
        nome = rgb.crop(
            (int(0.241 * lar), int(0.759 * alt), int(0.757 * lar), int(0.866 * alt))
        )
    vaso = _aparar_transparente(_rgba_sem_fundo_claro(vaso))
    nome = _aparar_transparente(_rgba_sem_fundo_claro(nome))
    vw = max(1, int(vaso.width * altura / max(1, vaso.height)))
    vaso = vaso.resize((vw, altura), Image.Resampling.LANCZOS)
    nh = max(22, int(altura * 0.52))
    nw = max(1, int(nome.width * nh / max(1, nome.height)))
    nome = nome.resize((nw, nh), Image.Resampling.LANCZOS)
    folga = max(8, int(altura * 0.14))
    canvas = Image.new("RGBA", (vw + folga + nw, altura), (0, 0, 0, 0))
    canvas.paste(vaso, (0, 0), vaso)
    canvas.paste(nome, (vw + folga, (altura - nh) // 2), nome)
    return canvas


def _imagem_icone_vaso(caminho: Path, lado: int = 32):
    """Recorte quadrado do vaso do logotipo, fundo transparente, para a barra de título."""
    from PIL import Image

    with Image.open(caminho) as orig:
        rgb = orig.convert("RGB")
        lar, alt = rgb.size
        vaso = rgb.crop(
            (int(0.277 * lar), int(0.124 * alt), int(0.725 * lar), int(0.730 * alt))
        )
    vaso = _aparar_transparente(_rgba_sem_fundo_claro(vaso))
    w, h = vaso.size
    m = max(w, h, 1)
    sq = Image.new("RGBA", (m, m), (0, 0, 0, 0))
    sq.paste(vaso, ((m - w) // 2, (m - h) // 2), vaso)
    return sq.resize((lado, lado), Image.Resampling.LANCZOS)


def _e_filete_cabecalho(ln: str) -> bool:
    """Linha de iguais (com BOM, NBSP ou espaços) vira filete, não texto."""
    t = "".join(ch for ch in ln.strip() if ch not in " \t\xa0\ufeff\u200b")
    return bool(t) and set(t) <= {"="}


def _linhas_cabecalho_windows(linhas: list[str]) -> list[str]:
    """No exe/Wine: tira caracteres ocultos e linhas em branco repetidas."""
    out: list[str] = []
    em_branco = False
    for ln in linhas:
        s = (
            ln.replace("\ufeff", "")
            .replace("\u200b", "")
            .replace("\xa0", " ")
            .rstrip()
        )
        if _e_filete_cabecalho(s):
            s = "=" * 8
        if not s.strip():
            if em_branco:
                continue
            em_branco = True
            out.append("")
            continue
        em_branco = False
        out.append(s)
    return out


def _texto_cabecalho() -> str:
    caminho = RAIZ / "CABECALHO.txt"
    try:
        bruto = caminho.read_bytes()
    except OSError:
        return "Não foi possível carregar o arquivo CABECALHO.txt."
    if not (congelado() or sys.platform == "win32"):
        texto = bruto.decode("utf-8-sig")
        linhas = [ln.replace("\ufeff", "").rstrip() for ln in texto.splitlines()]
        return "\n".join(linhas).strip()
    if bruto.startswith(b"\xff\xfe") or bruto.startswith(b"\xfe\xff"):
        texto = bruto.decode("utf-16")
    else:
        texto = bruto.decode("utf-8-sig", errors="replace")
    texto = (
        texto.replace("\ufeff", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u200b", "")
    )
    linhas = _linhas_cabecalho_windows([ln.rstrip() for ln in texto.split("\n")])
    return "\n".join(linhas).strip()


def _blocos_autoria_sobre() -> list[str | None]:
    """Parágrafos do Sobre; None marca um filete entre seções (sem linhas de iguais)."""
    blocos: list[str | None] = []
    atual: list[str] = []
    for ln in _texto_cabecalho().splitlines():
        if _e_filete_cabecalho(ln):
            if atual:
                blocos.append("\n".join(atual).strip())
                atual = []
            if blocos and blocos[-1] is not None:
                blocos.append(None)
            continue
        atual.append(ln)
    if atual:
        blocos.append("\n".join(atual).strip())
    while blocos and blocos[0] is None:
        blocos.pop(0)
    while blocos and blocos[-1] is None:
        blocos.pop()
    return blocos


def _texto_historico() -> str | None:
    """Corpo do histórico, sem o comentário de cabeçalho nem o título Markdown."""
    try:
        bruto = MD_HISTORICO.read_text(encoding="utf-8")
    except OSError:
        return None
    while True:
        i = bruto.find("<!--")
        j = bruto.find("-->", i)
        if i < 0 or j < 0:
            break
        bruto = bruto[:i] + bruto[j + 3 :]
    blocos: list[str] = []
    atual: list[str] = []
    for ln in bruto.splitlines():
        s = ln.strip()
        if s.startswith("#"):
            continue
        if s:
            atual.append(s)
            continue
        if atual:
            blocos.append(" ".join(atual))
            atual = []
    if atual:
        blocos.append(" ".join(atual))
    texto = "\n\n".join(blocos).strip()
    return texto or None


def _delta_roda(evt: tk.Event) -> tuple[int, int]:
    """Delta da roda: Windows/Wine (incluindo HIWORD) e X11 (num 4/5)."""
    n = int(getattr(evt, "num", 0) or 0)
    d = int(getattr(evt, "delta", 0) or 0)
    if abs(d) > 10000:
        d = (d >> 16) & 0xFFFF
        if d >= 0x8000:
            d -= 0x10000
    return d, n


def _rolar_texto(caixa: tk.Text, evt: tk.Event) -> str:
    """Linux usa Button-4/5; Windows/macOS/Wine usam MouseWheel."""
    d, n = _delta_roda(evt)
    try:
        if n == 4 or d > 0:
            caixa.yview_scroll(-3, "units")
        elif n == 5 or d < 0:
            caixa.yview_scroll(3, "units")
    except tk.TclError:
        pass
    return "break"


def _ligar_scroll_texto(caixa: tk.Text, *widgets: tk.Misc) -> None:
    def _roda(evt: tk.Event) -> str:
        return _rolar_texto(caixa, evt)

    for w in (caixa, *widgets):
        w.bind("<MouseWheel>", _roda)
        w.bind("<Button-4>", _roda)
        w.bind("<Button-5>", _roda)
        w.bind("<ButtonPress-4>", _roda)
        w.bind("<ButtonPress-5>", _roda)


def _abrir_desligado(comando: list[str]) -> bool:
    """Lança o visualizador fora do grupo do CeraForm, sem herdar o terminal."""
    try:
        subprocess.Popen(
            comando,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except OSError:
        return False


def _abrir_arquivo_sistema(caminho: Path) -> bool:
    """Abre um arquivo com o programa padrão do sistema operacional."""
    caminho = Path(caminho).resolve()
    uri = caminho.as_uri()
    if sys.platform == "win32":
        try:
            os.startfile(caminho)  # type: ignore[attr-defined]
            return True
        except OSError:
            pass
        try:
            if webbrowser.open(uri, new=2):
                return True
        except Exception:
            pass
        return _abrir_desligado(["cmd", "/c", "start", "", str(caminho)])
    if sys.platform == "darwin":
        return _abrir_desligado(["open", str(caminho)])
    xdg = shutil.which("xdg-open")
    if xdg:
        return _abrir_desligado([xdg, str(caminho)])
    try:
        return bool(webbrowser.open(uri, new=2))
    except Exception:
        return False


def _pdf_como_funciona_desatualizado() -> bool:
    """Verdadeiro se o Markdown ou o cabeçalho for mais recente que o PDF."""
    md = DOCUMENTACAO / "como_o_sistema_funciona.md"
    cab = RAIZ / "CABECALHO.txt"
    if not md.is_file():
        return False
    if not PDF_COMO_FUNCIONA.is_file():
        return True
    fontes = [md]
    if cab.is_file():
        fontes.append(cab)
    mais_novo = max(p.stat().st_mtime for p in fontes)
    return mais_novo > PDF_COMO_FUNCIONA.stat().st_mtime + 0.5


def _gerar_pdf_como_funciona() -> str | None:
    """Regenera o PDF a partir do Markdown. Devolve texto de erro ou None."""
    script = DOCUMENTACAO / "gerar_pdf_como_funciona.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(RAIZ),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return str(exc)
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout or "Falha ao gerar o PDF.")[:1200]
    return None


def _ligar_texto_somente_leitura(caixa: tk.Text) -> None:
    """Permite seleção e cópia; bloqueia edição."""

    def _ao_teclar(evt: tk.Event) -> str | None:
        if evt.state & 0x4 and evt.keysym.lower() in ("c", "a", "insert"):
            return None
        if evt.keysym in (
            "Left",
            "Right",
            "Up",
            "Down",
            "Home",
            "End",
            "Prior",
            "Next",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
        ):
            return None
        return "break"

    caixa.bind("<Key>", _ao_teclar)
    caixa.bind("<<Paste>>", lambda _e: "break")


def _f(texto: str) -> float:
    t = (texto or "").strip().replace(",", ".")
    if not t:
        return 0.0
    return round(float(t), 3)


def _texto_medida(val: float) -> str:
    """Formata medida para o campo: até 3 casas decimais, vírgula decimal."""
    arred = round(float(val), 3)
    if abs(arred) < 1e-12:
        return "0"
    if abs(arred - round(arred)) < 1e-9:
        return str(int(round(arred)))
    s = f"{arred:.3f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _texto_volume_resumo(volume_l: float, volume_90_l: float, volume_85_l: float) -> str:
    """100 %, depois 90 %, 85 % e tamanho relativo após travessão."""
    return (
        f"{volume_l:.3f} L (100 %)     "
        f"efetiva 90 %: {volume_90_l:.3f} L     "
        f"efetiva 85 %: {volume_85_l:.3f} L — {rotulo_tamanho(volume_l)}"
    )


_ROTULO_FICHA_3D = {
    "Número do desenho": "Nº do desenho",
    "Forma geométrica": "Forma",
    "Volume do objeto": "Volume Total",
    "Capacidade efetiva a 90 % da altura total": "Volume 90%",
    "Capacidade efetiva a 85 % da altura total": "Volume 85%",
    "Ponto de equilíbrio": "Ponto de Equilíbrio",
    "Diâmetro da borda": "Diâm. da borda",
    "Diâmetro da base": "Diâm. da base",
    "Maior diâmetro da peça": "Maior diâmetro",
    "Altura da base até o maior diâmetro": "Alt. até o maior diâm.",
    "Diâmetro da cintura": "Diâm. da cintura",
    "Espessura da parede": "Espessura",
    "Junção bojo–pescoço": "Junção bojo–pescoço",
}


def _rotulo_ficha_3d(rotulo: str) -> str:
    return _ROTULO_FICHA_3D.get(rotulo, rotulo)


_FONTES_SERIF_REGULAR = (
    "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/times.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
)
_FONTES_SERIF_NEGRITO = (
    "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/timesbd.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
)


def _truetype_serif(caminhos: tuple[str, ...], tamanho: int):
    """Times (ou Liberation Serif), a mesma família da tela."""
    from PIL import ImageFont

    for caminho in caminhos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def _largura_texto_png(font, texto: str) -> float:
    s = str(texto or "")
    if not s:
        return 0.0
    try:
        return float(font.getlength(s))
    except AttributeError:
        caixa = font.getbbox(s)
        return float(caixa[2] - caixa[0])


def _envolver_texto_png(texto: str, font, max_px: float) -> list[str]:
    """Quebra o valor para caber na coluna, como o rótulo na tela."""
    s = str(texto or "").strip()
    if not s:
        return [""]
    limite = max(float(max_px), 8.0)
    if _largura_texto_png(font, s) <= limite:
        return [s]

    def _partir_palavra(palavra: str) -> list[str]:
        if _largura_texto_png(font, palavra) <= limite:
            return [palavra]
        partes: list[str] = []
        atual = ""
        for ch in palavra:
            tentativa = atual + ch
            if atual and _largura_texto_png(font, tentativa) > limite:
                partes.append(atual)
                atual = ch
            else:
                atual = tentativa
        if atual:
            partes.append(atual)
        return partes or [palavra]

    linhas: list[str] = []
    atual = ""
    for palavra in s.split():
        pedacos = _partir_palavra(palavra)
        for pedaco in pedacos:
            tentativa = pedaco if not atual else f"{atual} {pedaco}"
            if atual and _largura_texto_png(font, tentativa) > limite:
                linhas.append(atual)
                atual = pedaco
            else:
                atual = tentativa
    if atual:
        linhas.append(atual)
    return linhas or [s]


class AppVasos(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        anotar_inicio("2 janela Tk criada")
        self.withdraw()
        fonte.aplicar_fonte(self)
        self.title("Reconstituição geométrica de cerâmicas — CeraForm")
        aplicar_geometria(self)
        if sys.platform == "win32":
            self.after_idle(self._aplicar_icone_janela)
        else:
            self._aplicar_icone_janela()
        anotar_inicio("3 geometria e fonte")
        self.banco = BancoVasos(DB_PATH)
        self.id_atual: int | None = None
        self._job_preview: str | None = None
        self._job_3d: str | None = None
        self._silencio = False
        self._cb_apos_salvar = None
        self._tela_atual = "cadastro"
        self.vista3d = None
        self._ficha: dict | None = None
        self._celulas_dados: list = []
        self._lbl_nota_dados: ttk.Label | None = None
        self.fig2 = None
        self.ax2 = None
        self.canvas_2d = None
        self._job_resize_2d: str | None = None
        self._job_ajuste_2d: str | None = None
        self._tam_2d: tuple[int, int] | None = None
        self._2d_pronto = False
        self._3d_pronto = False
        self._col_dados_3d = None
        self._consulta_pronta = False
        self._relatorio_pronto = False
        self._sobre_pronto = False
        self._canvas_sobre: tk.Canvas | None = None
        self._caixa_sobre: tk.Text | None = None
        self._evs_sobre: list[str] = []
        self._icone_janela = None
        self._jan_historico: tk.Toplevel | None = None
        self.var_modo_2d = tk.StringVar(value="corte")
        self.logo_ceraform_img: tk.PhotoImage | None = None
        self._lbl_rodape: ttk.Label | None = None

        self.var_sitio = tk.StringVar()
        self.var_numero = tk.StringVar()
        self.var_h = tk.StringVar()
        self.var_db = tk.StringVar()
        self.var_dmax = tk.StringVar()
        self.var_hmax = tk.StringVar()
        self.var_dbase = tk.StringVar()
        self.var_dmeio = tk.StringVar()
        self.var_esp = tk.StringVar()
        self.var_comp = tk.StringVar()
        self.var_larg = tk.StringVar()
        self.var_contorno = tk.StringVar(value="")
        self.var_tipo_base = tk.StringVar(value="")
        self.var_perfil = tk.StringVar(value="")
        self.var_perfil_base = tk.StringVar(value="")
        self.var_perfil_borda = tk.StringVar(value="")
        self.var_h_juncao = tk.StringVar()
        self.var_d_juncao = tk.StringVar()
        self.var_h_carena = tk.StringVar()
        self.var_d_carena = tk.StringVar()
        self.var_h_carena2 = tk.StringVar()
        self.var_d_carena2 = tk.StringVar()
        self.var_d_14 = tk.StringVar()
        self.var_d_12 = tk.StringVar()
        self.var_d_34 = tk.StringVar()
        self._amostras_outras: list[tuple[float, float]] = []
        self.var_forma_sug = tk.StringVar(value="")
        self.var_forma_sec_sug = tk.StringVar(value="")
        self.var_forma = tk.StringVar(value="")
        self.var_forma_sec = tk.StringVar(value="")
        self.var_aprox = tk.StringVar(value="")
        self.var_volume = tk.StringVar(value="")

        self._montar()
        self.protocol("WM_DELETE_WINDOW", self._sair)
        mostrar_quando_pronta(self)
        anotar_inicio("4 cadastro visível")
        if sys.platform != "win32":
            self.after(400, self._aquecer_matplotlib)
        else:
            self.after(800, self._importar_matplotlib_fundo)

    def _aplicar_icone_janela(self) -> None:
        """Troca a pena padrão do Tk pelo logotipo do CeraForm na barra de título.

        O Windows (e o Wine) alinham o título à esquerda; isso é da barra do
        sistema, não dá para centrar. O ícone .ico também entra no executável.
        """
        ico = RAIZ / "Imagens" / "ceraform.ico"
        png = _caminho_logo_ceraform()
        if sys.platform == "win32" and ico.is_file():
            try:
                self.iconbitmap(default=str(ico))
            except tk.TclError:
                try:
                    self.iconbitmap(str(ico))
                except tk.TclError:
                    pass
        origem = png if png is not None and png.is_file() else None
        if origem is None:
            return
        try:
            from PIL import ImageTk

            im = _imagem_icone_vaso(origem, 32)
            self._icone_janela = ImageTk.PhotoImage(im)
            self.iconphoto(True, self._icone_janela)
        except Exception:
            pass

    def _montar(self) -> None:
        self.corpo = ttk.Frame(self)
        self.corpo.pack(fill=tk.BOTH, expand=True)
        self.corpo.rowconfigure(0, weight=1)
        self.corpo.columnconfigure(0, weight=1)
        self.frm_cadastro = ttk.Frame(self.corpo)
        self.frm_consulta = ttk.Frame(self.corpo)
        self.frm_relatorio = ttk.Frame(self.corpo)
        self.frm_2d = ttk.Frame(self.corpo)
        self.frm_3d = ttk.Frame(self.corpo)
        self.frm_sobre = ttk.Frame(self.corpo)
        self._telas = {
            "cadastro": self.frm_cadastro,
            "consulta": self.frm_consulta,
            "relatorio": self.frm_relatorio,
            "2d": self.frm_2d,
            "3d": self.frm_3d,
            "sobre": self.frm_sobre,
        }
        self._montar_cadastro()
        self.frm_cadastro.grid(row=0, column=0, sticky="nsew")
        self._tela_atual = "cadastro"

    def _montar_cabecalho(self, parent: tk.Misc) -> ttk.Frame:
        cab = ttk.Frame(parent, padding=(10, 6, 10, 6))
        linha = ttk.Frame(cab)
        linha.pack(anchor="center")

        caminho_logo = _caminho_logo_ceraform()
        if caminho_logo is not None:
            try:
                from PIL import ImageTk

                composto = _imagem_logo_cabecalho(caminho_logo, _ALTURA_LOGO)
                self.logo_ceraform_img = ImageTk.PhotoImage(composto)
                ttk.Label(linha, image=self.logo_ceraform_img).pack(side=tk.LEFT)
            except Exception:
                self.logo_ceraform_img = None
        if self.logo_ceraform_img is None:
            ttk.Label(
                linha,
                text="CeraForm",
                font=(fonte.FAMILIA, 16, "bold"),
                foreground="#6A2D15",
            ).pack(side=tk.LEFT)
        return cab

    def _montar_rodape(self, parent: tk.Misc) -> ttk.Frame:
        rod = ttk.Frame(parent, padding=(10, 0))
        self._lbl_rodape = ttk.Label(
            rod,
            text=_TEXTO_RODAPE,
            font=(fonte.FAMILIA, 9),
            foreground="#4a4540",
            anchor="w",
            justify="left",
        )
        self._lbl_rodape.pack(fill=tk.X)
        ttk.Separator(rod, orient="horizontal").pack(fill=tk.X, pady=(2, 0))
        rod.bind("<Configure>", self._ajustar_largura_rodape)
        return rod

    def _ajustar_largura_rodape(self, _evt: object | None = None) -> None:
        if self._lbl_rodape is None:
            return
        largura = self._lbl_rodape.master.winfo_width()
        if largura > 40:
            self._lbl_rodape.configure(wraplength=max(200, largura - 16))

    def _montar_autoria_canvas(self, corpo: ttk.Frame) -> None:
        """Linux: quadro com filetes; a roda do X11 chega no Canvas."""
        holder = tk.Frame(
            corpo,
            bg="#ffffff",
            highlightbackground="#c8c0b8",
            highlightthickness=1,
            bd=0,
        )
        holder.grid(row=1, column=0, sticky="ew")
        holder.columnconfigure(0, weight=1)

        canvas = tk.Canvas(
            holder,
            bg="#ffffff",
            highlightthickness=0,
            bd=0,
            height=416,
        )
        rolagem = tk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=rolagem.set)
        canvas.grid(row=0, column=0, sticky="ew")
        rolagem.grid(row=0, column=1, sticky="ns")

        inner = tk.Frame(canvas, bg="#ffffff")
        janela_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        tk.Frame(inner, bg="#ffffff", height=8, bd=0).pack(fill=tk.X)
        self._lbls_sobre: list[tk.Label] = []
        for bloco in _blocos_autoria_sobre():
            if bloco is None:
                tk.Frame(inner, bg="#c8c0b8", height=1, bd=0).pack(
                    fill=tk.X, padx=10, pady=(8, 8)
                )
                continue
            lbl = tk.Label(
                inner,
                text=bloco,
                bg="#ffffff",
                fg="#1a1512",
                font=fonte.FONTE,
                justify="left",
                anchor="w",
                wraplength=900,
            )
            lbl.pack(fill=tk.X, padx=10, pady=(0, 2))
            self._lbls_sobre.append(lbl)
        tk.Frame(inner, bg="#ffffff", height=8, bd=0).pack(fill=tk.X)

        def _rolar_sobre(evt: tk.Event) -> str | None:
            d, n = _delta_roda(evt)
            if n == 4 or d > 0:
                canvas.yview_scroll(-3, "units")
            elif n == 5 or d < 0:
                canvas.yview_scroll(3, "units")
            return "break"

        def _ligar_roda(w: tk.Misc) -> None:
            w.bind("<MouseWheel>", _rolar_sobre)
            w.bind("<Button-4>", _rolar_sobre)
            w.bind("<Button-5>", _rolar_sobre)
            for filho in w.winfo_children():
                _ligar_roda(filho)

        def _sync_inner(_evt: tk.Event | None = None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _largura_sobre(evt: tk.Event) -> None:
            if evt.widget is not canvas or evt.width < 80:
                return
            canvas.itemconfigure(janela_id, width=evt.width)
            larg = max(evt.width - 20, 360)
            for lbl in self._lbls_sobre:
                lbl.configure(wraplength=larg)

        inner.bind("<Configure>", _sync_inner)
        canvas.bind("<Configure>", _largura_sobre)
        _ligar_roda(holder)
        self._canvas_sobre = canvas

    def _montar_autoria_texto(self, corpo: ttk.Frame) -> None:
        """Windows/Wine: Text nativo, o mesmo tipo que já rola no Histórico."""
        painel = ttk.Frame(corpo)
        painel.grid(row=1, column=0, sticky="ew")
        painel.columnconfigure(0, weight=1)
        caixa = tk.Text(
            painel,
            wrap=tk.WORD,
            width=1,
            height=19,
            font=fonte.FONTE,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#c8c0b8",
            padx=12,
            pady=8,
            spacing1=0,
            spacing2=0,
            spacing3=2,
            takefocus=True,
        )
        rolagem = tk.Scrollbar(painel, orient="vertical", command=caixa.yview)
        caixa.configure(yscrollcommand=rolagem.set)
        caixa.grid(row=0, column=0, sticky="ew")
        rolagem.grid(row=0, column=1, sticky="ns")
        caixa.tag_configure("filete", foreground="#c8c0b8", spacing1=8, spacing3=0)
        for bloco in _blocos_autoria_sobre():
            if bloco is None:
                caixa.insert("end", "─" * 72 + "\n", "filete")
                continue
            caixa.insert("end", bloco.strip() + "\n")
        _ligar_texto_somente_leitura(caixa)
        _ligar_scroll_texto(caixa, painel, corpo, self.frm_sobre, rolagem)
        self._caixa_sobre = caixa

    def _montar_sobre(self) -> None:
        self.frm_sobre.rowconfigure(0, weight=1)
        self.frm_sobre.columnconfigure(0, weight=1)

        corpo = ttk.Frame(self.frm_sobre, padding=(12, 10))
        corpo.grid(row=0, column=0, sticky="nsew")
        corpo.columnconfigure(0, weight=1)

        ttk.Label(
            corpo,
            text="Autoria, termos de uso e referência bibliográfica",
            font=fonte.FONTE_NEGRITO,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        if sys.platform == "win32":
            self._montar_autoria_texto(corpo)
        else:
            self._montar_autoria_canvas(corpo)

        ref = ttk.LabelFrame(
            corpo,
            text="Como referenciar este aplicativo",
            padding=(8, 6),
        )
        ref.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ref.columnconfigure(0, weight=1)

        citacao = tk.Text(
            ref,
            wrap=tk.WORD,
            font=fonte.FONTE,
            height=4,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#c8c0b8",
            padx=8,
            pady=4,
        )
        citacao.grid(row=0, column=0, sticky="ew")
        citacao.insert("1.0", _CITACAO_SOFTWARE)
        citacao.tag_configure("titulo_abnt", font=fonte.FONTE_NEGRITO)
        i0 = len(_CITACAO_ANTES)
        i1 = i0 + len(_CITACAO_NEGRITO)
        citacao.tag_add("titulo_abnt", f"1.{i0}", f"1.{i1}")
        _ligar_texto_somente_leitura(citacao)

        ttk.Button(ref, text="Copiar referência", command=self._copiar_citacao).grid(
            row=1, column=0, sticky="e", pady=(6, 0)
        )

        barra = ttk.Frame(self.frm_sobre, padding=(8, 6))
        barra.grid(row=1, column=0, sticky="ew")
        tk.Button(
            barra,
            text="Como funciona",
            command=self._abrir_como_funciona,
            bg="#1B7A3D",
            fg="white",
            activebackground="#166533",
            activeforeground="white",
            font=fonte.FONTE,
            padx=12,
            pady=2,
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            barra,
            text="Arquitetura e fluxo",
            command=self._abrir_arquitetura,
            bg="#1B7A3D",
            fg="white",
            activebackground="#166533",
            activeforeground="white",
            font=fonte.FONTE,
            padx=12,
            pady=2,
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            barra,
            text="Histórico",
            command=self._abrir_historico,
            bg="#1B7A3D",
            fg="white",
            activebackground="#166533",
            activeforeground="white",
            font=fonte.FONTE,
            padx=12,
            pady=2,
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            barra,
            text="Fechar",
            command=lambda: self._mostrar_tela("cadastro"),
            bg="#B42318",
            fg="white",
            activebackground="#8F1B13",
            activeforeground="white",
            font=fonte.FONTE,
            padx=12,
            pady=2,
        ).pack(side=tk.RIGHT, padx=4)

    def _copiar_citacao(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(_CITACAO_SOFTWARE)
        self.update_idletasks()

    def _montar_cadastro(self) -> None:
        self._montar_cabecalho(self.frm_cadastro).pack(side=tk.TOP, fill=tk.X)

        barra = ttk.Frame(self.frm_cadastro, padding=(8, 6))
        barra.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(
            barra,
            text="Salvar",
            command=self._salvar,
            bg="#1B7A3D",
            fg="white",
            activebackground="#166533",
            activeforeground="white",
            font=fonte.FONTE,
            padx=12,
            pady=2,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(barra, text="Consulta", command=self._abrir_consulta).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(barra, text="Perfil 2D", command=self._abrir_2d).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(barra, text="Desenho 3D", command=self._abrir_3d).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(barra, text="Relatório", command=self._abrir_relatorio).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(
            barra,
            text="Sair",
            command=self._sair,
            bg="#B42318",
            fg="white",
            activebackground="#8F1B13",
            activeforeground="white",
            font=fonte.FONTE,
            padx=12,
            pady=2,
        ).pack(side=tk.RIGHT, padx=4)
        ttk.Button(barra, text="Ajuda", command=self._abrir_ajuda).pack(
            side=tk.RIGHT, padx=4
        )
        ttk.Button(barra, text="Sobre", command=self._abrir_sobre).pack(
            side=tk.RIGHT, padx=4
        )

        if sys.platform != "win32":
            self._montar_rodape(self.frm_cadastro).pack(side=tk.BOTTOM, fill=tk.X)

        area = ttk.Frame(self.frm_cadastro)
        area.pack(fill=tk.BOTH, expand=True)
        self.form = ttk.Frame(area, padding=6)
        self.form.pack(fill=tk.BOTH, expand=True)

        bloco_a = ttk.LabelFrame(
            self.form,
            text="A — Dados básicos (mínimo para o cálculo)",
            padding=6,
        )
        bloco_a.pack(fill=tk.X, pady=(0, 6))
        for c in (1, 3, 5):
            bloco_a.columnconfigure(c, weight=1)
        self._entrada(bloco_a, "Nome do sítio (obrigatório)", self.var_sitio, 0, 0, span=3)
        self._entrada(
            bloco_a,
            "Número do desenho (obrigatório)",
            self.var_numero,
            0,
            2,
            largura=20,
            filtro=self._filtro_numero_desenho,
        )
        self._entrada(bloco_a, "Altura total (cm)", self.var_h, 1, 0, largura=7)
        self._entrada(bloco_a, "Diâmetro da borda (cm)", self.var_db, 1, 1, largura=7)
        self._entrada(bloco_a, "Diâmetro da base (cm)", self.var_dbase, 1, 2, largura=7)
        self._entrada(
            bloco_a, "Maior diâmetro da peça (cm)", self.var_dmax, 2, 0, largura=7
        )
        self._entrada(
            bloco_a,
            "Altura da base até o maior diâmetro (cm)",
            self.var_hmax,
            2,
            1,
            largura=7,
        )
        self._combo(
            bloco_a,
            "Tipo de base (obrigatório)",
            self.var_tipo_base,
            TIPOS_BASE,
            3,
            0,
        )
        self.cmb_perfil = self._combo(
            bloco_a,
            "Perfil geométrico (obrigatório)",
            self.var_perfil,
            PERFIS_GEOMETRICOS,
            3,
            1,
            largura=24,
        )

        bloco_b = ttk.LabelFrame(self.form, text="B — Resultados da peça", padding=6)
        bloco_b.pack(fill=tk.X, pady=(0, 6))
        for c in (1, 3):
            bloco_b.columnconfigure(c, weight=1)
        ttk.Label(bloco_b, text="Sugestão Forma Principal").grid(
            row=0, column=0, sticky="w", pady=2, padx=(0, 6)
        )
        ttk.Label(bloco_b, textvariable=self.var_forma_sug, foreground="#1a56db").grid(
            row=0, column=1, sticky="w", padx=(0, 10), pady=2
        )
        self.cmb_forma = self._combo(bloco_b, "Forma confirmada", self.var_forma, FORMAS, 0, 1)
        self.lbl_sug_sec = ttk.Label(bloco_b, text="Sugestão Forma Secundária")
        self.val_sug_sec = ttk.Label(bloco_b, textvariable=self.var_forma_sec_sug)
        self.lbl_sug_sec.grid(row=1, column=0, sticky="w", pady=2, padx=(0, 6))
        self.val_sug_sec.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=2)
        self.lbl_forma_sec = ttk.Label(bloco_b, text="Segunda forma confirmada")
        self.cmb_forma_sec = ttk.Combobox(
            bloco_b,
            textvariable=self.var_forma_sec,
            values=("",) + FORMAS,
            state="readonly",
            width=max(len(str(v)) for v in FORMAS) + 3,
        )
        self.lbl_forma_sec.grid(row=1, column=2, sticky="w", pady=2, padx=(0, 6))
        self.cmb_forma_sec.grid(row=1, column=3, sticky="w", pady=2, padx=(0, 10))
        self.cmb_forma_sec.bind(
            "<<ComboboxSelected>>", lambda _e: self._atualizar_preview()
        )
        self.lbl_aprox = ttk.Label(
            bloco_b, textvariable=self.var_aprox, wraplength=960
        )
        ttk.Label(bloco_b, text="Volume do objeto em (L):").grid(
            row=2, column=0, sticky="w", pady=(4, 0)
        )
        ttk.Label(bloco_b, textvariable=self.var_volume).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=(4, 0)
        )
        ttk.Label(
            bloco_b,
            text="Sugestões de Forma - corrija se a forma observada for outra",
            foreground="#1a56db",
        ).grid(row=2, column=2, columnspan=2, sticky="w", pady=(4, 0), padx=(0, 6))

        bloco_c = ttk.LabelFrame(self.form, text="C — Informações adicionais", padding=6)
        bloco_c.pack(fill=tk.X, pady=(0, 6))
        self._entrada(
            bloco_c,
            "Diâmetro da cintura (cm)",
            self.var_dmeio,
            0,
            0,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            bloco_c,
            "Espessura da parede (cm)",
            self.var_esp,
            0,
            1,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._combo(
            bloco_c, "Contorno (vista de cima)", self.var_contorno, CONTORNOS_PLANTA, 1, 0
        )
        self._entrada(
            bloco_c,
            "Comprimento (vista de cima) (cm)",
            self.var_comp,
            2,
            0,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            bloco_c,
            "Largura (vista de cima) (cm)",
            self.var_larg,
            2,
            1,
            largura=7,
            filtro=self._filtro_medida,
        )
        self.lbl_ajuda_composto = ttk.Label(
            bloco_c,
            text=(
                "Trechos do perfil composto: perfil do bojo (junto à base) "
                "e do pescoço (junto à borda)."
            ),
            foreground="#4b5563",
        )
        self.lbl_ajuda_composto.grid(
            row=3, column=0, columnspan=6, sticky="w", pady=(4, 2)
        )
        self.cmb_perfil_base = self._combo(
            bloco_c,
            "Perfil do trecho junto à base",
            self.var_perfil_base,
            PERFIS_TRECHO,
            4,
            0,
        )
        self.cmb_perfil_borda = self._combo(
            bloco_c,
            "Perfil do trecho junto à borda",
            self.var_perfil_borda,
            PERFIS_TRECHO,
            4,
            1,
        )
        self._entrada(
            bloco_c,
            "Altura da junção bojo–pescoço (cm)",
            self.var_h_juncao,
            5,
            0,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            bloco_c,
            "Diâmetro da junção bojo–pescoço (cm)",
            self.var_d_juncao,
            5,
            1,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            bloco_c,
            "Altura da carena (cm)",
            self.var_h_carena,
            6,
            0,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            bloco_c,
            "Diâmetro da carena (cm)",
            self.var_d_carena,
            6,
            1,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            bloco_c,
            "Altura da segunda quebra (cm)",
            self.var_h_carena2,
            7,
            0,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            bloco_c,
            "Diâmetro da segunda quebra (cm)",
            self.var_d_carena2,
            7,
            1,
            largura=7,
            filtro=self._filtro_medida,
        )
        linha_ex = ttk.Frame(bloco_c)
        linha_ex.grid(row=8, column=0, columnspan=6, sticky="w", pady=(4, 0))
        ttk.Label(linha_ex, text="Medições extras:").pack(
            side=tk.LEFT, padx=(0, 12), pady=2
        )
        frm_ex = ttk.Frame(linha_ex)
        frm_ex.pack(side=tk.LEFT)
        self._entrada(
            frm_ex,
            "1/4 da altura (cm)",
            self.var_d_14,
            0,
            0,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            frm_ex,
            "1/2 da altura (cm)",
            self.var_d_12,
            0,
            1,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._entrada(
            frm_ex,
            "3/4 da altura (cm)",
            self.var_d_34,
            0,
            2,
            largura=7,
            filtro=self._filtro_medida,
        )
        self._sincronizar_composto()

    def _entrada(
        self,
        parent: tk.Misc,
        rotulo: str,
        var: tk.StringVar,
        row: int,
        col: int = 0,
        span: int = 1,
        largura: int = 14,
        filtro=None,
    ) -> ttk.Entry:
        c0 = col * 2
        ttk.Label(parent, text=rotulo).grid(
            row=row, column=c0, sticky="w", pady=2, padx=(0, 6)
        )
        ent = ttk.Entry(parent, textvariable=var, width=largura)
        ent.grid(
            row=row,
            column=c0 + 1,
            columnspan=span,
            sticky="w" if largura <= 8 else "ew",
            pady=2,
            padx=(0, 8),
        )
        if filtro is not None:
            vcmd = (self.register(filtro), "%P")
            ent.configure(validate="key", validatecommand=vcmd)
        elif largura <= 8:
            vcmd = (self.register(self._filtro_medida), "%P")
            ent.configure(validate="key", validatecommand=vcmd)
        if filtro is self._filtro_medida or (filtro is None and largura <= 8):
            ent.bind(
                "<FocusOut>",
                lambda _e, v=var: self._normalizar_var_medida(v),
            )
        var.trace_add("write", self._agendar_preview)
        return ent

    def _normalizar_var_medida(self, var: tk.StringVar) -> None:
        t = var.get().strip()
        if not t:
            return
        try:
            var.set(_texto_medida(_f(t)))
        except ValueError:
            pass

    def _filtro_numero_desenho(self, proposto: str) -> bool:
        if len(proposto) > 20:
            return False
        return all(ch.isalnum() or ch in ".-/" for ch in proposto)

    def _filtro_medida(self, proposto: str) -> bool:
        if len(proposto) > 12:
            return False
        if proposto in ("", "-", ".", ",", "-.", "-,"):
            return True
        if proposto.count("-") > 1 or ("-" in proposto and not proposto.startswith("-")):
            return False
        if not all(ch.isdigit() or ch in ".,-" for ch in proposto):
            return False
        sep = "," if "," in proposto else ("." if "." in proposto else None)
        if sep:
            _inteiro, fracao = proposto.split(sep, 1)
            if len(fracao) > 3:
                return False
            corpo = proposto.replace(",", ".", 1)
            if corpo.count(".") > 1:
                return False
        return True

    def _combo(
        self,
        parent: tk.Misc,
        rotulo: str,
        var: tk.StringVar,
        valores: tuple,
        row: int,
        col: int = 0,
        span: int = 1,
        largura: int | None = None,
    ) -> ttk.Combobox:
        c0 = col * 2
        ttk.Label(parent, text=rotulo).grid(row=row, column=c0, sticky="w", pady=2, padx=(0, 6))
        visiveis = tuple(v for v in valores if str(v).strip())
        opcoes = ("",) + visiveis
        nmax = max((len(str(v)) for v in visiveis), default=12)
        combo = ttk.Combobox(
            parent,
            textvariable=var,
            values=opcoes,
            state="readonly",
            width=largura if largura is not None else max(nmax + 6, 20),
        )
        combo.grid(
            row=row, column=c0 + 1, columnspan=span, sticky="w", pady=2, padx=(0, 10)
        )
        combo.bind("<<ComboboxSelected>>", lambda _e: self._atualizar_preview())
        return combo

    def _sincronizar_composto(self) -> None:
        if not hasattr(self, "cmb_perfil_base"):
            return
        ativo = self.var_perfil.get() == "Composto"
        estado = "readonly" if ativo else "disabled"
        for w in (self.cmb_perfil_base, self.cmb_perfil_borda):
            w.configure(state=estado)
        secundarios = (
            self.lbl_sug_sec,
            self.val_sug_sec,
            self.lbl_forma_sec,
            self.cmb_forma_sec,
        )
        for w in secundarios:
            if ativo:
                w.grid()
            else:
                w.grid_remove()
        if not ativo:
            self.var_forma_sec.set("")
            self.var_forma_sec_sug.set("")

    def _preencher_caixa_dados(self, ficha: dict | None) -> None:
        self._ficha = ficha
        if not getattr(self, "_celulas_dados", None):
            return
        celulas = list((ficha or {}).get("celulas") or [])
        nota = str((ficha or {}).get("nota") or "")
        for i, (cap, val) in enumerate(self._celulas_dados):
            if i < len(celulas):
                rotulo, valor = celulas[i]
                if rotulo == "Ponto de equilíbrio":
                    valor = valor.replace(" acima do apoio", "")
                cap.configure(text=_rotulo_ficha_3d(rotulo))
                val.configure(text=valor)
                cap.grid()
                val.grid()
            else:
                cap.configure(text="")
                val.configure(text="")
                cap.grid_remove()
                val.grid_remove()
        if self._lbl_nota_dados is not None:
            self._lbl_nota_dados.configure(text=nota)

    def _ler_formulario(self) -> dict:
        dados = {
            "sitio": self.var_sitio.get().strip(),
            "numero": self.var_numero.get().strip(),
            "h": _f(self.var_h.get()),
            "db": _f(self.var_db.get()),
            "dmax": _f(self.var_dmax.get()),
            "hmax": _f(self.var_hmax.get()),
            "dbase": _f(self.var_dbase.get()),
            "dmeio": _f(self.var_dmeio.get()),
            "espessura_parede": _f(self.var_esp.get()),
            "largura": _f(self.var_comp.get()),
            "profundidade": _f(self.var_larg.get()),
            "contorno_planta": self.var_contorno.get().strip(),
            "tipo_base": self.var_tipo_base.get().strip(),
            "perfil_geometrico": self.var_perfil.get().strip(),
            "perfil_trecho_base": self.var_perfil_base.get().strip(),
            "perfil_trecho_borda": self.var_perfil_borda.get().strip(),
            "altura_juncao": _f(self.var_h_juncao.get()),
            "diametro_juncao": _f(self.var_d_juncao.get()),
            "altura_carena": _f(self.var_h_carena.get()),
            "diametro_carena": _f(self.var_d_carena.get()),
            "altura_carena2": _f(self.var_h_carena2.get()),
            "diametro_carena2": _f(self.var_d_carena2.get()),
            "d_14": _f(self.var_d_14.get()),
            "d_12": _f(self.var_d_12.get()),
            "d_34": _f(self.var_d_34.get()),
            "geratriz": "",
        }
        dados["amostras"] = texto_amostras_gravadas(
            dados["h"],
            dados["d_14"],
            dados["d_12"],
            dados["d_34"],
            getattr(self, "_amostras_outras", []),
        )
        return dados

    def _escalas_planta(self, d: dict) -> tuple[float, float]:
        rmax = max(d["dmax"] / 2.0, 1e-6)
        comp, larg = d["largura"], d["profundidade"]
        if (d["contorno_planta"] or "Circular") in (
            "Oval",
            "Quadrangular",
            "Assimétrico",
        ) and comp > 0 and larg > 0:
            return (comp / 2.0) / rmax, (larg / 2.0) / rmax
        return 1.0, 1.0

    def _perfil_atual(self, d: dict):
        amostras = pares_amostra(d.get("amostras", ""))
        z, r = perfil_raios(
            h=max(d["h"], 0.1),
            db=max(d["db"], 0.05),
            dmax=max(d["dmax"], 0.05),
            hmax=d["hmax"] if d["hmax"] > 0 else max(d["h"], 0.1) / 2,
            dbase=max(float(d["dbase"]), 0.0),
            dmeio=d["dmeio"],
            perfil_geometrico=d["perfil_geometrico"],
            perfil_trecho_base=d["perfil_trecho_base"],
            perfil_trecho_borda=d["perfil_trecho_borda"],
            amostras=amostras,
            altura_carena=d["altura_carena"],
            diametro_carena=d["diametro_carena"],
            altura_carena2=d["altura_carena2"],
            diametro_carena2=d["diametro_carena2"],
            altura_juncao=d["altura_juncao"],
            diametro_juncao=d["diametro_juncao"],
            tipo_base=d.get("tipo_base") or "Reta",
        )
        return z, r, amostras

    def _formulario_pronto_para_geometria(self, d: dict | None = None) -> bool:
        dados = d if d is not None else self._ler_formulario()
        if dados["h"] <= 0 or dados["dmax"] <= 0:
            return False
        if not dados["tipo_base"] or not dados["perfil_geometrico"]:
            return False
        if dados["perfil_geometrico"] == "Composto" and (
            not dados["perfil_trecho_base"] or not dados["perfil_trecho_borda"]
        ):
            return False
        return True

    def _geometria_atual(self):
        d = self._ler_formulario()
        if not self._formulario_pronto_para_geometria(d):
            raise ValueError("cadastro incompleto para a reconstituição")
        res = classificar(
            h=d["h"],
            db=d["db"],
            dmax=d["dmax"],
            hmax=d["hmax"],
            dbase=d["dbase"],
            dmeio=d["dmeio"],
            largura=d["largura"],
            profundidade=d["profundidade"],
            perfil_geometrico=d["perfil_geometrico"],
            perfil_trecho_base=d["perfil_trecho_base"],
            perfil_trecho_borda=d["perfil_trecho_borda"],
            contorno_planta=d["contorno_planta"],
            altura_carena=d["altura_carena"],
            diametro_carena=d["diametro_carena"],
            altura_carena2=d["altura_carena2"],
            diametro_carena2=d["diametro_carena2"],
            n_amostras=len(pares_amostra(d["amostras"])),
            altura_juncao=d["altura_juncao"],
            diametro_juncao=d["diametro_juncao"],
        )
        z, r, _am = self._perfil_atual(d)
        sx, sy = self._escalas_planta(d)
        caps = capacidades_litros(
            z,
            r,
            d["h"],
            rx_scale=sx,
            ry_scale=sy,
            tipo_planta=d.get("contorno_planta") or "Circular",
        )
        vol = caps["volume_transbordamento"]
        d["volume_l"] = vol
        d["volume_85_l"] = caps["capacidade_efetiva_85"]
        d["volume_90_l"] = caps["capacidade_efetiva_90"]
        d["_sx"], d["_sy"] = sx, sy
        titulo = self.var_forma.get() or res.forma
        if res.aproximacao:
            titulo += " (aproximação)"
        z_cm, ficha = _v2d().resumo_peca(z, r, d, titulo)
        pts = pontos_meridiano(z, r, d.get("tipo_base") or "Reta", rx_scale=sx)
        sy_rel = (sy / sx) if sx else 1.0
        return d, res, z, r, pts, z_cm, sy_rel, ficha

    def _agendar_preview(self, *_a: object) -> None:
        if self._silencio:
            return
        if self._job_preview is not None:
            self.after_cancel(self._job_preview)
        self._job_preview = self.after(180, self._atualizar_preview)

    def _atualizar_preview(self) -> None:
        self._job_preview = None
        self._sincronizar_composto()
        d0 = self._ler_formulario()
        if not self._formulario_pronto_para_geometria(d0):
            self.var_forma_sug.set("")
            self.var_forma_sec_sug.set("")
            self.var_volume.set("")
            self.var_aprox.set("")
            self.lbl_aprox.grid_remove()
            if self.id_atual is None:
                self.var_forma.set("")
            self._preencher_caixa_dados(None)
            if self.ax2 is not None and self.canvas_2d is not None:
                self.ax2.clear()
                self.ax2.set_axis_off()
                self.canvas_2d.draw_idle()
            return
        try:
            d, res, z, r, pts, z_cm, sy_rel, ficha = self._geometria_atual()
        except ValueError:
            return
        self.var_forma_sug.set(res.forma)
        if d["perfil_geometrico"] == "Composto":
            self.var_forma_sec_sug.set(res.forma_secundaria or "")
        if self.id_atual is None:
            self.var_forma.set(res.forma)
        if res.aproximacao:
            self.var_aprox.set(res.observacao)
            self.lbl_aprox.grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))
        else:
            self.var_aprox.set("")
            self.lbl_aprox.grid_remove()
        self.var_volume.set(
            _texto_volume_resumo(d["volume_l"], d["volume_90_l"], d["volume_85_l"])
        )
        self._preencher_caixa_dados(ficha)
        if self._tela_atual == "2d" and self.ax2 is not None and self.canvas_2d is not None:
            self._redesenhar_2d(d, res, z, r)
        if self.vista3d is not None and self._tela_atual == "3d":
            self._agendar_redesenho_3d(
                pts,
                z_cm,
                sy_rel,
                float(d.get("espessura_parede") or 0),
                str(d.get("contorno_planta") or "Circular"),
            )

    def _agendar_redesenho_3d(
        self,
        pts,
        z_cm: float,
        sy_rel: float,
        espessura: float,
        planta: str,
    ) -> None:
        if self._job_3d is not None:
            self.after_cancel(self._job_3d)
        self._job_3d = self.after(
            220,
            lambda: self._redesenhar_3d(pts, z_cm, sy_rel, espessura, planta),
        )

    def _redesenhar_3d(
        self,
        pts,
        z_cm: float,
        sy_rel: float,
        espessura: float,
        planta: str,
    ) -> None:
        self._job_3d = None
        if self.vista3d is None or self._tela_atual != "3d":
            return
        try:
            self.vista3d.mostrar(
                pts,
                z_cm,
                sy_rel,
                espessura=espessura,
                planta=planta,
            )
        except tk.TclError:
            self.vista3d = None

    def _importar_matplotlib_fundo(self) -> None:
        """No Windows, importa o Matplotlib depois da tela útil, sem travar o cadastro."""
        import threading

        def _carga() -> None:
            try:
                import matplotlib.figure  # noqa: F401
                import matplotlib.backends.backend_agg  # noqa: F401
            except Exception:
                pass

        threading.Thread(target=_carga, daemon=True, name="mpl-fundo").start()

    def _ligar_scroll_sobre_win(self, ligar: bool) -> None:
        caixa = self._caixa_sobre
        if ligar and caixa is not None:
            try:
                caixa.focus_set()
            except tk.TclError:
                pass

    def _mostrar_tela(self, nome: str) -> None:
        if nome == "sobre":
            self._garantir_sobre()
        elif nome == "consulta":
            self._garantir_consulta()
        elif nome == "relatorio":
            self._garantir_relatorio()
        elif nome == "2d":
            self._garantir_2d()
        elif nome == "3d":
            self._garantir_3d()
        frm = self._telas[nome]
        frm.grid(row=0, column=0, sticky="nsew")
        frm.tkraise()
        if sys.platform == "win32" and nome == "cadastro":
            self.after_idle(self._repintar_blocos_cadastro)
        self._tela_atual = nome
        self._ligar_scroll_sobre_win(False)
        if self.vista3d is not None:
            self.vista3d.definir_ativa(nome == "3d")
        if nome == "sobre":
            self._ligar_scroll_sobre_win(True)
        titulos = {
            "cadastro": "Reconstituição geométrica de cerâmicas — CeraForm",
            "consulta": "Consulta",
            "relatorio": "Relatório por sítio",
            "2d": "Perfil 2D — reconstituição geométrica",
            "3d": "Desenho 3D — reconstituição geométrica",
            "sobre": "Sobre o sistema",
        }
        self.title(titulos.get(nome, titulos["cadastro"]))
        if nome == "2d":
            self.after_idle(self._atualizar_preview)
        elif nome == "3d":
            self.after_idle(self._atualizar_preview)
            if self.vista3d is not None:
                try:
                    self.vista3d.rotulo.focus_set()
                except tk.TclError:
                    pass
        elif nome == "consulta":
            atual = getattr(self, "_consulta_atualizar", None)
            if atual is not None:
                atual()
        elif nome == "relatorio":
            atual = getattr(self, "_relatorio_atualizar", None)
            if atual is not None:
                atual()

    def _repintar_blocos_cadastro(self) -> None:
        """Windows: o tema ttk some com a borda de baixo do LabelFrame ao voltar da Consulta."""
        if not hasattr(self, "form"):
            return
        try:
            self.form.update_idletasks()
            for filho in self.form.winfo_children():
                if str(filho.winfo_class()) == "TLabelframe":
                    filho.configure(text=filho.cget("text"))
        except tk.TclError:
            pass

    def _garantir_sobre(self) -> None:
        if self._sobre_pronto:
            return
        self._montar_sobre()
        self._sobre_pronto = True

    def _garantir_consulta(self) -> None:
        if self._consulta_pronta:
            return
        montar_consulta(self, self.frm_consulta)
        self._consulta_pronta = True

    def _garantir_relatorio(self) -> None:
        if self._relatorio_pronto:
            return
        montar_relatorio(self, self.frm_relatorio)
        self._relatorio_pronto = True

    def _abrir_3d(self) -> None:
        self._mostrar_tela("3d")

    def _garantir_3d(self) -> None:
        if self._3d_pronto:
            return
        jan = self.frm_3d
        barra = ttk.Frame(jan, padding=(8, 6))
        barra.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(barra, text="PNG", command=self._png).pack(side=tk.LEFT, padx=4)
        ttk.Button(barra, text="STL", command=self._stl).pack(side=tk.LEFT, padx=4)
        ttk.Button(barra, text="OBJ", command=self._obj).pack(side=tk.LEFT, padx=4)
        ttk.Button(barra, text="PLY", command=self._ply).pack(side=tk.LEFT, padx=4)
        ttk.Button(barra, text="Fechar", command=lambda: self._mostrar_tela("cadastro")).pack(
            side=tk.RIGHT, padx=4
        )
        ttk.Button(barra, text="Ajuda", command=self._abrir_ajuda).pack(
            side=tk.RIGHT, padx=4
        )

        corpo = ttk.Frame(jan)
        corpo.pack(fill=tk.BOTH, expand=True)

        col_dados = ttk.Frame(corpo, width=420)
        col_dados.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 4), pady=4)
        col_dados.pack_propagate(False)
        self._col_dados_3d = col_dados

        info = ttk.LabelFrame(col_dados, text="Dados do objeto", padding=(8, 6))
        info.pack(fill=tk.BOTH, expand=True)

        ficha_fnt = fonte.FONTE
        ficha_neg = fonte.FONTE_NEGRITO
        grelha = ttk.Frame(info)
        grelha.pack(fill=tk.BOTH, expand=True)
        grelha.columnconfigure(1, weight=1)
        self._celulas_dados = []
        for i in range(24):
            cap = ttk.Label(grelha, text="", foreground="#6b6358", font=ficha_fnt)
            val = ttk.Label(
                grelha,
                text="",
                foreground="#1a1512",
                font=ficha_neg,
            )
            cap.grid(row=i, column=0, sticky="w", pady=3, padx=(0, 12))
            val.grid(row=i, column=1, sticky="w", pady=3)
            self._celulas_dados.append((cap, val))
            cap.grid_remove()
            val.grid_remove()
        self._lbl_nota_dados = ttk.Label(
            info,
            text="",
            foreground="#4a4038",
            wraplength=390,
            justify="left",
            font=ficha_fnt,
        )
        self._lbl_nota_dados.pack(fill=tk.X, side=tk.BOTTOM, pady=(6, 0))

        def _largura_nota(evt: tk.Event) -> None:
            if self._lbl_nota_dados is None:
                return
            if evt.widget is info and evt.width > 80:
                self._lbl_nota_dados.configure(wraplength=max(evt.width - 24, 180))

        info.bind("<Configure>", _largura_nota)

        from ceraform.vista_solido import VistaSolido

        self.vista3d = VistaSolido(corpo)
        self.vista3d.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4), pady=4)
        if sys.platform == "win32":
            texto_dica = (
                "Arraste para girar. Teclas + e − para ampliar e reduzir."
            )
        else:
            texto_dica = (
                "Arraste para girar. Roda do mouse ou teclas + e − "
                "para ampliar e reduzir."
            )
        dica = tk.Label(
            self.vista3d,
            text=texto_dica,
            fg="#d4c4b0",
            bg="#2b2b2b",
            font=fonte.FONTE,
        )
        dica.place(relx=1.0, rely=1.0, anchor="se", x=-8, y=-4)
        dica.bind("<MouseWheel>", self.vista3d._roda)
        dica.bind("<Button-4>", self.vista3d._roda)
        dica.bind("<Button-5>", self.vista3d._roda)
        self._3d_pronto = True
        if self._ficha:
            self._preencher_caixa_dados(self._ficha)

    def _fechar_3d(self) -> None:
        if self.vista3d is not None:
            try:
                self.vista3d.fechar()
            except Exception:
                pass
        self.vista3d = None
        self._celulas_dados = []
        self._lbl_nota_dados = None
        self._col_dados_3d = None
        self._3d_pronto = False

    def _sincronizar_tamanho_fig2(self) -> None:
        if self.fig2 is None or self.ax2 is None or self.canvas_2d is None:
            return
        _v2d().ajustar_figura_tela(self.fig2, self.ax2)

    def _ajuste_folha_tardio_2d(self) -> None:
        self._job_ajuste_2d = None
        if self._tela_atual != "2d":
            return
        self._sincronizar_tamanho_fig2()
        if self.canvas_2d is not None:
            self.canvas_2d.draw_idle()

    def _agendar_ajuste_folha_2d(self) -> None:
        if self._job_ajuste_2d is not None:
            self.after_cancel(self._job_ajuste_2d)
        self._job_ajuste_2d = self.after(150, self._ajuste_folha_tardio_2d)

    def _sincronizar_e_desenhar_2d(self) -> None:
        self._job_resize_2d = None
        self._sincronizar_tamanho_fig2()
        if self.canvas_2d is not None:
            self.canvas_2d.draw_idle()

    def _ao_redimensionar_2d(self, evt: tk.Event) -> None:
        if self._tela_atual != "2d":
            return
        if self.canvas_2d is None or evt.widget is not self.canvas_2d.get_tk_widget():
            return
        tam = (int(evt.width), int(evt.height))
        if tam == self._tam_2d:
            return
        self._tam_2d = tam
        if self._job_resize_2d is not None:
            self.after_cancel(self._job_resize_2d)
        self._job_resize_2d = self.after(180, self._sincronizar_e_desenhar_2d)

    def _redesenhar_2d(self, d: dict, res, z, r) -> None:
        if self.ax2 is None or self.canvas_2d is None:
            return
        kwargs = {
            "forma": self.var_forma.get() or res.forma,
            "volume_l": float(d.get("volume_l") or 0.0),
            "tipo_base": d.get("tipo_base") or "Reta",
            "modo": "tela",
        }
        v = _v2d()
        if self.var_modo_2d.get() == "publicacao":
            v.desenhar_elevacao_publicacao(self.ax2, z, r, d, **kwargs)
        else:
            v.desenhar_perfil_completo(
                self.ax2,
                z,
                r,
                d,
                espessura=d["espessura_parede"],
                **kwargs,
            )
        v.ajustar_figura_tela(self.fig2, self.ax2)
        self.canvas_2d.draw_idle()
        self._agendar_ajuste_folha_2d()

    def _ao_mudar_modo_2d(self) -> None:
        pub = self.var_modo_2d.get() == "publicacao"
        btn = getattr(self, "_btn_pdf_2d", None)
        if btn is not None:
            if pub:
                btn.state(["disabled"])
            else:
                btn.state(["!disabled"])
        try:
            d, res, z, r, *_resto = self._geometria_atual()
        except ValueError:
            return
        self._redesenhar_2d(d, res, z, r)

    def _abrir_2d(self) -> None:
        self._mostrar_tela("2d")

    def _garantir_2d(self) -> None:
        if self._2d_pronto:
            return
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        fonte.aplicar_matplotlib()
        jan = self.frm_2d
        barra = ttk.Frame(jan, padding=(8, 6))
        barra.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Radiobutton(
            barra,
            text="Corte técnico",
            variable=self.var_modo_2d,
            value="corte",
            command=self._ao_mudar_modo_2d,
        ).pack(side=tk.LEFT, padx=(4, 2))
        ttk.Radiobutton(
            barra,
            text="Publicação",
            variable=self.var_modo_2d,
            value="publicacao",
            command=self._ao_mudar_modo_2d,
        ).pack(side=tk.LEFT, padx=(2, 10))
        self._btn_pdf_2d = ttk.Button(barra, text="PDF", command=self._pdf_2d)
        self._btn_pdf_2d.pack(side=tk.LEFT, padx=4)
        ttk.Button(barra, text="PNG da tela", command=self._png_2d).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(barra, text="Fechar", command=lambda: self._mostrar_tela("cadastro")).pack(
            side=tk.RIGHT, padx=4
        )
        ttk.Button(barra, text="Ajuda", command=self._abrir_ajuda).pack(
            side=tk.RIGHT, padx=4
        )
        v = _v2d()
        self.fig2 = Figure(
            figsize=(11.0, 7.8), dpi=v._FOLHA_DPI_TELA, facecolor=v._COR_FUNDO_TELA
        )
        self.fig2.subplots_adjust(**v._MARGEM_FIGURA)
        self.ax2 = self.fig2.add_subplot(111)
        self.canvas_2d = FigureCanvasTkAgg(self.fig2, master=jan)
        wid = self.canvas_2d.get_tk_widget()
        wid.pack(fill=tk.BOTH, expand=True)
        wid.bind("<Configure>", self._ao_redimensionar_2d)
        wid.bind("<Map>", lambda _evt: self._agendar_ajuste_folha_2d())
        self._2d_pronto = True

    def _fechar_2d(self) -> None:
        self.fig2 = None
        self.ax2 = None
        self.canvas_2d = None
        self._2d_pronto = False

    def _aquecer_matplotlib(self) -> None:
        """Primeira carga do Matplotlib fora do clique em Perfil 2D."""
        try:
            fonte.aplicar_matplotlib()
            from matplotlib.figure import Figure

            Figure(figsize=(1.0, 1.0))
        except Exception:
            pass

    def _abrir_consulta(self) -> None:
        self._mostrar_tela("consulta")

    def _abrir_relatorio(self) -> None:
        self._mostrar_tela("relatorio")

    def _abrir_sobre(self) -> None:
        self._mostrar_tela("sobre")

    def _abrir_ajuda(self) -> None:
        caminho = RAIZ / "ajuda" / "index.html"
        if not caminho.is_file():
            aviso(
                self,
                "Ajuda",
                "Não encontrei as páginas de ajuda neste diretório.",
            )
            return
        if not _abrir_arquivo_sistema(caminho):
            aviso(
                self,
                "Ajuda",
                "Não foi possível abrir a ajuda no navegador.\n\n"
                "Instale um navegador web (Firefox, Chrome ou Edge) e tente "
                "novamente.",
            )

    def _abrir_como_funciona(self) -> None:
        if _pdf_como_funciona_desatualizado():
            try:
                self.config(cursor="watch")
                self.update_idletasks()
                erro_geracao = _gerar_pdf_como_funciona()
            finally:
                self.config(cursor="")
            if erro_geracao and not PDF_COMO_FUNCIONA.is_file():
                aviso(
                    self,
                    "Como funciona",
                    "Não foi possível gerar o PDF a partir do texto atual.\n\n"
                    + erro_geracao,
                )
                return
            if erro_geracao:
                aviso(
                    self,
                    "Como funciona",
                    "O texto em Markdown é mais recente, mas o PDF não pôde "
                    "ser gerado de novo. Vou abrir o PDF que já existe.\n\n"
                    + erro_geracao,
                )
        if not PDF_COMO_FUNCIONA.is_file():
            aviso(
                self,
                "Como funciona",
                "Não encontrei o documento PDF neste diretório.\n\n"
                f"Esperado: {PDF_COMO_FUNCIONA.name} dentro da pasta "
                f"«{DOCUMENTACAO.name}».",
            )
            return
        if not _abrir_arquivo_sistema(PDF_COMO_FUNCIONA):
            aviso(
                self,
                "Como funciona",
                "Não foi possível abrir o documento PDF.\n\n"
                "Instale um visualizador de PDF (por exemplo, Evince, Okular ou "
                "Adobe Reader) ou use um navegador que exiba PDF e tente "
                "novamente.\n\n"
                "Se o arquivo já estava aberto, feche essa janela e volte a "
                "abrir: alguns visualizadores não recarregam o PDF sozinhos.",
            )

    def _abrir_arquitetura(self) -> None:
        if HTML_ARQUITETURA.is_file():
            caminho = HTML_ARQUITETURA
        elif SVG_ARQUITETURA.is_file():
            caminho = SVG_ARQUITETURA
        else:
            caminho = DRAWIO_ARQUITETURA
        if not caminho.is_file():
            aviso(
                self,
                "Arquitetura e fluxo",
                "Não encontrei o desenho neste diretório.\n\n"
                f"Esperado: {HTML_ARQUITETURA.name} (ou "
                f"{SVG_ARQUITETURA.name}) dentro da pasta "
                f"«{DOCUMENTACAO.name}».",
            )
            return
        if not _abrir_arquivo_sistema(caminho):
            aviso(
                self,
                "Arquitetura e fluxo",
                "Não foi possível abrir o desenho da arquitetura.\n\n"
                "Use um navegador (Firefox, Chrome ou Edge) para abrir o "
                f"arquivo {caminho.name} na pasta «{DOCUMENTACAO.name}».",
            )

    def _abrir_historico(self) -> None:
        texto = _texto_historico()
        if not texto:
            aviso(
                self,
                "Histórico",
                "Não encontrei o texto do histórico neste diretório.\n\n"
                f"Esperado: {MD_HISTORICO.name} dentro da pasta "
                f"«{DOCUMENTACAO.name}».",
            )
            return
        jan = self._jan_historico
        if jan is not None:
            try:
                if jan.winfo_exists():
                    jan.destroy()
            except tk.TclError:
                pass
            self._jan_historico = None

        jan = tk.Toplevel(self)
        jan.withdraw()
        jan.title("Histórico")
        jan.minsize(480, 360)
        jan.transient(self)
        w, h = 840, 640

        def _ao_fechar(_evt: object | None = None) -> None:
            self._jan_historico = None
            try:
                jan.destroy()
            except tk.TclError:
                pass

        barra = ttk.Frame(jan, padding=(8, 6))
        barra.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(
            barra,
            text="Fechar",
            command=_ao_fechar,
            bg="#B42318",
            fg="white",
            activebackground="#8F1B13",
            activeforeground="white",
            font=fonte.FONTE,
            padx=12,
            pady=2,
        ).pack(side=tk.RIGHT, padx=4)

        corpo = ttk.Frame(jan, padding=(12, 10))
        corpo.pack(fill=tk.BOTH, expand=True)
        corpo.rowconfigure(1, weight=1)
        corpo.columnconfigure(0, weight=1)

        ttk.Label(
            corpo,
            text="Histórico do CeraForm",
            font=fonte.FONTE_NEGRITO,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        painel = ttk.Frame(corpo)
        painel.grid(row=1, column=0, sticky="nsew")
        painel.rowconfigure(0, weight=1)
        painel.columnconfigure(0, weight=1)

        caixa = tk.Text(
            painel,
            wrap=tk.WORD,
            width=1,
            height=1,
            font=fonte.FONTE,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#c8c0b8",
            padx=12,
            pady=8,
            spacing1=0,
            spacing2=0,
            spacing3=0,
            takefocus=True,
        )
        rolagem = tk.Scrollbar(painel, orient="vertical", command=caixa.yview)
        caixa.configure(yscrollcommand=rolagem.set)
        caixa.grid(row=0, column=0, sticky="nsew")
        rolagem.grid(row=0, column=1, sticky="ns")
        caixa.insert("1.0", texto)
        _ligar_texto_somente_leitura(caixa)
        _ligar_scroll_texto(caixa, painel, corpo, jan, rolagem)
        jan.protocol("WM_DELETE_WINDOW", _ao_fechar)
        jan.bind("<Escape>", _ao_fechar)
        self._jan_historico = jan
        centrar_janela(jan, self, w, h)
        jan.deiconify()
        jan.lift()

        def _repor_centro(_evt: object | None = None) -> None:
            try:
                if jan.winfo_exists():
                    centrar_janela(jan, self, w, h)
            except tk.TclError:
                pass

        jan.after(40, _repor_centro)
        jan.focus_set()

    def _novo(self) -> None:
        self.id_atual = None
        self._silencio = True
        self.var_sitio.set("")
        self.var_numero.set("")
        self.var_h.set("")
        self.var_db.set("")
        self.var_dmax.set("")
        self.var_hmax.set("")
        self.var_dbase.set("")
        for v in (
            self.var_dmeio,
            self.var_esp,
            self.var_comp,
            self.var_larg,
            self.var_h_juncao,
            self.var_d_juncao,
            self.var_h_carena,
            self.var_d_carena,
            self.var_h_carena2,
            self.var_d_carena2,
            self.var_d_14,
            self.var_d_12,
            self.var_d_34,
        ):
            v.set("")
        self._amostras_outras = []
        self.var_contorno.set("")
        self.var_tipo_base.set("")
        self.var_perfil.set("")
        self.var_perfil_base.set("")
        self.var_perfil_borda.set("")
        self.var_forma.set("")
        self.var_forma_sec.set("")
        self.var_forma_sug.set("")
        self.var_forma_sec_sug.set("")
        self.var_volume.set("")
        self.var_aprox.set("")
        self.lbl_aprox.grid_remove()
        self._silencio = False
        self._atualizar_preview()

    def _salvar(self) -> None:
        d = self._ler_formulario()
        if not d["sitio"]:
            aviso(
                self,
                "Cadastro",
                "Informe o nome do sítio. Este campo é obrigatório.",
            )
            return
        if not d["numero"]:
            aviso(
                self,
                "Cadastro",
                "Informe o número do desenho. Este campo é obrigatório.",
            )
            return
        if not self._filtro_numero_desenho(d["numero"]):
            aviso(self,
                "Cadastro",
                "O número do desenho tem no máximo 20 caracteres e aceita "
                "algarismos, letras, ponto, hífen e barra.",
            )
            return
        if not d["tipo_base"]:
            aviso(
                self,
                "Cadastro",
                "Informe o tipo de base. Este campo é obrigatório.",
            )
            return
        if not d["perfil_geometrico"]:
            aviso(
                self,
                "Cadastro",
                "Informe o perfil geométrico. Este campo é obrigatório.",
            )
            return
        if d["perfil_geometrico"] == "Composto" and (
            not d["perfil_trecho_base"] or not d["perfil_trecho_borda"]
        ):
            aviso(
                self,
                "Cadastro",
                "Com perfil geométrico composto, informe o perfil do trecho "
                "junto à base e o perfil do trecho junto à borda.",
            )
            return
        if min(d["h"], d["db"], d["dmax"], d["hmax"]) <= 0:
            aviso(
                self,
                "Cadastro",
                "Informe as medidas mínimas: altura total, diâmetro da borda, "
                "maior diâmetro da peça e altura da base até o maior diâmetro.",
            )
            return
        if d["dbase"] < 0:
            aviso(
                self,
                "Cadastro",
                "O diâmetro da base não pode ser negativo. "
                "Use 0 cm quando a base for convexa arredondada "
                "(reconstituição sem anel determinado).",
            )
            return
        z, r, amostras = self._perfil_atual(d)
        res = classificar(
            h=d["h"],
            db=d["db"],
            dmax=d["dmax"],
            hmax=d["hmax"],
            dbase=d["dbase"],
            dmeio=d["dmeio"],
            largura=d["largura"],
            profundidade=d["profundidade"],
            perfil_geometrico=d["perfil_geometrico"],
            perfil_trecho_base=d["perfil_trecho_base"],
            perfil_trecho_borda=d["perfil_trecho_borda"],
            contorno_planta=d["contorno_planta"],
            altura_carena=d["altura_carena"],
            diametro_carena=d["diametro_carena"],
            altura_carena2=d["altura_carena2"],
            diametro_carena2=d["diametro_carena2"],
            n_amostras=len(amostras),
            altura_juncao=d["altura_juncao"],
            diametro_juncao=d["diametro_juncao"],
        )
        d["forma"] = res.forma
        d["forma_secundaria"] = res.forma_secundaria
        d["forma_confirmada"] = self.var_forma.get() or res.forma
        d["forma_secundaria_confirmada"] = self.var_forma_sec.get()
        d["forma_alterada_manualmente"] = int(
            (d["forma_confirmada"] or "") != (res.forma or "")
            or (d["forma_secundaria_confirmada"] or "") != (res.forma_secundaria or "")
        )
        d["aproximacao"] = 1 if res.aproximacao else 0
        sx, sy = self._escalas_planta(d)
        caps = capacidades_litros(
            z,
            r,
            d["h"],
            rx_scale=sx,
            ry_scale=sy,
            tipo_planta=d.get("contorno_planta") or "Circular",
        )
        d["volume_l"] = caps["volume_transbordamento"]
        d["volume_85_l"] = caps["capacidade_efetiva_85"]
        d["volume_90_l"] = caps["capacidade_efetiva_90"]
        id_gravar = self.id_atual
        if id_gravar is not None:
            atual = self.banco.obter(id_gravar)
            if atual is not None and (
                atual["sitio"] != d["sitio"] or atual["numero"] != d["numero"]
            ):
                id_gravar = None
        try:
            self.id_atual = self.banco.salvar(d, id_gravar)
        except sqlite3.IntegrityError:
            erro(self,
                "Cadastro",
                "Já existe objeto com este nome do sítio e número do desenho.",
            )
            return
        aviso(self,"Cadastro", "Objeto gravado.")
        cb = self._cb_apos_salvar
        self._cb_apos_salvar = None
        self._novo()
        if cb is not None:
            cb()

    def _excluir(self) -> None:
        if self.id_atual is None:
            return
        if not sim_nao(self, "Excluir", "Excluir o objeto selecionado?"):
            return
        self.banco.excluir(self.id_atual)
        self._novo()

    def _destino(self, titulo: str, tipos: list, sufixo: str) -> Path | None:
        caminho = filedialog.asksaveasfilename(
            parent=self,
            title=titulo,
            defaultextension=sufixo,
            filetypes=tipos,
            initialdir=str(PASTA_DADOS),
        )
        return Path(caminho) if caminho else None

    def _png(self) -> None:
        dest = self._destino("Figura PNG", [("PNG", "*.png")], ".png")
        if dest is None:
            return
        self._garantir_3d()
        try:
            d, _res, _z, _r, pts, z_cm, sy_rel, ficha = self._geometria_atual()
        except ValueError:
            return
        self._preencher_caixa_dados(ficha)
        self.update_idletasks()
        if self._compor_png_3d_com_ficha(dest):
            aviso(self, "Exportar", f"Figura gravada em {dest}")
            return
        # Fallback: só o sólido, se a montagem com a ficha falhar.
        esp = float(d.get("espessura_parede") or 0)
        if self.vista3d is not None:
            self.vista3d.salvar_png(str(dest))
        else:
            from ceraform.vista_solido import gravar_png_solido

            gravar_png_solido(
                str(dest),
                pts,
                z_cm,
                sy_rel,
                espessura=esp,
                planta=str(d.get("contorno_planta") or "Circular"),
            )
        aviso(self, "Exportar", f"Figura gravada em {dest}")

    def _compor_png_3d_com_ficha(self, dest: Path) -> bool:
        """Monta PNG: painel «Dados do objeto» à esquerda + sólido à direita."""
        if self.vista3d is None:
            return False
        try:
            from PIL import Image, ImageDraw
        except Exception:
            return False
        import tempfile

        fd, tmp_name = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            self.vista3d.salvar_png(str(tmp))
            with Image.open(tmp) as im:
                img3d = im.convert("RGB").copy()
        except Exception:
            return False
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

        ficha = self._ficha or {}
        celulas = list(ficha.get("celulas") or [])
        nota = str(ficha.get("nota") or "")
        margem = 16
        linha_h = 22
        titulo_h = 32
        linhas_util: list[tuple[str, str]] = []
        for rotulo, valor in celulas:
            if rotulo == "Ponto de equilíbrio":
                valor = valor.replace(" acima do apoio", "")
            linhas_util.append((_rotulo_ficha_3d(rotulo), valor))

        largura_painel = 420
        col = getattr(self, "_col_dados_3d", None)
        if col is not None:
            try:
                self.update_idletasks()
                w_col = int(col.winfo_width())
                if w_col > 80:
                    largura_painel = w_col
            except tk.TclError:
                pass

        # Times New Roman 12, igual ao restante da interface.
        font_t = _truetype_serif(_FONTES_SERIF_NEGRITO, 12)
        font_r = _truetype_serif(_FONTES_SERIF_REGULAR, 12)
        font_v = _truetype_serif(_FONTES_SERIF_NEGRITO, 12)
        x_valor = margem
        if linhas_util:
            x_valor = margem + int(
                max(_largura_texto_png(font_r, rot) for rot, _ in linhas_util)
            ) + 12
        largura_valor = max(largura_painel - x_valor - margem, 48)
        # Se o nome do sítio (ou outro valor) não cabe numa linha, alarga o
        # painel até o texto inteiro, como na tela — sem truncar.
        extra = 0.0
        for _rot, valor in linhas_util:
            extra = max(extra, _largura_texto_png(font_v, valor))
        if extra > largura_valor:
            largura_painel = min(
                int(x_valor + extra + margem + 4),
                max(largura_painel, 640),
            )
            largura_valor = max(largura_painel - x_valor - margem, 48)

        linhas_desenhadas: list[tuple[str, list[str]]] = []
        for rotulo, valor in linhas_util:
            linhas_desenhadas.append(
                (rotulo, _envolver_texto_png(valor, font_v, largura_valor))
            )
        n_linhas = sum(len(vs) for _r, vs in linhas_desenhadas)
        trechos_nota: list[str] = []
        if nota:
            trechos_nota = _envolver_texto_png(nota, font_r, largura_painel - 2 * margem)
        alt_texto = titulo_h + margem + n_linhas * linha_h
        if trechos_nota:
            alt_texto += 8 + len(trechos_nota) * 16
        altura = max(img3d.height, alt_texto + margem)
        painel = Image.new("RGB", (largura_painel, altura), (245, 242, 238))
        draw = ImageDraw.Draw(painel)
        draw.text((margem, margem), "Dados do objeto", fill=(26, 21, 18), font=font_t)
        y = margem + titulo_h
        for rotulo, valores in linhas_desenhadas:
            draw.text((margem, y), rotulo, fill=(107, 99, 88), font=font_r)
            for i, trecho in enumerate(valores):
                draw.text((x_valor, y), trecho, fill=(26, 21, 18), font=font_v)
                if i < len(valores) - 1:
                    y += linha_h
            y += linha_h
        if trechos_nota:
            y += 8
            for t in trechos_nota:
                draw.text((margem, y), t, fill=(74, 64, 56), font=font_r)
                y += 16
        out = Image.new("RGB", (largura_painel + img3d.width, altura), (43, 43, 43))
        out.paste(painel, (0, 0))
        out.paste(img3d, (largura_painel, (altura - img3d.height) // 2))
        out.save(str(dest), format="PNG")
        return True

    def _pdf_2d(self) -> None:
        """PDF apenas do corte técnico (a publicação exporta só PNG da tela)."""
        self._garantir_2d()
        try:
            d, res, z, r, *_resto = self._geometria_atual()
        except ValueError:
            aviso(self, "Exportar", "Não foi possível calcular a geometria da peça.")
            return
        dest = self._destino("Perfil PDF", [("PDF", "*.pdf")], ".pdf")
        if dest is None:
            return
        from matplotlib.figure import Figure

        fig_pdf = Figure(dpi=300, facecolor="white")
        ax_pdf = fig_pdf.add_subplot(111)
        v = _v2d()
        v.desenhar_perfil_completo(
            ax_pdf,
            z,
            r,
            d,
            forma=self.var_forma.get() or res.forma,
            volume_l=float(d.get("volume_l") or 0.0),
            tipo_base=d.get("tipo_base") or "Reta",
            espessura=d["espessura_parede"],
            modo="pdf",
        )
        folha = getattr(ax_pdf, "_folha_tamanho", (29.7, 21.0))
        v.preparar_folha_exportacao(fig_pdf, ax_pdf, folha)
        fig_pdf.savefig(
            str(dest),
            format="pdf",
            facecolor="white",
            edgecolor="none",
            dpi=300,
        )
        aviso(self, "Exportar", f"Perfil gravado em {dest}")

    def _png_2d(self) -> None:
        self._garantir_2d()
        if self.fig2 is None or self.ax2 is None or self.canvas_2d is None:
            aviso(self, "Exportar", "Não foi possível gravar a figura do perfil.")
            return
        try:
            d, res, z, r, *_resto = self._geometria_atual()
        except ValueError:
            aviso(self, "Exportar", "Não foi possível calcular a geometria da peça.")
            return
        self._redesenhar_2d(d, res, z, r)
        dest = self._destino("Perfil PNG", [("PNG", "*.png")], ".png")
        if dest is None:
            return
        self.canvas_2d.draw()
        self.fig2.savefig(
            str(dest),
            format="png",
            facecolor=_v2d()._COR_FUNDO_TELA,
            edgecolor="none",
            dpi=200,
            bbox_inches=None,
        )
        aviso(self, "Exportar", f"Figura gravada em {dest}")

    def _malha(self, kind: str) -> None:
        ext = {"stl": ".stl", "obj": ".obj", "ply": ".ply"}[kind]
        tipos = [(kind.upper(), f"*{ext}")]
        dest = self._destino(f"Malha {kind.upper()}", tipos, ext)
        if dest is None:
            return
        try:
            d, _res, _z, _r, pts, _z_cm, sy_rel, _q = self._geometria_atual()
        except ValueError:
            return
        esp = float(d.get("espessura_parede") or 0)
        if self.vista3d is not None and self.vista3d.salvar_malha(str(dest)):
            aviso(self,"Exportar", f"Malha gravada em {dest}")
            return
        from ceraform.vista_solido import gravar_malha_solido

        if gravar_malha_solido(
            str(dest),
            pts,
            sy_rel,
            espessura=esp,
            planta=str(d.get("contorno_planta") or "Circular"),
        ):
            aviso(self,"Exportar", f"Malha gravada em {dest}")
        else:
            erro(self,"Exportar", "Não foi possível gravar a malha.")

    def _stl(self) -> None:
        self._malha("stl")

    def _obj(self) -> None:
        self._malha("obj")

    def _ply(self) -> None:
        self._malha("ply")

    def _relatorio(self) -> None:
        sitio = self.var_sitio.get().strip()
        if not sitio:
            aviso(self,"Relatório", "Informe o nome do sítio.")
            return
        linhas = self.banco.listar_sitio(sitio)
        if not linhas:
            aviso(self,"Relatório", "Não há objetos gravados neste sítio.")
            return
        dest = self._destino("Relatório HTML", [("HTML", "*.html")], ".html")
        if dest is None:
            return
        gravar_relatorio_html(dest, sitio, linhas)
        pdf = dest.with_suffix(".pdf")
        self._html_para_pdf(dest, pdf)
        _abrir_arquivo_sistema(dest)
        aviso(self,"Relatório", f"Relatório gravado em {dest}")

    def _html_para_pdf(self, html: Path, pdf: Path) -> None:
        import shutil
        import subprocess

        chrome = shutil.which("google-chrome") or shutil.which("chromium")
        if not chrome:
            return
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}",
                html.as_uri(),
            ],
            check=False,
            capture_output=True,
            start_new_session=True,
        )

    def _plotly(self) -> None:
        try:
            import plotly.graph_objects as go
        except ImportError:
            aviso(self,"Plotly", "Plotly não está instalado neste ambiente.")
            return
        try:
            d, _res, _z, _r, pts, _z_cm, sy_rel, _q = self._geometria_atual()
        except ValueError:
            return
        from ceraform.vista_solido import superficie_numpy

        x, y, zz = superficie_numpy(
            pts,
            n_theta=250,
            sy_scale=sy_rel,
            planta=str(d.get("contorno_planta") or "Circular"),
        )
        fig = go.Figure(
            data=[
                go.Surface(
                    x=x,
                    y=y,
                    z=zz,
                    colorscale=[
                        [0.0, "rgb(139,69,19)"],
                        [0.55, "rgb(196,122,82)"],
                        [1.0, "rgb(210,160,120)"],
                    ],
                    showscale=False,
                    lighting=dict(ambient=0.18, diffuse=0.85, roughness=0.35, specular=0.82),
                )
            ]
        )
        fig.update_layout(
            title=self.var_forma.get(),
            scene=dict(
                aspectmode="data",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
            ),
            margin=dict(l=0, r=0, t=40, b=0),
        )
        dest = PASTA_DADOS / "preview_plotly.html"
        fig.write_html(str(dest), include_plotlyjs="cdn")
        _abrir_arquivo_sistema(dest)

    def _carregar_id(self, id_: int) -> None:
        row = self.banco.obter(id_)
        if row is None:
            return
        self.id_atual = int(row["id"])
        self._silencio = True
        self.var_sitio.set(str(row["sitio"] or "").strip())
        self.var_numero.set(str(row["numero"] or "").strip())
        keys = [
            ("h", self.var_h),
            ("db", self.var_db),
            ("dmax", self.var_dmax),
            ("hmax", self.var_hmax),
            ("dbase", self.var_dbase),
        ]
        for col, var in keys:
            try:
                val = float(row[col] or 0)
            except (TypeError, ValueError):
                val = 0.0
            var.set(_texto_medida(val))
        opcionais = [
            ("dmeio", self.var_dmeio),
            ("espessura_parede", self.var_esp),
            ("largura", self.var_comp),
            ("profundidade", self.var_larg),
            ("altura_juncao", self.var_h_juncao),
            ("diametro_juncao", self.var_d_juncao),
            ("altura_carena", self.var_h_carena),
            ("diametro_carena", self.var_d_carena),
            ("altura_carena2", self.var_h_carena2),
            ("diametro_carena2", self.var_d_carena2),
        ]
        for col, var in opcionais:
            try:
                val = row[col]
            except (IndexError, KeyError):
                val = 0
            try:
                num = float(val or 0)
            except (TypeError, ValueError):
                num = 0.0
            var.set("" if not num else _texto_medida(num))
        amostras_txt = row["amostras"] or ""
        h_row = float(row["h"] or 0)
        d14, d12, d34 = diametros_fracao(amostras_txt, h_row)
        self._amostras_outras = amostras_exceto_fracoes(amostras_txt, h_row)
        self.var_d_14.set("" if not d14 else _texto_medida(float(d14)))
        self.var_d_12.set("" if not d12 else _texto_medida(float(d12)))
        self.var_d_34.set("" if not d34 else _texto_medida(float(d34)))
        self.var_contorno.set(row["contorno_planta"] or "")
        try:
            self.var_tipo_base.set(row["tipo_base"] or "")
        except (IndexError, KeyError):
            self.var_tipo_base.set("")
        self.var_perfil.set(row["perfil_geometrico"] or "")
        self.var_perfil_base.set(row["perfil_trecho_base"] or "")
        self.var_perfil_borda.set(row["perfil_trecho_borda"] or "")
        self.var_forma.set(row["forma_confirmada"] or row["forma"] or "")
        self.var_forma_sec.set(row["forma_secundaria_confirmada"] or "")
        self._silencio = False
        self._atualizar_preview()

    def _sair(self) -> None:
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.unbind_all("<MouseWheel>")
        if self.vista3d is not None:
            try:
                self.vista3d.fechar()
            except Exception:
                pass
        self.banco.fechar()
        self.destroy()


def main() -> None:
    app = AppVasos()
    app.mainloop()

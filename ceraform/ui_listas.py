# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, font as tkfont
from tkinter import ttk
import tkinter as tk

from ceraform.caminhos import pasta_dados
from ceraform import fonte
from ceraform.janela import aviso, sim_nao
from ceraform.relatorio import (
    _forma_exibida,
    ficha_cabecalho_sitio,
    gravar_relatorio_csv,
    gravar_relatorio_html,
    html_para_pdf,
)
from ceraform.volume import rotulo_tamanho

PASTA_DADOS = pasta_dados()

COLS_REL = (
    "numero",
    "forma",
    "tamanho",
    "h",
    "db",
    "dmax",
    "hmax",
    "dbase",
    "volume",
    "aprox",
)
TITULOS_REL = {
    "numero": "Número do desenho",
    "forma": "Forma geométrica",
    "tamanho": "Tamanho",
    "h": "Altura total (cm)",
    "db": "Diâmetro da borda (cm)",
    "dmax": "Maior diâmetro da peça (cm)",
    "hmax": "Altura da base até o maior diâmetro (cm)",
    "dbase": "Diâmetro da base (cm)",
    "volume": "Volume do objeto (L)",
    "aprox": "Aproximação",
}
LARGURAS_REL = (180, 210, 140, 170, 210, 280, 360, 210, 200, 140)
COLS_NUM_REL = {"h", "db", "dmax", "hmax", "dbase", "volume"}
ORDEM_TAMANHO = ("Pequeno", "Médio", "Grande", "Extra grande")

COLS = ("id", "sitio", "numero", "forma", "tamanho", "volume")
TITULOS = {
    "id": "Id",
    "sitio": "Nome do sítio",
    "numero": "Número do desenho",
    "forma": "Forma geométrica",
    "tamanho": "Tamanho",
    "volume": "Volume do objeto (L)",
}


def _preencher_lista(tree: ttk.Treeview, linhas) -> None:
    for i in tree.get_children():
        tree.delete(i)
    for row in linhas:
        forma = row["forma_confirmada"] or row["forma"] or ""
        vol = float(row["volume_l"] or 0)
        tree.insert(
            "",
            tk.END,
            iid=str(row["id"]),
            values=(
                row["id"],
                row["sitio"],
                row["numero"],
                forma,
                rotulo_tamanho(vol),
                f"{vol:.3f}",
            ),
        )
    _listrar(tree)
    _ajustar_largura_colunas(tree, COLS, TITULOS)


def _fonte_celula():
    try:
        return tkfont.nametofont("TkDefaultFont")
    except tk.TclError:
        return tkfont.Font(family=fonte.FAMILIA, size=fonte.TAMANHO)


def _fonte_titulo():
    try:
        return tkfont.nametofont("TkHeadingFont")
    except tk.TclError:
        return tkfont.Font(family=fonte.FAMILIA, size=fonte.TAMANHO, weight="bold")


def _ajustar_largura_colunas(
    tree: ttk.Treeview,
    colunas: tuple[str, ...],
    titulos: dict[str, str],
) -> None:
    """Largura inicial pelo conteúdo; o usuário pode puxar o divisor com o mouse."""
    fnt_cel = _fonte_celula()
    fnt_tit = _fonte_titulo()
    pad = 32
    filhos = tree.get_children("")
    amostra = filhos[:40]
    for col in colunas:
        largura = fnt_tit.measure(titulos.get(col, col)) + pad
        for iid in amostra:
            largura = max(largura, fnt_cel.measure(str(tree.set(iid, col))) + pad)
        tree.column(
            col,
            width=min(max(largura, 48), 720),
            minwidth=36,
            stretch=False,
        )


def _nomes_colunas(tree: ttk.Treeview) -> list[str]:
    visiveis = tree["displaycolumns"]
    if not visiveis or visiveis[0] == "#all":
        return list(tree["columns"])
    return list(visiveis)


def _coluna_no_separador(tree: ttk.Treeview, x: int, y: int) -> str | None:
    """Coluna à esquerda do divisor sob o ponteiro (área um pouco mais larga)."""
    for dx in range(-8, 9):
        if tree.identify_region(x + dx, y) != "separator":
            continue
        ident = tree.identify_column(x + dx)
        if not ident or not ident.startswith("#"):
            continue
        try:
            idx = int(ident[1:]) - 1
        except ValueError:
            continue
        nomes = _nomes_colunas(tree)
        if 0 <= idx < len(nomes):
            return nomes[idx]
    return None


def _ligar_redimensionar_colunas(tree: ttk.Treeview) -> None:
    """Arrastar o divisor do título amplia ou reduz a coluna (Linux/ttk)."""
    estado: dict[str, object] = {"col": None, "x": 0, "w": 0}

    def pressionar(event) -> str | None:
        col = _coluna_no_separador(tree, event.x, event.y)
        if col is None:
            return None
        estado["col"] = col
        estado["x"] = event.x
        estado["w"] = int(tree.column(col, "width"))
        tree.configure(cursor="sb_h_double_arrow")
        return "break"

    def arrastar(event) -> str | None:
        col = estado["col"]
        if col is None:
            return None
        nova = max(36, int(estado["w"]) + (event.x - int(estado["x"])))
        tree.column(str(col), width=nova)
        return "break"

    def soltar(_event) -> None:
        estado["col"] = None
        tree.configure(cursor="")

    def cursor(event) -> None:
        if estado["col"] is not None:
            tree.configure(cursor="sb_h_double_arrow")
            return
        if _coluna_no_separador(tree, event.x, event.y):
            tree.configure(cursor="sb_h_double_arrow")
        else:
            tree.configure(cursor="")

    tree.bind("<ButtonPress-1>", pressionar, add="+")
    tree.bind("<B1-Motion>", arrastar, add="+")
    tree.bind("<ButtonRelease-1>", soltar, add="+")
    tree.bind("<Motion>", cursor, add="+")


def _montar_lista(parent: tk.Misc, altura: int = 16) -> ttk.Treeview:
    frm = ttk.Frame(parent)
    frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
    scroll = ttk.Scrollbar(frm, orient=tk.VERTICAL)
    xs = ttk.Scrollbar(frm, orient=tk.HORIZONTAL)
    tree = ttk.Treeview(
        frm,
        columns=COLS,
        show="headings",
        height=altura,
        yscrollcommand=scroll.set,
        xscrollcommand=xs.set,
    )
    scroll.configure(command=tree.yview)
    xs.configure(command=tree.xview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    xs.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    for c, w in zip(COLS, (56, 280, 170, 240, 200, 180)):
        tree.column(c, width=w, anchor="w", minwidth=36, stretch=False)
    tree.tag_configure("par", background="#FFFFFF")
    tree.tag_configure("impar", background="#E2EFDA")
    _ligar_ordenacao(tree, COLS, TITULOS, {"id", "volume"})
    _ajustar_largura_colunas(tree, COLS, TITULOS)
    _ligar_redimensionar_colunas(tree)
    return tree


def _chave_ordenacao(valor: str, coluna: str, colunas_num: set[str]):
    texto = str(valor).strip()
    if coluna == "tamanho":
        base = texto.split(" (")[0]
        try:
            return (ORDEM_TAMANHO.index(base), texto.lower())
        except ValueError:
            return (len(ORDEM_TAMANHO), texto.lower())
    if coluna in colunas_num or coluna in {"id", "numero", "volume"}:
        try:
            return (0, float(texto.replace(",", ".")))
        except ValueError:
            return (1, texto.lower())
    return (0, texto.lower())


def _listrar(tree: ttk.Treeview) -> None:
    for i, iid in enumerate(tree.get_children("")):
        tree.item(iid, tags=("impar" if i % 2 else "par",))


def _ligar_ordenacao(
    tree: ttk.Treeview,
    colunas: tuple[str, ...],
    titulos: dict[str, str],
    colunas_num: set[str],
) -> None:
    estado: dict[str, bool] = {}

    def ordenar(col: str) -> None:
        invertido = estado.get(col, False)
        itens = [(tree.set(iid, col), iid) for iid in tree.get_children("")]
        itens.sort(
            key=lambda par: _chave_ordenacao(par[0], col, colunas_num),
            reverse=invertido,
        )
        for i, (_val, iid) in enumerate(itens):
            tree.move(iid, "", i)
        estado[col] = not invertido
        _listrar(tree)

    for col in colunas:
        tree.heading(
            col,
            text=titulos[col],
            command=lambda c=col: ordenar(c),
        )


def montar_consulta(app: tk.Tk, parent: tk.Misc) -> None:
    acoes = ttk.Frame(parent, padding=8)
    acoes.pack(side=tk.BOTTOM, fill=tk.X)
    var_status = tk.StringVar(value="")
    ttk.Label(parent, textvariable=var_status).pack(side=tk.BOTTOM, anchor="w", padx=10)

    ttk.Label(
        parent,
        text="Consultar, alterar e excluir objetos",
        font=fonte.FONTE_NEGRITO,
    ).pack(anchor="w", padx=10, pady=(10, 4))

    filtro = ttk.LabelFrame(parent, text="Filtro", padding=8)
    filtro.pack(fill=tk.X, padx=8, pady=4)
    var_sitio = tk.StringVar()
    var_numero = tk.StringVar()
    ttk.Label(filtro, text="Nome do sítio").grid(row=0, column=0, sticky="w")
    ttk.Entry(filtro, textvariable=var_sitio, width=40).grid(
        row=0, column=1, sticky="ew", padx=8
    )
    ttk.Label(filtro, text="Número do desenho").grid(row=0, column=2, sticky="w")
    ttk.Entry(filtro, textvariable=var_numero, width=20).grid(
        row=0, column=3, sticky="w", padx=8
    )
    filtro.columnconfigure(1, weight=1)

    tree = _montar_lista(parent)

    def consultar() -> None:
        linhas = app.banco.filtrar(var_sitio.get(), var_numero.get())
        _preencher_lista(tree, linhas)
        n = len(linhas)
        var_status.set(
            f"{n} objeto encontrado." if n == 1 else f"{n} objetos encontrados."
        )

    def selecionado(acao: str) -> int | None:
        sel = tree.selection()
        if not sel:
            aviso(
                parent,
                "Consulta",
                f"Selecione um objeto na lista e depois use {acao}.",
            )
            return None
        return int(sel[0])

    def voltar_lista() -> None:
        consultar()
        app._mostrar_tela("consulta")

    def alterar() -> None:
        id_ = selecionado("Alterar")
        if id_ is None:
            return
        app._carregar_id(id_)
        app._cb_apos_salvar = voltar_lista
        app._mostrar_tela("cadastro")

    def excluir() -> None:
        id_ = selecionado("Excluir")
        if id_ is None:
            return
        if not sim_nao(
            parent,
            "Excluir",
            "Esta ação não poderá ser desfeita.\n\nExcluir o objeto selecionado?",
        ):
            return
        app.banco.excluir(id_)
        if app.id_atual == id_:
            app.id_atual = None
            app._novo()
        consultar()

    def ao_fechar() -> None:
        app._cb_apos_salvar = None
        app._mostrar_tela("cadastro")

    ttk.Button(filtro, text="Consultar", command=consultar).grid(
        row=0, column=4, padx=(8, 0)
    )
    ttk.Button(acoes, text="Alterar", command=alterar).pack(
        side=tk.LEFT, padx=4, ipady=4
    )
    ttk.Button(acoes, text="Excluir", command=excluir).pack(side=tk.LEFT, padx=4, ipady=4)
    ttk.Button(acoes, text="Fechar", command=ao_fechar).pack(
        side=tk.RIGHT, padx=4, ipady=4
    )
    ttk.Button(acoes, text="Ajuda", command=app._abrir_ajuda).pack(
        side=tk.RIGHT, padx=4, ipady=4
    )
    app._consulta_atualizar = consultar
    consultar()


def montar_relatorio(app: tk.Tk, parent: tk.Misc) -> None:
    acoes = ttk.Frame(parent, padding=8)
    acoes.pack(side=tk.BOTTOM, fill=tk.X)

    resumo = ttk.LabelFrame(parent, text="Resumo do sítio", padding=(12, 10))
    resumo.pack(fill=tk.X, padx=8, pady=(10, 0))
    grelha = ttk.Frame(resumo)
    grelha.pack(fill=tk.X)
    for c in range(3):
        grelha.columnconfigure(c, weight=1, uniform="resumo_sitio")
    celulas_resumo: list[tuple[ttk.Label, ttk.Label, ttk.Frame]] = []
    for i in range(18):
        linha, col = divmod(i, 3)
        caixa = ttk.Frame(grelha)
        caixa.grid(row=linha, column=col, sticky="nsew", padx=(0, 16), pady=(0, 8))
        cap = ttk.Label(caixa, text="", foreground="#6b6358")
        cap.pack(anchor="w")
        val = ttk.Label(caixa, text="", foreground="#1a1512", font=fonte.FONTE_NEGRITO)
        val.pack(anchor="w")
        celulas_resumo.append((cap, val, caixa))
        caixa.grid_remove()
    lbl_nota = ttk.Label(
        resumo,
        text="",
        foreground="#4a4038",
        wraplength=1100,
        justify="left",
    )
    lbl_nota.pack(fill=tk.X, pady=(2, 0))

    def preencher_resumo(ficha: dict) -> None:
        pares = list(ficha.get("celulas") or [])
        nota = str(ficha.get("nota") or "")
        for i, (cap, val, caixa) in enumerate(celulas_resumo):
            if i < len(pares):
                rotulo, valor = pares[i]
                cap.configure(text=rotulo)
                val.configure(text=valor)
                caixa.grid()
            else:
                cap.configure(text="")
                val.configure(text="")
                caixa.grid_remove()
        lbl_nota.configure(text=nota)

    def _largura_nota(evt: tk.Event) -> None:
        if evt.widget is resumo and evt.width > 80:
            lbl_nota.configure(wraplength=max(evt.width - 28, 200))

    resumo.bind("<Configure>", _largura_nota)

    filtro = ttk.LabelFrame(parent, text="Filtro", padding=8)
    filtro.pack(fill=tk.X, padx=8, pady=4)
    var_sitio = tk.StringVar()
    ttk.Label(filtro, text="Nome do sítio").grid(row=0, column=0, sticky="w")
    combo = ttk.Combobox(
        filtro, textvariable=var_sitio, values=app.banco.sitios(), width=48
    )
    combo.grid(row=0, column=1, sticky="ew", padx=8)
    filtro.columnconfigure(1, weight=1)

    frm = ttk.Frame(parent)
    frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
    ys = ttk.Scrollbar(frm, orient=tk.VERTICAL)
    xs = ttk.Scrollbar(frm, orient=tk.HORIZONTAL)
    tree = ttk.Treeview(
        frm,
        columns=COLS_REL,
        show="headings",
        yscrollcommand=ys.set,
        xscrollcommand=xs.set,
    )
    ys.configure(command=tree.yview)
    xs.configure(command=tree.xview)
    ys.pack(side=tk.RIGHT, fill=tk.Y)
    xs.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    for c, w in zip(COLS_REL, LARGURAS_REL):
        tree.column(c, width=w, anchor="w", minwidth=36, stretch=False)
    tree.tag_configure("par", background="#FFFFFF")
    tree.tag_configure("impar", background="#E2EFDA")
    _ligar_ordenacao(tree, COLS_REL, TITULOS_REL, COLS_NUM_REL)
    _ajustar_largura_colunas(tree, COLS_REL, TITULOS_REL)
    _ligar_redimensionar_colunas(tree)

    linhas_atual: list = []

    def preencher_planilha(linhas) -> None:
        for i in tree.get_children():
            tree.delete(i)
        for i, r in enumerate(linhas):
            vol = float(r["volume_l"] or 0)
            tree.insert(
                "",
                tk.END,
                values=(
                    r["numero"],
                    _forma_exibida(r),
                    rotulo_tamanho(vol),
                    f"{float(r['h']):.1f}",
                    f"{float(r['db']):.1f}",
                    f"{float(r['dmax']):.1f}",
                    f"{float(r['hmax']):.1f}",
                    f"{float(r['dbase']):.1f}",
                    f"{vol:.3f}",
                    "sim" if r["aproximacao"] else "não",
                ),
                tags=("impar" if i % 2 else "par",),
            )
        _ajustar_largura_colunas(tree, COLS_REL, TITULOS_REL)

    def atualizar() -> None:
        nonlocal linhas_atual
        combo.configure(values=app.banco.sitios())
        sitio = var_sitio.get().strip()
        if not sitio:
            linhas_atual = []
            preencher_planilha([])
            preencher_resumo(ficha_cabecalho_sitio("", []))
            return
        linhas_atual = app.banco.listar_sitio(sitio)
        if not linhas_atual:
            preencher_planilha([])
            preencher_resumo(ficha_cabecalho_sitio(sitio, []))
            return
        preencher_planilha(linhas_atual)
        preencher_resumo(ficha_cabecalho_sitio(sitio, linhas_atual))

    def _linhas_ok() -> bool:
        if not var_sitio.get().strip():
            aviso(parent, "Relatório", "Informe o nome do sítio.")
            return False
        if not linhas_atual:
            aviso(parent, "Relatório", "Não há objetos gravados neste sítio.")
            return False
        return True

    def exportar_pdf() -> None:
        if not _linhas_ok():
            return
        sitio = var_sitio.get().strip()
        dest = filedialog.asksaveasfilename(
            parent=app,
            title="Exportar PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=str(PASTA_DADOS),
        )
        if not dest:
            return
        pdf = Path(dest)
        html = pdf.with_suffix(".html")
        gravar_relatorio_html(html, sitio, linhas_atual)
        if html_para_pdf(html, pdf):
            aviso(parent, "Relatório", f"PDF gravado em {pdf}")
        else:
            aviso(
                parent,
                "Relatório",
                "Não foi possível gravar o PDF neste computador. "
                f"O relatório em HTML ficou em {html}.",
            )

    def exportar_csv() -> None:
        if not _linhas_ok():
            return
        dest = filedialog.asksaveasfilename(
            parent=app,
            title="Exportar CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(PASTA_DADOS),
        )
        if not dest:
            return
        gravar_relatorio_csv(Path(dest), var_sitio.get().strip(), linhas_atual)
        aviso(parent, "Relatório", f"CSV gravado em {dest}")

    def ao_fechar() -> None:
        app._mostrar_tela("cadastro")

    ttk.Button(filtro, text="Atualizar", command=atualizar).grid(
        row=0, column=2, padx=(8, 0)
    )
    ttk.Button(acoes, text="Exportar PDF", command=exportar_pdf).pack(
        side=tk.LEFT, padx=4, ipady=4
    )
    ttk.Button(acoes, text="Exportar CSV", command=exportar_csv).pack(
        side=tk.LEFT, padx=4, ipady=4
    )
    ttk.Button(acoes, text="Fechar", command=ao_fechar).pack(
        side=tk.RIGHT, padx=4, ipady=4
    )
    ttk.Button(acoes, text="Ajuda", command=app._abrir_ajuda).pack(
        side=tk.RIGHT, padx=4, ipady=4
    )
    combo.bind("<<ComboboxSelected>>", lambda _e: atualizar())
    app._relatorio_atualizar = atualizar
    sitios = app.banco.sitios()
    if sitios:
        var_sitio.set(sitios[0])
    atualizar()

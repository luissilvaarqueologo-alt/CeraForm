# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

"""Gera o PDF do veredito das malhas PLY de Bordas_3D_PLY."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

PASTA = Path(__file__).resolve().parent
PDF = PASTA / "veredito_malhas_Bordas_3D_PLY.pdf"

FONTE_R = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf")
FONTE_B = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf")
FONTE_I = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf")
FONTE_M = Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf")

LINHAS = (
    ("Ceramica-1-PLY.ply", "39", "235 064", "16,3", "12,2 × 10,4", "0,42", "245", "Usável"),
    ("Ceramica-2-PLY.ply", "51", "308 742", "19,1", "15,5 × 10,1", "0,41", "338", "Usável (maior)"),
    ("Ceramica-3-PLY.ply", "25", "152 093", "15,0", "13,8 × 8,6", "0,41", "165", "Usável"),
    ("Ceramica-4-PLY.ply", "28", "167 972", "15,3", "10,7 × 8,5", "0,41", "179", "Usável"),
    ("Ceramica-5-PLY.ply", "35", "212 841", "17,4", "14,1 × 12,6", "0,41", "233", "Usável"),
    ("Ceramica-6-PLY.ply", "37", "223 736", "17,5", "13,2 × 11,1", "0,42", "237", "Usável"),
    ("Ceramica-7-PLY.ply", "21", "122 515", "12,4", "10,4 × 6,4", "0,41", "134", "Usável (menor arco)"),
    ("Ceramica-8-PLY.ply", "17", "99 307", "10,8", "8,2 × 6,7", "0,41", "109", "Usável (menor peça)"),
)

CABECALHO_TABELA = (
    "Arquivo",
    "MB",
    "Vértices",
    "Diagonal\n(cm)",
    "Caixa PCA\n(cm)",
    "Aresta p50\n(mm)",
    "Área\n(cm²)",
    "Situação",
)
LARGURAS = (38, 10, 20, 18, 24, 20, 16, 36)


class PdfVeredito(FPDF):
    def header(self) -> None:
        return

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Livro", size=8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, f"{self.page_no()}", align="C")


def _paragrafo(pdf: FPDF, texto: str, *, negrito: bool = False, tamanho: float = 10.5) -> None:
    pdf.set_font("Livro", "B" if negrito else "", size=tamanho)
    pdf.set_text_color(17, 17, 17)
    pdf.multi_cell(0, 5.1, texto, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.2)


def gerar(destino: Path = PDF) -> Path:
    pdf = PdfVeredito(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_font("Livro", "", str(FONTE_R))
    pdf.add_font("Livro", "B", str(FONTE_B))
    pdf.add_font("Livro", "I", str(FONTE_I))
    pdf.add_font("Codigo", "", str(FONTE_M))
    pdf.add_page()
    pdf.set_left_margin(14)
    pdf.set_right_margin(14)

    pdf.set_font("Codigo", size=6.4)
    pdf.set_text_color(34, 34, 34)
    identificacao = (
        "CERAFORM — RECONSTITUIÇÃO GEOMÉTRICA DE CERÂMICA (Versão 1.0)\n"
        "Autora (Idealização e Metodologia Arqueológica): Cláudia Alves de Oliveira\n"
        "Autor (Arquitetura e Desenvolvimento de Software): Luís Antônio da Silva\n"
        "Titulares: pessoas físicas, autoria em partes iguais (50% cada).\n"
        "Ano de Desenvolvimento: 2026  ·  SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC\n"
        "© 2026 OLIVEIRA, Cláudia Alves de; SILVA, Luís Antônio da. Todos os direitos reservados."
    )
    pdf.multi_cell(0, 3.1, identificacao, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    y = pdf.get_y()
    pdf.set_draw_color(34, 34, 34)
    pdf.set_line_width(0.25)
    pdf.line(14, y, 196, y)
    pdf.ln(4)

    pdf.set_font("Livro", "B", size=16)
    pdf.set_text_color(17, 17, 17)
    pdf.multi_cell(0, 7, "Veredito das malhas PLY — lote inicial", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Livro", "I", size=9.5)
    pdf.set_text_color(51, 51, 51)
    pdf.multi_cell(
        0,
        4.6,
        "Projeto anexo CeraForm 3D  ·  pasta CeraForm_3D_Project/Bordas_3D_PLY  ·  "
        "escala assumida em milímetro  ·  4 de setembro de 2026",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(3)

    resumo = (
        ("8/8", "Malhas com geometria útil"),
        ("0,41 mm", "Aresta mediana (todas)"),
        ("0", "Arquivos de textura na pasta"),
        ("1", "Peça conexa após soldar UV"),
    )
    x0 = 14
    larg = 44.5
    y0 = pdf.get_y()
    for i, (num, rotulo) in enumerate(resumo):
        x = x0 + i * (larg + 2)
        pdf.set_xy(x, y0)
        pdf.set_draw_color(136, 136, 136)
        pdf.rect(x, y0, larg, 16)
        pdf.set_xy(x + 2, y0 + 1.5)
        pdf.set_font("Livro", "B", size=13)
        pdf.set_text_color(17, 17, 17)
        pdf.cell(larg - 4, 6.5, num)
        pdf.set_xy(x + 2, y0 + 8.2)
        pdf.set_font("Livro", size=8)
        pdf.multi_cell(larg - 4, 3.4, rotulo)
    pdf.set_y(y0 + 18)

    pdf.set_fill_color(243, 243, 243)
    pdf.set_draw_color(34, 34, 34)
    pdf.set_line_width(0.3)
    texto_ver = (
        "Veredicto. Os oito arquivos servem para desenvolver o programa anexo: "
        "são fragmentos de borda com lábio, parede e curvatura visíveis, malha "
        "triangular, normais e coordenadas em milímetro. Não serve ainda o trecho "
        "de decoração, engobo ou pintura por cor — as PNG referidas no cabeçalho "
        "do PLY não estão na pasta."
    )
    pdf.set_font("Livro", size=10.5)
    pdf.set_text_color(17, 17, 17)
    y = pdf.get_y()
    pdf.multi_cell(0, 5.1, texto_ver, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Livro", "B", size=7.4)
    pdf.set_fill_color(236, 236, 236)
    pdf.set_draw_color(136, 136, 136)
    pdf.set_line_width(0.2)
    with pdf.table(
        col_widths=LARGURAS,
        text_align=(
            "LEFT",
            "RIGHT",
            "RIGHT",
            "RIGHT",
            "CENTER",
            "RIGHT",
            "RIGHT",
            "LEFT",
        ),
        line_height=4.0,
        markdown=False,
    ) as tabela:
        linha = tabela.row()
        for titulo in CABECALHO_TABELA:
            linha.cell(titulo)
        pdf.set_font("Livro", size=7.3)
        for dados in LINHAS:
            linha = tabela.row()
            for cel in dados:
                linha.cell(cel)

    pdf.ln(1)
    pdf.set_font("Livro", "I", size=8.3)
    pdf.set_text_color(51, 51, 51)
    pdf.multi_cell(
        0,
        4.0,
        "Área é a soma das faces (interno + externo). Diagonal e caixa PCA assumem "
        "unidade milímetro. Ceramica-7 e Ceramica-8 são as peças menores — o arco "
        "da borda só se confirma depois do apoio do lábio no plano virtual. Aresta "
        "mediana medida nas faces triangulares.",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)

    pdf.set_font("Livro", "B", size=12.2)
    pdf.set_text_color(17, 17, 17)
    pdf.cell(0, 7, "O que já está certo", new_x="LMARGIN", new_y="NEXT")
    _paragrafo(
        pdf,
        "Formato. PLY binário little-endian, triângulos, posição em double, "
        "normais por vértice, coordenadas de textura por face. Depois de soldar "
        "vértices duplicados pelas ilhas de UV (tolerância 0,02 mm), cada arquivo "
        "vira uma única malha conexa.",
    )
    _paragrafo(
        pdf,
        "Escala e tamanho. Coordenadas na casa das centenas (Z ≈ 600–740): típico "
        "de fotogrametria em milímetro, não centrada na origem. Diagonais de "
        "10,8 cm a 19,1 cm — tamanho de caco de borda, não de vasilha inteira nem "
        "de nuvem em metro.",
    )

    pdf.set_font("Livro", "B", size=12.2)
    pdf.cell(0, 7, "Ressalvas antes de medir o diâmetro da borda", new_x="LMARGIN", new_y="NEXT")
    _paragrafo(
        pdf,
        "Textura ausente. Sete arquivos pedem output_material_0_map_Kd.png; "
        "Ceramica-3 pede C.png. Sem esses PNG não há cor de superfície — engobo, "
        "pintura e acabamento visível ficam para quando a textura chegar, ou para "
        "leitura só pela geometria.",
        negrito=False,
    )
    _paragrafo(
        pdf,
        "Resolução um pouco mais grossa que o pedido. O pedido técnico era "
        "0,10–0,20 mm entre pontos. A aresta mediana aqui é 0,41 mm (p10 ≈ 0,12 mm "
        "nas zonas densas). Continua abaixo do teto de 0,50 mm e dá para o plano "
        "do lábio; o diâmetro da borda em arcos curtos (Ceramica-7 e Ceramica-8) "
        "terá mais incerteza.",
    )
    _paragrafo(
        pdf,
        "Confirmar o milímetro numa peça real. A unidade não vem escrita no PLY. "
        "Vale medir com paquímetro a maior cota de um fragmento e conferir com a "
        "diagonal da malha. Se bater, fecha-se milímetro para o lote inteiro.",
    )

    pdf.set_font("Livro", "B", size=12.2)
    pdf.cell(
        0,
        7,
        "Chmyz 1976 — vocabulário para a ficha (ainda não fechada)",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    _paragrafo(
        pdf,
        "Terminologia arqueológica brasileira para a cerâmica, 2.ª edição revista "
        "e ampliada (Cadernos de Arqueologia, 1976). O PDF na pasta Bibliografia "
        "é imagem, sem texto selecionável. As listas abaixo são só referência; "
        "nada entra no programa até a Dra. Cláudia Alves de Oliveira confirmar os "
        "campos da ficha.",
    )
    _paragrafo(
        pdf,
        "Borda (p. 123–125): direta; expandida; extrovertida; reforçada internamente; "
        "dobrada; reforçada externamente; cambada; contraída; vasada; introvertida; "
        "vertical; inclinada internamente; inclinada externamente.",
    )
    _paragrafo(
        pdf,
        "Lábio (p. 134–135): plano; arredondado; apontado; biselado; dentado ou "
        "serrilhado. Os cortes do Chmyz já desenham o lábio encostado numa reta "
        "horizontal — o mesmo critério do plano virtual.",
    )
    _paragrafo(
        pdf,
        "Acabamento e decoração (amostra): alisado; polido; polido-estriado; banho; "
        "engobo; pintado; simples; escovado; corrugado (simples, complicado, "
        "imbricado, espatulado, ungulado); inciso; ponteado; digitado; roletado; "
        "entalhado; gretada; erodida.",
    )
    _paragrafo(
        pdf,
        "Pasta, queima, base. Pasta: argila + tempero. Queima: oxidação ou redução, "
        "lida na cor e na textura da fratura. Formas de base no Chmyz: plana, "
        "côncava, plano-côncava, convexa, em pedestal, anelar, cônica, trípode, "
        "tetrápode, polípode. No esboço a partir do fragmento: só convexa com "
        "diâmetro da base 0 cm, ou sem base.",
    )

    pdf.set_font("Livro", "B", size=12.2)
    pdf.cell(0, 7, "Próximo passo técnico", new_x="LMARGIN", new_y="NEXT")
    _paragrafo(
        pdf,
        "Copiar as PNG de textura para Bordas_3D_PLY (ou reexportar o PLY com cor "
        "por vértice). Medir uma cota real. Com isso o anexo começa pelo apoio do "
        "lábio no plano virtual sobre este lote — ainda sem ligar ao CeraForm "
        "original por uma tela hub.",
    )
    pdf.set_font("Livro", "I", size=8.4)
    pdf.set_text_color(68, 68, 68)
    pdf.multi_cell(
        0,
        4.1,
        "Fonte da tabela: cabeçalhos PLY e malha lida em PyVista (área, comprimento "
        "de aresta, conexidade após solda de 0,02 mm). Fonte do vocabulário: "
        "CHMYZ1976.pdf. Este documento descreve o lote de testes do projeto anexo; "
        "não altera o cadastro por desenho técnico do CeraForm 1.0.",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destino))
    return destino


if __name__ == "__main__":
    caminho = gerar()
    print(f"PDF gravado: {caminho} ({caminho.stat().st_size} bytes)")

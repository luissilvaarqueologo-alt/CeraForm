# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import sqlite3
from collections import Counter
from pathlib import Path

from ceraform.volume import faixa_tamanho, rotulo_tamanho

_CAB = Path(__file__).resolve().parent.parent / "CABECALHO.txt"


def _forma_exibida(row: sqlite3.Row) -> str:
    a = (row["forma_confirmada"] or row["forma"] or "").strip()
    b = (row["forma_secundaria_confirmada"] or row["forma_secundaria"] or "").strip()
    if a and b:
        return f"{a} / {b}"
    return a or "(sem forma)"


def _qtde(n: int) -> str:
    return f"Qtde: {n}"


def _qtde_percentual(n: int, pct: float) -> str:
    """Quantidade e percentual com travessão e vírgula decimal (pt-BR)."""
    return f"Qtde: {n} — {pct:.1f} %".replace(".", ",")


def ficha_cabecalho_sitio(sitio: str, linhas: list[sqlite3.Row] | None) -> dict:
    """Pares (rótulo, valor) do resumo do sítio, para grade de três colunas."""
    nome = (sitio or "").strip()
    if not nome:
        return {
            "celulas": [
                ("Situação", "Informe o nome do sítio para ver o relatório."),
            ],
            "nota": "",
        }
    linhas = list(linhas or [])
    total = len(linhas)
    celulas: list[tuple[str, str]] = [
        ("Nome do sítio", nome),
        ("Total de objetos", _qtde(total)),
    ]
    if total == 0:
        return {
            "celulas": celulas,
            "nota": "Não há objetos gravados neste sítio.",
        }
    formas = [_forma_exibida(r).split(" / ")[0] for r in linhas]
    cont = Counter(formas)
    ordem = sorted(cont.items(), key=lambda kv: (-kv[1], kv[0]))
    for forma, n in ordem:
        pct = 100.0 * n / total
        celulas.append((f"Ocorrência — {forma}", _qtde_percentual(n, pct)))
    faixas: Counter[str] = Counter()
    for r in linhas:
        faixas[faixa_tamanho(float(r["volume_l"] or 0))] += 1
    for faixa, n in faixas.most_common():
        celulas.append((f"Tamanho — {faixa}", _qtde(n)))
    return {
        "celulas": celulas,
        "nota": (
            "Medidas em centímetro. Volume do objeto em litro. "
            "Formas em ordem de ocorrência neste sítio."
        ),
    }


def cabecalho_estatistico(sitio: str, linhas: list[sqlite3.Row]) -> str:
    ficha = ficha_cabecalho_sitio(sitio, linhas)
    partes = [f"{rotulo}: {valor}" for rotulo, valor in ficha["celulas"]]
    if ficha["nota"]:
        partes.append(str(ficha["nota"]))
    return "    ·    ".join(partes)


def html_relatorio_sitio(sitio: str, linhas: list[sqlite3.Row]) -> str:
    cab = _CAB.read_text(encoding="utf-8").strip() if _CAB.exists() else ""
    total = len(linhas)
    formas = [_forma_exibida(r).split(" / ")[0] for r in linhas]
    cont = Counter(formas)
    ordem = sorted(cont.items(), key=lambda kv: (-kv[1], kv[0]))
    blocos_pct = []
    for nome, n in ordem:
        pct = 100.0 * n / total if total else 0.0
        pct_txt = f"{pct:.1f} %".replace(".", ",")
        blocos_pct.append(
            f"<tr><td>{nome}</td><td>{_qtde(n)}</td><td>{pct_txt}</td></tr>"
        )
    objs = []
    for r in sorted(linhas, key=lambda x: (-cont[_forma_exibida(x).split(' / ')[0]], x["numero"])):
        vol = float(r["volume_l"] or 0)
        aprox = " sim" if r["aproximacao"] else " não"
        objs.append(
            "<tr>"
            f"<td>{r['numero']}</td>"
            f"<td>{_forma_exibida(r)}</td>"
            f"<td>{rotulo_tamanho(vol)}</td>"
            f"<td>{float(r['h']):.1f}</td>"
            f"<td>{float(r['dmax']):.1f}</td>"
            f"<td>{vol:.3f}</td>"
            f"<td>{aprox}</td>"
            "</tr>"
        )
    faixas: Counter[str] = Counter()
    for r in linhas:
        faixas[faixa_tamanho(float(r["volume_l"] or 0))] += 1
    resumo = "".join(
        f"<tr><td>{nome}</td><td>{n}</td></tr>" for nome, n in faixas.most_common()
    )
    ficha = ficha_cabecalho_sitio(sitio, linhas)
    blocos_ficha = "".join(
        f'<div class="cel"><span class="rot">{rotulo}</span>'
        f"<strong>{valor}</strong></div>"
        for rotulo, valor in ficha["celulas"]
    )
    nota_ficha = ficha["nota"]
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório do sítio {sitio}</title>
<style>
  body {{ font-family: "Times New Roman", Times, "Liberation Serif", serif; font-size: 12pt; margin: 24px; color: #111; }}
  pre.cab {{ font-size: 12pt; white-space: pre-wrap; border-bottom: 1px solid #ccc; padding-bottom: 12px; }}
  h1 {{ font-size: 16pt; font-weight: bold; }}
  h2 {{ font-size: 13pt; font-weight: bold; }}
  .ficha {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px 24px; margin: 12px 0 8px; }}
  .cel .rot {{ display: block; color: #6b6358; }}
  .cel strong {{ font-weight: bold; color: #1a1512; }}
  .nota {{ color: #4a4038; margin: 0 0 20px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; font-size: 12pt; }}
  th, td {{ border: 1px solid #bbb; padding: 4px 8px; text-align: left; }}
  th {{ background: #eee; }}
</style>
</head>
<body>
<pre class="cab">{cab}</pre>
<h1>Relatório por sítio</h1>
<div class="ficha">
{blocos_ficha}
</div>
<p class="nota">{nota_ficha}</p>
<h2>Ocorrência das formas</h2>
<table>
<tr><th>Forma geométrica</th><th>Quantidade</th><th>Percentual</th></tr>
{''.join(blocos_pct)}
</table>
<h2>Objetos cadastrados</h2>
<table>
<tr><th>Número do desenho</th><th>Forma geométrica</th><th>Tamanho</th>
<th>Altura total</th>
<th>Diâmetro máximo</th><th>Volume (L)</th><th>Aproximação</th></tr>
{''.join(objs)}
</table>
<h2>Resumo por volume</h2>
<p>Pequeno: até 1,0 L (inclui volumes abaixo de 0,150 L, com observação).
Médio: 1,0 L até 4,0 L. Grande: 4,0 L até 16,0 L.
Extra grande: a partir de 16,0 L (inclui volumes a partir de 50,0 L, com observação).</p>
<table>
<tr><th>Tamanho</th><th>Quantidade</th></tr>
{resumo}
</table>
</body>
</html>
"""


def gravar_relatorio_html(caminho: Path, sitio: str, linhas: list[sqlite3.Row]) -> None:
    caminho.write_text(html_relatorio_sitio(sitio, linhas), encoding="utf-8")


def texto_relatorio_sitio(sitio: str, linhas: list[sqlite3.Row]) -> str:
    total = len(linhas)
    formas = [_forma_exibida(r).split(" / ")[0] for r in linhas]
    cont = Counter(formas)
    ordem = sorted(cont.items(), key=lambda kv: (-kv[1], kv[0]))
    out = [
        f"Sítio: {sitio}",
        f"Total de objetos: {total}",
        "Medidas em centímetro. Volume do objeto em litro.",
        "",
        "Ocorrência das formas",
        "-" * 48,
    ]
    for nome, n in ordem:
        pct = 100.0 * n / total if total else 0.0
        out.append(f"  {nome}: {_qtde_percentual(n, pct)}")
    out += ["", "Objetos cadastrados", "-" * 48]
    for r in sorted(linhas, key=lambda x: str(x["numero"])):
        vol = float(r["volume_l"] or 0)
        aprox = "sim" if r["aproximacao"] else "não"
        out.append(
            f"  Número do desenho {r['numero']}  |  "
            f"{_forma_exibida(r)}  |  "
            f"altura total {float(r['h']):.1f} cm  |  "
            f"maior diâmetro da peça {float(r['dmax']):.1f} cm  |  "
            f"volume do objeto {vol:.3f} L  |  "
            f"tamanho {rotulo_tamanho(vol)}  |  "
            f"aproximação {aprox}"
        )
    faixas: Counter[str] = Counter()
    for r in linhas:
        faixas[faixa_tamanho(float(r["volume_l"] or 0))] += 1
    out += ["", "Resumo por volume", "-" * 48]
    for nome, n in faixas.most_common():
        out.append(f"  {nome}: {_qtde(n)}")
    return "\n".join(out) + "\n"


def gravar_relatorio_csv(caminho: Path, sitio: str, linhas: list[sqlite3.Row]) -> None:
    import csv

    campos = [
        "Nome do sítio",
        "Número do desenho",
        "Forma geométrica",
        "Tamanho",
        "Altura total (cm)",
        "Diâmetro da borda (cm)",
        "Maior diâmetro da peça (cm)",
        "Altura da base até o maior diâmetro (cm)",
        "Diâmetro da base (cm)",
        "Volume do objeto (L)",
        "Aproximação",
    ]
    with caminho.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(campos)
        for r in linhas:
            vol = float(r["volume_l"] or 0)
            w.writerow(
                [
                    r["sitio"],
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
                ]
            )


def html_para_pdf(html: Path, pdf: Path) -> bool:
    import shutil
    import subprocess

    chrome = (
        shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
    )
    if chrome:
        proc = subprocess.run(
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
        )
        return proc.returncode == 0 and pdf.exists()
    wk = shutil.which("wkhtmltopdf")
    if wk:
        proc = subprocess.run(
            [wk, str(html), str(pdf)],
            check=False,
            capture_output=True,
        )
        return proc.returncode == 0 and pdf.exists()
    return False

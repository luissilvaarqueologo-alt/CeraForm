# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import http.server
import shutil
import socketserver
import subprocess
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = Path(__file__).resolve().parent
MD = PASTA / "como_o_sistema_funciona.md"
PDF = PASTA / "como_o_sistema_funciona.pdf"
CAB = RAIZ / "CABECALHO.txt"

FONTS = [
    (
        "Livro",
        "normal",
        "normal",
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
        "Livro-Regular.ttf",
    ),
    (
        "Livro",
        "normal",
        "italic",
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"),
        "Livro-Italic.ttf",
    ),
    (
        "Livro",
        "bold",
        "normal",
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
        "Livro-Bold.ttf",
    ),
    (
        "Livro",
        "bold",
        "italic",
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
        "Livro-BoldItalic.ttf",
    ),
    (
        "Codigo",
        "normal",
        "normal",
        Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
        "Codigo-Regular.ttf",
    ),
]


CSS = """
@font-face { font-family: Livro; src: url("Livro-Regular.ttf") format("truetype"); font-weight: normal; font-style: normal; }
@font-face { font-family: Livro; src: url("Livro-Italic.ttf") format("truetype"); font-weight: normal; font-style: italic; }
@font-face { font-family: Livro; src: url("Livro-Bold.ttf") format("truetype"); font-weight: bold; font-style: normal; }
@font-face { font-family: Livro; src: url("Livro-BoldItalic.ttf") format("truetype"); font-weight: bold; font-style: italic; }
@font-face { font-family: Codigo; src: url("Codigo-Regular.ttf") format("truetype"); font-weight: normal; font-style: normal; }

@page {
  size: A4;
  margin: 18mm 16mm 20mm 16mm;
}

html, body {
  font-family: Livro, "Liberation Serif", "Times New Roman", serif;
  font-size: 11pt;
  line-height: 1.42;
  color: #111;
  background: #fff;
  margin: 0;
}

pre.cab {
  font-family: Codigo, "Liberation Mono", monospace;
  font-size: 7.6pt;
  line-height: 1.28;
  white-space: pre-wrap;
  border-bottom: 0.7pt solid #222;
  padding-bottom: 10pt;
  margin: 0 0 16pt;
  color: #222;
}

h1 { font-size: 18pt; font-weight: bold; margin: 0.6em 0 0.5em; page-break-after: avoid; }
h2 { font-size: 13.2pt; font-weight: bold; margin: 1.35em 0 0.45em; page-break-after: avoid; }
h3 { font-size: 11.6pt; font-weight: bold; margin: 1.1em 0 0.35em; page-break-after: avoid; }
h4 { font-size: 11pt; font-weight: bold; font-style: italic; margin: 0.9em 0 0.3em; page-break-after: avoid; }

p { margin: 0.55em 0; text-align: justify; hyphens: auto; }
li { margin: 0.2em 0; }
code, kbd {
  font-family: Codigo, "Liberation Mono", monospace;
  font-size: 0.88em;
}
pre {
  font-family: Codigo, "Liberation Mono", monospace;
  font-size: 8.4pt;
  background: #f4f4f4;
  border: 0.4pt solid #ccc;
  padding: 7pt 9pt;
  white-space: pre-wrap;
  page-break-inside: avoid;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 8pt 0 12pt;
  font-size: 8.6pt;
  page-break-inside: auto;
}
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th, td {
  border: 0.4pt solid #888;
  padding: 2.5pt 4.5pt;
  vertical-align: top;
  text-align: left;
}
th { background: #ececec; font-weight: bold; }
hr { border: none; border-top: 0.4pt solid #bbb; margin: 1.1em 0; }
blockquote { margin: 0.6em 1.2em; color: #333; }

mjx-container {
  page-break-inside: avoid;
}
mjx-container[jax="CHTML"][display="true"] {
  margin: 0.85em 0 !important;
  font-size: 110% !important;
}
"""


def _chrome() -> str:
    for nome in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        achado = shutil.which(nome)
        if achado:
            return achado
    raise RuntimeError("Chrome/Chromium não encontrado para imprimir o PDF.")


def _corpo_html(md: Path) -> str:
    proc = subprocess.run(
        [
            "pandoc",
            "-f",
            "markdown+tex_math_single_backslash+tex_math_dollars+pipe_tables+backtick_code_blocks+fenced_code_blocks+auto_identifiers",
            "-t",
            "html5",
            "--mathjax",
            "--wrap=none",
            str(md),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def _pagina(corpo: str, cabecalho: str) -> str:
    cab_esc = (
        cabecalho.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Como o sistema funciona</title>
<style>{CSS}</style>
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['\\\\(','\\\\)']],
    displayMath: [['\\\\[','\\\\]']],
    processEscapes: false,
    tags: 'ams'
  }},
  chtml: {{
    scale: 1.06,
    displayAlign: 'center',
    mtextInheritFont: true
  }},
  startup: {{
    pageReady: function () {{
      return MathJax.startup.defaultPageReady().then(function () {{
        document.documentElement.setAttribute('data-mathjax', 'pronto');
      }});
    }}
  }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body>
<pre class="cab">{cab_esc}</pre>
{corpo}
</body>
</html>
"""


def _servir(diretorio: Path) -> tuple[socketserver.TCPServer, str]:
    pasta = str(diretorio)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=pasta, **kwargs)

        def log_message(self, *_args) -> None:
            return

    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    porta = httpd.server_address[1]
    return httpd, f"http://127.0.0.1:{porta}/como.html"


def _esperar_mathjax(chrome: str, url: str, tentativas: int = 20) -> None:
    """Espera o MathJax compor as fórmulas (mjx-container no DOM)."""
    for _ in range(tentativas):
        proc = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--virtual-time-budget=4000",
                "--dump-dom",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if "mjx-container" in (proc.stdout or ""):
            return
        time.sleep(0.4)
    raise RuntimeError(
        "MathJax não compostou as fórmulas a tempo. Verifique a rede (cdn.jsdelivr.net)."
    )


def gerar(destino: Path = PDF) -> Path:
    if not MD.exists():
        raise FileNotFoundError(MD)
    trabalho = PASTA / ".pdf_build_como_funciona"
    if trabalho.exists():
        shutil.rmtree(trabalho)
    trabalho.mkdir()
    for _fam, _w, _s, origem, nome in FONTS:
        if origem.exists():
            shutil.copy2(origem, trabalho / nome)
    cab = CAB.read_text(encoding="utf-8").strip() if CAB.exists() else ""
    (trabalho / "como.html").write_text(
        _pagina(_corpo_html(MD), cab), encoding="utf-8"
    )
    httpd, url = _servir(trabalho)
    chrome = _chrome()
    try:
        time.sleep(0.3)
        _esperar_mathjax(chrome, url)
        proc = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--allow-insecure-localhost",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=25000",
                f"--print-to-pdf={destino}",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0 or not destino.exists():
            raise RuntimeError(
                "Falha ao imprimir o PDF.\n"
                + (proc.stderr or proc.stdout or "")[:2000]
            )
    finally:
        httpd.shutdown()
        shutil.rmtree(trabalho, ignore_errors=True)
    return destino


if __name__ == "__main__":
    caminho = gerar()
    print(f"PDF gravado: {caminho} ({caminho.stat().st_size} bytes)")

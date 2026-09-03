# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ceraform.relatorio import (
    ficha_cabecalho_sitio,
    gravar_relatorio_csv,
    gravar_relatorio_html,
    html_para_pdf,
    html_relatorio_sitio,
)


def _linhas(registos: list[dict]) -> list[sqlite3.Row]:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE vasos (
            sitio TEXT,
            numero TEXT,
            forma TEXT,
            forma_confirmada TEXT,
            forma_secundaria TEXT,
            forma_secundaria_confirmada TEXT,
            volume_l REAL,
            aproximacao INTEGER,
            h REAL,
            dmax REAL,
            db REAL,
            hmax REAL,
            dbase REAL
        )
        """
    )
    for r in registos:
        con.execute(
            """
            INSERT INTO vasos VALUES (
                :sitio, :numero, :forma, :forma_confirmada,
                :forma_secundaria, :forma_secundaria_confirmada,
                :volume_l, :aproximacao, :h, :dmax, :db, :hmax, :dbase
            )
            """,
            {
                "sitio": r.get("sitio", "Sítio Teste"),
                "numero": r["numero"],
                "forma": r.get("forma", "Globular"),
                "forma_confirmada": r.get("forma_confirmada", r.get("forma", "Globular")),
                "forma_secundaria": r.get("forma_secundaria", ""),
                "forma_secundaria_confirmada": r.get("forma_secundaria_confirmada", ""),
                "volume_l": r.get("volume_l", 0.5),
                "aproximacao": r.get("aproximacao", 0),
                "h": r.get("h", 100.0),
                "dmax": r.get("dmax", 80.0),
                "db": r.get("db", 40.0),
                "hmax": r.get("hmax", 50.0),
                "dbase": r.get("dbase", 30.0),
            },
        )
    return list(con.execute("SELECT * FROM vasos"))


class TestRelatorioSitio(unittest.TestCase):
    """HTML, CSV e PDF usam a forma confirmada e as faixas da seção 10."""

    def setUp(self) -> None:
        self.linhas = _linhas(
            [
                {
                    "numero": "01",
                    "forma": "Ovoide",
                    "forma_confirmada": "Globular",
                    "volume_l": 0.5,
                    "aproximacao": 0,
                },
                {
                    "numero": "02",
                    "forma": "Globular",
                    "forma_confirmada": "Globular",
                    "volume_l": 2.0,
                    "aproximacao": 0,
                },
                {
                    "numero": "03",
                    "forma": "Cilíndrico",
                    "forma_confirmada": "Cilíndrico",
                    "volume_l": 0.10,
                    "aproximacao": 1,
                },
            ]
        )

    def test_ocorrencia_usa_forma_confirmada(self) -> None:
        ficha = ficha_cabecalho_sitio("Sítio Teste", self.linhas)
        rotulos = dict(ficha["celulas"])
        self.assertEqual(rotulos["Total de objetos"], "Qtde: 3")
        self.assertEqual(rotulos["Ocorrência — Globular"], "Qtde: 2 — 66,7 %")
        self.assertEqual(rotulos["Ocorrência — Cilíndrico"], "Qtde: 1 — 33,3 %")
        self.assertNotIn("Ocorrência — Ovoide", rotulos)

    def test_html_tem_percentual_com_virgula_e_campos_por_extenso(self) -> None:
        html = html_relatorio_sitio("Sítio Teste", self.linhas)
        self.assertIn("Relatório por sítio", html)
        self.assertIn("Número do desenho", html)
        self.assertIn("Altura total", html)
        self.assertIn("66,7 %", html)
        self.assertIn("Globular", html)
        self.assertIn("Pequeno (abaixo de 0,150 L)", html)
        self.assertIn(" não", html)
        self.assertIn(" sim", html)

    def test_csv_usa_forma_confirmada_e_separador_ponto_e_virgula(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "sitio.csv"
            gravar_relatorio_csv(caminho, "Sítio Teste", self.linhas)
            with caminho.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.reader(fh, delimiter=";"))
        self.assertEqual(rows[0][0], "Nome do sítio")
        self.assertEqual(rows[0][2], "Forma geométrica")
        formas = [row[2] for row in rows[1:]]
        self.assertIn("Globular", formas)
        self.assertNotIn("Ovoide", formas)

    def test_html_gravado_gera_pdf_quando_ha_conversor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "sitio.html"
            pdf_path = Path(tmp) / "sitio.pdf"
            gravar_relatorio_html(html_path, "Sítio Teste", self.linhas)
            self.assertTrue(html_path.exists())
            ok = html_para_pdf(html_path, pdf_path)
            if ok:
                dados = pdf_path.read_bytes()[:5]
                self.assertEqual(dados, b"%PDF-")
            else:
                self.assertFalse(pdf_path.exists())


if __name__ == "__main__":
    unittest.main()

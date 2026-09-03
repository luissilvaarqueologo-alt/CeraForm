# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NOME_ARQUIVO_BANCO = "ceraform.sqlite"
NOMES_BANCO_LEGADOS = ("archform.sqlite", "vasos.sqlite")


def caminho_banco(raiz: Path) -> Path:
    """Arquivo SQLite do programa; se só existir um nome antigo, passa a usar o novo."""
    novo = Path(raiz) / NOME_ARQUIVO_BANCO
    if novo.exists():
        return novo
    for nome in NOMES_BANCO_LEGADOS:
        antigo = Path(raiz) / nome
        if antigo.exists():
            antigo.rename(novo)
            return novo
    return novo


def garantir_banco(pasta_dados: Path, pasta_recursos: Path | None = None) -> Path:
    """SQLite gravável ao lado do .exe; na primeira abertura copia o modelo embarcado."""
    destino = caminho_banco(pasta_dados)
    if destino.exists():
        return destino
    if pasta_recursos is not None:
        modelo = Path(pasta_recursos) / NOME_ARQUIVO_BANCO
        if modelo.is_file() and modelo.resolve() != destino.resolve():
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(modelo, destino)
    return destino


SCHEMA = """
CREATE TABLE IF NOT EXISTS vasos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sitio TEXT NOT NULL DEFAULT '',
    numero TEXT NOT NULL DEFAULT '',
    h REAL NOT NULL DEFAULT 0,
    db REAL NOT NULL DEFAULT 0,
    dmax REAL NOT NULL DEFAULT 0,
    hmax REAL NOT NULL DEFAULT 0,
    dbase REAL NOT NULL DEFAULT 0,
    dmeio REAL NOT NULL DEFAULT 0,
    largura REAL NOT NULL DEFAULT 0,
    profundidade REAL NOT NULL DEFAULT 0,
    geratriz TEXT NOT NULL DEFAULT '',
    forma TEXT NOT NULL DEFAULT '',
    forma_secundaria TEXT NOT NULL DEFAULT '',
    forma_confirmada TEXT NOT NULL DEFAULT '',
    forma_secundaria_confirmada TEXT NOT NULL DEFAULT '',
    aproximacao INTEGER NOT NULL DEFAULT 0,
    perfil_geometrico TEXT NOT NULL DEFAULT 'Convexo',
    perfil_trecho_base TEXT NOT NULL DEFAULT '',
    perfil_trecho_borda TEXT NOT NULL DEFAULT '',
    contorno_planta TEXT NOT NULL DEFAULT 'Circular',
    altura_carena REAL NOT NULL DEFAULT 0,
    diametro_carena REAL NOT NULL DEFAULT 0,
    altura_carena2 REAL NOT NULL DEFAULT 0,
    diametro_carena2 REAL NOT NULL DEFAULT 0,
    altura_juncao REAL NOT NULL DEFAULT 0,
    diametro_juncao REAL NOT NULL DEFAULT 0,
    espessura_parede REAL NOT NULL DEFAULT 0,
    amostras TEXT NOT NULL DEFAULT '',
    volume_l REAL NOT NULL DEFAULT 0,
    tipo_base TEXT NOT NULL DEFAULT 'Reta',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    forma_alterada_manualmente INTEGER NOT NULL DEFAULT 0,
    UNIQUE (sitio, numero)
);
"""

CAMPOS = (
    "sitio",
    "numero",
    "h",
    "db",
    "dmax",
    "hmax",
    "dbase",
    "dmeio",
    "largura",
    "profundidade",
    "geratriz",
    "forma",
    "forma_secundaria",
    "forma_confirmada",
    "forma_secundaria_confirmada",
    "aproximacao",
    "perfil_geometrico",
    "perfil_trecho_base",
    "perfil_trecho_borda",
    "contorno_planta",
    "altura_carena",
    "diametro_carena",
    "altura_carena2",
    "diametro_carena2",
    "altura_juncao",
    "diametro_juncao",
    "espessura_parede",
    "amostras",
    "volume_l",
    "tipo_base",
    "updated_at",
    "forma_alterada_manualmente",
)

_NOVAS = (
    ("forma_secundaria", "TEXT NOT NULL DEFAULT ''"),
    ("forma_confirmada", "TEXT NOT NULL DEFAULT ''"),
    ("forma_secundaria_confirmada", "TEXT NOT NULL DEFAULT ''"),
    ("aproximacao", "INTEGER NOT NULL DEFAULT 0"),
    ("perfil_geometrico", "TEXT NOT NULL DEFAULT 'Convexo'"),
    ("perfil_trecho_base", "TEXT NOT NULL DEFAULT ''"),
    ("perfil_trecho_borda", "TEXT NOT NULL DEFAULT ''"),
    ("contorno_planta", "TEXT NOT NULL DEFAULT 'Circular'"),
    ("altura_carena", "REAL NOT NULL DEFAULT 0"),
    ("diametro_carena", "REAL NOT NULL DEFAULT 0"),
    ("altura_carena2", "REAL NOT NULL DEFAULT 0"),
    ("diametro_carena2", "REAL NOT NULL DEFAULT 0"),
    ("altura_juncao", "REAL NOT NULL DEFAULT 0"),
    ("diametro_juncao", "REAL NOT NULL DEFAULT 0"),
    ("espessura_parede", "REAL NOT NULL DEFAULT 0"),
    ("amostras", "TEXT NOT NULL DEFAULT ''"),
    ("volume_l", "REAL NOT NULL DEFAULT 0"),
    ("tipo_base", "TEXT NOT NULL DEFAULT 'Reta'"),
    ("updated_at", "TEXT"),
    ("forma_alterada_manualmente", "INTEGER NOT NULL DEFAULT 0"),
)


def _escalar_amostras(texto: str, fator: float) -> str:
    linhas_out: list[str] = []
    for linha in (texto or "").splitlines():
        bruta = linha.strip().replace(";", ",")
        if not bruta:
            continue
        partes = [p.strip() for p in bruta.replace("\t", ",").split(",") if p.strip()]
        if len(partes) < 2:
            linhas_out.append(linha)
            continue
        try:
            alt = float(partes[0].replace(",", ".")) * fator
            diam = float(partes[1].replace(",", ".")) * fator
        except ValueError:
            linhas_out.append(linha)
            continue
        resto = ",".join(partes[2:])
        if resto:
            linhas_out.append(f"{alt:.1f}, {diam:.1f}, {resto}")
        else:
            linhas_out.append(f"{alt:.1f}, {diam:.1f}")
    return "\n".join(linhas_out)


class BancoVasos:
    def __init__(self, caminho: Path) -> None:
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.caminho, timeout=30)
        self.con.row_factory = sqlite3.Row
        self.con.execute(SCHEMA)
        self._migrar()
        self._migrar_cm_para_mm()
        self.con.commit()

    def _migrar(self) -> None:
        existentes = {
            r[1] for r in self.con.execute("PRAGMA table_info(vasos)").fetchall()
        }
        for nome, tipo in _NOVAS:
            if nome not in existentes:
                self.con.execute(f"ALTER TABLE vasos ADD COLUMN {nome} {tipo}")
        existentes = {
            r[1] for r in self.con.execute("PRAGMA table_info(vasos)").fetchall()
        }
        if "updated_at" in existentes:
            self.con.execute(
                """
                UPDATE vasos
                SET updated_at = datetime('now')
                WHERE updated_at IS NULL OR trim(updated_at) = ''
                """
            )
        self.con.execute(
            """
            UPDATE vasos SET
                forma = 'Piriforme'
            WHERE forma = 'Peraforme/Piriforme'
            """
        )
        self.con.execute(
            """
            UPDATE vasos SET
                forma_secundaria = 'Piriforme'
            WHERE forma_secundaria = 'Peraforme/Piriforme'
            """
        )
        self.con.execute(
            """
            UPDATE vasos SET
                forma_confirmada = 'Piriforme'
            WHERE forma_confirmada = 'Peraforme/Piriforme'
            """
        )
        self.con.execute(
            """
            UPDATE vasos SET
                forma_secundaria_confirmada = 'Piriforme'
            WHERE forma_secundaria_confirmada = 'Peraforme/Piriforme'
            """
        )

    def _migrar_cm_para_mm(self) -> None:
        """Garante que o banco esteja em centímetro.

        Histórico de migrações gravadas na tabela meta (chave 'unidade_linear'):
          - ausente ou 'cm' (legado do VASOS.EXE) → converte × 10 → grava 'mm'  [fase 1]
          - 'mm' → converte ÷ 10 → grava 'cm'  [fase 2, adotada em agosto/2026]
          - 'cm' → nada a fazer
        """
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT NOT NULL)"
        )
        row = self.con.execute(
            "SELECT valor FROM meta WHERE chave = 'unidade_linear'"
        ).fetchone()
        unidade = row[0] if row else None

        if unidade == "cm":
            return

        lineares = (
            "h", "db", "dmax", "hmax", "dbase", "dmeio",
            "largura", "profundidade",
            "altura_carena", "diametro_carena",
            "altura_carena2", "diametro_carena2",
            "altura_juncao", "diametro_juncao",
            "espessura_parede",
        )

        if unidade == "mm":
            # Banco estava em milímetro → converter para centímetro (÷ 10)
            sets = ", ".join(f"{c} = {c} / 10.0" for c in lineares)
            self.con.execute(f"UPDATE vasos SET {sets}")
            for rec in self.con.execute(
                "SELECT id, amostras FROM vasos WHERE amostras IS NOT NULL AND amostras <> ''"
            ):
                self.con.execute(
                    "UPDATE vasos SET amostras = ? WHERE id = ?",
                    (_escalar_amostras(rec["amostras"], 0.1), rec["id"]),
                )
        else:
            # Legado do VASOS.EXE (unidade ausente = centímetro original) →
            # o VASOS.EXE já gravava em cm; nenhuma conversão necessária.
            pass

        self._recalcular_volumes()
        self.con.execute(
            "INSERT OR REPLACE INTO meta (chave, valor) VALUES ('unidade_linear', 'cm')"
        )

    def _recalcular_volumes(self) -> None:
        from ceraform.perfil import pares_amostra, perfil_raios
        from ceraform.volume import volume_litros

        for rec in self.con.execute("SELECT * FROM vasos"):
            d = dict(rec)
            if float(d["h"] or 0) <= 0 or float(d["dmax"] or 0) <= 0:
                continue
            z, r = perfil_raios(
                h=max(float(d["h"]), 0.1),
                db=max(float(d["db"] or 0), 0.05),
                dmax=max(float(d["dmax"]), 0.05),
                hmax=float(d["hmax"] or 0) or max(float(d["h"]), 0.1) / 2.0,
                dbase=max(float(d["dbase"] or 0), 0.0),
                dmeio=float(d["dmeio"] or 0),
                perfil_geometrico=d.get("perfil_geometrico") or "Convexo",
                perfil_trecho_base=d.get("perfil_trecho_base") or "",
                perfil_trecho_borda=d.get("perfil_trecho_borda") or "",
                amostras=pares_amostra(d.get("amostras") or ""),
                altura_carena=float(d.get("altura_carena") or 0),
                diametro_carena=float(d.get("diametro_carena") or 0),
                altura_carena2=float(d.get("altura_carena2") or 0),
                diametro_carena2=float(d.get("diametro_carena2") or 0),
                altura_juncao=float(d.get("altura_juncao") or 0),
                diametro_juncao=float(d.get("diametro_juncao") or 0),
                tipo_base=str(d.get("tipo_base") or "Reta"),
            )
            sx = sy = 1.0
            rmax = max(float(d["dmax"]) / 2.0, 1e-6)
            planta = str(d.get("contorno_planta") or "Circular")
            comp = float(d.get("largura") or 0)
            larg = float(d.get("profundidade") or 0)
            if planta in ("Oval", "Quadrangular", "Assimétrico") and comp > 0 and larg > 0:
                sx = (comp / 2.0) / rmax
                sy = (larg / 2.0) / rmax
            vol = volume_litros(
                z,
                r,
                rx_scale=sx,
                ry_scale=sy,
                tipo_planta=planta,
            )
            self.con.execute("UPDATE vasos SET volume_l = ? WHERE id = ?", (vol, d["id"]))

    def filtrar(self, sitio: str = "", numero: str = "") -> list[sqlite3.Row]:
        sql = "SELECT * FROM vasos WHERE 1=1"
        args: list[str] = []
        if (sitio or "").strip():
            sql += " AND sitio LIKE ?"
            args.append(f"%{sitio.strip()}%")
        if (numero or "").strip():
            sql += " AND numero LIKE ?"
            args.append(f"%{numero.strip()}%")
        sql += " ORDER BY sitio, numero"
        return list(self.con.execute(sql, args).fetchall())

    def listar(self) -> list[sqlite3.Row]:
        return self.filtrar()

    def listar_sitio(self, sitio: str) -> list[sqlite3.Row]:
        cur = self.con.execute(
            "SELECT * FROM vasos WHERE sitio = ? ORDER BY numero", (sitio,)
        )
        return list(cur.fetchall())

    def sitios(self) -> list[str]:
        cur = self.con.execute(
            "SELECT DISTINCT sitio FROM vasos WHERE sitio <> '' ORDER BY sitio"
        )
        return [r[0] for r in cur.fetchall()]

    def obter(self, id_: int) -> sqlite3.Row | None:
        cur = self.con.execute("SELECT * FROM vasos WHERE id = ?", (id_,))
        return cur.fetchone()

    def salvar(self, dados: dict[str, Any], id_: int | None = None) -> int:
        texto = {
            "sitio",
            "numero",
            "geratriz",
            "forma",
            "forma_secundaria",
            "forma_confirmada",
            "forma_secundaria_confirmada",
            "perfil_geometrico",
            "perfil_trecho_base",
            "perfil_trecho_borda",
            "contorno_planta",
            "amostras",
            "tipo_base",
        }
        payload = {}
        for c in CAMPOS:
            if c in dados:
                payload[c] = dados[c]
            elif c == "perfil_geometrico":
                payload[c] = "Convexo"
            elif c == "contorno_planta":
                payload[c] = "Circular"
            elif c == "tipo_base":
                payload[c] = "Reta"
            elif c == "updated_at":
                payload[c] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            elif c == "forma_alterada_manualmente":
                payload[c] = 0
            elif c in texto:
                payload[c] = ""
            else:
                payload[c] = 0
        payload["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        try:
            payload["forma_alterada_manualmente"] = int(
                bool(int(payload.get("forma_alterada_manualmente") or 0))
            )
        except (TypeError, ValueError):
            payload["forma_alterada_manualmente"] = 0
        vals = tuple(payload[c] for c in CAMPOS)
        ph = ",".join("?" * len(CAMPOS))
        cols = ",".join(CAMPOS)
        if id_ is None:
            cur = self.con.execute(
                f"INSERT INTO vasos ({cols}) VALUES ({ph})",
                vals,
            )
            self.con.commit()
            return int(cur.lastrowid)
        sets = ",".join(f"{c}=?" for c in CAMPOS)
        self.con.execute(f"UPDATE vasos SET {sets} WHERE id=?", vals + (id_,))
        self.con.commit()
        return id_

    def excluir(self, id_: int) -> None:
        self.con.execute("DELETE FROM vasos WHERE id = ?", (id_,))
        self.con.commit()

    def fechar(self) -> None:
        self.con.close()

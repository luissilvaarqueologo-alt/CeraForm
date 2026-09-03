# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

from pathlib import Path
from typing import Any

from ceraform.classificar import classificar


def _pascal_str(buf: bytes) -> str:
    n = buf[0]
    n = min(n, len(buf) - 1)
    return buf[1 : 1 + n].decode("cp850", errors="replace").strip()


def _tp_real(b: bytes) -> float:
    exp = b[0]
    if exp == 0:
        return 0.0
    sign = -1.0 if (b[5] & 0x80) else 1.0
    mantissa = (
        b[1]
        | (b[2] << 8)
        | (b[3] << 16)
        | (b[4] << 24)
        | ((b[5] & 0x7F) << 32)
    )
    return sign * (mantissa / (2.0 ** 39)) * (2.0 ** (exp - 129))


def ler_vasos_arq(caminho: Path) -> list[dict[str, Any]]:
    data = Path(caminho).read_bytes()
    rec_size = 41
    if len(data) % rec_size != 0:
        raise ValueError(f"VASOS.ARQ: tamanho {len(data)} não é múltiplo de {rec_size}")
    out: list[dict[str, Any]] = []
    for i in range(0, len(data), rec_size):
        rec = data[i : i + rec_size]
        sitio = _pascal_str(rec[0:6])
        numero = _pascal_str(rec[6:17])
        h = _tp_real(rec[17:23]) * 10.0
        dmax = _tp_real(rec[23:29]) * 10.0
        db = _tp_real(rec[29:35]) * 10.0
        dbase = _tp_real(rec[35:41]) * 10.0
        hmax = h / 2.0 if h > 0 else 0.0
        res = classificar(
            h=h, db=db, dmax=dmax, hmax=hmax, dbase=dbase, geratriz="externa"
        )
        out.append(
            {
                "sitio": sitio,
                "numero": numero,
                "h": h,
                "db": db,
                "dmax": dmax,
                "hmax": hmax,
                "dbase": dbase,
                "dmeio": 0.0,
                "largura": 0.0,
                "profundidade": 0.0,
                "geratriz": "externa",
                "forma": res.forma,
            }
        )
    return out

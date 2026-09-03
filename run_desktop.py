# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from pathlib import Path
import os
import sys
import traceback

_congelado = bool(getattr(sys, "frozen", False))
if _congelado:
    _raiz = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
else:
    _raiz = Path(__file__).resolve().parent
    _venv = _raiz / ".venv" / "bin" / "python"
    if not _venv.exists():
        _venv = _raiz / ".venv" / "bin" / "python3"
    _site = (
        _raiz
        / ".venv"
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    if _site.is_dir():
        sys.path.insert(0, str(_site))

    _em_ipython = "IPython" in sys.modules
    if (
        not _em_ipython
        and _venv.exists()
        and Path(sys.executable).resolve() != _venv.resolve()
    ):
        try:
            os.execv(str(_venv), [str(_venv), *sys.argv])
        except OSError:
            pass

sys.path.insert(0, str(_raiz))

if _congelado:
    _dados = Path(sys.executable).resolve().parent
    _mpl = _dados / ".mplconfig"
    _mpl.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(_mpl))
    os.environ.setdefault("XDG_CACHE_HOME", str(_dados / ".cache"))
    os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
    _meipass = getattr(sys, "_MEIPASS", None)
    if _meipass:
        os.environ["PATH"] = str(_meipass) + os.pathsep + os.environ.get("PATH", "")


def _pasta_erro() -> Path:
    if _congelado:
        return Path(sys.executable).resolve().parent
    return _raiz


if __name__ == "__main__":
    try:
        from ceraform.caminhos import anotar_inicio

        anotar_inicio("0 python iniciado")
        from ceraform.ui_desktop import main

        anotar_inicio("1 tela importada")
        main()
    except Exception:
        dest = _pasta_erro() / "ceraform_erro.txt"
        try:
            dest.write_text(traceback.format_exc(), encoding="utf-8")
        except OSError:
            pass
        raise

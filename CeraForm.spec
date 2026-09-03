# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from pathlib import Path

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_all, collect_data_files

RAIZ = Path(SPECPATH)

datas = [
    (str(RAIZ / "ajuda"), "ajuda"),
    (str(RAIZ / "documentacao" / "como_o_sistema_funciona.pdf"), "documentacao"),
    (str(RAIZ / "documentacao" / "arquitetura_e_fluxo.html"), "documentacao"),
    (str(RAIZ / "documentacao" / "arquitetura_e_fluxo.svg"), "documentacao"),
    (str(RAIZ / "documentacao" / "historico.md"), "documentacao"),
    (str(RAIZ / "Imagens" / "Logo CeraForm.png"), "Imagens"),
    (str(RAIZ / "CABECALHO.txt"), "."),
    (str(RAIZ / "build" / "demo_sqlite" / "ceraform.sqlite"), "."),
]
datas += collect_data_files("matplotlib", includes=["mpl-data/**"])
binaries = []
hidden = [
    "matplotlib.backends.backend_tkagg",
    "matplotlib.backends.backend_agg",
    "PIL._tkinter_finder",
    "scipy.interpolate",
    "numpy",
    "pyvista",
    "vtk",
    "vtkmodules",
    "vtkmodules.all",
    "vtkmodules.util",
    "vtkmodules.util.numpy_support",
    "vtkmodules.vtkRenderingOpenGL2",
    "vtkmodules.vtkRenderingUI",
    "vtkmodules.vtkRenderingCore",
    "vtkmodules.vtkRenderingFreeType",
    "vtkmodules.vtkRenderingAnnotation",
    "vtkmodules.vtkFiltersCore",
    "vtkmodules.vtkFiltersGeneral",
    "vtkmodules.vtkFiltersSources",
    "vtkmodules.vtkFiltersGeometry",
    "vtkmodules.vtkFiltersExtraction",
    "vtkmodules.vtkFiltersTexture",
    "vtkmodules.vtkCommonCore",
    "vtkmodules.vtkCommonDataModel",
    "vtkmodules.vtkCommonExecutionModel",
    "vtkmodules.vtkCommonTransforms",
    "vtkmodules.vtkCommonMath",
    "vtkmodules.vtkIOImage",
    "vtkmodules.vtkIOXML",
    "vtkmodules.vtkIOLegacy",
    "vtkmodules.vtkImagingCore",
    "scooby",
    "pooch",
]

for pacote in ("pyvista", "vtkmodules", "vtk", "scooby"):
    try:
        d, b, h = collect_all(pacote)
    except Exception:
        continue
    datas += d
    binaries += b
    hidden += h

_PULAR_DADOS = (
    "plotly",
    "pyvista/examples",
    "pyvista/jupyter",
    "/tests/",
    "trame",
)


def _dado_necessario(item) -> bool:
    destino = str(item[1] if isinstance(item, (tuple, list)) else item)
    s = destino.replace("\\", "/").casefold()
    return not any(p in s for p in _PULAR_DADOS)


datas = [x for x in datas if _dado_necessario(x)]
hidden = [h for h in hidden if "plotly" not in str(h).casefold() and "trame" not in str(h).casefold()]

excludes = [
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
    "tkinter.test",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "plotly",
]

a = Analysis(
    [str(RAIZ / "run_desktop.py")],
    pathex=[str(RAIZ)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(RAIZ / "ceraform" / "rthook_vtk.py")],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CeraForm",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(RAIZ / "Imagens" / "ceraform.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CeraForm_Windows",
)

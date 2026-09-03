# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

"""Runtime hook PyInstaller: DLLs do VTK e modo off-screen no executável."""

import os
import sys

_meipass = getattr(sys, "_MEIPASS", None)
if _meipass:
    os.environ["PATH"] = str(_meipass) + os.pathsep + os.environ.get("PATH", "")
    os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
    os.environ.setdefault("VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN", "1")

    eh_wine = False
    if sys.platform == "win32":
        try:
            import winreg

            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Wine")
            eh_wine = True
        except OSError:
            eh_wine = bool(os.environ.get("WINELOADER") or os.environ.get("WINEPREFIX"))
    if eh_wine:
        os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
        os.environ.setdefault("GALLIUM_DRIVER", "llvmpipe")
        os.environ.setdefault("MESA_GL_VERSION_OVERRIDE", "3.3")
        os.environ.setdefault("MESA_GLSL_VERSION_OVERRIDE", "330")

    try:
        import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
        import vtkmodules.vtkRenderingUI  # noqa: F401
        import vtkmodules.vtkRenderingCore  # noqa: F401
        import vtkmodules.vtkRenderingFreeType  # noqa: F401
    except Exception:
        pass

# SPDX-License-Identifier: GPL-2.0-or-later
"""TurboCAD — FreeCAD addon for native CAD file inspection.

Modern ``freecad/`` namespace layout. Importing this package is headless-safe:
no FreeCAD GUI is required. The actual analysis lives in the pure-Python
``turbo_cad`` subpackage, which is also usable from scripts and CI.
"""
import os

try:
    from FreeCAD import Console
except ImportError:  # plain Python (tests, CLI, CI)
    Console = None

__version__ = "0.0.2"

from . import turbo_cad  # noqa: E402  (import order: version first)

if Console is not None:
    try:
        Console.PrintLog(f"TurboCAD {__version__}: loaded\n")
    except Exception:  # noqa: BLE001 — logging must never break startup
        pass

_MOD = os.path.dirname(os.path.abspath(__file__))
_ICONS = os.path.join(_MOD, "Resources", "Icons")
if os.path.isdir(_ICONS):
    os.environ.setdefault("TURBOCAD_ICON_DIR", _ICONS)

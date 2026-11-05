# SPDX-License-Identifier: GPL-2.0-or-later
"""TurboCAD GUI bootstrap.

FreeCAD imports this module automatically for addons in the ``freecad/``
namespace whenever the GUI is available. It registers the workbench, its
toolbar/menu and the ``TurboCAD_Inspect`` command.
"""
import os

import FreeCADGui

from . import __version__  # noqa: F401
from .turbo_cad import commands

_ICONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources", "Icons")
ICON_PATH = os.path.join(_ICONS, "turbocad.svg")


class TurboCADWorkbench(FreeCADGui.Workbench):
    """Workbench for inspecting native Solid Edge and Inventor files."""

    MenuText = "TurboCAD"
    ToolTip = "Native Solid Edge / Inventor interoperability (TurboCAD)"
    Icon = ICON_PATH

    def __init__(self):
        pass

    def Initialize(self):
        commands.register_commands()
        self.appendToolbar("TurboCAD", ["TurboCAD_Inspect"])
        self.appendMenu("TurboCAD", ["TurboCAD_Inspect"])

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addIconPath(_ICONS)
FreeCADGui.addWorkbench(TurboCADWorkbench)

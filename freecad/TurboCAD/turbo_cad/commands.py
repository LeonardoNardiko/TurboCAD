# SPDX-License-Identifier: GPL-2.0-or-later
"""commands.py — comandos do workbench TurboCAD (Fase 0).

Comando principal: TurboCAD_Inspect — "Analisar arquivo nativo".
Abre diálogo de arquivo, analisa via orchestrator e exibe relatório PySide,
com opção de salvar .md. FreeCADGui/PySide importados apenas dentro de funções
para que o módulo continue importável em modo headless (scripts/CI).
"""
from __future__ import annotations

import os

from . import orchestrator

FILTERS = (
    "Formatos nativos (*.par *.asm *.psm *.pwd *.ipt *.iam *.idw *.ipn);;"
    "Solid Edge (*.par *.asm *.psm *.pwd);;"
    "Inventor (*.ipt *.iam *.idw *.ipn);;"
    "Todos (*.*)"
)


def _get_gui():
    import FreeCADGui
    return FreeCADGui


def _get_qt():
    import PySide2  # FreeCAD 1.x usa PySide2/Qt5 internamente (fallback PySide6)
    QtWidgets = PySide2.QtWidgets
    QtCore = PySide2.QtCore
    return QtWidgets, QtCore


def _show_report_window(title: str, text: str, path: str):
    """Abre janela de relatório com botão salvar .md. Bloqueia até fechar."""
    QtWidgets, QtCore = _get_qt()
    from PySide2.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QPushButton, QHBoxLayout
    from PySide2.QtCore import Qt

    dlg = QDialog()
    dlg.setWindowTitle(title)
    dlg.resize(900, 640)
    layout = QVBoxLayout(dlg)

    txt = QPlainTextEdit()
    txt.setReadOnly(True)
    txt.setPlainText(text)
    txt.setFont(QtWidgets.QFont("Consolas", 9))
    layout.addWidget(txt)

    btn_row = QHBoxLayout()
    save_btn = QPushButton("Salvar relatório .md")
    close_btn = QPushButton("Fechar")

    def save():
        from PySide2.QtWidgets import QFileDialog
        default = os.path.splitext(path)[0] + "_turbofreecad.md"
        target, _ = QFileDialog.getSaveFileName(dlg, "Salvar relatório", default, "Markdown (*.md)")
        if target:
            try:
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write(text)
                dlg.setWindowTitle(title + f" — salvo: {os.path.basename(target)}")
            except OSError as exc:
                QtWidgets.QMessageBox.warning(dlg, "TurboCAD", f"Não foi possível salvar:\n{exc}")

    save_btn.clicked.connect(save)
    close_btn.clicked.connect(dlg.accept)
    btn_row.addStretch(1)
    btn_row.addWidget(save_btn)
    btn_row.addWidget(close_btn)
    layout.addLayout(btn_row)

    dlg.exec_()


class InspectCommand:
    """TurboCAD: Analisar arquivo nativo (.par/.asm/.ipt/.iam)."""

    def GetCommands(self):
        return ["TurboCAD_Inspect"]

    def GetDefault(self):
        return "TurboCAD_Inspect"

    def GetToolbarName(self):
        return "TurboCAD"

    def IsActive(self):
        return True


class TurboCADInspect:
    def GetResources(self):
        return {
            "Pixmap": "turbocad.svg",
            "MenuText": "Analisar arquivo nativo",
            "ToolTip": "Analisa .par/.asm/.psm/.ipt/.iam: tipo, sinais, streams e metadados",
        }

    def Activated(self):
        FreeCADGui = _get_gui()
        QtWidgets, _ = _get_qt()
        from PySide2.QtWidgets import QFileDialog

        fpath, _ = QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(), "Selecionar arquivo CAD nativo", "", FILTERS
        )
        if not fpath:
            return
        bundle = orchestrator.inspect(fpath)
        report = orchestrator.render_report(bundle)
        title = f"TurboCAD — {os.path.basename(fpath)}"
        if bundle.errors:
            QtWidgets.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "TurboCAD",
                "Análise concluída com avisos/erros (ver relatório).",
            )
        _show_report_window(title, report, fpath)

    def IsActive(self):
        return True


def register_commands():
    """Registra os comandos no FreeCAD (chamado pelo Init.py)."""
    FreeCADGui = _get_gui()
    if hasattr(FreeCADGui, "addCommand"):
        FreeCADGui.addCommand("TurboCAD_Inspect", TurboCADInspect())

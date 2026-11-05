# SPDX-License-Identifier: GPL-2.0-or-later
"""model.py — modelo unificado (Fase 0: metadados/estrutura).

Estruturas de dados compartilhadas entre núcleo, relatório e futuras engines.
Python puro, sem dependência FreeCAD.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetaBundle:
    """Resultado da análise de um arquivo nativo (container + estrutura + metadados)."""

    path: str = ""
    container: str | None = None          # "ole2" | None
    ole: bool = False
    clsid: str | None = None
    signals: dict = field(default_factory=dict)
    type: dict = field(default_factory=dict)       # family/kind/ext_type/confidence
    streams: list = field(default_factory=list)    # [{name,size,size_fmt}]
    stream_count: int = 0
    properties: dict = field(default_factory=dict)  # property sets / iProperties
    fidelity: str = "unknown"                      # unknown | metadata | brep | mesh | parametric
    errors: list = field(default_factory=list)

    def is_ok(self) -> bool:
        return not self.errors and self.ole

    def has_signal(self, name: str) -> bool:
        return bool(self.signals.get(name))


@dataclass
class InspectReport:
    """Relatório textual consolidado para exibição/exportação."""

    text: str = ""
    bundle: MetaBundle | None = None
    md_path: str | None = None

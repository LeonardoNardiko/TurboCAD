# SPDX-License-Identifier: GPL-2.0-or-later
"""orchestrator.py — orquestração: detecção de formato e seleção de engine.

Fase 0: usa turbo_cad.ole_reader (fonte única de verdade) + metadata.
Nas fases seguintes constrói o modelo unificado (MetaBundle) e escolhe engine.
"""
from __future__ import annotations

from . import metadata, model, ole_reader


def inspect(path: str) -> model.MetaBundle:
    """Analisa um arquivo nativo e devolve MetaBundle completo. Nunca lança."""
    raw = ole_reader.analyze(path)
    bundle = model.MetaBundle(
        path=path,
        container=raw.get("container"),
        ole=raw.get("ole", False),
        clsid=raw.get("clsid"),
        signals=raw.get("signals", {}),
        type=raw.get("type", {}),
        streams=raw.get("streams", []),
        stream_count=raw.get("stream_count", 0),
        errors=list(raw.get("errors", [])),
    )
    meta = metadata.extract_all(path, raw.get("signals"))
    bundle.properties = {
        "property_sets": meta.get("property_sets", {}),
        "inventor": meta.get("inventor", {}),
    }
    bundle.errors.extend(meta.get("errors", []))
    # Fidelidade: nesta fase só metadados/estrutura foram decodificados.
    bundle.fidelity = "metadata"
    return bundle


def render_report(bundle: model.MetaBundle) -> str:
    """Gera relatório textual rico (base para GUI e exportação .md)."""
    lines = [f"# Turbo FreeCAD — Análise", ""]
    lines.append(f"- **Arquivo:** `{bundle.path}`")
    lines.append(f"- **Container:** {bundle.container or '—'}")
    t = bundle.type or {}
    lines.append(f"- **Tipo (sinal):** {t.get('family') or 'desconhecido'} (confiança: {t.get('confidence') or 'n/d'})")
    if t.get("ext_type"):
        lines.append(f"- **Tipo (extensão):** {t['ext_type']}")
    lines.append(f"- **CLSID (offset 8):** {bundle.clsid or '—'}")
    lines.append(f"- **Fidelidade:** {bundle.fidelity}")
    lines.append("")

    if bundle.signals:
        lines.append("## Sinais detectados")
        for k in sorted(bundle.signals):
            lines.append(f"- `{k}`: {'sim' if bundle.signals[k] else 'não'}")
        lines.append("")

    if bundle.stream_count:
        lines.append(f"## Streams ({bundle.stream_count})")
        lines.append("| Stream | Tamanho |")
        lines.append("|---|---|")
        for s in sorted(bundle.streams, key=lambda x: x["name"].lower()):
            lines.append(f"| `{s['name']}` | {s['size_fmt']} |")
        lines.append("")

    props = bundle.properties or {}
    ps = props.get("property_sets", {})
    if ps:
        lines.append("## Property sets")
        for sname, entries in ps.items():
            lines.append(f"### {sname}")
            if isinstance(entries, dict) and entries:
                for k, v in entries.items():
                    lines.append(f"- **{k}:** `{v}`")
            lines.append("")
    inv = props.get("inventor", {})
    if inv:
        lines.append("## Metadados Inventor")
        for label, text in inv.items():
            if text.startswith("_error"):
                lines.append(f"- **{label}:** {text}")
            else:
                lines.append(f"### {label}")
                lines.append("```text")
                lines.append(text)
                lines.append("```")
        lines.append("")

    if bundle.errors:
        lines.append("## Erros/avisos")
        for e in bundle.errors:
            lines.append(f"- {e}")
        lines.append("")
    return "\n".join(lines)


def engines_available() -> dict:
    """Quais engines estão disponíveis neste ambiente (Fase 0)."""
    out = {"direct": True}
    try:
        import pythonnet  # noqa: F401
        out["bridge_se_com"] = True
    except Exception:  # noqa: BLE001
        out["bridge_se_com"] = False
    out["bridge_se_cli"] = _find_se_translator() is not None
    return out


def _find_se_translator():
    import glob

    cands = glob.glob(
        r"C:\Program Files\Siemens\Solid Edge*\Program\SolidEdgeTranslationServices.exe"
    )
    return cands[0] if cands else None

# SPDX-License-Identifier: GPL-2.0-or-later
"""ole_reader.py — núcleo único de leitura OLE2 para o Turbo FreeCAD.

FONTE ÚNICA DE VERDADE para dissessão de containers OLE2 de CAD proprietário
(Solid Edge .par/.asm/.psm/.pwd e Inventor .ipt/.iam/.idw/.ipn).

Falhas à prova:
- CLSID é lido do offset correto do header CFB (bytes 8..24), não dos primeiros
  16 bytes (magic + zeros) — bug histórico corrigido.
- Detecção de tipo usa ASSINATURAS de stream (mais confiável que CLSID, que vem
  zerado em arquivos reais): PARASOLID/PSM => Solid Edge; RSeStorage/UFRxDoc => Inventor.
- Nenhuma função lança exceção: erros viram entradas em `errors`.

Dependência: olefile (presente no FreeCAD 1.0.2). Este módulo é Python puro —
não importa FreeCAD, para ser reusável por scripts e pelo workbench.
"""
from __future__ import annotations

import os

import olefile

# Sinais -> tipo de aplicação (detecção por assinatura)
SIGNAL_TYPES = {
    "parasolid": "Solid Edge",
    "psm": "Solid Edge",
    "rsestorage": "Inventor",
    "ufrxdoc": "Inventor",
    "protein": "Inventor",
}

TYPE_BY_EXT = {
    ".par": "Solid Edge Part",
    ".asm": "Solid Edge Assembly",
    ".psm": "Solid Edge Sheet Metal",
    ".pwd": "Solid Edge Weld",
    ".ipt": "Inventor Part",
    ".iam": "Inventor Assembly",
    ".idw": "Inventor Drawing",
    ".ipn": "Inventor Presentation",
}

EXT_NATIVE = tuple(TYPE_BY_EXT.keys())


def read_clsid(path: str):
    """Lê o CLSID do header CFB (bytes 8..24). Retorna hex minúsculo ou None."""
    try:
        with open(path, "rb") as f:
            f.seek(8)
            head = f.read(16)
        if len(head) == 16:
            return head.hex()
    except OSError:
        return None
    return None


def _stream_name(parts) -> str:
    return "/".join(parts)


def _signals(names: str) -> dict:
    """Mapa sinal->bool. Usa nomes de stream normalizados."""
    return {
        "parasolid": "PARASOLID" in names,
        "psm": "PSM" in names,
        "rsestorage": "RSeStorage" in names,
        "ufrxdoc": "UFRxDoc" in names,
        "protein": "Protein" in names,
    }


def _detect_type(signals: dict, ext: str) -> dict:
    """Tipo pelo sinal predominante, com fallback pela extensão."""
    score = {"Solid Edge": 0, "Inventor": 0}
    for sig, app in SIGNAL_TYPES.items():
        if signals.get(sig):
            score[app] += 1
    app = max(score, key=score.get) if any(score.values()) else None
    kind = None
    if app == "Solid Edge":
        kind = "Solid Edge"
    elif app == "Inventor":
        kind = "Inventor"
    ext_type = TYPE_BY_EXT.get(ext)
    return {
        "family": app,          # None | "Solid Edge" | "Inventor"
        "kind": kind,           # igual a family nesta versão (granularidade futura)
        "ext_type": ext_type,   # "Inventor Part" etc., conforme extensão
        "confidence": "signal" if app else ("extension" if ext_type else None),
    }


def analyze(path: str) -> dict:
    """Analisa um arquivo e retorna dict nunca-nulo, nunca-lança.

    Retorna:
        container: "ole2" | None
        ole: bool
        clsid: str|None          (offset 8..24, hex)
        signals: dict[str, bool]
        type: dict               (family/kind/ext_type/confidence)
        streams: list[dict]      (name, size, size_fmt) — apenas se OLE2
        stream_count: int
        property_sets: dict      (best-effort, ver metadata.py para versão rica)
        errors: list[str]
    """
    result = {
        "container": None,
        "ole": False,
        "clsid": None,
        "signals": {},
        "type": {"family": None, "kind": None, "ext_type": None, "confidence": None},
        "streams": [],
        "stream_count": 0,
        "property_sets": {},
        "errors": [],
    }
    if not os.path.exists(path):
        result["errors"].append(f"arquivo não encontrado: {path}")
        return result

    result["clsid"] = read_clsid(path)

    if not olefile.isOleFile(path):
        result["errors"].append("não é container OLE2 (pode ser ZIP, X_T texto ou outro)")
        return result

    ext = os.path.splitext(path)[1].lower()
    try:
        ole = olefile.OleFileIO(path)
    except Exception as exc:  # noqa: BLE001 — falha de parse vira erro reportado
        result["errors"].append(f"falha ao abrir OLE2: {type(exc).__name__}: {exc}")
        return result

    try:
        result["container"] = "ole2"
        result["ole"] = True
        try:
            names = [_stream_name(p) for p in ole.listdir()]
        except Exception as exc:  # noqa: BLE001
            names = []
            result["errors"].append(f"falha ao listar streams: {type(exc).__name__}: {exc}")
        joined = "|".join(names)
        result["signals"] = _signals(joined)
        result["type"] = _detect_type(result["signals"], ext)

        streams = []
        for p in ole.listdir():
            name = _stream_name(p)
            size = -1
            try:
                size = ole.get_size(p)
            except Exception:  # noqa: BLE001 — tamanho opcional
                pass
            streams.append({"name": name, "size": size, "size_fmt": _fmt_size(size)})
        result["streams"] = sorted(streams, key=lambda s: s["name"].lower())
        result["stream_count"] = len(streams)
    finally:
        try:
            ole.close()
        except Exception:  # noqa: BLE001
            pass

    return result


def _fmt_size(n) -> str:
    if n < 0:
        return "?"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def format_report(result: dict) -> str:
    """Relatório textual (console e base do painel GUI)."""
    lines = []
    lines.append("=" * 72)
    lines.append("Turbo FreeCAD — análise OLE2")
    lines.append("=" * 72)
    t = result["type"]
    lines.append(f"  container:      {result['container'] or '—'}")
    lines.append(f"  tipo (sinal):   {t['family'] or 'desconhecido'}  ({t['confidence'] or 'n/d'})")
    if t["ext_type"]:
        lines.append(f"  tipo (extensão): {t['ext_type']}")
    lines.append(f"  CLSID (off 8):  {result['clsid'] or '—'}")
    sigs = result["signals"]
    if sigs:
        lines.append("  sinais:")
        for k in sorted(sigs):
            lines.append(f"    + {k:12s} {'sim' if sigs[k] else 'não'}")
    if result["stream_count"]:
        lines.append(f"  streams ({result['stream_count']}):")
        for s in result["streams"]:
            lines.append(f"    {s['name']:60s} {s['size_fmt']:>10s}")
    for err in result["errors"]:
        lines.append(f"  ! {err}")
    return "\n".join(lines)

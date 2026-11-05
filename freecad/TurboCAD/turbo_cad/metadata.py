# SPDX-License-Identifier: GPL-2.0-or-later
"""metadata.py — extração de metadados de .par/.asm/.ipt/.iam (best-effort).

- Property sets OLE padrão (`SummaryInformation`, `DocumentSummaryInformation`) —
  presentes em .par do Solid Edge (streams com prefixo \\x05).
- iProperties do Inventor: vivem em `RSeStorage/RSeEmbeddings/Contents` e em
  `UFRxDoc` (texto UTF-16). Extração raw + heurísticas.
- Nunca lança: falha vira erro reportado no dict.

Referência de IDs dos property sets (DCE/PIDSI):
  1=codepage, 2=PIDSI_TITLE, 3=PIDSI_SUBJECT, 4=PIDSI_AUTHOR, 5=PIDSI_KEYWORDS,
  6=PIDSI_COMMENTS, 7=PIDSI_TEMPLATE, 8=PIDSI_LASTAUTHOR, 9=PIDSI_REVNUMBER,
  12=PIDSI_CREATE_DTM, 13=PIDSI_LASTSAVE_DTM, 14=PIDSI_LASTPRINTED, 15=PIDSI_EDITTIME
"""
from __future__ import annotations

import os

import olefile

PIDSI_NAMES = {
    1: "codepage",
    2: "title",
    3: "subject",
    4: "author",
    5: "keywords",
    6: "comments",
    7: "template",
    8: "last_author",
    9: "revision",
    12: "created",
    13: "last_saved",
    14: "last_printed",
    15: "edit_time",
}

PROPERTY_STREAMS = ("SummaryInformation", "DocumentSummaryInformation")


def _normalize(value):
    """Converte bytes de propriedades OLE para texto legível."""
    if isinstance(value, bytes):
        for enc in ("utf-16-le", "utf-8", "cp1252"):
            try:
                s = value.decode(enc)
                s = s.strip("\x00 \t\r\n")
                if s:
                    return s
            except UnicodeDecodeError:
                continue
        return value.hex()[:40]
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return value


def extract_property_sets(path: str) -> dict:
    """Lê property sets OLE padrão. Retorna dict {nome_stream: {id: valor}}."""
    out = {}
    if not os.path.exists(path) or not olefile.isOleFile(path):
        return out
    try:
        ole = olefile.OleFileIO(path)
    except Exception:  # noqa: BLE001
        return out
    try:
        try:
            stream_paths = list(ole.listdir())
        except Exception:  # noqa: BLE001
            stream_paths = []
        stream_names = ["/".join(p) for p in stream_paths]
        for sname in ("\x05" + n for n in PROPERTY_STREAMS):
            if sname not in stream_names:
                continue
            try:
                props = ole.getproperties([sname])
                out[sname] = {PIDSI_NAMES.get(k, str(k)): _normalize(v)
                              for k, v in props.items()}
            except Exception as exc:  # noqa: BLE001
                out[sname] = {"_error": f"{type(exc).__name__}: {exc}"}
    finally:
        try:
            ole.close()
        except Exception:  # noqa: BLE001
            pass
    return out


def _extract_utf16(raw: bytes, limit: int = 4000) -> str:
    """Extrai texto legível de um blob possivelmente UTF-16LE."""
    try:
        s = raw.decode("utf-16-le", errors="ignore")
    except UnicodeDecodeError:
        try:
            s = raw.decode("cp1252", errors="ignore")
        except UnicodeDecodeError:
            s = raw.decode("latin-1", errors="ignore")
    chars = []
    for c in s:
        if c == "\x00":
            continue
        if 32 <= ord(c) < 127 or c in "\r\n\t":
            chars.append(c)
        else:
            chars.append("?")
    text = "".join(chars)
    text = "".join(text.split())  # normaliza espaços
    return text[:limit]


def extract_inventor_text(path: str) -> dict:
    """Extrai texto legível dos streams característicos do Inventor (best-effort).

    Retorna dict {stream: texto}, com chaves limitadas a streams relevantes:
    RSeEmbeddings/Contents, UFRxDoc, RSeSegInfo, RSeDbRevisionInfo.
    """
    out = {}
    if not os.path.exists(path) or not olefile.isOleFile(path):
        return out
    try:
        ole = olefile.OleFileIO(path)
    except Exception:  # noqa: BLE001
        return out
    wanted = {
        ("RSeStorage", "RSeEmbeddings", "Contents"): "iProperties (Contents)",
        ("UFRxDoc",): "referências / model states (UFRxDoc)",
        ("RSeStorage", "RSeSegInfo"): "segmentos (RSeSegInfo)",
    }
    try:
        for p in ole.listdir():
            for key, label in wanted.items():
                if tuple(p) == key or tuple(p[: len(key)]) == key:
                    try:
                        raw = ole.openstream(p).read()
                        text = _extract_utf16(raw)
                        if text:
                            out[label] = text
                    except Exception as exc:  # noqa: BLE001
                        out[label] = f"_error: {type(exc).__name__}: {exc}"
                    break
    finally:
        try:
            ole.close()
        except Exception:  # noqa: BLE001
            pass
    return out


def extract_all(path: str, signals: dict | None = None) -> dict:
    """Extrai todos os metadados disponíveis de um arquivo. Nunca lança.

    Retorna:
        property_sets: dict
        inventor: dict
        errors: list[str]
    """
    out = {"property_sets": {}, "inventor": {}, "errors": []}
    try:
        out["property_sets"] = extract_property_sets(path)
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"property sets: {type(exc).__name__}: {exc}")
    try:
        out["inventor"] = extract_inventor_text(path)
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"inventor text: {type(exc).__name__}: {exc}")
    return out

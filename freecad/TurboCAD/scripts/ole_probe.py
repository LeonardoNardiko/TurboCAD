#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""ole_probe.py — dissector de containers OLE2 de CAD proprietário (TurboCAD).

CLI fino sobre turbo_cad.ole_reader (fonte única de verdade). Analisa Solid Edge
(.par/.asm/.psm/.pwd) e Autodesk Inventor (.ipt/.iam/.idw/.ipn), listando streams,
tamanhos e sinais-chave: Parasolid, RSeStorage, property sets, thumbnails.

Uso:
    python ole_probe.py ARQUIVO [ARQUIVO...]
    python ole_probe.py --dir PASTA        # varre um diretório (recursivo)
    python ole_probe.py --md ARQUIVO       # gera relatório Markdown

Dependência: olefile (presente no Python do FreeCAD 1.0.2).
"""
import argparse
import glob
import os
import sys

try:
    import olefile  # noqa: F401 — valida dependência antes de importar o núcleo
except ImportError:
    sys.exit("ERRO: instale olefile (pip install olefile) ou use o Python do FreeCAD.")

# Permite rodar direto do diretório do addon sem instalar o workbench.
_ADDON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ADDON not in sys.path:
    sys.path.insert(0, _ADDON)

from turbo_cad import ole_reader, orchestrator  # noqa: E402


def _probe(path, out_lines):
    result = ole_reader.analyze(path)
    out_lines.append(ole_reader.format_report(result))
    bundle = orchestrator.inspect(path)
    md = orchestrator.render_report(bundle)
    out_lines.append(md)
    return result


def _setup_utf8_stdout():
    """Faz print() sobreviver a console cp1252 (relatórios contêm caracteres não-ASCII)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — stdout sem reconfigure (versões antigas)
        pass


def main():
    _setup_utf8_stdout()
    ap = argparse.ArgumentParser(description="Dissector OLE2 de CAD proprietário")
    ap.add_argument("files", nargs="*", help="arquivos a analisar")
    ap.add_argument("--dir", help="varre diretório recursivamente")
    ap.add_argument("--md", metavar="OUT.md", help="escreve relatório Markdown")
    args = ap.parse_args()

    files = list(args.files)
    if args.dir:
        for ext in ("*.par", "*.asm", "*.psm", "*.pwd", "*.ipt", "*.iam", "*.idw", "*.ipn"):
            files += glob.glob(os.path.join(args.dir, "**", ext), recursive=True)

    if not files:
        ap.print_help()
        sys.exit(1)

    out_lines = []
    for f in files:
        try:
            _probe(f, out_lines)
        except Exception as e:  # noqa: BLE001 — nunca derruba a varredura por um arquivo
            out_lines.append(f"! erro ao analisar {f}: {type(e).__name__}: {e}")

    text = "\n\n".join(out_lines)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Relatório Markdown salvo em: {args.md}")
    else:
        print(text)


if __name__ == "__main__":
    main()

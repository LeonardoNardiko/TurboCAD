# SPDX-License-Identifier: GPL-2.0-or-later
"""test_smoke.py — smoke test headless do núcleo TurboCAD.

Analisa arquivos nativos de amostra (`.par`/`.ipt`) via ole_reader + orchestrator.
Sem GUI. Se não houver amostras, imprime SKIP e sai 0 (usado pelo CI).

Coloque arquivos nativos em ``tests/samples/`` (pasta gitignored) para executar.

Uso:
    python test_smoke.py
    python test_smoke.py [ARQUIVO...]
"""
import glob
import os
import sys

_ADDON = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _ADDON not in sys.path:
    sys.path.insert(0, _ADDON)

from turbo_cad import ole_reader, orchestrator  # noqa: E402

_SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

EXPECTED = {
    "BevelG.par": "Solid Edge",
    "WellmanSpurTemplate1A.par": "Solid Edge",
    "ARollerChainTemplate.par": "Solid Edge",
    "ANSI_ASME_B36.19M_Cano1_Schedule40S_6000_SS.ipt": "Inventor",
}


def collect(files=None):
    found = list(files or [])
    if not found:
        for ext in ("*.par", "*.ipt", "*.asm", "*.psm", "*.iam", "*.idw", "*.ipn"):
            found += glob.glob(os.path.join(_SAMPLES, "**", ext), recursive=True)
    return [f for f in found if "__" not in os.path.basename(f)]


def run(files):
    fails = []
    for f in sorted(files):
        res = ole_reader.analyze(f)
        name = os.path.basename(f)
        expected = EXPECTED.get(name)
        issues = []
        if not res["ole"]:
            issues.append("não é OLE2")
        if res["errors"]:
            issues.append(f"erros: {res['errors']}")
        if expected and res["type"]["family"] != expected:
            issues.append(f"tipo esperado {expected}, veio {res['type']['family']}")
        bundle = orchestrator.inspect(f)
        report = orchestrator.render_report(bundle)
        if not report:
            issues.append("relatório vazio")
        if issues:
            fails.append((name, issues))
            print(f"  FAIL {name}: {'; '.join(issues)}")
        else:
            print(f"  OK   {name}: {res['type']['family']} | {res['stream_count']} streams")
    return fails


def main():
    files = collect(sys.argv[1:])
    if not files:
        print(f"SKIP: sem amostras nativas em {_SAMPLES} (adicione .par/.ipt p/ rodar)")
        return 0
    fails = run(files)
    if fails:
        print(f"\nRESULTADO: FAIL ({len(fails)}/{len(files)})")
        return 1
    print(f"\nRESULTADO: PASS ({len(files)}/{len(files)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

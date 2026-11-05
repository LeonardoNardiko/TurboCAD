# SPDX-License-Identifier: GPL-2.0-or-later
"""test_core.py — unit tests for the turbo_cad core.

Runs with any Python 3.11+ that has `olefile` installed. No FreeCAD and no
sample CAD files required. Used by CI (`.github/workflows/ci.yml`).

Usage:
    python test_core.py
"""
import os
import sys

_ADDON = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _ADDON not in sys.path:
    sys.path.insert(0, _ADDON)

from turbo_cad import ole_reader, orchestrator  # noqa: E402
from turbo_cad import __version__  # noqa: E402


def test_imports():
    assert len(ole_reader.SIGNAL_TYPES) >= 5
    assert len(ole_reader.TYPE_BY_EXT) >= 8
    assert isinstance(__version__, str) and __version__


def test_missing_file_never_raises():
    res = ole_reader.analyze(os.path.join(_ADDON, "definitely_missing.par"))
    assert res["ole"] is False
    assert res["clsid"] is None
    assert res["errors"], "missing file must be reported as an error"


def test_non_ole_file_never_raises():
    p = os.path.join(_ADDON, "..", "..", "README.md")
    res = ole_reader.analyze(p)
    assert res["ole"] is False
    assert res["errors"]


def test_inspect_missing_returns_bundle():
    bundle = orchestrator.inspect(os.path.join(_ADDON, "nope.ipt"))
    assert bundle.ole is False
    assert bundle.errors


def test_render_report_never_empty():
    bundle = orchestrator.inspect(os.path.join(_ADDON, "nope.ipt"))
    report = orchestrator.render_report(bundle)
    assert isinstance(report, str) and report.strip()


def test_engines_available_never_raises():
    eng = orchestrator.engines_available()
    assert eng.get("direct") is True
    assert "bridge_se_com" in eng and "bridge_se_cli" in eng


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {t.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"RESULTADO: {'PASS' if not failed else 'FAIL'} ({len(tests) - failed}/{len(tests)})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

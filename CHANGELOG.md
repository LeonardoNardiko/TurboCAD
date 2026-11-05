# Changelog

## [0.0.2] - 2026-08-14

- Modern FreeCAD addon layout (`freecad/TurboCAD` namespace package).
- `package.xml` moved to the repository root (Addon Manager ready).
- Split GUI bootstrap: `__init__.py` (headless-safe) + `init_gui.py` (workbench registration).
- Added unit tests (`test_core.py`) that run without FreeCAD or sample files.
- Added GitHub Actions CI (byte-compile + unit tests).

## [0.0.1] - 2026-08-13

- First release: native CAD file inspection.
  - OLE2 reader (`ole_reader.py`) with stream-signature type detection and correct CLSID offset.
  - Metadata extraction: Solid Edge property sets and Inventor iProperties/`UFRxDoc`.
  - `TurboCAD_Inspect` command with PySide report window and `.md` export.
  - CLI `ole_probe.py`.

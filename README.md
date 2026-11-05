# TurboCAD — Native CAD Inspector for FreeCAD

[![CI](https://github.com/LeonardoNardiko/TurboCAD/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonardoNardiko/TurboCAD/actions/workflows/ci.yml)
[![FreeCAD 1.x](https://img.shields.io/badge/FreeCAD-1.0%2B%20%7C%201.1-0284c7.svg)](https://www.freecad.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg)](pyproject.toml)
[![License: GPL-2.0+](https://img.shields.io/badge/License-GPL--2.0--or--later-22c55e.svg)](LICENSE)
[![Ecosystem: TecnoPRO](https://img.shields.io/badge/Ecosystem-tecnopro.me-d97706.svg)](https://tecnopro.me)

Inspect native CAD files directly inside FreeCAD — **Solid Edge** (`.par`, `.asm`, `.psm`, `.pwd`) and **Autodesk Inventor** (`.ipt`, `.iam`, `.idw`, `.ipn`) — without opening the source application.

FreeCAD does not natively read these proprietary formats, and neutral formats such as STEP/IGES discard the modelling tree (features, sketches, parameters). TurboCAD starts filling that gap by reading the files themselves: type detection, OLE2 container structure, streams, CLSID and metadata.

> **Current scope (v0.0.2):** structural and metadata inspection. Geometry import and native writing are planned for upcoming releases.

## Features

- **`TurboCAD_Inspect` command** (toolbar/menu of the TurboCAD workbench): pick a native file and get a report with
  - detected type (by stream signature: `PARASOLID`/`PSM` → Solid Edge; `RSeStorage`/`UFRxDoc`/`Protein` → Inventor)
  - OLE2 signals, stream list + sizes, CLSID (correct offset 8–24)
  - property sets (`.par`), Inventor iProperties and `UFRxDoc` text (`.ipt`)
  - "Save report as .md" button
- **CLI tool**: `scripts/ole_probe.py FILE | --dir FOLDER | --md OUT.md`
- Pure-Python core (`freecad/TurboCAD/turbo_cad/`), no FreeCAD import required — usable from scripts and CI.

## Supported formats

| Family | Extensions | Detection signal |
|---|---|---|
| Solid Edge | `.par` `.asm` `.psm` `.pwd` | `PARASOLID`, `PSM` |
| Autodesk Inventor | `.ipt` `.iam` `.idw` `.ipn` | `RSeStorage`, `UFRxDoc`, `Protein` |

## Installation

### Via the FreeCAD Addon Manager (recommended)

Once indexed, open the Addon Manager (Tools → Addon manager), search for **TurboCAD** and install it. Restart FreeCAD and switch to the **TurboCAD** workbench.

### Manual install

1. Download a release (or clone this repository).
2. Copy the `TurboCAD` folder that lives under `freecad/` into FreeCAD's `Mod` directory:
   - Windows: `%APPDATA%\FreeCAD\Mod\`
   - Linux: `~/.local/share/FreeCAD/Mod/`
   - macOS: `~/Library/Application Support/FreeCAD/Mod/`
3. Restart FreeCAD.

## Usage

1. Switch to the **TurboCAD** workbench.
2. Click **Analyze native file** (or *TurboCAD → Analyze native file*).
3. Select a `.par`, `.asm`, `.psm`, `.ipt` or `.iam` file.
4. Review the report; use **Save report .md** to export it.

From a terminal:

```bash
python freecad/TurboCAD/scripts/ole_probe.py model.par
python freecad/TurboCAD/scripts/ole_probe.py --dir /path/to/files --md report.md
```

## Development

```bash
pip install -e ".[dev]"
pip install olefile          # runtime dependency
python freecad/TurboCAD/tests/test_core.py    # unit tests (no FreeCAD needed)
python freecad/TurboCAD/tests/test_smoke.py   # smoke test (needs sample files, see below)
```

Drop native sample files (`.par`/`.ipt`) into `freecad/TurboCAD/tests/samples/` to run the smoke test against them. The folder is gitignored.

## Compatibility

- FreeCAD 1.x (tested on 1.0.2, Python 3.11, `olefile` 0.47).
- Core: cross-platform (pure Python + `olefile`).
- No data leaves your machine — everything runs locally.

## License

[GPL-2.0-or-later](LICENSE). Copyright (C) 2026 Leonardo Nardiko.

# Roop PDF -> Markdown (English-only)

Offline desktop app to convert PDF files into audit-first Markdown/TXT with page markers and OCR fallback.

## Features (v0.2)

- Cross-platform desktop GUI (PySide6)
- Offline conversion (no uploads, no telemetry by default)
- Audit-first output with stable markers: `--- Page N ---`
- Per-page mode decision:
  - `EXTRACT` for robust text-layer pages
  - `OCR` for near-empty/image-heavy/garbled extraction pages (Tesseract `eng`)
- OCR settings:
  - DPI (default `300`)
  - Tesseract auto-detect + manual override
  - Preprocess toggles:
    - Grayscale (default ON)
    - Autocontrast (default ON)
    - Threshold (default OFF)
- Optional de-hyphenation toggle (default OFF)
- Progress UI with page count, elapsed time, ETA, and mode per page
- Preview tabs for Markdown and Text with per-page streaming append
- Metadata JSON output with per-page modes/timings/errors
- Rotating local logs in `logs/`

## Requirements

- Python `3.11+`
- Tesseract OCR installed locally (English language data)
  - Linux (example): `sudo apt install tesseract-ocr tesseract-ocr-eng`
  - Windows: install Tesseract and ensure `tesseract.exe` is on `PATH`, or set it in app Settings

## Quick Start (Linux/Windows)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell

pip install -U pip
pip install -e .
```

Run app:

```bash
python -m roop_pdfmd
```

## Output Files

Given `input.pdf`, output folder contains:

- `input.md`
- `input.txt`
- `input.meta.json`

## Development

Install dev tools:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

## Build Executables

Linux:

```bash
bash scripts/build_linux.sh
```

Windows PowerShell:

```powershell
./scripts/build_windows.ps1
```

Artifacts are created under `dist/`.

## Packaging Notes

- v1 expects user-installed Tesseract.
- Future Windows bundling plan: include `tesseract.exe` and `tessdata/eng.traineddata` in installer/package and default `tesseract_cmd` to bundled path.

## Limitations

- English OCR only (`eng`)
- No advanced layout reconstruction
- ETA is best-effort based on average page time

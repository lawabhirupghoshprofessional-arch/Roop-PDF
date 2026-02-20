$ErrorActionPreference = "Stop"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "PyInstaller not found. Install dev dependencies first: pip install -r requirements-dev.txt"
    exit 1
}

# v1: Tesseract is expected to be user-installed.
# Future: include bundled tesseract + tessdata and wire default path accordingly.
pyinstaller --noconfirm packaging/roop_pdfmd_windows.spec

Write-Host "Build complete. See dist/roop-pdfmd/"

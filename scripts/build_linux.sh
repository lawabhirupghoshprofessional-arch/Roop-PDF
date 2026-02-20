#!/usr/bin/env bash
set -euo pipefail

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "PyInstaller not found. Install dev dependencies first: pip install -r requirements-dev.txt"
  exit 1
fi

pyinstaller --noconfirm packaging/roop_pdfmd_linux.spec

echo "Build complete. See dist/roop-pdfmd/"

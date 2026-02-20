from __future__ import annotations

import argparse

from roop_pdfmd.gui.app import run_app


def main() -> int:
    parser = argparse.ArgumentParser(description="Roop PDF -> Markdown desktop app")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Launch UI in smoke mode and exit immediately.",
    )
    args = parser.parse_args()
    return run_app(smoke=args.smoke)


if __name__ == "__main__":
    raise SystemExit(main())

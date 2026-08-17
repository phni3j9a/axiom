#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python tools/validate.py
python -m unittest discover -s tests -v

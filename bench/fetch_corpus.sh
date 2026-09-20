#!/bin/sh
# Henter korpusene som bench/-skriptene trenger, inn i bench/data/ (gitignorert).
# NoReC: 43k norske anmeldelser 1998-2019, CC BY-NC 4.0. Avledede ressurser
# (frekvenslister o.l.) kan brukes fritt iflg. lisensnoten i repoet.
set -e
cd "$(dirname "$0")/data"
[ -d norec ] || git clone --depth 1 https://github.com/ltgoslo/norec
echo "OK. Kjør deretter:"
echo "  python bench/build_baseline.py"
echo "  python bench/validate_wordlists.py > bench/report_wordlists.md"
echo "  python bench/negative_control.py 500 | tee bench/report_negative_control.md"

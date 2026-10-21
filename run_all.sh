#!/usr/bin/env bash
# Rebuild every output from the committed raw data snapshots. No network access is needed.
# Usage: ./run_all.sh            (from anywhere; Python 3.10+ with requirements.txt installed)
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"

echo "[1/6] Decompressing raw data snapshots"
"$PY" scripts/unpack_raw.py

echo "[2/6] Indicator specification (99 indicators, 2018 values)"
"$PY" scripts/build_spec.py

echo "[3/6] Per-source results (raw/ -> results/)"
for s in oecd_spend/build.py oecd_health/build.py oecd_quality/build.py wb_who/build.py \
         cmwf/build_cmwf.py pharma/build_pharma.py country/urban_rural_physicians.py country/build_results.py; do
  echo "      scripts/$s"; "$PY" "scripts/$s" > /dev/null
done

echo "[4/6] Master dataset, quality checks, figure notes"
mkdir -p outputs/data outputs/figures outputs/validation
"$PY" scripts/final/build_final.py
"$PY" scripts/final/qc.py > /dev/null
"$PY" scripts/final/make_meta.py

echo "[5/6] Figures (modern data) and the 2018 reproduction check"
"$PY" scripts/viz/render_figures.py --data outputs/data/plot_data.csv --meta spec/figure_meta_2026.json --outdir outputs/figures
mv outputs/figures/figures_combined.pdf outputs/Papanicolas2018_figures_2026_update.pdf
"$PY" scripts/viz/make_test_2018_data.py
"$PY" scripts/viz/render_figures.py --data outputs/validation/test_2018_data.csv --meta spec/figure_meta_2018.json \
      --outdir outputs/validation/figures_2018_reproduction --no-combined

echo "[6/6] Excel workbooks"
"$PY" scripts/final/build_workbook.py
"$PY" scripts/final/build_rank_changes.py
"$PY" scripts/final/export_rank_pdf.py || echo "      (LibreOffice not installed: skipped rank-matrix PDF)"
echo "Done. See outputs/"

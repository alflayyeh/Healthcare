"""Write the ORIGINAL 2018 values from spec/indicators.csv in long format, used to check that the
renderer reproduces the published JAMA figures (outputs/validation/figures_2018_reproduction)."""
import csv, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
C = ["USA","GBR","DEU","SWE","FRA","NLD","CHE","DNK","CAN","JPN","AUS"]
out = os.path.join(ROOT, 'outputs', 'validation', 'test_2018_data.csv'); os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['indicator_id', 'country', 'value'])
    for r in csv.DictReader(open(os.path.join(ROOT, 'spec', 'indicators.csv'))):
        for c in C: w.writerow([r['indicator_id'], c, r[f'orig_{c}']])
print('wrote', out)

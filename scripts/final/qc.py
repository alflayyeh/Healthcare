import csv, glob, os, re, collections
rows = list(csv.DictReader(open('outputs/data/master_modern_dataset.csv')))
by = collections.defaultdict(list)
for r in rows: by[r['indicator_id']].append(r)
# raw text corpus per agent for traceability
corpus = {}
for ag in set(r['research_agent'] for r in rows):
    txt = []
    for f in glob.glob(f'raw/{ag}/**/*', recursive=True):
        if os.path.isfile(f) and os.path.getsize(f) < 60e6 and not f.endswith(('.pdf','.geojson','.xlsx','.zip')):
            try: txt.append(open(f, errors='ignore').read())
            except Exception: pass
    corpus[ag] = set(re.findall(r'-?\d+(?:\.\d+)?', '\n'.join(txt)))
def _trace(x, ag, sval=None):
    t = corpus.get(ag)
    if not t: return 'n/a'
    d = len(sval.split('.')[1]) if sval and '.' in sval and not sval.endswith('.0') else 0
    tol = 0.5 * 10**(-d) + 1e-9
    for tok in t:
        try:
            if abs(float(tok) - x) <= tol: return 'yes'
        except ValueError: pass
    return 'no'
qc = []
for i, rs in by.items():
    plot = [r for r in rs if r['value_plot'] != 'NA']
    units = {r['unit'] for r in plot}
    qc.append((i, 'one unit across plotted countries', 'PASS' if len(units) <= 1 else 'REVIEW', '; '.join(units)))
    qc.append((i, '11 countries present, no duplicates', 'PASS' if sorted(r['country'] for r in rs) == sorted(set(r['country'] for r in rs)) and len(rs) == 11 else 'FAIL', ''))
    nosrc = [r['country'] for r in plot if not r['url'] or not r['obs_year']]
    qc.append((i, 'every plotted value has source URL + year', 'PASS' if not nosrc else 'FAIL', ','.join(nosrc)))
    # magnitude vs 2018 (catches %/fraction, per-1000/per-100k, nominal/PPP slips)
    odd = []
    for r in plot:
        o = r['orig_2018_value']
        if o not in ('NA', '') and float(o) != 0 and float(r['value_plot']) != 0:
            q = float(r['value_plot']) / float(o)
            if not (0.33 <= q <= 3): odd.append(f"{r['country']} {o}->{r['value_plot']}")
    qc.append((i, 'magnitude within 1/3x–3x of 2018 value', 'PASS' if not odd else 'REVIEW', '; '.join(odd)))
    nt = [r['country'] for r in plot if r['value_as_retrieved'] != 'NA' and _trace(float(r['value_as_retrieved']), r['research_agent'], r['value_as_retrieved']) == 'no'
          and r['research_agent'] not in ('derived',)]
    qc.append((i, 'retrieved value found verbatim in saved raw source files', 'PASS' if not nt else 'REVIEW', ','.join(nt)))
with open('outputs/data/qc_results.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['indicator_id', 'test', 'result', 'detail']); w.writerows(qc)
c = collections.Counter((t, r) for _, t, r, _ in qc)
for k, v in sorted(c.items()): print(k, v)
for q in qc:
    if q[2] != 'PASS': print(q)

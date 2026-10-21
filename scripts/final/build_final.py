"""Assemble final modern dataset from agent results + orchestrator comparability decisions."""
import csv, glob, re, json, collections
C = ["USA","GBR","DEU","SWE","FRA","NLD","CHE","DNK","CAN","JPN","AUS"]
spec = {r['indicator_id']: r for r in csv.DictReader(open('spec/indicators.csv'))}
order = list(spec)
data = {}; audit = {}
for f in glob.glob('results/*_data.csv'):
    agent = f.split('/')[-1].replace('_data.csv','')
    for r in csv.DictReader(open(f)):
        r['agent'] = agent; data[(r['indicator_id'], r['country'])] = r
for f in glob.glob('results/*_audit.csv'):
    for r in csv.DictReader(open(f)): audit[r['indicator_id']] = r
num = lambda v: None if v in ('NA','',None) else float(v)

rows = {}   # (id,c) -> dict
for (i,c),r in data.items():
    d = dict(r); d['value_raw'] = num(r['value']); d['value_plot'] = d['value_raw']; d['decision'] = ''
    rows[(i,c)] = d

def exclude(i, c, why):
    rows[(i,c)]['value_plot'] = None; rows[(i,c)]['decision'] = 'EXCLUDED FROM FIGURE: ' + why

# --- status-level rule: NOT COMPARABLE / UNAVAILABLE rows are not plotted
for i,a in audit.items():
    if a['status'] in ('NOT COMPARABLE','UNAVAILABLE'):
        for c in C:
            if rows[(i,c)]['value_raw'] is not None:
                exclude(i, c, f"indicator status {a['status']}; value retained in dataset for reference only")

# --- country-level comparability exclusions
exclude('F7_09','USA','OECD US data inpatient-only (2010); outpatient hysterectomies excluded')
exclude('F7_13','USA','OECD US PCI inpatient-only (2010); original used HCUP incl. outpatient; no current HCUP national estimate found')
exclude('F11_09','DEU','German regional physician counts cover ambulatory physicians only')
exclude('F11_10','DEU','German regional physician counts cover ambulatory physicians only')
for i in ('F9_08','F9_09'):
    exclude(i,'USA','US SHA now books employer/individual private insurance as compulsory (HF.1.2.2), so public vs private-insurance split not comparable with 2018 concept')

# --- F1_04: switch to land area (AG.LND.TOTL.K2), consistent for all 11
for c in C:
    d = rows[('F1_04',c)]
    m = re.search(r'AG\.LND\.TOTL\.K2, (\d{4})\) = ([\d.]+) thousand km2', d['notes'])
    assert m, c
    d['value_plot'] = float(m.group(2)); d['plot_year'] = m.group(1)
    d['decision'] = 'Plotted World Bank LAND area (AG.LND.TOTL.K2) instead of surface area: WB surface-area series now includes coastal waters for CAN/FRA/SWE'

# --- F5_02/F5_03: one OECD definition for all countries with data
ph = list(csv.DictReader(open('raw/country/oecd_phys_cat.csv')))
cat = collections.defaultdict(dict)
for x in ph:
    if x['UNIT_MEASURE']=='PT_WR_PRF_HLTH': cat[(x['REF_AREA'],x['HEALTH_PROF'])][x['TIME_PERIOD']] = float(x['OBS_VALUE'])
for c in C:
    g, p = cat.get((c,'EMPLGENE'),{}), cat.get((c,'EMPLPEDI'),{})
    yrs = sorted(set(g)&set(p))
    for i in ('F5_02','F5_03'):
        d = rows[(i,c)]
        if not yrs:
            d['value_plot']=None; d['decision']='EXCLUDED FROM FIGURE: no OECD generalist category (uniform definition); national value kept in value_raw'; continue
        y = yrs[-1]; pc = g[y]+p[y]
        d['value_plot'] = round(pc if i=='F5_02' else 100-pc, 1); d['plot_year'] = y
        d['decision'] = (f'Recomputed with one OECD definition for all countries: generalist medical practitioners {g[y]}% + general paediatricians {p[y]}% of all physicians (OECD unit PT_WR_PRF_HLTH), {y}. Excludes general internal medicine (not separable in OECD/Eurostat).')
        if c=='USA':
            d['plot_url']='https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,DSD_HEALTH_EMP_REAC@DF_PHYS_CAT,1.1/'

# --- remuneration: deflate current-price USD PPP to 2025 USD with US CPI-U (as paper did to 2017 USD)
cpi = {int(r['year']): float(r['cpi_u_annual_avg']) for r in csv.DictReader(open('results/oecd_spend_us_cpi.csv'))}
wage = {(r['country'],int(r['year'])): float(r['value_current_usd_ppp']) for r in csv.DictReader(open('results/oecd_spend_wages_current_ppp.csv'))}
REFY = 2025
for i in ('F5_05','F5_06','F5_07'):
    for c in C:
        d = rows[(i,c)]
        if d['value_raw'] is None: continue
        y = int(d['obs_year']); f = cpi[REFY]/cpi[y]
        d['cpi_factor'] = f; d['value_plot'] = round(d['value_raw']*f)
        d['decision'] = f'Deflated from current {y} USD PPP to {REFY} USD with US CPI-U ({cpi[REFY]}/{cpi[y]}={f:.4f}), following paper method'
# ratios F5_09..11 = remuneration (current, year t) / average wage (current USD PPP, same year t)
for rid, src in (('F5_09','F5_05'),('F5_10','F5_06'),('F5_11','F5_07')):
    for c in C:
        s = rows[(src,c)]; d = {'indicator_id':rid,'country':c,'agent':'derived','flags':'','retrieval_date':'2026-10-07',
             'url': s.get('url','') + ' ; https://sdmx.oecd.org/public/rest/data/OECD.ELS.SAE,DSD_EARNINGS@AV_AN_WAGE,1.0/'}
        ok = s['value_raw'] is not None and not (c=='JPN' and rid!='F5_11')
        if ok:
            y = int(s['obs_year']); w = wage.get((c,y))
            ok = w is not None
        if ok:
            d.update(value_raw=round(s['value_raw']/w,3), value_plot=round(s['value_raw']/w,2), obs_year=str(y), unit='ratio',
                     modern_source=f"Derived: {src} ({s['modern_source']}) / OECD average annual wage, current USD PPP, same year",
                     notes=f"{s['value_raw']:.0f} / {w:.0f} ({y})", decision='')
        else:
            d.update(value_raw=None, value_plot=None, obs_year='', unit='ratio', modern_source='Derived',
                     url='', notes='NA: remuneration missing' if c!='JPN' else 'NA: Japan remuneration is a combined GP+specialist figure (as in 2018 paper)', decision='')
        rows[(rid,c)] = d

# marker for Germany self-reported overweight etc. kept via flags
out=[]
for i in order:
    for c in C:
        d = rows[(i,c)]; s = spec[i]
        out.append({'indicator_id':i,'figure':s['figure'],'section':s['section'],'label':s['label'],'country':c,
            'value_plot':'NA' if d['value_plot'] is None else d['value_plot'],
            'value_as_retrieved':'NA' if d.get('value_raw') is None else d['value_raw'],
            'unit':d.get('unit',''),'obs_year':d.get('plot_year') or d.get('obs_year',''),
            'orig_2018_value':s[f'orig_{c}'],'modern_source':d.get('modern_source',''),'dataset_code':d.get('dataset_code',''),
            'url':d.get('plot_url') or d.get('url',''),'retrieval_date':d.get('retrieval_date','2026-10-07'),'flags':d.get('flags',''),
            'status':audit.get(i,{}).get('status','CLOSE MODERN EQUIVALENT' if i in('F5_09','F5_10','F5_11') else ''),
            'orchestrator_decision':d.get('decision',''),'agent_notes':d.get('notes',''),'research_agent':d.get('agent','')})
with open('outputs/data/master_modern_dataset.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
with open('outputs/data/plot_data.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['indicator_id','country','value'])
    for r in out: w.writerow([r['indicator_id'],r['country'],r['value_plot']])
print(len(out),'rows')

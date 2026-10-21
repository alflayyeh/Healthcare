"""Build results/oecd_spend_data.csv, _audit.csv, wages_current_ppp.csv, us_cpi.csv from raw/oecd_spend files.
Run: python3 -I scripts/oecd_spend/build.py   (from the repository root)
"""
import csv, json, collections, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = ROOT + '/raw/oecd_spend/'
RES = ROOT + '/results/'
CTRY = ['USA', 'GBR', 'DEU', 'SWE', 'FRA', 'NLD', 'CHE', 'DNK', 'CAN', 'JPN', 'AUS']
C = '+'.join(CTRY)
RD = '2026-10-07'
B = 'https://sdmx.oecd.org/public/rest/data/'

URL = {
    'pop': B + f'OECD.ELS.SAE,DSD_POPULATION@DF_POP_HIST,1.0/{C}.POP.PT_POP._T.Y_GE65.?startPeriod=2015&format=csvfilewithlabels',
    'gdp': B + f'OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0/{C}.A.GDPPOP._T.USD_PPP_PS....?startPeriod=2015&format=csvfilewithlabels',
    'idd': B + f'OECD.WISE.INE,DSD_WISE_IDD@DF_IDD,1.0/{C}.A.PR_INC_DISP..PT_POP._T...PL_60?startPeriod=2012&format=csvfilewithlabels',
    'sha': B + f'OECD.ELS.HD,DSD_SHA@DF_SHA,1.1/{C}.A.EXP_HEALTH.XDC+PT_EXP_HLTH._T+HF3._Z..._T._Z._Z.?startPeriod=2015&format=csvfilewithlabels',
    'prot': B + f'OECD.ELS.HD,DSD_HEALTH_PROT@DF_HEALTH_PROT,1.1/{C}.A.HIC.PT_POP.?startPeriod=2015&format=csvfilewithlabels',
    'nhis': 'https://www.cdc.gov/nchs/data/nhis/earlyrelease/Health-Insurance-Coverage-Early-Release-of-Estimates-2025.pdf',
    'phys': B + f'OECD.ELS.HD,DSD_HEALTH_EMP_REAC@DF_PHYS,1.1/{C}.HSE.10P3HB._Z._Z.PHYS._Z.._Z?startPeriod=2010&format=csvfilewithlabels',
    'nurse': B + f'OECD.ELS.HD,DSD_HEALTH_REAC_EMP@DF_NURSE,1.1/{C}.HSE.10P3HB._Z._Z.MINU+MINUQUAL+MINUASSO._Z.._Z?startPeriod=2010&format=csvfilewithlabels',
    'remun': B + f'OECD.ELS.HD,DSD_HEALTH_REAC_EMP@DF_REMUN,1.1/{C}.AI.USD_PPP+XDC+FCTR_WG_A_SAL_A._Z..RINF.._Z.V?startPeriod=2010&format=csvfilewithlabels',
    'wage': B + f'OECD.ELS.SAE,DSD_EARNINGS@AV_AN_WAGE,1.0/{C}.WG..A..MEAN._Z?startPeriod=2010&format=csvfilewithlabels',
    'ppp': B + f'OECD.SDD.NAD,DSD_NAMAIN10@DF_TABLE4,2.0/A.{C}...........?startPeriod=2010&format=csvfilewithlabels',
    'medtech': B + f'OECD.ELS.HD,DSD_HEALTH_REAC_HOSP@DF_MED_TECH,1.1/{C}.MTU.10P6HB._Z._Z._Z._Z.MRI+CT_SCAN+MAMM._T+HP1+HP34?startPeriod=2010&format=csvfilewithlabels',
    'beds': B + f'OECD.ELS.HD,DSD_HEALTH_REAC_HOSP@DF_BEDS_FUNC,1.1/{C}.HB.10P3HB._Z._Z._T._T._Z._Z?startPeriod=2010&format=csvfilewithlabels',
    'bedsltc': B + f'OECD.ELS.HD,DSD_HEALTH_REAC_HOSP@DF_BEDS_FUNC,1.1/{C}.HB.10P3HB+BD._Z._Z.HC3._T._Z._Z?startPeriod=2013&format=csvfilewithlabels',
    'ltcbed': B + f'OECD.ELS.HD,DSD_HEALTH_LTCR@DF_HEALTH_LTCR_BED,1.0/{C}.LTCB.10P3HB_Y_GE65._Z._Z._Z..._Z._Z.A?startPeriod=2010&format=csvfilewithlabels',
    'hfce': B + f'OECD.SDD.NAD,DSD_NAMAIN10@DF_TABLE1_EXPENDITURE,2.0/A.{C}.S14+S1M+S14_S15..P3..........?startPeriod=2015&format=csvfilewithlabels',
    'bls': 'https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0',
}


def rd(f):
    return list(csv.DictReader(open(RAW + f, encoding='utf-8')))


def flagstr(r):
    return ';'.join(x for x in [r.get('OBS_STATUS', ''), r.get('OBS_STATUS2', ''), r.get('OBS_STATUS3', '')] if x and x != 'A')


def series(rows, filt, key=lambda r: r['REF_AREA']):
    d = collections.defaultdict(dict)
    for r in rows:
        if filt(r) and r['OBS_VALUE'] != '':
            d[key(r)][r['TIME_PERIOD']] = (float(r['OBS_VALUE']), flagstr(r))
    return d


def latest(d, c):
    v = d.get(c, {})
    if not v:
        return None, None, ''
    y = max(v)
    return y, v[y][0], v[y][1]


DATA = []
AUDIT = []


def add(ind, c, val, unit, year, src, ds, url, flags='', notes='', dec=None):
    if val is None:
        DATA.append([ind, c, 'NA', unit, '', src, ds, url, RD, flags, notes])
    else:
        v = (int(round(val)) if dec == 0 else round(val, dec)) if dec is not None else val
        DATA.append([ind, c, v, unit, year, src, ds, url, RD, flags, notes])


def audit(ind, status, osrc, msrc, mdef, change, notes):
    rows = [r for r in DATA if r[0] == ind]
    yrs = sorted(set(str(r[4]) for r in rows if r[4] != ''))
    n = sum(1 for r in rows if r[2] != 'NA')
    AUDIT.append([ind, status, osrc, msrc, mdef, ';'.join(yrs), n, change, notes])


# ---------------- F1_02 population 65+ ----------------
d = series(rd('pop65.csv'), lambda r: r['UNIT_MEASURE'] == 'PT_POP' and r['AGE'] == 'Y_GE65')
for c in CTRY:
    y, v, f = latest(d, c)
    add('F1_02', c, v, '% of population', y, 'OECD Population data (historical)', 'OECD.ELS.SAE:DSD_POPULATION@DF_POP_HIST(1.0)', URL['pop'], f,
        'OECD historical population series; original JP/NL/CH came from Commonwealth Fund, now all from OECD' if c in ('JPN', 'NLD', 'CHE') else '', 1)
audit('F1_02', 'DIRECTLY UPDATED', 'OECD.stat elderly population (JP, NL, CH: Commonwealth Fund)', 'OECD Data Explorer, Population data (DF_POP_HIST)',
      'Population aged 65+ as % of total population', 'Same OECD concept; all 11 countries now from OECD (no Commonwealth Fund exception)',
      '2025 values for all countries (status normal).')

# ---------------- F1_03 GDP per capita ----------------
d = series(rd('pdb_gdppop.csv'), lambda r: r['PRICE_BASE'] == 'V' and r['UNIT_MEASURE'] == 'USD_PPP_PS' and r['TRANSFORMATION'] == 'N')
for c in CTRY:
    y, v, f = latest(d, c)
    add('F1_03', c, v / 1000 if v else None, 'thousand USD, current prices, current PPPs', y, 'OECD Productivity Database (PDB)', 'OECD.SDD.TPS:DSD_PDB@DF_PDB(2.0)', URL['gdp'], f, '', 2)
audit('F1_03', 'CLOSE MODERN EQUIVALENT', 'OECD.stat PDB_LV (productivity levels)', 'OECD Data Explorer, Productivity database DF_PDB (GDPPOP, current prices, current PPPs)',
      'GDP per capita, USD current prices and current PPPs (thousands)', 'PDB_LV dataflow is archived (non-production); same measure taken from its successor DF_PDB 2.0',
      'All 2025; SWE and AUS 2025 flagged E (estimate).')

# ---------------- F1_05 poverty 60% ----------------
d = series(rd('idd_pov60.csv'), lambda r: r['AGE'] == '_T' and r['METHODOLOGY'] == 'METH2012' and r['DEFINITION'] == 'D_CUR' and r['POVERTY_LINE'] == 'PL_60')
for c in CTRY:
    y, v, f = latest(d, c)
    add('F1_05', c, v, '% of population', y, 'OECD Income Distribution Database (IDD)', 'OECD.WISE.INE:DSD_WISE_IDD@DF_IDD(1.0)', URL['idd'], f,
        'income definition since 2012, current definition' + ('; latest IDD year for Australia is 2020' if c == 'AUS' else '') + ('; latest IDD year for Japan is 2021' if c == 'JPN' else ''), 1)
audit('F1_05', 'DIRECTLY UPDATED', 'OECD IDD 2015', 'OECD IDD (DF_IDD), PR_INC_DISP, PL_60, METH2012, D_CUR',
      'Poverty rate after taxes and transfers, 60% of median equivalised disposable income, total population, %', 'Same database; values given in % (original was fraction x100).',
      'Years vary by country (AUS 2020, JPN 2021, DNK 2022, NLD 2024 provisional).')

# ---------------- F1_09..F1_16 SHA functional shares ----------------
sha = rd('sha_function_mode.csv')
S = collections.defaultdict(dict)  # (c,func,mode,fs) -> {year:(v,flag)}
for r in sha:
    if r['UNIT_MEASURE'] == 'XDC' and r['PRICE_BASE'] == 'V' and r['OBS_VALUE'] != '':
        S[(r['REF_AREA'], r['FUNCTION'], r['MODE_PROVISION'], r['FINANCING_SCHEME'])][r['TIME_PERIOD']] = (float(r['OBS_VALUE']), flagstr(r))


def g(c, f, m, y, fs='_T'):
    return S.get((c, f, m, fs), {}).get(y)


sha_notes = {}
fun_rows = {k: [] for k in ['F1_09', 'F1_10', 'F1_11', 'F1_12', 'F1_13', 'F1_14', 'F1_15', 'F1_16']}
for c in CTRY:
    # choose latest year with complete breakdown incl. inpatient mode
    cand = sorted(S.get((c, '_T', '_T', '_T'), {}), reverse=True)
    yr = None
    for y in cand:
        if all(g(c, f, m, y) for f, m in [('HC1HC2', 'HBEDT'), ('HC1HC2', 'HBOUT'), ('HC3', '_T'), ('HC5', '_T'), ('HC6', '_T'), ('HC7', '_T')]):
            yr = y
            break
    T = g(c, '_T', '_T', yr)[0]
    comp = {}
    flags = set()
    def val(f, m):
        x = g(c, f, m, yr)
        if x:
            if x[1]:
                flags.update(x[1].split(';'))
            return x[0]
        return None
    inp = val('HC1HC2', 'HBEDT')
    out = val('HC1HC2', 'HBOUT')
    day = val('HC1HC2', 'DAY')
    home = val('HC1HC2', 'HB')
    ltc = val('HC3', '_T')
    goods = val('HC5', '_T')
    gov = val('HC7', '_T')
    prev = val('HC6', '_T')
    hc4 = val('HC4', '_T') or 0.0
    hc0 = val('HC0', '_T') or 0.0
    cur = val('HC1HC2', '_T')
    outp = out + (day or 0.0) if c != 'USA' else out
    shares = {
        'F1_09': 100 * inp / T,
        'F1_10': 100 * outp / T,
        'F1_11': 100 * ltc / T,
        'F1_12': 100 * goods / T,
        'F1_13': 100 * gov / T,
        'F1_14': (100 * home / T) if home is not None else None,
        'F1_15': 100 * prev / T,
    }
    known = sum(v for v in shares.values() if v is not None)
    shares['F1_16'] = 100 - known
    unalloc = (cur - inp - out - (day or 0) - (home or 0)) if cur else 0.0
    total8 = sum(v for v in shares.values() if v is not None)
    note = (f'SHA {yr}, current health expenditure={T:.1f} million NCU; shares computed from XDC values. HC4 ancillary={100*hc4/T:.2f}%, HC9(HC0 unknown)={100*hc0/T:.2f}%, '
            f'curative/rehab not allocated by mode={100*unalloc/T:.2f}%, residual of other functions={100*(T-cur-ltc-hc4-goods-prev-gov-hc0)/T:.2f}%; '
            f'Other = 100 - other 7 rows. Sum of 8 rows = {total8:.1f}.')
    if c not in ('USA',):
        note += f' Outpatient includes day care HC.1.2+HC.2.2 ({100*(day or 0)/T:.2f}%).'
    if day is None and c != 'USA':
        note += ' Day care not reported separately (included in in/outpatient by country).'
    if home is None:
        note += ' Home-based curative care not reported separately.'
    sha_notes[c] = (yr, note, ';'.join(sorted(flags)))
    for k, v in shares.items():
        fun_rows[k].append((c, v, yr))

US_EXTRA = ('US: OECD reports the full mode-of-provision split (inpatient/outpatient) only to 2018; from 2019 the US series reports HC.1+HC.2 total and an outpatient line '
            '(2024: outpatient 29.6%, curative not split = 38.4% of current health expenditure; LTC 7.7, goods 13.5, governance 7.4, prevention 3.3) that is not comparable with the paper\'s split. '
            '2018 is therefore used for all 8 US functions. US outpatient = HC.1.3+HC.2.3 as reported (day care not separable in US NHEA). '
            'The paper\'s +2pp observation-stay adjustment to US inpatient is NOT applied. US home-based curative care not reported by OECD (paper\'s US value 3 likely reflected HC.3 home-based LTC).')
labels = {'F1_09': 'Inpatient curative & rehabilitative (HC.1.1+HC.2.1)', 'F1_10': 'Outpatient curative & rehab (HC.1.3+HC.2.3) + day care (HC.1.2+HC.2.2) for non-US',
          'F1_11': 'Long-term care (health) HC.3', 'F1_12': 'Medical goods HC.5', 'F1_13': 'Governance & financing administration HC.7',
          'F1_14': 'Home-based curative & rehabilitative care HC.1.4+HC.2.4', 'F1_15': 'Preventive care HC.6',
          'F1_16': 'Other: HC.4 ancillary + HC.9 other + any residual (100 minus other 7 rows)'}
for k, rows in fun_rows.items():
    for c, v, yr in rows:
        yr_, note, fl = sha_notes[c]
        n = note + (' ' + US_EXTRA if c == 'USA' else '')
        if c == 'NLD':
            n += ' NLD SHA series has a break in 2021 (all functions flagged B): reclassification shifted spending from inpatient to outpatient/day care, so NLD inpatient (14.5) vs paper (32) is largely methodological.'
        if c == 'CHE' and k == 'F1_16':
            n = 'CHE reports ancillary services HC.4 (7.5%) and HC.9 (2.6%) separately, hence higher Other than in paper (1). ' + n
        if c == 'USA' and k == 'F1_09':
            n = 'OECD inpatient 16.5% (2018); paper had added ~2pp for observation stays (authors estimate) - not replicated. ' + n
        if c == 'USA' and k == 'F1_16':
            n = 'US Other mainly = HC.1+HC.2 spending not allocated by mode (HC.4 not reported separately for US). ' + n
        add(k, c, v, '% of current health expenditure', yr, 'OECD/Eurostat/WHO System of Health Accounts (OECD Health Statistics)', 'OECD.ELS.HD:DSD_SHA@DF_SHA(1.1)', URL['sha'],
            fl, n, 1)
    status = 'DIRECTLY UPDATED'
    chg = 'Same SHA 2011 functional classification; OECD Data Explorer replaces OECD.stat.'
    if k == 'F1_09':
        chg += ' US: paper\'s +2pp observation-stay adjustment not applied (OECD figure reported).'
    if k == 'F1_16':
        chg += ' Other defined as residual so the 8 functions sum to 100%.'
    audit(k, status, 'OECD/Eurostat/WHO SHA (JHAQ) 2015', 'OECD Health Statistics, DF_SHA (function x mode of provision, financing total)', labels[k] + ', % of current expenditure on health',
          chg, 'Latest year with complete function x mode breakdown per country (NLD, DNK, CAN 2025 provisional; JPN, AUS 2023; USA 2018 because US inpatient/outpatient split discontinued after 2018 - see US notes). Same year used for all 8 functions within a country; shares sum to 100.')

# ---------------- F1_17 coverage ----------------
d = series(rd('health_prot.csv'), lambda r: r['UNIT_MEASURE'] == 'PT_POP' and r['INSURANCE_TYPE'] == 'TPRIBASI')
for c in CTRY:
    y, v, f = latest(d, c)
    if c == 'USA':
        add('F1_17', c, 91.7, '% of population', '2025', 'CDC NCHS National Health Interview Survey, Early Release 2025 (100 - % uninsured, all ages)',
            'NHIS Early Release: Health Insurance Coverage 2025', URL['nhis'], '',
            f'NHIS 2025: 8.3% (28.0 million) of all ages uninsured at interview -> 91.7% insured (2024: 8.2% uninsured). Method closest to original (CBO/NHIS). '
            f'Alternative: OECD DF_HEALTH_PROT US public+primary private coverage = {v}% ({y}).', 1)
    else:
        add('F1_17', c, v, '% of population', y, 'OECD Health Statistics, Social protection (healthcare coverage)', 'OECD.ELS.HD:DSD_HEALTH_PROT@DF_HEALTH_PROT(1.1)', URL['prot'], f,
            'Government/compulsory + primary private health insurance (TPRIBASI)', 1)
audit('F1_17', 'DIRECTLY UPDATED', 'OECD Health Statistics; US: CBO/NHIS', 'OECD DF_HEALTH_PROT (TPRIBASI); US: CDC NHIS Early Release 2025',
      'Total public and primary private health insurance coverage, % population', 'Same sources; US from NHIS (CBO not used; NHIS is the survey CBO-style estimates are based on).',
      'US OECD alternative 91.8% (2024). NLD and AUS flagged E.')

# ---------------- F5_01 physicians, F5_04 nurses ----------------
phys = series(rd('phys.csv'), lambda r: True, key=lambda r: (r['REF_AREA'], r['HEALTH_PROF_ACTIVITY_STATUS']))
for c in CTRY:
    y, v, f = latest(phys, (c, 'P'))
    note = 'Practising physicians'
    if v is None:
        y, v, f = latest(phys, (c, 'PA'))
        note = 'Professionally active (practising not reported)'
        f = (f + ';D').strip(';')
    add('F5_01', c, v, 'per 1,000 population', y, 'OECD Health Statistics, Health workforce', 'OECD.ELS.HD:DSD_HEALTH_EMP_REAC@DF_PHYS(1.1)', URL['phys'], f, note, 2)
audit('F5_01', 'CLOSE MODERN EQUIVALENT', 'National sources / Eurostat / OECD (eTable 10), 2013-2017', 'OECD Health Statistics DF_PHYS, practising physicians per 1,000',
      'Practising physicians per 1,000 population', 'Original mixed national sources; now uniformly OECD practising-physician series.',
      'USA latest 2022; AUS values flagged E; GBR 2023 break.')

nur = series(rd('nurse.csv'), lambda r: r['HEALTH_PROF'] == 'MINU', key=lambda r: (r['REF_AREA'], r['HEALTH_PROF_ACTIVITY_STATUS']))
for c in CTRY:
    y, v, f = latest(nur, (c, 'P'))
    note = 'Practising nurses (professional + associate)'
    if v is None:
        y, v, f = latest(nur, (c, 'PA'))
        note = 'Professionally active nurses (practising not reported by OECD for this country); flagged'
        f = (f + ';D').strip(';')
    if c == 'GBR':
        note += '; GBR series flagged D (definition differs)'
    if c == 'DNK':
        note += '; DNK series break 2022; paper value (16.3) not comparable with current practising definition'
    add('F5_04', c, v, 'per 1,000 population', y, 'OECD Health Statistics, Health workforce', 'OECD.ELS.HD:DSD_HEALTH_REAC_EMP@DF_NURSE(1.1)', URL['nurse'], f, note, 2)
audit('F5_04', 'DIRECTLY UPDATED', 'OECD 2015', 'OECD Health Statistics DF_NURSE (MINU, practising)', 'Practising nurses per 1,000 population',
      'Same OECD series.', 'USA only professionally active (12.6, 2024; flagged D). FRA latest 2023.')

# ---------------- F5_07 remuneration hospital nurses ----------------
rem = series(rd('remun_nurse.csv'), lambda r: r['UNIT_MEASURE'] == 'USD_PPP' and r['SEX'] == '_T')
remr = series(rd('remun_nurse.csv'), lambda r: r['UNIT_MEASURE'] == 'FCTR_WG_A_SAL_A' and r['SEX'] == '_T')
for c in CTRY:
    y, v, f = latest(rem, c)
    ry = remr.get(c, {}).get(y)
    note = 'Salaried hospital nurses, current-price USD PPP of observation year (OECD Health Statistics)'
    if ry:
        note += f'; OECD ratio to average wage = {ry[0]:.2f}'
    if c in ('SWE', 'CHE'):
        note += '; NA in original paper, now available'
    add('F5_07', c, v, 'USD PPP current prices, obs year', y, 'OECD Health Statistics, Remuneration of health professionals', 'OECD.ELS.HD:DSD_HEALTH_REAC_EMP@DF_REMUN(1.1)', URL['remun'], f, note, 0)
audit('F5_07', 'DIRECTLY UPDATED', 'OECD.stat remuneration of hospital nurses 2015 (paper: 2017 USD CPI-adjusted)', 'OECD DF_REMUN (RINF, employees, USD_PPP)',
      'Annual remuneration of salaried hospital nurses, USD PPP, current prices of observation year', 'Same series; reported in current USD PPP of the obs year (paper had CPI-inflated to 2017 USD; use results/oecd_spend_us_cpi.csv to rebase if needed).',
      'Most observations flagged D (country-specific definitions as in original). DEU latest 2022, FRA 2023.')

# ---------------- F5_08 average wages ----------------
wrows = rd('avwage_all.csv')
wq = series(wrows, lambda r: r['UNIT_MEASURE'] == 'USD_PPP' and r['PRICE_BASE'] == 'Q')
base = {r['REF_AREA']: r['BASE_PER'] for r in wrows if r['UNIT_MEASURE'] == 'USD_PPP'}
for c in CTRY:
    y, v, f = latest(wq, c)
    add('F5_08', c, v, f'USD PPP, constant prices, {base[c]} reference year (={base[c]} USD PPPs)', y, 'OECD Average annual wages', 'OECD.ELS.SAE:DSD_EARNINGS@AV_AN_WAGE(1.0)',
        URL['wage'].replace('.WG..', '.WG.USD_PPP.'), f, 'Average annual wages per full-time equivalent dependent employee', 0)
audit('F5_08', 'DIRECTLY UPDATED', 'OECD Average annual wages, 2016 constant prices, 2016 USD PPPs', 'OECD AV_AN_WAGE (USD_PPP, constant prices, reference year 2025)',
      'Average annual wages, constant prices at 2025 USD PPPs (equals current 2025 USD PPP for 2025)', 'Same dataset; reference year moved from 2016 to 2025.',
      'Current-price USD PPP series 2015-2025 in results/oecd_spend_wages_current_ppp.csv = wages in national currency (current prices, AV_AN_WAGE PRICE_BASE V) / OECD PPP for household final consumption (DF_TABLE4 PPP_P31S14).')

# wages current ppp table
wv = series(wrows, lambda r: r['PRICE_BASE'] == 'V' and r['UNIT_MEASURE'] not in ('USD_PPP',))
ppp = series(rd('ppp_table4.csv'), lambda r: r['TRANSACTION'] == 'PPP_P31S14')
out = []
chk = []
for c in CTRY:
    for y in sorted(wv.get(c, {})):
        if y >= '2015' and y in ppp.get(c, {}):
            val = wv[c][y][0] / ppp[c][y][0]
            out.append([c, y, round(val, 0)])
            if y == base[c] and y in wq.get(c, {}):
                chk.append((c, round(val), round(wq[c][y][0])))
with open(RES + 'oecd_spend_wages_current_ppp.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['country', 'year', 'value_current_usd_ppp']); w.writerows(out)
print('wage check (computed current 2025 vs OECD constant 2025):', chk)

# CPI
cpi = {}
for fn in ['bls_cpiu_2010_2019.json', 'bls_cpiu_2016_2025.json']:
    for x in json.load(open(RAW + fn))['Results']['series'][0]['data']:
        if x['period'] == 'M13':
            cpi[x['year']] = x['value']
with open(RES + 'oecd_spend_us_cpi.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['year', 'cpi_u_annual_avg', 'series_id', 'source_url'])
    for y in sorted(cpi):
        w.writerow([y, cpi[y], 'CUUR0000SA0 (CPI-U, US city average, all items, 1982-84=100, NSA)', URL['bls']])

# ---------------- F5_12..14 medical technology ----------------
mt = series(rd('medtech.csv'), lambda r: True, key=lambda r: (r['REF_AREA'], r['MEDICAL_TECH'], r['HEALTH_CARE_PROVIDER']))
for ind, tech, nm in [('F5_12', 'MRI', 'MRI units'), ('F5_13', 'CT_SCAN', 'CT scanners'), ('F5_14', 'MAMM', 'Mammographs')]:
    for c in CTRY:
        y, v, f = latest(mt, (c, tech, '_T'))
        note = f'{nm}, total (hospitals + ambulatory)'
        if v is None:
            hy, hv, hf = latest(mt, (c, tech, 'HP1'))
            note = f'No OECD total; hospital-only value {hv} ({hy}) not used (definition differs).' if hv is not None else 'Not reported to OECD.'
        if c == 'CAN' and tech == 'MRI':
            note += ' Original used Commonwealth Fund; OECD now has the Canadian total.'
        if c == 'GBR' and tech == 'MAMM':
            note += ' Original used a BJC journal article (21.0); OECD total now available (estimate, break 2023).'
        if c == 'FRA' and tech == 'MAMM':
            note += ' Paper value 7.5 likely hospital-only.'
        add(ind, c, v, 'per 1,000,000 population', y, 'OECD Health Statistics, Medical technology', 'OECD.ELS.HD:DSD_HEALTH_REAC_HOSP@DF_MED_TECH(1.1)', URL['medtech'], f, note, 2)
audit('F5_12', 'DIRECTLY UPDATED', 'OECD 2014 (Canada: Commonwealth Fund)', 'OECD DF_MED_TECH MRI total', 'MRI units per million population (hospitals+ambulatory)',
      'Same OECD series; Canada now from OECD.', 'CHE total not reported (hospital-only 26.9 in 2024, not used). USA latest 2021, CAN 2022.')
audit('F5_13', 'DIRECTLY UPDATED', 'OECD 2015', 'OECD DF_MED_TECH CT total', 'CT scanners per million population', 'Same OECD series.', 'USA latest 2021, CAN 2022; SWE now available.')
audit('F5_14', 'DIRECTLY UPDATED', 'OECD 2015 (UK: BJC article)', 'OECD DF_MED_TECH mammographs total', 'Mammographs per million population',
      'Same OECD series; UK now from OECD (much lower than the journal figure used in 2018).', 'DEU, FRA, NLD totals not reported (hospital-only exists for DEU/FRA, not used).')

# ---------------- F5_15 hospital beds ----------------
bd = series(rd('beds.csv'), lambda r: True)
for c in CTRY:
    y, v, f = latest(bd, c)
    note = 'Total hospital beds'
    if c == 'AUS':
        rows = rd('beds_aus.csv')
        b2 = series(rows, lambda r: r['UNIT_MEASURE'] == '10P3HB' and r['HEALTH_FUNCTION'] == '_T' and r['CARE_TYPE'] == '_T')
        y, v, f = latest(b2, 'AUS')
        note += '; OECD has no Australian total after 2016'
    add('F5_15', c, v, 'per 1,000 population', y, 'OECD Health Statistics, Hospital beds', 'OECD.ELS.HD:DSD_HEALTH_REAC_HOSP@DF_BEDS_FUNC(1.1)', URL['beds'], f, note, 2)
audit('F5_15', 'DIRECTLY UPDATED', 'OECD 2014', 'OECD DF_BEDS_FUNC total hospital beds', 'Total hospital beds per 1,000 population', 'Same OECD series.',
      'AUS latest 2016, USA 2022, DNK 2025 provisional, CHE 2024 break.')

# ---------------- F5_16 LTC beds ----------------
lb = series(rd('ltcbed.csv'), lambda r: True)
hl = series(rd('beds_ltc_hosp.csv'), lambda r: r['UNIT_MEASURE'] == '10P3HB')
p65 = series(rd('pop65.csv'), lambda r: r['UNIT_MEASURE'] == 'PT_POP')
for c in CTRY:
    y, v, f = latest(lb, c)
    note = 'LTC beds in institutions (nursing homes/residential LTC) per 1,000 aged 65+. '
    h = hl.get(c, {}).get(y)
    if h and y in p65.get(c, {}):
        note += f'Hospital LTC beds (HC.3) same year = {h[0]*100/p65[c][y][0]:.1f} per 1,000 65+ (not added, to keep cross-country definition consistent).'
    else:
        note += 'Hospital LTC beds not reported for this country/year.'
    if c == 'JPN':
        note += ' Japan original 35.1 included hospital LTC beds (~11 per 1,000 65+); not available now -> large apparent drop.'
    add('F5_16', c, v, 'per 1,000 population 65+', y, 'OECD Health Statistics, Long-term care resources', 'OECD.ELS.HD:DSD_HEALTH_LTCR@DF_HEALTH_LTCR_BED(1.0)', URL['ltcbed'], f, note, 1)
audit('F5_16', 'CLOSE MODERN EQUIVALENT', 'OECD 2015 (LTC beds in institutions and hospitals)', 'OECD DF_HEALTH_LTCR_BED (institutions only)',
      'Long-term care beds in institutions per 1,000 population aged 65+', 'OECD no longer publishes the combined institutions+hospitals series; only institution beds are in the LTC dataflow. Hospital LTC (HC.3) beds exist only for CAN, CHE, DEU, NLD, USA (small: 0-2.3 per 1,000 65+) and not for JPN, so they are not added.',
      'USA latest 2022. Many values flagged E (AUS, CAN, GBR, JPN).')

# ---------------- F11_03 OOP % household consumption ----------------
hf = rd('hfce.csv')
hfce = series(hf, lambda r: r['SECTOR'] == 'S14' and r['UNIT_MEASURE'] == 'XDC' and r['PRICE_BASE'] == 'V')
for c in CTRY:
    yrs = [y for y in S.get((c, '_T', '_T', 'HF3'), {}) if g(c, 'HC3', '_T', y, 'HF3') and y in hfce.get(c, {})]
    if not yrs:
        add('F11_03', c, None, '% of household final consumption', None, '', '', '', '', 'missing'); continue
    y = max(yrs)
    oop, f1 = g(c, '_T', '_T', y, 'HF3'); ltc, f2 = g(c, 'HC3', '_T', y, 'HF3'); hc, f3 = hfce[c][y]
    val = 100 * (oop - ltc) / hc
    fl = ';'.join(sorted(set(x for x in (f1 + ';' + f2 + ';' + f3).split(';') if x)))
    note = (f'Computed: (HF.3 OOP current health expenditure {oop:.1f} - HF.3 on HC.3 LTC {ltc:.1f}) / households final consumption expenditure P.31 S.14 {hc:.1f} (million NCU, current prices, {y}). '
            f'Incl. LTC would be {100*oop/hc:.2f}%.')
    if c == 'AUS':
        note += ' SHA for Australia refers to financial year; NA denominator calendar year.'
    add('F11_03', c, val, '% of household final consumption', y, 'OECD SHA (DF_SHA) + OECD National Accounts (DF_TABLE1_EXPENDITURE)', 'OECD.ELS.HD:DSD_SHA@DF_SHA(1.1); OECD.SDD.NAD:DSD_NAMAIN10@DF_TABLE1_EXPENDITURE(2.0)',
        URL['sha'] + ' ; ' + URL['hfce'], fl, note, 2)
audit('F11_03', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2015 (OOP medical spending excl. LTC as % of household final consumption)',
      'Computed from OECD SHA HF.3 (excl. HC.3) and OECD national accounts P.31 S.14',
      'Out-of-pocket medical spending excluding long-term care (health) as % of households final consumption expenditure', 'Ready-made Health at a Glance ratio is not in the SDMX API; recomputed with the same components (HF.3 minus HF.3xHC.3) / HFCE S.14. Social LTC (HCR.1) is not in HC.3 and so is excluded as well.',
      'Same year numerator/denominator per country; NLD, DNK, CAN 2025 (DNK/CAN provisional); JPN, AUS 2023.')

# ---------------- write ----------------
with open(RES + 'oecd_spend_data.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['indicator_id', 'country', 'value', 'unit', 'obs_year', 'modern_source', 'dataset_code', 'url', 'retrieval_date', 'flags', 'notes'])
    w.writerows(DATA)
with open(RES + 'oecd_spend_audit.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['indicator_id', 'status', 'original_source', 'modern_source', 'modern_definition', 'years_used', 'n_countries_available', 'change_vs_2018', 'notes'])
    w.writerows(AUDIT)
cnt = collections.Counter(r[0] for r in DATA)
print(len(DATA), 'rows;', dict(cnt))

# Build results/oecd_quality_data.csv and results/oecd_quality_audit.csv
# Run from project root: python3 -I scripts/oecd_quality/build.py
import csv, os, collections

ROOT = os.getcwd()
RAW = os.path.join(ROOT, 'raw', 'oecd_quality')
C = ['USA', 'GBR', 'DEU', 'SWE', 'FRA', 'NLD', 'CHE', 'DNK', 'CAN', 'JPN', 'AUS']
RD = '2026-10-07'
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,{df},{v}/all?startPeriod=2008&format=csvfilewithlabels'
URL = {k: BASE.format(df=k, v=v) for k, v in [('DSD_HCQO@DF_PE', '2.1'), ('DSD_HCQO@DF_AC', '2.1'), ('DSD_HCQO@DF_PS', '2.1'),
                                               ('DSD_HCQO@DF_PC', '2.1'), ('DSD_HEALTH_PROC@DF_IMMUN', '1.2'),
                                               ('DSD_HEALTH_PROC@DF_SCREEN', '1.2')]}
FLAGNAMES = {'E': 'estimated value', 'B': 'break in series', 'D': 'difference in methodology', 'P': 'provisional'}

def load(df):
    return list(csv.DictReader(open(os.path.join(RAW, 'data_' + df.replace('@', '_') + '.csv'), encoding='utf-8')))

def latest(rows, filt):
    """country -> (year, value, flags) for latest non-missing obs."""
    out = {}
    for r in rows:
        if r['REF_AREA'] not in C or not filt(r) or r['OBS_VALUE'] == '':
            continue
        y = int(r['TIME_PERIOD'])
        fl = ';'.join(f for f in (r.get('OBS_STATUS', ''), r.get('OBS_STATUS2', ''), r.get('OBS_STATUS3', ''), r.get('OBS_STATUS4', '')) if f)
        if r['REF_AREA'] not in out or y > out[r['REF_AREA']][0]:
            out[r['REF_AREA']] = (y, float(r['OBS_VALUE']), fl)
    return out

def flagnote(fl):
    return '; '.join('%s=%s' % (f, FLAGNAMES.get(f, f)) for f in fl.split(';') if f)

data, audit = [], []

def emit(ind, unit, src, df, vals, notes_by_c=None, gen_note='', urls=None):
    for c in C:
        nb = (notes_by_c or {}).get(c, '')
        if c in vals:
            y, v, fl = vals[c]
            n = '; '.join(x for x in [gen_note, nb, flagnote(fl)] if x)
            data.append([ind, c, round(v, 4), unit, y, src, df, (urls or {}).get(c, URL.get(df, '')), RD, fl, n])
        else:
            data.append([ind, c, 'NA', unit, '', src, df, (urls or {}).get(c, URL.get(df, '')), RD, '', '; '.join(x for x in [gen_note, nb or 'no observation in source'] if x)])

def yrs(vals):
    ys = sorted(set(v[0] for v in vals.values()))
    return '-'.join(map(str, [ys[0], ys[-1]])) if len(ys) > 1 else (str(ys[0]) if ys else '')

SRC = 'OECD Data Explorer, Health Care Quality and Outcomes'
PE, AC, PS, PC = load('DSD_HCQO@DF_PE'), load('DSD_HCQO@DF_AC'), load('DSD_HCQO@DF_PS'), load('DSD_HCQO@DF_PC')
IM, SC = load('DSD_HEALTH_PROC@DF_IMMUN'), load('DSD_HEALTH_PROC@DF_SCREEN')

# ---------- F10_03 regular doctor spending enough time ----------
v = latest(PE, lambda r: r['MEASURE'] == 'RHPTIPAT' and r['AGE'] == 'Y_GE16' and r['SEX'] == '_T' and r['STATISTICAL_OPERATION'] == 'VALUEW')
nb = {'CAN': 'CAN 2023 (63.3) is much lower than 2020 (82.4): Commonwealth Fund IHP 2023 survey round; OECD flags difference in methodology',
      'NLD': 'national survey (annual), not Commonwealth Fund',
      'JPN': 'only HPRTIPAT (any doctor, not regular doctor) reported; not the same measure -> NA',
      'DNK': 'not reported to OECD',
      'FRA': 'value from Commonwealth Fund IHP survey as reported by OECD'}
for c in ['USA', 'GBR', 'DEU', 'SWE', 'CHE', 'AUS']:
    nb[c] = 'OECD value sourced from Commonwealth Fund International Health Policy Survey %s (fielded during COVID-19)' % v[c][0] if c in v and v[c][0] == 2020 else ''
emit('F10_03', '% of patients', SRC + ' - Patient experiences (RHPTIPAT)', 'DSD_HCQO@DF_PE', v, nb,
     'Regular doctor spending enough time with patients during consultation, 16+, weighted value')
audit.append(['F10_03', 'DIRECTLY UPDATED', 'OECD.stat HCQI patient experience', SRC + ' DF_PE, measure RHPTIPAT',
              'Regular doctor spending enough time with patients during the consultation, % of patients aged 16+ (weighted)', yrs(v), len(v),
              'Same OECD measure. Original values matched 2013 survey round; newest is mostly CMWF 2020 round (COVID-era); CAN 2023, NLD 2024 national survey.',
              'Most countries rely on Commonwealth Fund IHP surveys (2020 latest in OECD). France now available (NA in original). DNK, JPN NA.'])

# ---------- F10_07 measles ----------
v = latest(IM, lambda r: r['DISEASE'] == 'MEAS' and r['UNIT_MEASURE'] == 'PT_CH_ELG_IM')
emit('F10_07', '% of children', 'OECD Data Explorer, Health care use - Immunisations', 'DSD_HEALTH_PROC@DF_IMMUN', v, {},
     'Measles vaccination coverage, % of children eligible (first dose by recommended age)')
audit.append(['F10_07', 'DIRECTLY UPDATED', 'OECD.stat', 'OECD Data Explorer DSD_HEALTH_PROC@DF_IMMUN, DISEASE=MEAS',
              'Children vaccinated against measles, % of children eligible', yrs(v), len(v),
              'Same OECD series (moved from OECD.stat to Data Explorer).',
              'USA, CAN, SWE latest values flagged E (estimates; WHO/UNICEF-based).'])

# ---------- F10_08 mammography ----------
# original basis per country, inferred by matching original 2013 values to OECD series
basis = {'USA': 'SRV', 'GBR': 'PRG', 'DEU': 'SRV', 'SWE': 'PRG', 'FRA': 'PRG', 'NLD': 'PRG', 'CHE': 'SRV', 'DNK': 'PRG',
         'CAN': 'SRV', 'JPN': 'SRV', 'AUS': 'PRG'}
v, nb = {}, {}
for c, b in basis.items():
    x = latest(SC, lambda r, c=c, b=b: r['REF_AREA'] == c and r['CANCER_SITE'] == 'CICDMNBR' and r['AGE'] == 'Y50T69' and r['SEX'] == 'F' and r['DATA_SRCE'] == b)
    if c in x:
        y, val, fl = x[c]
        v[c] = (y, val, ';'.join(f for f in [fl, b] if f))
    nb[c] = ('programme data' if b == 'PRG' else 'survey data') + ' (same basis as original)'
nb['SWE'] = 'programme data; original used a non-OECD source for women 40-49 (error in original); replaced with OECD 50-69 programme data (survey 2019 = 95.2 also exists)'
nb['DEU'] = 'survey data (EHIS 2019) - same basis as original (71 = 2012 survey); programme data 2024 = 53.8 (E) also available'
nb['CAN'] = 'survey data (same basis as original 72 = 2012 survey); 2024 flagged D (difference in methodology); programme data 2019 = 59.7 (E)'
FLAGNAMES['PRG'] = 'programme-based'; FLAGNAMES['SRV'] = 'survey-based'
emit('F10_08', '% of women 50-69', 'OECD Data Explorer, Health care use - Screening', 'DSD_HEALTH_PROC@DF_SCREEN', v, nb,
     'Mammography screening within past 2 years (or national interval), women 50-69')
audit.append(['F10_08', 'DIRECTLY UPDATED', 'OECD.stat (SE: non-OECD source, ages 40-49)', 'OECD Data Explorer DSD_HEALTH_PROC@DF_SCREEN, CANCER_SITE=CICDMNBR, AGE=Y50T69',
              'Mammography screening, % women 50-69; programme or survey basis matched to original per country (flag PRG/SRV)', yrs(v), len(v),
              'Same OECD series. Sweden corrected to OECD 50-69 programme data (original used 40-49 from a journal article).',
              'Basis per country inferred by matching original 2013 values: SRV for USA, DEU, CHE, CAN, JPN; PRG otherwise. Survey years older (DEU 2019, CHE 2022, JPN 2022).'])

# ---------- F10_09 / F10_10 30-day mortality unlinked ----------
for ind, m, lab, oy in [('F10_09', 'MORTISTI', 'ischaemic stroke', '2014'), ('F10_10', 'MORTAMII', 'AMI', '2013')]:
    v = latest(AC, lambda r: r['MEASURE'] == m and r['SEX'] == '_T' and r['STATISTICAL_OPERATION'] == 'OBS' and r['METHODOLOGY'] == 'AGE_SEX_STANDARD' and r['AGE'] == 'Y_GE45')
    nb = {'FRA': 'unlinked series ends 2015 (no newer unlinked data); linked series not used to avoid mixing',
          'JPN': 'Japan values flagged estimated (E); was NA in original',
          'NLD': 'was NA in original', 'DNK': 'was NA in original'}
    emit(ind, 'per 100 admissions', SRC + ' - Acute care (%s)' % m, 'DSD_HCQO@DF_AC', v, nb,
         '30-day mortality after admission for %s, same hospital (unlinked data), age 45+, age-sex standardised per 100 admissions' % lab)
    audit.append([ind, 'DIRECTLY UPDATED', 'OECD HCQI', SRC + ' DF_AC, measure %s' % m,
                  '%s 30-day mortality during same hospital admission, unlinked data, 45+, age-sex standardised per 100 admissions' % lab,
                  yrs(v), len(v), 'Same OECD unlinked indicator; linked (patient-based) series exists separately and was not mixed in.',
                  'FRA latest unlinked year 2015. JPN estimated values (E). NLD, DNK, JPN newly available (NA originally).'])

# ---------- F10_11 foreign body ----------
emit('F10_11', 'per 100,000 discharges', 'not available', 'DSD_HCQO@DF_PS', {}, {c: 'indicator discontinued' for c in C},
     'Foreign body left in during procedure is no longer collected/published in OECD HCQO patient-safety data (absent from DF_PS and the HCQO measure codelist)')
audit.append(['F10_11', 'UNAVAILABLE', 'OECD HCQI patient safety', 'none (OECD DF_PS no longer contains this measure)', '', '', 0,
              'OECD discontinued the foreign-body-left-in indicator; current patient-safety set covers obstetric trauma, post-op PE/DVT and sepsis (unlinked and linked).',
              'Checked HCQO DF_PS data and its full measure codelist (struct_DSD_HCQO_DF_PS.xml): no foreign-body code.'])

# ---------- F10_12 obstetric trauma ----------
v = latest(PS, lambda r: r['MEASURE'] == 'OBSTVDWO')
emit('F10_12', 'per 100 vaginal deliveries', SRC + ' - Patient safety (OBSTVDWO)', 'DSD_HCQO@DF_PS', v,
     {'FRA': 'France not reported in current OECD series', 'JPN': 'not reported'},
     '3rd/4th degree obstetric trauma, vaginal delivery without instrument, crude rate per 100 deliveries')
audit.append(['F10_12', 'DIRECTLY UPDATED', 'OECD HCQI patient safety', SRC + ' DF_PS, measure OBSTVDWO',
              'Obstetric trauma (3rd/4th degree perineal tear) per 100 vaginal deliveries without instrument, crude rate', yrs(v), len(v),
              'Same OECD indicator (crude rate, unit "per 100 deliveries"). OECD notes rates are sensitive to coding/recording practices across countries.',
              'FRA (0.6 in original) no longer in OECD data; JPN NA. DNK latest 2020, NLD 2021.'])

# ---------- F10_13 / F10_15 avoidable admissions ----------
adm = {}
for ind, m, lab in [('F10_13', 'ADMRDBUC', 'Diabetes'), ('F10_15', 'ADMRASTH', 'Asthma')]:
    v = latest(PC, lambda r: r['MEASURE'] == m and r['SEX'] == '_T' and r['STATISTICAL_OPERATION'] == 'OBS' and r['METHODOLOGY'] == 'AGE_SEX_STANDARD')
    adm[ind] = v
    emit(ind, 'per 100,000 population 15+', SRC + ' - Primary care (%s)' % m, 'DSD_HCQO@DF_PC', v,
         {'FRA': 'France latest year 2015 in OECD series', 'JPN': 'Japan not reported in current OECD series (was reported in original)'},
         '%s hospital admission, population 15+, age-sex standardised per 100,000 (2010 OECD standard population)' % lab)
    audit.append([ind, 'DIRECTLY UPDATED', 'OECD Health at a Glance 2015 (OECD HCQI)', SRC + ' DF_PC, measure %s' % m,
                  '%s hospital admissions per 100,000 population aged 15+, age-sex standardised' % lab, yrs(v), len(v),
                  'Same OECD indicator (HaaG figures are drawn from this database).',
                  'JPN missing in current data; FRA latest 2015; DEU latest 2023 (odd years only recently).'])

# ---------- F10_14 diabetes ratio ----------
prev = {r['country']: float(r['prev_2024']) for r in csv.DictReader(open(os.path.join(RAW, 'idf_prevalence_2024.csv')))}
purl = {r['country']: r['url'] for r in csv.DictReader(open(os.path.join(RAW, 'idf_prevalence_2024.csv')))}
v, nb = {}, {}
for c in C:
    if c in adm['F10_13']:
        y, rate, fl = adm['F10_13'][c]
        ratio = rate / 100000 / (prev[c] / 100) * 100
        v[c] = (y, ratio, fl)
        nb[c] = 'ratio = admission rate %.1f/100k (%d) / IDF 2024 age-standardised prevalence 20-79 %.1f%%' % (rate, y, prev[c])
    else:
        nb[c] = 'no admission rate (IDF prevalence %.1f%% available)' % prev[c]
emit('F10_14', 'admissions per 100 people with diabetes', 'Derived: OECD DF_PC ADMRDBUC / IDF Diabetes Atlas 11th ed. (2024)', 'DSD_HCQO@DF_PC + IDF', v, nb,
     'obs_year = admissions year; prevalence year 2024', urls={c: URL['DSD_HCQO@DF_PC'] + ' ; ' + purl[c] for c in C})
audit.append(['F10_14', 'CLOSE MODERN EQUIVALENT', 'Derived (OECD admissions / diabetes prevalence)',
              'OECD DF_PC ADMRDBUC (15+, age-sex std) / IDF Diabetes Atlas 11th edition 2024 age-standardised prevalence 20-79 (as used in OECD Health at a Glance)',
              'Diabetes admissions per 100 people with diabetes = (rate per 100,000 / 100,000) / (prevalence %/100) x 100', yrs(v), len(v),
              'Original prevalence denominator undocumented (implied prevalence varies ~4-12%, e.g. FRA ~12.5% implied); modern denominator is IDF 2024 age-standardised 20-79. Numerator 15+, denominator 20-79 (age bases differ, as in original).',
              'IDF 11th ed. raises US prevalence to 13.7% (vs 9.4% in 2011), lowering US ratio. FRA numerator 2015 vs prevalence 2024. JPN NA (no admissions). Inputs in raw/oecd_quality/idf_prevalence_2024.csv.'])

# ---------- F10_16 asthma ratio ----------
emit('F10_16', 'admissions per 100 people with asthma', 'not available', '', {}, {c: '' for c in C},
     'No OECD/WHO-reported asthma prevalence; GBD (IHME) estimates are not redistributable via OWID and original denominator source is undocumented')
audit.append(['F10_16', 'UNAVAILABLE', 'Derived (asthma admissions / asthma prevalence, source undocumented)', 'none', '', '', 0,
              'No defensible, accessible prevalence denominator: OECD Health at a Glance does not report asthma prevalence; WHO GHO has none; GBD 2023 asthma prevalence (age-standardised) is non-redistributable (OWID download blocked) and not accessible programmatically.',
              'Numerator (F10_15) is available; implied original prevalences (3.7-11.6%) cannot be traced to a source.'])

# ---------- F11_01 horizontal inequity ----------
hi = {'USA': (2016, 5.3, '*', 'MEPS 2016'), 'GBR': (2014, 0.4, '', 'EHIS-2 2014'), 'DEU': (2014, 0.8, '*', 'EHIS-2 2014'),
      'SWE': (2014, 0.3, '', 'EHIS-2 2014'), 'FRA': (2014, 1.1, '*', 'EHIS-2 2014'), 'NLD': (2014, 0.5, '', 'EHIS-2 2014'),
      'DNK': (2014, -1.3, '*', 'EHIS-2 2014'), 'CAN': (2016, 2.2, '*', 'CCHS 2015-16')}
v = {c: (y, val, '') for c, (y, val, s, sv) in hi.items()}
nb = {c: 'concentration index of need-standardised probability (CI=%.3f) x100; survey %s%s' % (val / 100, sv, '; significant at 5%' if s else '; not significant')
      for c, (y, val, s, sv) in hi.items()}
nb.update({'CHE': 'Switzerland not covered by the OECD 2019 analysis', 'JPN': 'not covered', 'AUS': 'not covered'})
HFE = 'https://www.oecd.org/content/dam/oecd/en/publications/reports/2019/09/health-for-everyone_ebff9e21/3c8385d0-en.pdf'
emit('F11_01', 'index x100', 'OECD (2019) Health for Everyone? Social Inequalities in Health and Health Systems, Annex Table 3.A.6', '', v, nb,
     'Horizontal inequity (concentration index of needs-standardised probability of a doctor visit in past 12 months, by income) x100', urls={c: HFE for c in C})
audit.append(['F11_01', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2013 (Devaux & de Looper 2012; ~2009 survey data)',
              'OECD (2019) Health for Everyone?, Annex Table 3.A.6 (p.124-125), column CI',
              'Income-related concentration index of the need-standardised (indirect standardisation) probability of a doctor (GP or specialist) visit in past 12 months, x100',
              '2014-2016', len(v),
              'Same HI concept/method (indirectly need-standardised concentration index by income), newer OECD analysis using EHIS-2 2014, CCHS 2015-16, MEPS 2016; need covariates and income definitions differ from the 2013 study.',
              'No newer OECD HI publication found. obs_year = survey year (CAN 2015-16 recorded as 2016). CHE, JPN, AUS not covered. DNK negative (pro-poor).'])

# ---------- F11_04 consultation skipped due to cost ----------
v = latest(PE, lambda r: r['MEASURE'] == 'COSKCOST' and r['SEX'] == '_T' and r['STATISTICAL_OPERATION'] == 'VALUEW' and r['INCOME_GROUP'] == '_T')
nb = {'NLD': 'national survey (annual)', 'AUS': 'ABS Patient Experience Survey (national, annual)',
      'CAN': 'Commonwealth Fund IHP 2023 (OECD flag D)', 'DNK': 'not reported', 'JPN': 'not reported'}
for c in ['USA', 'GBR', 'DEU', 'SWE', 'FRA', 'CHE']:
    if c in v and v[c][0] == 2020:
        nb[c] = 'Commonwealth Fund IHP survey 2020 as reported by OECD (COVID-era fieldwork)'
emit('F11_04', '% of adults', SRC + ' - Patient experiences (COSKCOST)', 'DSD_HCQO@DF_PE', v, nb,
     'Consultation skipped due to costs, % of population (OECD unit PT_POP), total income group')
audit.append(['F11_04', 'DIRECTLY UPDATED', 'OECD.stat', SRC + ' DF_PE, measure COSKCOST',
              'Consultation skipped due to costs, % (respondents with a medical problem in reference year per OECD definition), weighted', yrs(v), len(v),
              'Same OECD measure; values for most countries come from Commonwealth Fund IHP 2020 round; NLD/AUS national surveys (2024); CAN 2023.',
              'OECD revises earlier values (e.g. USA 2016 now 21.8 vs 22.3 in original). DNK, JPN NA.'])

os.makedirs(os.path.join(ROOT, 'results'), exist_ok=True)
with open(os.path.join(ROOT, 'results', 'oecd_quality_data.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['indicator_id', 'country', 'value', 'unit', 'obs_year', 'modern_source', 'dataset_code', 'url', 'retrieval_date', 'flags', 'notes'])
    w.writerows(data)
with open(os.path.join(ROOT, 'results', 'oecd_quality_audit.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['indicator_id', 'status', 'original_source', 'modern_source', 'modern_definition', 'years_used', 'n_countries_available', 'change_vs_2018', 'notes'])
    w.writerows(audit)
print(len(data), 'data rows;', len(audit), 'audit rows')

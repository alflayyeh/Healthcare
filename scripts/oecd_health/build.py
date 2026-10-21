# Build results/oecd_health_data.csv and results/oecd_health_audit.csv from raw OECD SDMX downloads.
# Run: python3 -I scripts/oecd_health/build.py
import csv, collections, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = ROOT + '/raw/oecd_health'
RET = '2026-10-07'
C11 = 'USA GBR DEU SWE FRA NLD CHE DNK CAN JPN AUS'.split()
FLAGNAMES = {'B': 'B (break in series)', 'D': 'D (definition differs)', 'E': 'E (estimated value)',
             'P': 'P (provisional)', 'M': 'M (missing)', 'U': 'U (low reliability)'}

_cache = {}
def load(df):
    if df not in _cache:
        rows = list(csv.DictReader(open(f'{RAW}/{df}.csv', encoding='utf-8-sig')))
        _cache[df] = rows
    return _cache[df]

def url(df):
    return open(f'{RAW}/{df}.url').read().strip()

def series(df, filt, country):
    out = {}
    for r in load(df):
        if r['REF_AREA'] == country and all(r[k] == v for k, v in filt.items()) and r['OBS_VALUE'] != '':
            fl = [r.get(k, '') for k in ('OBS_STATUS', 'OBS_STATUS2', 'OBS_STATUS3', 'OBS_STATUS4')]
            fl = [FLAGNAMES.get(x, x) for x in fl if x and x != 'A']
            out[r['TIME_PERIOD']] = (float(r['OBS_VALUE']), fl)
    return out

def latest(df, filt, country):
    s = series(df, filt, country)
    if not s:
        return None
    y = max(s)
    return y, s[y][0], s[y][1]

data_rows = []
audit_rows = []

def add(ind, country, val, unit, year, df, dataset_code, u, flags, notes, source='OECD Health Statistics 2026 (OECD Data Explorer, SDMX)'):
    data_rows.append(dict(indicator_id=ind, country=country,
                          value='NA' if val is None else val, unit=unit,
                          obs_year='' if val is None else year, modern_source=source if val is not None else '',
                          dataset_code=dataset_code, url=u, retrieval_date=RET,
                          flags='; '.join(flags), notes=notes))

def simple(ind, df, filt, unit, dec, scale=1.0, overrides=None, cnotes=None, extra_flags=None, stale_before=2018):
    """overrides: country -> (filt, extra flag list, note) ; cnotes: country -> note"""
    overrides = overrides or {}
    cnotes = cnotes or {}
    for c in C11:
        f, xfl, note = filt, [], ''
        if c in overrides:
            f, xfl, note = overrides[c]
        r = latest(df, f, c)
        note = '; '.join(x for x in (note, cnotes.get(c, '')) if x)
        dsc = f"OECD.ELS.HD:{df} " + ','.join(f'{k}={v}' for k, v in f.items())
        if r is None:
            add(ind, c, None, unit, '', df, dsc, url(df), [], note or 'No observation in OECD dataflow for this country')
            continue
        y, v, fl = r
        fl = fl + xfl
        if int(y) < stale_before:
            fl.append(f'stale ({y})')
        vv = round(v * scale, dec)
        if dec == 0: vv = int(vv)
        add(ind, c, vv, unit, y, df, dsc, url(df), fl, note)

def audit(ind, status, orig, modern, mdef, change, notes):
    rows = [r for r in data_rows if r['indicator_id'] == ind]
    yrs = collections.Counter(r['obs_year'] for r in rows if r['value'] != 'NA')
    years_used = '; '.join(f'{y} (n={n})' for y, n in sorted(yrs.items(), reverse=True))
    n = sum(1 for r in rows if r['value'] != 'NA')
    audit_rows.append(dict(indicator_id=ind, status=status, original_source=orig, modern_source=modern,
                           modern_definition=mdef, years_used=years_used, n_countries_available=n,
                           change_vs_2018=change, notes=notes))

OECD = 'OECD Health Statistics 2026 via OECD Data Explorer (SDMX)'

# ---------------- F4_01 daily smokers ----------------
simple('F4_01', 'DF_HEALTH_LVNG_TC', dict(MEASURE='SP_DS', AGE='Y_GE15', SEX='_T', UNIT_MEASURE='PT_POP'),
       '% of population 15+', 1,
       cnotes={'FRA': 'France 2022-2024 flagged D (survey methodology change, Barometre sante); 2024 drop 23.1->18.2 partly methodological',
               'SWE': 'Sweden 2023+ flagged D (new survey methodology)',
               'CAN': 'Canada break in series 2023 (B); 2024 after break',
               'CHE': 'Swiss Health Survey every 5 years'})
audit('F4_01', 'DIRECTLY UPDATED', 'OECD Health at a Glance 2017 (2015)', OECD + ' DSD_HEALTH_LVNG@DF_HEALTH_LVNG_TC',
      'Share of population aged 15+ who are daily smokers, total, %', 'None in definition; same OECD series (now in Data Explorer).',
      'Self-reported survey data; survey frequency varies (CHE 2022, AUS 2022). FRA and SWE latest years flagged D (methodology differs).')

# ---------------- F4_02 alcohol ----------------
simple('F4_02', 'DF_HEALTH_LVNG_AC', dict(MEASURE='AC', AGE='Y_GE15', SEX='_T', UNIT_MEASURE='L_PS'),
       'litres pure alcohol per capita 15+', 1,
       cnotes={'DNK': 'Denmark flagged D (definition differs) in OECD for recent years'})
audit('F4_02', 'DIRECTLY UPDATED', 'OECD Health at a Glance 2017 (2015)', OECD + ' DSD_HEALTH_LVNG@DF_HEALTH_LVNG_AC',
      'Recorded alcohol consumption, litres of pure alcohol per person aged 15+', 'None.',
      'Recorded sales only; unrecorded consumption excluded.')

# ---------------- F4_03 overweight incl obese ----------------
BWF = dict(MEASURE='SP_OVRGHT_OBS', SEX='_T', UNIT_MEASURE='PT_POP')
MS = dict(BWF, METHODOLOGY='MSRD'); SR = dict(BWF, METHODOLOGY='SR')
agenote = 'Age base per OECD country notes (mostly 15+; some surveys 16+/18+ e.g. GBR 16+, FRA/CAN measured 18+); API gives AGE=_T only'
ov = {c: (MS, ['measured'], 'Measured data (same type as original)') for c in ['USA', 'GBR', 'FRA', 'CAN', 'JPN', 'AUS']}
ov.update({c: (SR, ['self-reported'], 'Self-reported data (same type as original, footnote a)') for c in ['SWE', 'NLD', 'CHE', 'DNK']})
ov['DEU'] = (SR, ['self-reported', 'TYPE CHANGED vs original (original measured 2012)'],
             'Original used measured data (2012 = 60.0); OECD has no measured data for Germany after 2012, so latest self-reported value used. NOT directly comparable with original DEU value')
ov['FRA'] = (MS, ['measured'], 'Measured data (ESTEBAN), latest measured year 2017 (>=2016 rule); self-reported 2019 = 45.3 also available')
ov['GBR'] = (MS, ['measured'], 'Measured (Health Survey for England), latest measured 2019; OECD self-reported series 2024 = 66.0 (flag D) not used')
ov['CAN'] = (MS, ['measured'], 'Measured (CHMS) latest 2019; self-reported 2024 = 57.7 not used')
simple('F4_03', 'DF_HEALTH_LVNG_BW', BWF, '% of population 15+', 1, overrides=ov,
       cnotes={c: agenote for c in C11}, stale_before=2016)
audit('F4_03', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2017 (2015)', OECD + ' DSD_HEALTH_LVNG@DF_HEALTH_LVNG_BW',
      'Share of population overweight incl. obese (BMI>=25), total; measured for USA/GBR/FRA/CAN/JPN/AUS, self-reported for SWE/NLD/CHE/DNK/DEU',
      'Germany switched from measured (orig 2012) to self-reported (no measured data since 2012). Measured-data years lag (FRA 2017, GBR/CAN 2019).',
      'Measured and self-reported values are not comparable (self-report understates); type recorded per country in flags. Age base varies by country survey.')

# ---------------- LE ----------------
for ind, age, sex, lab in [('F4_04', 'Y0', '_T', 'at birth, total'), ('F4_06', 'Y40', 'F', 'at age 40, females'), ('F4_07', 'Y40', 'M', 'at age 40, males')]:
    simple(ind, 'DF_LE', dict(MEASURE='LFEXP', AGE=age, SEX=sex, UNIT_MEASURE='Y'), 'years', 1,
           cnotes={'GBR': 'OECD flags UK/JPN total-population LE as estimated (E) where shown'} if ind == 'F4_04' else None)
    audit(ind, 'DIRECTLY UPDATED', 'OECD Health Statistics 2017 (2015)', OECD + ' DSD_HEALTH_STAT@DF_LE',
          f'Life expectancy {lab}, years', 'None.', 'No 2025 values yet for these countries in OECD; 2024 used throughout.')

# ---------------- MIM ----------------
simple('F4_08', 'DF_MIM', dict(MEASURE='MATM', UNIT_MEASURE='DT_10P5BR_L'), 'per 100,000 live births', 1,
       cnotes={'CAN': 'Canada now available from OECD (original used GBD); OECD used per rule',
               'USA': 'US NCHS series; OECD has no US 2015 value (pre-2018 revision); annual value',
               'FRA': 'France latest OECD value 2018 (Inserm ENCMM confidential enquiry cycle)',
               'DNK': 'Very small counts (0-4 deaths/yr): highly volatile, single year reported',
               'CHE': 'Small counts: volatile year-to-year (2022 1.2, 2024 7.7)',
               'SWE': 'Small counts: volatile', 'AUS': 'Break in series 2023 (B); earlier years flagged D'},
       extra_flags=None)
audit('F4_08', 'CLOSE MODERN EQUIVALENT', 'OECD 2015; Canada: Global Burden of Disease', OECD + ' DSD_HEALTH_STAT@DF_MIM',
      'Maternal deaths per 100,000 live births (vital registration), single latest year, not averaged (OECD presents annual values, no 3-yr averages in this dataflow)',
      'Canada now from OECD instead of GBD. Original 2018 values (e.g. US 26.4, UK 9.2, DE 9.0) look like GBD-modelled estimates rather than OECD vital-registration figures, so modern OECD values are systematically lower for several countries.',
      'Volatile in small countries (DNK, CHE, SWE, NLD). France only up to 2018.')
simple('F4_09', 'DF_MIM', dict(MEASURE='INM', UNIT_MEASURE='DT_10P3BR_L', GESTATION_THRESHOLD='NONE'), 'per 1,000 live births', 1,
       cnotes={'CAN': 'Canada now available from OECD (original used Conference Board of Canada)',
               'FRA': 'France 2025 flagged estimated (E)', 'AUS': 'Australia 2024 provisional (P)'})
audit('F4_09', 'DIRECTLY UPDATED', 'OECD 2015; Canada: Conference Board of Canada', OECD + ' DSD_HEALTH_STAT@DF_MIM',
      'Infant deaths (<1 y) per 1,000 live births, no minimum gestation/birthweight threshold (OECD headline series; matches original values)',
      'Canada now from OECD instead of Conference Board.', 'A 22-week threshold series also exists but is incomplete (no CAN/AUS, old DEU/NLD); not used.')
simple('F4_10', 'DF_MIM', dict(MEASURE='NEOM', UNIT_MEASURE='DT_10P3BR_L', GESTATION_THRESHOLD='NONE'), 'per 1,000 live births', 1,
       cnotes={'CAN': 'Canada now available from OECD (original used World Data Atlas)',
               'AUS': 'Australia flagged D (definition differs) in OECD, consistently since 2015'})
audit('F4_10', 'DIRECTLY UPDATED', 'OECD 2015; Canada: World Data Atlas', OECD + ' DSD_HEALTH_STAT@DF_MIM',
      'Neonatal deaths (<28 days) per 1,000 live births, no minimum threshold', 'Canada now from OECD.', '')

# ---------------- LBW ----------------
simple('F4_12', 'DF_IH_LB', dict(MEASURE='LOWB', UNIT_MEASURE='PT_BR_L'), '% of live births', 1,
       cnotes={'DEU': 'Germany: OECD latest is 2013 (no newer data reported)', 'CHE': 'Switzerland now reported (NA in original)'})
audit('F4_12', 'DIRECTLY UPDATED', 'OECD 2015', OECD + ' DSD_HEALTH_STAT@DF_IH_LB',
      'Live births weighing <2500 g, % of live births', 'None; Switzerland now available.', 'Germany stuck at 2013 in OECD.')

# ---------------- discharges ----------------
for ind, code, lab in [('F7_01', 'DICDA903', 'Acute myocardial infarction (I21-I22)'),
                       ('F7_02', 'DICDA500', 'Mental and behavioural disorders (F00-F99)'),
                       ('F7_03', 'DICDB002', 'Pneumonia (J12-J18)'),
                       ('F7_04', 'DICDB006', 'COPD and bronchiectasis (J40-J44, J47)')]:
    cn = {'USA': 'US: latest OECD discharge data 2010 (same as original); include some same-day separations',
          'DNK': 'Denmark: gap 2017-2022; 2023 value after LPR3 registry change, level shift vs 2016 (no B flag in OECD)',
          'GBR': 'UK latest OECD year 2018; public/publicly funded hospitals only',
          'JPN': 'Japan reported every 3 years (Patient Survey)'}
    if ind == 'F7_02':
        cn['NLD'] = 'Netherlands excludes psychiatric hospitals (very low value, as in original)'
        cn['FRA'] = 'France: break in series 2016 (B; psychiatric hospital stays added, level jumps 368->1187) and 2022 (B); modern value NOT comparable with original 368'
    if ind == 'F7_03':
        cn['CAN'] = 'Pneumonia discharges fell during COVID (2020-21) and rebounded; 2024 used'
    simple(ind, 'DF_HOSP_DISCHARGE', dict(DIAGNOSTIC_TYPE=code, UNIT_MEASURE='DSC_10P5PS', SEX='_T'), 'per 100,000 population', 0,
           cnotes=cn, stale_before=2018)
    audit(ind, 'DIRECTLY UPDATED', 'OECD (2016; US 2010)', OECD + ' DSD_HEALTH_PROC@DF_HOSP_DISCHARGE',
          f'Inpatient hospital discharges per 100,000 population, {lab} (ISHMT); dataflow contains inpatient discharges only (same-day cases excluded except US)',
          'None in definition. ' + ('ISHMT category is COPD and bronchiectasis, as in OECD 2017.' if ind == 'F7_04' else ''),
          'US still 2010, UK 2018, DNK 2023 after registry change; COVID-era disruption to pneumonia/COPD rates.' + (' France series break 2016 (now includes psychiatric hospitals: ~3x original); NLD excludes psychiatric hospitals.' if ind == 'F7_02' else ''))

# ---------------- diagnostic exams ----------------
for ind, fac, lab in [('F7_05', 'MRI', 'MRI'), ('F7_06', 'CT_SCAN', 'CT')]:
    base = dict(HEALTH_FACILITY=fac, UNIT_MEASURE='EXM_10P3PS')
    ov = {c: (dict(base, PROVIDER='HP1'), ['hospital only'], 'Hospital exams only (OECD has no total for this country; original also hospital/public only)') for c in ['GBR', 'CHE']}
    simple(ind, 'DF_DIAG_EXAM', dict(base, PROVIDER='_T'), 'per 1,000 population', 0, overrides=ov,
           cnotes={'SWE': 'Sweden does not report exams (NA in original too)', 'JPN': 'Japan latest OECD value 2014',
                   'AUS': 'Australia flagged D: exams for private patients only (in & out of hospital)', 'DEU': 'Germany values estimated (E)',
                   'USA': 'US latest 2021', 'DNK': 'Denmark: total available (hospital-only before 2020 break)'},
           stale_before=2018)
    audit(ind, 'DIRECTLY UPDATED', 'OECD (2015)', OECD + ' DSD_HEALTH_PROC@DF_DIAG_EXAM',
          f'{lab} exams per 1,000 population, total (hospital + ambulatory; PROVIDER=_T); GBR and CHE hospital only (HP1)',
          'None.', 'Coverage differences as in original (UK/CHE hospital only, AUS private patients only). Japan 2014 only.')

# ---------------- surgical procedures ----------------
SP = 'DF_SURG_PROC'
def surg(ind, proc, unit_tot, unit_us, unit, dec=0, scale=1.0, cn=None, us_note='', us_flags=None):
    ov = {'USA': (dict(MEDICAL_PROCEDURE=proc, UNIT_MEASURE=unit_us, MODE_PROVISION='HBEDT'), us_flags or ['inpatient cases only'], us_note)}
    simple(ind, SP, dict(MEDICAL_PROCEDURE=proc, UNIT_MEASURE=unit_tot, MODE_PROVISION='_T'), unit, dec, scale=scale, overrides=ov,
           cnotes=dict({'JPN': 'Japan reports no surgical procedure data to OECD', 'GBR': 'UK: publicly funded hospitals only',
                        'NLD': '', 'DNK': ''}, **(cn or {})), stale_before=2018)

usnote = 'US: OECD only has inpatient cases (HCUP NIS), latest 2010 (original also US ~2010)'
surg('F7_07', 'CM8151_8153', 'PRC_10P5PS', 'CS_10P5PS', 'per 100,000 population', us_note=usnote)
audit('F7_07', 'DIRECTLY UPDATED', 'OECD (2013)', OECD + ' DSD_HEALTH_PROC@DF_SURG_PROC',
      'Hip replacement (total and partial incl. revision), procedures per 100,000 population, total (inpatient + day case)',
      'Measure is now total procedures (inpatient+day); US remains inpatient cases 2010.', 'Japan NA (no data). US 2010 stale. COVID backlog recovery raises 2022-24 levels.')
surg('F7_08', 'CM8154', 'PRC_10P5PS', 'CS_10P5PS', 'per 100,000 population', us_note=usnote)
audit('F7_08', 'DIRECTLY UPDATED', 'OECD (2013)', OECD + ' DSD_HEALTH_PROC@DF_SURG_PROC',
      'Knee replacement (incl. revision), procedures per 100,000 population, total (inpatient + day case)',
      'As F7_07.', 'Japan NA. US 2010 inpatient.')
surg('F7_09', 'CM683_687_689', 'PRC_10P5W', 'CS_10P5W', 'per 100,000 females',
     us_note='US: OECD only has inpatient hysterectomies 2010 (104.3/100k women); outpatient/laparoscopic hysterectomies excluded -> large undercount vs original 266; NOT comparable',
     us_flags=['inpatient cases only', 'NOT COMPARABLE (excludes outpatient)'])
audit('F7_09', 'DIRECTLY UPDATED', 'OECD (2013)', OECD + ' DSD_HEALTH_PROC@DF_SURG_PROC',
      'Hysterectomy, procedures per 100,000 women (OECD unit PRC_10P5W, direct; no recomputation needed), total inpatient + day case',
      'OECD now publishes per 100,000 women directly.', 'US value (2010 inpatient only) not comparable with others/original; Japan NA.')
surg('F7_10', 'CM74_CAE', 'PRC_10P3BR_L', 'PRC_10P3BR_L', 'per 100 live births', dec=1, scale=0.1,
     us_note='US: OECD reports inpatient caesareans per 1,000 live births (virtually all caesareans are inpatient)', us_flags=['inpatient'],
     cn={'AUS': 'Australia total (_T) only 2022-2023', 'CAN': 'Canada latest 2023'})
audit('F7_10', 'DIRECTLY UPDATED', 'OECD Health at a Glance 2015 (2013)', OECD + ' DSD_HEALTH_PROC@DF_SURG_PROC',
      'Caesarean sections per 100 live births (OECD per 1,000 live births / 10), total; US inpatient',
      'Value kept to 1 decimal (original integer).', 'Japan NA (no OECD data). Note GBR rise to ~40.')
surg('F7_11', 'CM131_138', 'PRC_10P5PS', 'CS_10P5PS', 'per 100,000 population',
     us_note='US: OECD has only a 2006 day-case value (1890.3/100k) and no inpatient/total; too old and partial -> NA',
     cn={'CHE': 'Switzerland: excludes procedures outside hospitals (low value, as in original)'})
# set US cataract NA explicitly
for r in data_rows:
    if r['indicator_id'] == 'F7_11' and r['country'] == 'USA':
        r.update(value='NA', obs_year='', flags='', modern_source='',
                 notes='OECD only has a 2006 US day-case-only value (1890.3 per 100,000; CS_10P5PS, MODE_PROVISION=DAY); stale and partial definition -> NA')
audit('F7_11', 'DIRECTLY UPDATED', 'OECD.stat (2013)', OECD + ' DSD_HEALTH_PROC@DF_SURG_PROC',
      'Cataract surgery, procedures per 100,000 population, total (inpatient + day case)', 'None.',
      'US NA (only 2006 day-case data in OECD); Japan NA.')
surg('F7_12', 'CM361', 'PRC_10P5PS', 'CS_10P5PS', 'per 100,000 population', us_note='US: OECD inpatient cases, latest 2009')
audit('F7_12', 'DIRECTLY UPDATED', 'OECD Health at a Glance (2015)', OECD + ' DSD_HEALTH_PROC@DF_SURG_PROC',
      'Coronary artery bypass graft, procedures per 100,000 population, total', 'None; Switzerland now available.', 'US 2009 inpatient; Japan NA.')
surg('F7_13', 'CM36_TRS', 'PRC_10P5PS', 'CS_10P5PS', 'per 100,000 population',
     us_note='Original US value came from HCUP incl. outpatient PCI; no current credible HCUP national estimate of all-setting PCI found (HCUP briefs SB223/SB287 do not report PCI totals), so OECD US inpatient-only 2010 value used: undercounts outpatient PCI (substantial share in US)',
     us_flags=['inpatient cases only', 'undercounts outpatient PCI'])
audit('F7_13', 'CLOSE MODERN EQUIVALENT', 'OECD; US: HCUP (incl. outpatient)', OECD + ' DSD_HEALTH_PROC@DF_SURG_PROC',
      'Transluminal coronary angioplasty (PTCA/PCI), procedures per 100,000 population, total; US = OECD inpatient cases 2010',
      'US source changes from HCUP (all settings) to OECD inpatient-only 2010 -> US undercounted vs original (248).',
      'Searched HCUP statistical briefs/HCUPnet; HCUPnet requires interactive queries, no citable all-setting national PCI estimate found. Japan NA.')

# ---------------- ALOS ----------------
for ind, code, lab in [('F7_14', 'DICDB505', 'Single spontaneous delivery (normal delivery, O80)'), ('F7_15', 'DICDA903', 'Acute myocardial infarction (I21-I22)')]:
    simple(ind, 'DF_HOSP_AV_LENGTH', dict(DIAGNOSTIC_TYPE=code, UNIT_MEASURE='D'), 'days', 1,
           cnotes={'USA': 'US latest OECD year 2010', 'JPN': 'Japan no longer reports ALOS by diagnosis to OECD',
                   'DNK': 'Denmark gap 2017-2022; 2023 after registry change', 'NLD': 'Netherlands latest 2023'},
           stale_before=2018)
    audit(ind, 'DIRECTLY UPDATED', 'OECD Health at a Glance (2013)', OECD + ' DSD_HEALTH_PROC@DF_HOSP_AV_LENGTH',
          f'Average length of stay, {lab}, days (inpatient)', 'None.', 'US 2010; Japan NA.')

# drop empty notes junk
for r in data_rows:
    r['notes'] = '; '.join(x for x in r['notes'].split('; ') if x)

os.makedirs(ROOT + '/results', exist_ok=True)
DC = 'indicator_id,country,value,unit,obs_year,modern_source,dataset_code,url,retrieval_date,flags,notes'.split(',')
AC = 'indicator_id,status,original_source,modern_source,modern_definition,years_used,n_countries_available,change_vs_2018,notes'.split(',')
with open(ROOT + '/results/oecd_health_data.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, DC); w.writeheader(); w.writerows(data_rows)
with open(ROOT + '/results/oecd_health_audit.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, AC); w.writeheader(); w.writerows(audit_rows)
print(len(data_rows), 'data rows', len(audit_rows), 'audit rows')

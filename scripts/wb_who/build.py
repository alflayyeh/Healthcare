"""Build results/wb_who_data.csv and results/wb_who_audit.csv from raw/wb_who/*.
Run from project root:  python3 -I scripts/wb_who/build.py
Raw files were fetched with curl (see URLs below / in data.csv url column)."""
import csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, 'raw/wb_who')
C = ['USA', 'GBR', 'DEU', 'SWE', 'FRA', 'NLD', 'CHE', 'DNK', 'CAN', 'JPN', 'AUS']
RET = '2026-10-07'
WBURL = ('https://api.worldbank.org/v2/country/USA;GBR;DEU;SWE;FRA;NLD;CHE;DNK;CAN;JPN;AUS/'
         'indicator/{}?format=json&per_page=2000&date=2010:2026')


def wb(code):
    d = json.load(open(os.path.join(RAW, f'wb_{code}.json')))
    out = {}
    for r in d[1]:
        if r['value'] is None:
            continue
        c, y = r['countryiso3code'], int(r['date'])
        out.setdefault(c, {})[y] = r['value']
    return out


def latest(series, c):
    s = series.get(c, {})
    if not s:
        return None, None
    y = max(s)
    return y, s[y]


def ghed():
    import openpyxl
    wbk = openpyxl.load_workbook(os.path.join(RAW, 'ghed_data.xlsx'), read_only=True)
    it = wbk['Data'].iter_rows(values_only=True)
    h = next(it)
    out = {}
    for r in it:
        if r[1] in C:
            out[(r[1], r[4])] = dict(zip(h, r))
    return out


def oecd():
    rows = list(csv.DictReader(open(os.path.join(RAW, 'oecd_sha_che.csv'))))
    lat, fin = {}, {}
    for r in rows:
        if r['OBS_VALUE'] == '':
            continue
        k = (r['REF_AREA'], r['UNIT_MEASURE'], r['FINANCING_SCHEME'], r['PRICE_BASE'])
        y = int(r['TIME_PERIOD'])
        if k not in lat or y > lat[k][0]:
            lat[k] = (y, float(r['OBS_VALUE']), r['OBS_STATUS'])
        if r['OBS_STATUS'] in ('', 'A') and (k not in fin or y > fin[k][0]):
            fin[k] = (y, float(r['OBS_VALUE']), r['OBS_STATUS'])
    return lat, fin


OECD_URL = open(os.path.join(RAW, 'oecd_sha_url.txt')).read().strip()
G = ghed()
OL, OF = oecd()


def oecd_note(c, unit, fs, pb):
    k = (c, unit, fs, pb)
    s = ''
    if k in OL:
        y, v, f = OL[k]
        s += f'OECD SHA cross-check (not used as value): {v:.1f} in {y}' + (f' [flag {f}]' if f else '')
    if k in OF and (k not in OL or OF[k][0] != OL[k][0]):
        y, v, f = OF[k]
        s += f'; latest unflagged OECD year {y}: {v:.1f}'
    return s


data, audit = [], []


def add(ind, c, val, unit, year, src, code, url, flags='', notes=''):
    data.append(dict(indicator_id=ind, country=c, value='NA' if val is None else val, unit=unit,
                     obs_year='' if val is None else year, modern_source=src, dataset_code=code, url=url,
                     retrieval_date=RET, flags=flags, notes=notes))


WB_SRC = 'World Bank WDI (API v2), July 2026 update'
GHED_SRC = 'WHO Global Health Expenditure Database (GHED, updated 12 Dec 2025) via World Bank WDI'

# ---------- F1_01 population ----------
s = wb('SP.POP.TOTL')
yrs = []
for c in C:
    y, v = latest(s, c)
    yrs.append(y)
    add('F1_01', c, round(v / 1e6, 3), 'millions', y, WB_SRC, 'SP.POP.TOTL', WBURL.format('SP.POP.TOTL'),
        notes=f'{int(v)} persons, midyear de facto')
audit.append(dict(indicator_id='F1_01', status='DIRECTLY UPDATED', original_source='World Bank WDI SP.POP.TOTL (2016)',
                  modern_source=WB_SRC, modern_definition='Total population, midyear, de facto (millions)',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018='None; same series.', notes=''))

# ---------- F1_04 surface area ----------
s = wb('AG.SRF.TOTL.K2'); land = wb('AG.LND.TOTL.K2')
yrs = []
for c in C:
    y, v = latest(s, c)
    yl, vl = latest(land, c)
    yrs.append(y)
    flag, note = '', f'Land area excl. inland water (AG.LND.TOTL.K2, {yl}) = {vl/1000:.1f} thousand km2; surface minus land = {(v-vl)/1000:.1f} thousand km2.'
    if c in ('CAN', 'FRA', 'SWE'):
        flag = 'D'
        old = {'CAN': '9,985 (old FAO total area incl. inland water)', 'FRA': '549',
               'SWE': '450'}[c]
        note = ('DEFINITION CHANGE in FAO/WB vintage: current WB series now includes coastal waters (internal waters/territorial sea) '
                f'for this country, revised back to 2013+ (2018 paper value {old}). ' + note +
                ' Not comparable with the 2018 value or with the other 8 countries; consider land area as a consistent alternative.')
    add('F1_04', c, round(v / 1000, 1), 'thousand sq km', y, WB_SRC + ' (source: FAO)', 'AG.SRF.TOTL.K2',
        WBURL.format('AG.SRF.TOTL.K2'), flag, note)
audit.append(dict(indicator_id='F1_04', status='CLOSE MODERN EQUIVALENT', original_source='World Bank WDI AG.SRF.TOTL.K2 (2015)',
                  modern_source=WB_SRC + ' (FAO)', modern_definition="Surface area: country's total area incl. inland water bodies and some coastal waterways (thousand km2)",
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018=('Same series code, but the FAO-sourced values were revised: CAN 15,634 (was 9,985), FRA 606 (was 549), SWE 529 (was 450) '
                                  'now include coastal/territorial waters; other 8 countries unchanged in concept. CAN would overtake USA as largest.'),
                  notes=('Flag D on CAN/FRA/SWE. Area is static; obs_year 2023 is just the latest WDI entry. Orchestrator may prefer AG.LND.TOTL.K2 (land area, '
                         'consistent across all 11, values in notes) or keep 2018 values. FAOSTAT API (inland waters item) requires authorization so a '
                         'land+inland-water reconstruction was not possible.')))

# ---------- F1_06 CHE % GDP ----------
s = wb('SH.XPD.CHEX.GD.ZS')
yrs = []
for c in C:
    y, v = latest(s, c)
    yrs.append(y)
    gv = G.get((c, y), {}).get('che_gdp')
    add('F1_06', c, round(v, 2), '% of GDP', y, GHED_SRC, 'SH.XPD.CHEX.GD.ZS (GHED che_gdp)', WBURL.format('SH.XPD.CHEX.GD.ZS'),
        notes=f'GHED direct file identical ({gv:.2f}); GHED has no later year. ' + oecd_note(c, 'PT_B1GQ', '_T', '_Z'))
audit.append(dict(indicator_id='F1_06', status='CLOSE MODERN EQUIVALENT', original_source='WHO GHED via World Bank SH.XPD.TOTL.ZS (2016)',
                  modern_source=GHED_SRC, modern_definition='Current health expenditure (SHA 2011, excl. capital formation) as % of GDP',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018='SH.XPD.TOTL.ZS discontinued; successor SH.XPD.CHEX.GD.ZS (GHED, SHA2011 current expenditure).',
                  notes=('WB mirror and GHED Dec-2025 file are the same vintage (no later year in GHED). 2024 for 7 countries, 2023 for USA/JPN/AUS/CHE. '
                         'OECD SHA (latest 2025 estimates/provisional) in notes for cross-check only: OECD is generally higher/newer (e.g. USA 17.6 2025E vs 16.7 2023).')))

# ---------- F1_07 GGHE-D % GDP ----------
s = wb('SH.XPD.GHED.GD.ZS')
yrs = []
for c in C:
    y, v = latest(s, c)
    yrs.append(y)
    g = G.get((c, y), {})
    hf1 = g['hf1'] / g['hf'] * g['che_gdp'] if g.get('hf1') and g.get('hf') else None
    flag = ''
    note = (f'GHED HF.1 (government + compulsory schemes) for {y} = {hf1:.2f}% GDP. ' if hf1 else '')
    if c in ('CHE', 'NLD'):
        flag = 'D'
        note = ('GGHE-D = FS.1 government transfers + FS.3 social insurance contributions; it EXCLUDES FS.4 compulsory private prepayment '
                '(Swiss KVG/LAMal premiums; Dutch Zvw nominal premiums), which GHED books as domestic private. Hence not comparable to the 2018 '
                f'"public" value ({"7.7" if c=="CHE" else "9.5"}). ' + note)
    if c == 'FRA':
        flag = 'B'
        note += ('Break in GHED series: FRA GGHE-D share of CHE falls from 75.3% (2022) to 67.7% (2023) while HF.1 is stable (~84%), i.e. a '
                 'revenue reclassification (FS.3 -> other), not a real change; 2022 GGHE-D = 8.91% GDP. ')
    if c == 'USA':
        note += 'US HF.1 includes compulsory private insurance (HF.1.2.2) so differs from GGHE-D; GGHE-D matches the 2018 concept for USA. '
    note += oecd_note(c, 'PT_B1GQ', 'HF1', '_Z') + ' (OECD = HF.1 government/compulsory schemes)'
    add('F1_07', c, round(v, 2), '% of GDP', y, GHED_SRC, 'SH.XPD.GHED.GD.ZS (GHED gghed_gdp)', WBURL.format('SH.XPD.GHED.GD.ZS'), flag, note)
audit.append(dict(indicator_id='F1_07', status='CLOSE MODERN EQUIVALENT', original_source='World Bank SH.XPD.PUBL (WHO GHED, 2016)',
                  modern_source=GHED_SRC, modern_definition='Domestic general government health expenditure (FS.1 + FS.3 social insurance contributions) as % GDP',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018=('SH.XPD.PUBL replaced by SH.XPD.GHED.GD.ZS. GGHE-D includes compulsory SOCIAL health insurance contributions (FS.3) '
                                  'but not compulsory PRIVATE insurance premiums (FS.4): CHE drops from 7.7 to ~3.9 and NLD from 9.5 to ~6.7 for definitional reasons.'),
                  notes=('Flag D on CHE and NLD (not comparable); flag B on FRA (2023 revenue-classification break in GHED). GHED gghed only to 2023 for DEU/NLD/SWE/GBR/USA/CHE/JPN/AUS; 2024 for CAN/DNK/FRA. '
                         'Alternative consistent with "government + compulsory" = GHED HF.1 share x CHE (values in notes), but it moves USA to ~13.9 '
                         '(compulsory private insurance), so neither series reproduces the 2018 mix exactly. OECD HF.1 values in notes for cross-check.')))

# ---------- F1_08 CHE per capita PPP ----------
s = wb('SH.XPD.CHEX.PP.CD'); nom = wb('SH.XPD.CHEX.PC.CD')
yrs = []
for c in C:
    y, v = latest(s, c)
    yrs.append(y)
    nv = nom.get(c, {}).get(y)
    add('F1_08', c, round(v), 'current international $ (PPP) per capita', y, GHED_SRC, 'SH.XPD.CHEX.PP.CD', WBURL.format('SH.XPD.CHEX.PP.CD'),
        notes=f'Nominal current US$ same year (SH.XPD.CHEX.PC.CD) = {nv:.0f}. ' + oecd_note(c, 'USD_PPP_PS', '_T', 'V') + ' (OECD current prices, current PPP USD)')
audit.append(dict(indicator_id='F1_08', status='CLOSE MODERN EQUIVALENT', original_source='World Bank SH.XPD.PCAP (2016; Methods say PPP-adjusted)',
                  modern_source=GHED_SRC, modern_definition='Current health expenditure per capita, PPP (current international $)',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018=('SH.XPD.PCAP discontinued; the paper\'s appendix cites the current-US$ series but Methods say spending was PPP-converted. '
                                  'The original CHE value (6,787, far below the nominal current-US$ value of ~9,200 for 2016) indicates the plotted values were PPP-based, so the PPP successor SH.XPD.CHEX.PP.CD is used; nominal US$ (SH.XPD.CHEX.PC.CD) in notes.'),
                  notes='Choice of PPP vs nominal changes CHE rank (nominal 11,784 vs PPP 10,602 in 2023). OECD 2025 E/P values in notes for cross-check only.'))

# ---------- F4_05 HALE ----------
M49 = {'840': 'USA', '826': 'GBR', '276': 'DEU', '752': 'SWE', '250': 'FRA', '528': 'NLD', '756': 'CHE', '208': 'DNK',
       '124': 'CAN', '392': 'JPN', '36': 'AUS', '036': 'AUS'}
hale = {}
for r in csv.DictReader(open(os.path.join(RAW, 'who_datadot_C64284D_ALL_LATEST.csv'), encoding='utf-8-sig')):
    if r['DIM_SEX'] == 'TOTAL' and r['DIM_GEO_CODE_M49'] in M49 and r['AMOUNT_N']:
        hale.setdefault(M49[r['DIM_GEO_CODE_M49']], {})[int(r['DIM_TIME'])] = float(r['AMOUNT_N'])
yrs = []
for c in C:
    y, v = latest(hale, c)
    yrs.append(y)
    v15 = hale[c].get(2015); v19 = hale[c].get(2019)
    add('F4_05', c, round(v, 2), 'years', y, 'WHO Global Health Estimates 2021 (GHO WHOSIS_000002) via WHO data portal bulk CSV',
        'WHOSIS_000002 (data.who.int C64284D)', 'https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/INDICATOR/C64284D_ALL_LATEST.csv',
        notes=f'Both sexes. Same-revision 2015 = {v15:.1f}, 2019 = {v19:.1f} (2021 reflects COVID-19 mortality).')
audit.append(dict(indicator_id='F4_05', status='CLOSE MODERN EQUIVALENT', original_source='OECD 2017 (Health at a Glance, citing WHO HALE), 2015',
                  modern_source='WHO Global Health Estimates 2021 (GHO indicator WHOSIS_000002), both sexes',
                  modern_definition='Healthy life expectancy (HALE) at birth, years, both sexes',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018=('HALE is a WHO-produced measure (OECD only republished it); taken from WHO directly. The GHE 2021 revision lowers levels by ~2-3 years '
                                  'vs the 2017-published figures for all countries (e.g. USA 2015: 69.1 then vs 66.3 now), so compare ranks not levels with 2018. '
                                  '2021 is the latest year (pandemic-affected; 2019 values in notes).'),
                  notes='GHO OData endpoint (ghoapi.azureedge.net/api/WHOSIS_000002) returned HTTP 502 repeatedly on 2026-10-07; identical WHO data taken from the official WHO data portal bulk CSV.'))

# ---------- F11_02 OOP % CHE ----------
s = wb('SH.XPD.OOPC.CH.ZS')
yrs = []
for c in C:
    y, v = latest(s, c)
    yrs.append(y)
    add('F11_02', c, round(v, 2), '% of current health expenditure', y, GHED_SRC, 'SH.XPD.OOPC.CH.ZS (GHED oops_che)', WBURL.format('SH.XPD.OOPC.CH.ZS'),
        notes='GHED direct file identical; no later year.')
audit.append(dict(indicator_id='F11_02', status='CLOSE MODERN EQUIVALENT', original_source='World Bank SH.XPD.OOPC.TO.ZS (WHO GHED, 2014)',
                  modern_source=GHED_SRC, modern_definition='Out-of-pocket expenditure (HF.3) as % of current health expenditure',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018='Successor series; denominator is now current (not total) health expenditure under SHA 2011.',
                  notes='2024 for 7 countries; 2023 for USA, JPN, AUS, CHE.'))

# ---------- F11_07 rural % ----------
s = wb('SP.RUR.TOTL.ZS')
yrs = []
for c in C:
    y, v = latest(s, c)
    yrs.append(y)
    v15 = s[c].get(2015)
    flag = ''
    note = f'WB value for 2015 in current vintage = {v15:.1f}. Partly WB staff estimate/projection based on UN WUP (national urban definitions).'
    if c in ('NLD', 'CHE'):
        flag = 'D'
        note += ' Large drop since 2015 reflects updated national urban definitions in the WB/UN estimates, not real ruralisation change alone.'
    add('F11_07', c, round(v, 2), '% of population', y, WB_SRC + ' (UN WUP-based staff estimates)', 'SP.RUR.TOTL.ZS', WBURL.format('SP.RUR.TOTL.ZS'), flag, note)
audit.append(dict(indicator_id='F11_07', status='CLOSE MODERN EQUIVALENT', original_source='OECD country statistical profiles (2015-2016); values match UN WUP / WB SP.RUR.TOTL.ZS',
                  modern_source=WB_SRC + ' (UN World Urbanization Prospects, national definitions)',
                  modern_definition='Rural population (% of total) = 100 - urban share by national definitions',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018=('OECD country statistical profiles discontinued; the OECD Data Explorer only offers regional-typology shares '
                                  '(OECD.CFE.EDS DSD_REG_DEMO@DF_REGION_TYPE_RURB, population in predominantly rural TL3 regions) or degree-of-urbanisation '
                                  'local-area data, which are different concepts. WB SP.RUR.TOTL.ZS (UN WUP national definitions) used instead.'),
                  notes=('WB metadata (Jul 2026) still cites WUP with national definitions, not the WUP 2025 degree-of-urbanisation method. '
                         'Values are model estimates/projections for 2025. NLD (4.1 vs 9 in 2018) and CHE (14.3 vs 26) fell sharply in the revised series - flag D.')))

# ---------- F11_08 density ----------
s = wb('EN.POP.DNST')
yrs = []
for c in C:
    y, v = latest(s, c)
    yrs.append(y)
    add('F11_08', c, round(v, 1), 'persons per sq km', y, WB_SRC + ' (FAO land area, WB population)', 'EN.POP.DNST', WBURL.format('EN.POP.DNST'),
        notes='Persons per km2 of LAND area (the 2018 figure label "per sq mile" is wrong; its values are per km2).')
audit.append(dict(indicator_id='F11_08', status='CLOSE MODERN EQUIVALENT', original_source='OECD country statistical profiles (2015-2016); values match WB EN.POP.DNST',
                  modern_source=WB_SRC, modern_definition='Midyear population / land area (persons per km2)',
                  years_used=f'{min(yrs)}-{max(yrs)}', n_countries_available=11,
                  change_vs_2018='OECD country statistical profiles discontinued; WB EN.POP.DNST reproduces the original magnitudes.',
                  notes='Unit is persons per km2, NOT per sq mile: orchestrator should correct the figure label. Latest WDI year 2023 (land area denominator unaffected by the surface-area revision).'))

os.makedirs(os.path.join(ROOT, 'results'), exist_ok=True)
with open(os.path.join(ROOT, 'results/wb_who_data.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['indicator_id', 'country', 'value', 'unit', 'obs_year', 'modern_source', 'dataset_code', 'url',
                                      'retrieval_date', 'flags', 'notes'])
    w.writeheader(); w.writerows(data)
with open(os.path.join(ROOT, 'results/wb_who_audit.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['indicator_id', 'status', 'original_source', 'modern_source', 'modern_definition', 'years_used',
                                      'n_countries_available', 'change_vs_2018', 'notes'])
    w.writeheader(); w.writerows(audit)
print(len(data), 'data rows;', len(audit), 'audit rows')

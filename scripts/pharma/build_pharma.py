"""Build results/pharma_data.csv and results/pharma_audit.csv (Figure 9, Pharmaceuticals).
Run: python3 -I scripts/pharma/build_pharma.py   (from the repository root)
Raw inputs (all in raw/pharma/):
  sha_hc51.csv            OECD DSD_SHA@DF_SHA, HC5/HC51/HC511 all financing schemes (URL in sha_hc51.url)
  phmc_DF_GEN_MRKT.csv    OECD HEALTH_PHMC@DF_GEN_MRKT (generics)
  hcqo_pipc.csv           OECD DSD_HCQO@DF_PIPC (prescribing in primary care; PRABOUDD antibiotics)
  haag2025_stat_*.xlsx    Health at a Glance 2025 StatLinks (Fig 9.1, 9.3, 6.6, ...)
  ecdc_esacnet_aer2024_rev2.pdf  ECDC ESAC-Net AER 2024, Table 4 (values transcribed below, page 11)
  efpia_figures_2026.pdf  EFPIA Pharmaceutical Industry in Figures 2026, p.8 (NCE chart, values transcribed below)
"""
import csv, os
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, 'raw/pharma')
C = "USA GBR DEU SWE FRA NLD CHE DNK CAN JPN AUS".split()
RET = '2026-10-07'
NAMES = {'United States': 'USA', 'United Kingdom': 'GBR', 'Germany': 'DEU', 'Sweden': 'SWE', 'France': 'FRA',
         'Netherlands': 'NLD', 'Switzerland': 'CHE', 'Denmark': 'DNK', 'Canada': 'CAN', 'Japan': 'JPN', 'Australia': 'AUS'}

SHA_URL = open(os.path.join(RAW, 'sha_hc51.url')).read().strip()
GEN_URL = 'https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,HEALTH_PHMC@DF_GEN_MRKT,1.1/all?startPeriod=2010&format=csvfilewithlabels'
PIPC_URL = 'https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,DSD_HCQO@DF_PIPC,2.1/all?startPeriod=2013&format=csvfilewithlabels'
ECDC_URL = 'https://www.ecdc.europa.eu/sites/default/files/documents/ESAC-Net-AER-2024_rev2.pdf'
EFPIA_URL = 'https://www.efpia.eu/media/owqczcqz/the-pharmaceutical-industry-in-figures-2026.pdf'

rows = []


def add(ind, c, value, unit, year, src, ds, url, flags='', notes=''):
    if value is None:
        year = ''
        value = 'NA'
    rows.append(dict(indicator_id=ind, country=c, value=value, unit=unit, obs_year=year, modern_source=src,
                     dataset_code=ds, url=url, retrieval_date=RET, flags=flags, notes=notes))


def statlink(code):
    wb = openpyxl.load_workbook(os.path.join(RAW, f'haag2025_stat_{code}.xlsx'), data_only=True)
    out = {}
    for ws in wb:
        for row in ws.iter_rows(values_only=True):
            if row[0] is None:
                continue
            name = str(row[0]).rstrip('¹²³* ').strip()
            if name in NAMES:
                out[NAMES[name]] = row
    return out

# ---------------- SHA (F9_02, F9_08-10) ----------------
sha = list(csv.DictReader(open(os.path.join(RAW, 'sha_hc51.csv'))))


def sha_series(c, unit, fs, price):
    d = {}
    for x in sha:
        if (x['REF_AREA'] == c and x['FUNCTION'] == 'HC51' and x['PROVIDER'] == '_T' and x['UNIT_MEASURE'] == unit
                and x['FINANCING_SCHEME'] == fs and x['PRICE_BASE'] == price and x['OBS_VALUE'] != ''):
            d[x['TIME_PERIOD']] = (float(x['OBS_VALUE']), '|'.join(f for f in (x['OBS_STATUS'], x['OBS_STATUS2'], x['OBS_STATUS3']) if f))
    return d

for c in C:
    s = sha_series(c, 'USD_PPP_PS', '_T', 'V')
    y = max(s)
    v, f = s[y]
    add('F9_02', c, round(v), 'USD PPP per capita', y, 'OECD Health Statistics (SHA 2011), Data Explorer', 'OECD.ELS.HD:DSD_SHA@DF_SHA(1.1) HC.5.1, HF _T, HP _T, USD_PPP_PS, current prices',
        SHA_URL, f, 'HC.5.1 pharmaceuticals and other medical non-durable goods (retail; hospital inpatient drugs excluded); current prices, current PPPs' + ('; provisional' if 'P' in f else ''))

fin_notes = {}
for c in C:
    tot = sha_series(c, 'XDC', '_T', 'V')
    y = max(tot)
    t, tf = tot[y]
    parts = {}
    for fs in ['HF1', 'HF2', 'HF21', 'HF22', 'HF23', 'HF3', 'HF122', 'HF2HF3']:
        s = sha_series(c, 'XDC', fs, 'V')
        if y in s:
            parts[fs] = (100 * s[y][0] / t, s[y][1])
    hf1 = parts['HF1'][0]
    hf3 = parts['HF3'][0]
    hf21 = parts.get('HF21', (None, ''))[0]
    other = 100 - hf1 - hf3 - (hf21 or 0)
    base = f'Shares of HC.5.1 current-price national-currency spending ({y}); HF1={hf1:.1f}, HF2.1={hf21 if hf21 is None else round(hf21,1)}, HF3={hf3:.1f}, other/residual={other:.1f}'
    flagp = tf
    add('F9_08', c, round(hf1, 1), '% of retail pharma spending', y, 'OECD Health Statistics (SHA 2011)', 'DSD_SHA@DF_SHA HC.5.1 HF.1 / _T (XDC)', SHA_URL, flagp,
        base + ('; US: includes employer/individual private insurance reported by the US as HF.1.2.2 compulsory private insurance (' + f"{parts['HF122'][0]:.1f}%" + ') since ACA mandate - not separable from public' if c == 'USA' else '')
        + ('; CHE/NLD: mandatory basic health insurance classified HF.1.2.2' if c in ('CHE', 'NLD') else ''))
    vnote = base
    vflag = flagp
    if hf21 is None:
        if c == 'USA':
            vnote += f"; US does not report HF.2.1: private insurance is classified as HF.1.2.2 compulsory private insurance and counted in F9_08 ({parts['HF122'][0]:.1f}%); HF.2 total={parts['HF2'][0]:.1f}% (non-VHI voluntary schemes). OECD Health at a Glance 2025 Fig 9.2 likewise shows US VHI = 0. Not comparable with original 36% (2011)."
            hf21v = 0.0
            vflag = (vflag + '|D').strip('|')
        else:
            vnote += '; no voluntary scheme reported (HF1+HF3=100%); recorded as 0 (OECD HaaG 2025 Fig 9.2 also shows 0)'
            hf21v = 0.0
    else:
        hf21v = round(hf21, 1)
    add('F9_09', c, hf21v, '% of retail pharma spending', y, 'OECD Health Statistics (SHA 2011)', 'DSD_SHA@DF_SHA HC.5.1 HF.2.1 / _T (XDC)', SHA_URL, vflag, vnote)
    add('F9_10', c, round(hf3, 1), '% of retail pharma spending', y, 'OECD Health Statistics (SHA 2011)', 'DSD_SHA@DF_SHA HC.5.1 HF.3 / _T (XDC)', SHA_URL, flagp, base)

# ---------------- F9_01 total pharma spending incl. hospital ----------------
f91 = statlink('x3emfc')   # retail per capita USD PPP, cols: Rx, OTC, total(no breakdown), Total
f93 = statlink('jv49fl')   # non-retail share of total pharma, cols: 2013, 2023
for c in C:
    if c in f93 and c in f91:
        retail = f91[c][4]
        share = f93[c][2]
        val = retail / (1 - share / 100)
        yr = '2022' if c == 'AUS' else '2023'
        add('F9_01', c, round(val), 'USD PPP per capita', yr, 'OECD Health at a Glance 2025 (Fig 9.1 retail per capita + Fig 9.3 non-retail share), OECD Health Statistics 2025', 'HaaG2025 StatLinks x3emfc & jv49fl',
            'https://stat.link/x3emfc ; https://stat.link/jv49fl', 'D',
            f'Derived: retail Rx+OTC per capita {retail:.1f} USD PPP / (1 - non-retail share {share:.1f}%) = total (retail+hospital/non-retail) pharmaceutical spending, net of rebates; OECD SHA basis, PPP (original IMS/IFPMA was nominal US$ at exchange rates, invoice/ex-manufacturer basis)')
    else:
        add('F9_01', c, None, 'USD PPP per capita', '', 'OECD Health at a Glance 2025 (Fig 9.1 + Fig 9.3)', 'HaaG2025 StatLinks x3emfc & jv49fl', 'https://stat.link/jv49fl', '',
            'Country not among the 15 OECD countries reporting non-retail (hospital) pharmaceutical expenditure in HaaG 2025 Fig 9.3; no single consistent public source covers it (EFPIA = Europe only, ex-factory/PPP-mixed, EUR totals; IQVIA per-capita country data not public)')

# ---------------- F9_03..F9_06 drug prices ----------------
for ind, drug in [('F9_03', 'Crestor/rosuvastatin'), ('F9_04', 'Lantus/insulin glargine'), ('F9_05', 'Advair/fluticasone-salmeterol'), ('F9_06', 'Humira/adalimumab')]:
    for c in C:
        add(ind, c, None, 'USD per month', '', 'none (Bloomberg/SSR Health 2015 graphic not updated)', '', 'https://www.bloomberg.com/graphics/2015-drug-prices/', '',
            f'No current multi-country single-methodology monthly price source for {drug}; national formulary prices not assembled (different methodology)')

# ---------------- F9_07 NCE ----------------
for c in C:
    if c in ('USA', 'JPN'):
        v = {'USA': 140, 'JPN': 33}[c]
        add('F9_07', c, v, 'count', '2021-2025', 'EFPIA, The Pharmaceutical Industry in Figures - Key Data 2026 (p.8), from Citeline Pharma R&D Annual Review 2026 & Scrip', 'EFPIA Key Data 2026 NCE chart', EFPIA_URL, 'D',
            'New chemical AND biological entities first launched on world market 2021-2025, by nationality of mother company (annual 2021-2025: USA 35,24,28,25,28; Japan 8,10,5,5,5). Original: Daemmrich NCEs 1982-2003 by originator nationality - different window/source/definition')
    else:
        add('F9_07', c, None, 'count', '', 'EFPIA Key Data 2026 (only Europe/USA/Japan/China/Others blocks)', 'EFPIA Key Data 2026 NCE chart', EFPIA_URL, '',
            'Only aggregate blocks published (Europe 87, China 133, Others 50 in 2021-2025); no per-country count for this country')

# ---------------- F9_11 / F9_12 generics ----------------
gen = list(csv.DictReader(open(os.path.join(RAW, 'phmc_DF_GEN_MRKT.csv'))))
# market per country: follows OECD Health at a Glance 2025 Fig 9.7/9.8 choice; SWE/AUS not in HaaG figure
MK = {'DEU': 'TPP', 'GBR': 'COMMUNITY', 'NLD': 'TPP', 'CAN': '_T', 'DNK': 'TPP', 'JPN': '_T', 'FRA': 'COMMUNITY', 'CHE': '_T', 'SWE': '_T', 'AUS': 'TPP'}
MKN = {'TPP': 'reimbursed (third-party-payer) market', 'COMMUNITY': 'community pharmacy market', '_T': 'total market'}
for ind, u in [('F9_11', 'PT_SL_VOL_M'), ('F9_12', 'PT_SL_VAL_M')]:
    unit = '% of pharmaceutical market volume' if ind == 'F9_11' else '% of pharmaceutical market value'
    for c in C:
        if c not in MK:
            add(ind, c, None, unit, '', 'OECD Health Statistics', 'OECD.ELS.HD:HEALTH_PHMC@DF_GEN_MRKT(1.1)', GEN_URL, '',
                'United States does not report generic market shares to OECD (original US value was from a non-OECD source)')
            continue
        m = MK[c]
        s = sorted([x for x in gen if x['REF_AREA'] == c and x['UNIT_MEASURE'] == u and x['MARKET_TYPE'] == m and x['OBS_VALUE']], key=lambda x: x['TIME_PERIOD'])
        x = s[-1]
        fl = '|'.join(f for f in (x['OBS_STATUS'], x['OBS_STATUS2']) if f)
        note = f'Market basis: {MKN[m]} (MARKET_TYPE={m})'
        if c in ('SWE', 'AUS'):
            note += '; country not shown in HaaG 2025 Fig 9.7/9.8, market chosen here (SWE total market; AUS only reports reimbursed/PBS market, OECD flag D = difference in methodology)'
        if c == 'JPN':
            note += '; OECD used instead of original Cabinet Office source'
        if c == 'GBR':
            note += '; UK reimbursed-market series ended 2017 (85.3% vol / 36.2% val), so not comparable with 2013 original basis'
        add(ind, c, float(x['OBS_VALUE']), unit, x['TIME_PERIOD'], 'OECD Health Statistics (pharmaceutical market)', f'OECD.ELS.HD:HEALTH_PHMC@DF_GEN_MRKT(1.1) {u} {m}', GEN_URL, fl, note)

# ---------------- F9_13 antibiotics ----------------
# EU countries: ECDC ESAC-Net AER 2024 Table 4 community J01 (transcribed from p.11 image)
ECDC = {'DEU': ('2024', 12.1, ''), 'FRA': ('2024', 24.7, ''), 'NLD': ('2024', 9.0, ''),
        'DNK': ('2024', 14.4, 'B'), 'SWE': ('2022', 9.6, 'B')}
for c, (y, v, f) in ECDC.items():
    n = 'Community sector consumption, ATC J01, DDD/1000 inhabitants/day; ECDC ESAC-Net (the source OECD HaaG uses for EU countries)'
    if c == 'DNK':
        n += '; ECDC note: external data used for Denmark in 2024, impact on comparability with previous years'
    if c == 'SWE':
        n += '; Sweden did not report community data for 2023-2024; ECDC note: external data used for 2022 (HaaG 2025 used 2021 = 8.7)'
    if c == 'NLD':
        n += '; NL excludes long-term care facilities'
    add('F9_13', c, v, 'DDD per 1,000 population per day', y, 'ECDC ESAC-Net Annual Epidemiological Report 2024 (Table 4)', 'ESAC-Net community J01', ECDC_URL, f, n)
# GBR: HaaG 2025 Fig 6.6 (ECDC 2021 report, 2019 data; UK left ESAC-Net)
f66 = statlink('f73vza')
add('F9_13', 'GBR', round(f66['GBR'][2], 1), 'DDD per 1,000 population per day', '2019', 'OECD Health at a Glance 2025 Fig 6.6 (ECDC 2021 for United Kingdom)', 'HaaG2025 StatLink f73vza', 'https://stat.link/f73vza', '',
    'Community setting; latest comparable UK figure is 2019 (UK no longer reports to ESAC-Net after Brexit)')
pipc = [x for x in csv.DictReader(open(os.path.join(RAW, 'hcqo_pipc.csv'))) if x['MEASURE'] == 'PRABOUDD' and x['SEX'] == '_T' and x['AGE'] == '_T']
for c in ('CAN', 'JPN', 'AUS'):
    s = sorted([x for x in pipc if x['REF_AREA'] == c and x['OBS_VALUE']], key=lambda x: x['TIME_PERIOD'])
    x = s[-1]
    fl = '|'.join(f for f in (x['OBS_STATUS'], x.get('OBS_STATUS2', '')) if f)
    add('F9_13', c, float(x['OBS_VALUE']), 'DDD per 1,000 population per day', x['TIME_PERIOD'], 'OECD Health Care Quality Indicators - Prescribing in primary care', 'OECD.ELS.HD:DSD_HCQO@DF_PIPC(2.1) PRABOUDD, sex _T', PIPC_URL, fl,
        'Total volume of antibiotics for systemic use prescribed (primary care / community), ATC J01; same series HaaG 2025 Fig 6.6 uses for non-EU countries')
add('F9_13', 'CHE', None, 'DDD per 1,000 population per day', '', 'OECD HCQO / ECDC', '', PIPC_URL, '', 'Switzerland not covered by ESAC-Net or OECD primary-care prescribing indicator (original also NA)')
add('F9_13', 'USA', None, 'DDD per 1,000 population per day', '', 'OECD HCQO / OECD HEALTH_PHMC', '', PIPC_URL, '',
    'No official US DDD-based figure in OECD (HCQO or HEALTH_PHMC consumption); CDC outpatient antibiotic prescribing is prescriptions per 1,000 persons - not comparable. Original US value was 2004.')

# order
order = ['F9_%02d' % i for i in range(1, 14)]
rows.sort(key=lambda r: (order.index(r['indicator_id']), C.index(r['country'])))
assert len(rows) == 13 * 11, len(rows)
fields = 'indicator_id,country,value,unit,obs_year,modern_source,dataset_code,url,retrieval_date,flags,notes'.split(',')
with open(os.path.join(ROOT, 'results/pharma_data.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)


def summ(ind):
    rr = [r for r in rows if r['indicator_id'] == ind and r['value'] != 'NA']
    ys = sorted(set(r['obs_year'] for r in rr))
    return ';'.join(ys), len(rr)

PRICE_NOTE = ('Searched for a current multi-country, single-methodology per-drug monthly price source: Bloomberg/SSR Health 2015 graphic was never updated; IFHP Comparative Price Reports ended ~2017; RAND (2021, 2024) international price comparisons report aggregate price indices (and insulin as a class) not per-drug monthly prices; Medbelle 2019 index is a commercial startup ranking (not credible/consistent). '
              'Assembling national formulary prices would be a different methodology. Also: rosuvastatin is generic since 2016 (US) and insulin glargine has biosimilars/unbranded versions (US list price cuts 2024), Humira biosimilars launched EU 2018 / US 2023, and US list vs net prices have diverged sharply (rebates), so the 2015 "US discounted price" concept no longer maps to a single number.')
audit = [
    ('F9_01', 'NOT COMPARABLE', 'IMS (2016) / IFPMA (2014), nominal US$', 'OECD Health at a Glance 2025 Fig 9.1 & 9.3 (OECD Health Statistics 2025)',
     'Total (retail + hospital/non-retail) pharmaceutical expenditure per capita, net of rebates, USD PPP; derived as retail Rx+OTC per capita / (1 - non-retail share)',
     'PPP not exchange-rate US$; SHA net spending vs IMS invoice sales; only 15 OECD countries report non-retail pharma (US, GBR, FRA, NLD, SWE, JPN do not)',
     'Sources checked: OECD SDMX has no direct total-pharma series (DF_SHA_FP lacks FP.3.1 for these countries); IQVIA Global Use of Medicines 2024/2026 public PDFs give no per-capita spending by country; EFPIA Key Data 2026 gives market value at ex-factory prices (EUR million totals, 7 of 11 countries, some at pharmacy purchasing prices) - not per capita and Europe only; IFPMA Facts & Figures not country-level. OECD HaaG chosen as single consistent source (5 countries).'),
    ('F9_02', 'DIRECTLY UPDATED', 'OECD.stat 2015', 'OECD Data Explorer DSD_SHA@DF_SHA', 'HC.5.1 per capita, current prices, current PPPs, all financing', '', 'Latest year per country; NLD, DNK, CAN 2025 are provisional (P). HaaG 2025 Fig 9.1 shows HC.5.1.1+HC.5.1.2 only (excl. other non-durables) - we keep HC.5.1 to match original definition'),
    ('F9_03', 'UNAVAILABLE', 'Bloomberg / SSR Health 2015', 'none', '', 'Source discontinued', PRICE_NOTE),
    ('F9_04', 'UNAVAILABLE', 'Bloomberg / SSR Health 2015', 'none', '', 'Source discontinued', PRICE_NOTE),
    ('F9_05', 'UNAVAILABLE', 'Bloomberg / SSR Health 2015', 'none', '', 'Source discontinued', PRICE_NOTE),
    ('F9_06', 'UNAVAILABLE', 'Bloomberg / SSR Health 2015', 'none', '', 'Source discontinued', PRICE_NOTE),
    ('F9_07', 'NOT COMPARABLE', 'Daemmrich 2009 (HBS WP 09-118), NCEs 1982-2003 by originator nationality', 'EFPIA Key Data 2026 (Citeline/Scrip), NCEs+NBEs 2021-2025 by nationality of mother company',
     'New chemical and biological entities first launched worldwide, 5-year window 2021-2025', '22-year window -> 5-year; biologicals included; only USA and Japan reported individually (Europe aggregated)',
     'IQVIA Institute R&D trend reports give novel active substances by company HQ region (US/Europe/China/Japan), not by our European countries; no counts computed from FDA lists'),
    ('F9_08', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2015 (2011 data)', 'OECD Data Explorer DSD_SHA@DF_SHA', 'Share of HC.5.1 financed by HF.1 government/compulsory schemes', 'US private insurance reclassified as HF.1.2.2 compulsory private insurance (post-ACA), inflating US "public" share (original 34% -> 69%)', 'Shares computed from national-currency values, same year as F9_02'),
    ('F9_09', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2015 (2011 data)', 'OECD Data Explorer DSD_SHA@DF_SHA', 'Share of HC.5.1 financed by HF.2.1 voluntary health insurance', 'US value set to 0 as in HaaG 2025: US private insurance now reported under HF.1.2.2 (not comparable with original 36%); GBR/SWE report no voluntary schemes (0)', 'Residual other voluntary schemes (HF.2.2/HF.2.3, US HF.2 0.7%) noted in data notes'),
    ('F9_10', 'DIRECTLY UPDATED', 'OECD Health at a Glance 2015 (2011 data)', 'OECD Data Explorer DSD_SHA@DF_SHA', 'Share of HC.5.1 financed by HF.3 household out-of-pocket', '', 'F9_08+F9_09+F9_10 + residual = 100'),
    ('F9_11', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2015 (2013); JP Cabinet Office', 'OECD HEALTH_PHMC@DF_GEN_MRKT', 'Generics share of market volume; market basis per country follows HaaG 2025 Fig 9.7', 'Mixed market bases (reimbursed/community/total) as in original; UK basis changed from reimbursed (to 2017) to community; JP now OECD; US not reported',
     'DEU/NLD/DNK/AUS reimbursed; GBR/FRA community pharmacy; CAN/JPN/CHE/SWE total market. Note HaaG 2025 statlink value labels for UK/France value appear inconsistent with database; database used.'),
    ('F9_12', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2015 (2013); JP Cabinet Office', 'OECD HEALTH_PHMC@DF_GEN_MRKT', 'Generics share of market value; same market basis as F9_11', 'As F9_11', 'As F9_11'),
    ('F9_13', 'CLOSE MODERN EQUIVALENT', 'OECD Health at a Glance 2017 (2015; US 2004)', 'ECDC ESAC-Net AER 2024 (EU countries), OECD HCQO DF_PIPC (CAN, JPN, AUS), HaaG 2025 Fig 6.6 (GBR 2019)',
     'Antibacterials for systemic use (J01), DDD/1000/day, community/primary-care setting (same source mix HaaG uses)', 'Community-only basis kept consistently; US and CHE NA',
     'Alternative OECD HEALTH_PHMC@DF_PHMC_CONSUM J01 (total consumption, mixed coverage, D flags; e.g. SWE 11.9, DNK 16.1, FRA 26.5 in 2024; no USA/CHE) not used to keep community basis. CDC US outpatient data are prescriptions per 1000 persons, not DDD.'),
]
with open(os.path.join(ROOT, 'results/pharma_audit.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow('indicator_id,status,original_source,modern_source,modern_definition,years_used,n_countries_available,change_vs_2018,notes'.split(','))
    for ind, st, os_, ms, md, ch, nt in audit:
        ys, n = summ(ind)
        w.writerow([ind, st, os_, ms, md, ys, n, ch, nt])
print('ok', len(rows))

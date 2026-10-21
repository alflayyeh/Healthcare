"""Builds results/country_data.csv and results/country_audit.csv for indicators
F4_11, F5_02, F5_03, F5_05, F5_06, F11_09, F11_10 from files in raw/country/."""
import os
import csv,json,collections
W=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/'; R=W+'raw/country/'
RET='2026-10-07'
C=['USA','GBR','DEU','SWE','FRA','NLD','CHE','DNK','CAN','JPN','AUS']
rows=[]
def add(i,c,v,unit,yr,src,ds,url,flags='',notes=''):
    rows.append(dict(indicator_id=i,country=c,value='NA' if v is None else v,unit=unit,obs_year='' if v is None else yr,
        modern_source=src if v is not None else (src or ''),dataset_code=ds,url=url,retrieval_date=RET,flags=flags,notes=notes))
CTRY='USA+GBR+DEU+SWE+FRA+NLD+CHE+DNK+CAN+JPN+AUS'
# ---------------- F5_02 / F5_03 -----------------
U_PC=f'https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,DSD_HEALTH_EMP_REAC@DF_PHYS_CAT,1.1/{CTRY}........?startPeriod=2010&format=csvfilewithlabels'
pc=collections.defaultdict(dict); fl=collections.defaultdict(dict)
for x in csv.DictReader(open(R+'oecd_phys_cat.csv')):
    if x['UNIT_MEASURE']=='PS':
        pc[(x['REF_AREA'],x['TIME_PERIOD'])][x['HEALTH_PROF']]=float(x['OBS_VALUE'])
        fl[(x['REF_AREA'],x['TIME_PERIOD'])][x['HEALTH_PROF']]=','.join(f for f in (x['OBS_STATUS'],x['OBS_STATUS2']) if f)
YEAR={'GBR':'2024','DEU':'2024','SWE':'2023','FRA':'2024','NLD':'2024','CHE':'2024','DNK':'2024','CAN':'2024','AUS':'2024'}
pcres={}
for c,y in YEAR.items():
    d=pc[(c,y)]; f=fl[(c,y)]
    gp_code='EMPLGENE'  # all generalist medical practitioners = Eurostat/OECD 'Generalists' category used by the original
    num=d[gp_code]+d['EMPLPEDI']
    alt_gp=(100*(d['EMPLGENP']+d['EMPLPEDI'])/(d['EMPLGENE']+d['EMPLSPMP']+d.get('EMPLOTPH',0))) if 'EMPLGENP' in d else None
    den=d['EMPLGENE']+d['EMPLSPMP']+d.get('EMPLOTPH',0)
    flags=sorted({v for k,v in f.items() if k in(gp_code,'EMPLPEDI','EMPLGENE','EMPLSPMP','EMPLOTPH') for v in v.split(',') if v})
    note=(f"OECD PHYS_CAT practising physicians (persons) {y}: numerator = Generalist medical practitioners (EMPLGENE, = original Eurostat 'generalists' category) {d[gp_code]:.0f} + General paediatricians (EMPLPEDI) {d['EMPLPEDI']:.0f}; "
          f"denominator = Generalists (EMPLGENE) {d['EMPLGENE']:.0f} + Specialists (EMPLSPMP) {d['EMPLSPMP']:.0f} + Doctors n.f.d. (EMPLOTPH) {d.get('EMPLOTPH',0):.0f} = {den:.0f}. "
          "General internal medicine & geriatrics cannot be isolated in OECD (inside 'medical group of specialists') so are counted as specialists; OB-GYN counted as specialist.")
    if alt_gp is not None and abs(alt_gp-100*num/den)>0.05: note+=f' Using only the GP sub-category (EMPLGENP {d["EMPLGENP"]:.0f}; excludes other non-specialist generalists, e.g. hospital junior doctors) the share would be {alt_gp:.1f}%.'
    if c=='SWE': note+=' 2024 values are provisional (P) and show an implausible drop in specialists, so 2023 (final) used.'
    if c=='FRA': note+=' France reports 45,714 doctors n.f.d. (mainly residents) since 2020; they are included in the denominator.'
    pcres[c]=(100*num/den,y,','.join(flags),note)
# USA - KFF (original source), Redi-Data May 2026
kff=dict(IM=278177,FM=141147,PED=101612,OBG=58639,PCP=579575,TOT=1068924)
v=100*(kff['IM']+kff['FM']+kff['PED'])/kff['TOT']
pcres['USA']=(v,'2026','',f"KFF State Health Facts (Redi-Data special request, active state-licensed MDs+DOs, May 2026): Internal Medicine {kff['IM']} + Family Medicine {kff['FM']} + Pediatrics {kff['PED']} = {kff['IM']+kff['FM']+kff['PED']} / total professionally active physicians {kff['TOT']}. OB-GYN ({kff['OBG']}) moved to specialists per the paper's definition (KFF itself counts OB-GYN as primary care: 579,575 = 54.2%). KFF 'Internal Medicine' may include some IM subspecialists; geriatrics not shown separately (within IM).")
# JPN - MHLW Survey of Physicians, Dentists and Pharmacists 2024, Table 4
j=dict(tot=331092,naika=62161,ped=18009,zenka=241,intern=18257)
v=100*(j['naika']+j['ped']+j['zenka'])/j['tot']
pcres['JPN']=(v,'2024','D',f"MHLW 'Statistics of Physicians, Dentists and Pharmacists 2024' Table 4 (physicians working in medical facilities by main specialty, 31 Dec 2024): general internal medicine (naika) {j['naika']} + paediatrics {j['ped']} + all-specialty/general (zenka) {j['zenka']} = {j['naika']+j['ped']+j['zenka']} / total {j['tot']} (incl. {j['intern']} clinical trainees, consistent with OECD practising totals; excluding trainees the share is {100*(j['naika']+j['ped']+j['zenka'])/(j['tot']-j['intern']):.1f}%). Japan has no GP register; general internists are the de facto primary-care physicians. Internal-medicine subspecialties counted as specialists.")
URLS={'USA':'https://www.kff.org/other/state-indicator/primary-care-physicians-by-field/ ; https://www.kff.org/other/state-indicator/total-active-physicians/',
      'JPN':'https://www.mhlw.go.jp/toukei/saikin/hw/ishi/24/dl/R06_1gaikyo.pdf'}
for c in C:
    v,y,f,n=pcres[c]
    src={'USA':'KFF State Health Facts (Redi-Data)','JPN':'MHLW Statistics of Physicians, Dentists and Pharmacists 2024'}.get(c,'OECD Health Statistics - Physicians by categories')
    ds={'USA':'KFF primary-care-physicians-by-field; total-active-physicians','JPN':'MHLW R06 ishi Table 4'}.get(c,'OECD.ELS.HD:DSD_HEALTH_EMP_REAC@DF_PHYS_CAT(1.1)')
    add('F5_02',c,round(v,1),'% of practising physicians',y,src,ds,URLS.get(c,U_PC),f,n)
    add('F5_03',c,round(100-v,1),'% of practising physicians',y,src,ds,URLS.get(c,U_PC),f,'= 100 - F5_02 (same source/year). '+n)
# ---------------- F5_05 / F5_06 -----------------
U_RM=f'https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,DSD_HEALTH_REAC_EMP@DF_REMUN,1.1/{CTRY}........?startPeriod=2010&format=csvfilewithlabels'
rm={}
for x in csv.DictReader(open(R+'oecd_remun.csv')):
    if x['UNIT_MEASURE']=='USD_PPP' and x['SEX']=='_T':
        rm[(x['REF_AREA'],x['HEALTH_PROF'],x['WORKER_STATUS'],x['TIME_PERIOD'])]=(float(x['OBS_VALUE']),','.join(f for f in (x['OBS_STATUS'],x['OBS_STATUS2']) if f))
def latest(c,p,w):
    ys=sorted(y for (cc,pp,ww,y) in rm if (cc,pp,ww)==(c,p,w)); return ys[-1] if ys else None
SE,SA='ICSE93_2T5','ICSE93_1'
CHOICE={ # country: (GP status, specialist status, rationale)
 'AUS':(SE,SE,'Original (Medicare/AIHW) = self-employed GPs and specialists; only self-employed reported.'),
 'CAN':(SE,SE,'Original CIHI National Physician Database = fee-for-service (self-employed) gross payments; only self-employed reported.'),
 'CHE':(SE,SE,'Original NA; OECD reports self-employed only.'),
 'DEU':(SE,SA,'Original GP from Laugesen & Glied (self-employed office GPs); original specialist from Kienbaum hospital study (salaried); matches original values in 2013-17.'),
 'DNK':(SE,SA,'GPs are self-employed contractors in DK; specialists salaried (original used OECD salaried specialists).'),
 'FRA':(SE,SA,'Original GP = INSEE self-employed GP income; original specialist = SIASP (public-sector salaried hospital physicians).'),
 'GBR':(SE,SA,'Original GP value (134,671) matches OECD self-employed (contractor/partner) GPs; specialists = NHS salaried consultants (NHS ESR).'),
 'NLD':(SA,SE,'Original NL values (OECD) matched salaried GPs (~110k) and self-employed specialists (~190k) in 2013-17.'),
 'SWE':(SA,SA,'Swedish physicians are salaried (county councils); only salaried reported.'),
}
for ind,prof,k in (('F5_05','EMPLGENP',0),('F5_06','EMPLSPMP',1)):
    for c in C:
        if c in CHOICE:
            st=CHOICE[c][k]; y=latest(c,prof,st); v,f=rm[(c,prof,st,y)]
            other=SA if st==SE else SE; yo=latest(c,prof,other)
            alt=f" Alternative {('salaried' if other==SA else 'self-employed')} value: {rm[(c,prof,other,yo)][0]:,.0f} ({yo})." if yo else ''
            mode='self-employed' if st==SE else 'salaried'
            add(ind,c,round(v),'USD PPP current prices, obs year',y,'OECD Health Statistics - Remuneration of health professionals','OECD.ELS.HD:DSD_HEALTH_REAC_EMP@DF_REMUN(1.1)',U_RM,
                ';'.join(x for x in (f,mode) if x),f"{'GPs' if prof=='EMPLGENP' else 'Specialists'}, {mode}, both sexes, annual income, USD PPP (OECD uses HFCE PPPs), current prices. {CHOICE[c][2]}{alt} Not deflated (orchestrator applies US CPI).")
        elif c=='USA':
            v=298000 if ind=='F5_05' else 417000
            add(ind,c,v,'USD nominal, obs year','2025','Medscape Physician Compensation Report 2026 (as reported by Advisory Board Daily Briefing 2026-06-04)','Medscape 2026 report',
                'https://www.advisory.com/daily-briefing/2026/06/04/physician-compensation','non-OECD national source',
                f"Average total compensation (salary+bonus+profit-sharing) of full-time US {'primary care physicians' if ind=='F5_05' else 'specialists'}, 2025 earnings, ~6,000 respondents (survey 5 Sep-17 Dec 2025). Same source family as original US specialist value (Medscape 2017); original US GP used AMA/Laugesen&Glied but Medscape 2017 PCP ($217k) ~= original $218k. Medscape report itself paywalled (medscape.com/sites/public/physician-comp/2026).")
        elif c=='JPN':
            if ind=='F5_05':
                yen=14845784; ppp=99.384798
                add(ind,c,round(yen/ppp),'USD PPP current prices, obs year','2024','MHLW 25th Survey on Economic Conditions in Health Care (2025), Table 23 + OECD HFCE PPP','MHLW iryou keizai jittai chousa 25; OECD DSD_NAMAIN10@DF_TABLE4 PPP_P31S14',
                    'https://www.mhlw.go.jp/bunya/iryouhoken/database/zenpan/jittaityousa/dl/25_houkoku_iryoukikan.pdf ; https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN10@DF_TABLE4,/A.JPN+CHE+GBR+USA...........?startPeriod=2022&format=csvfilewithlabels',
                    'combined GP+specialist;salaried;non-OECD national source',
                    f"Combined GP+specialist figure (as in original, footnote a): average annual salary+bonus of full-time physicians (excl. hospital directors) in general hospitals, all ownership types, FY2024 = JPY {yen:,} (FY2023: 14,810,849); converted with OECD PPP for household final consumption 2024 = {ppp} JPY/USD (same PPP basis as OECD REMUN). Clinic physicians (salaried) FY2024 avg ~JPY 11.0m not included.")
            else:
                add(ind,c,None,'USD PPP current prices, obs year','','','','','','Japan has no separate specialist remuneration series; original also NA (combined figure shown under generalists). MHLW hospital-physician figure (USD PPP ~149k, 2024) recorded under F5_05.')
# ---------------- F11_09 / F11_10 -----------------
ur=json.load(open(R+'urban_rural_physicians_result.json'))
U_UR='https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_HEALTH@DF_CARE,2.5/A....DOC...?startPeriod=2000&format=csvfilewithlabels'
TYPNOTE={'SWE':'Region classes = Eurostat NUTS-2021 urban-rural typology, which reproduces OECD PU/IN/PR population totals exactly.',
 'CHE':'Region classes = Eurostat NUTS-2021 urban-rural typology, which reproduces OECD PU/IN/PR population totals exactly.',
 'FRA':'Region classes = Eurostat NUTS-2024 typology with Corse-du-Sud reclassified to PR, reproducing OECD totals exactly.',
 'JPN':'Region (prefecture) classes reconstructed by exact subset search against OECD PU/IN/PR population (2022-23), land-area and PRR/PRC totals (unique solution): PU = 12 prefectures, PR = 13.',
 'AUS':'TL3 classes reconstructed by exact subset search against OECD PU/IN population totals 2022-23 (unique; PU land area exact); AUZZZ (other territories, not regionalised) excluded.',
 'DEU':'OECD per-region class not recoverable; Eurostat NUTS-2024 urban-rural typology used (population by class differs from OECD aggregates by ~1.1m PU / ~1.6m PR).'}
for ind,k in (('F11_09','PU'),('F11_10','PR')):
    for c in C:
        if c in ur:
            d=ur[c]; P,N,n=d['detail'][k]
            fl='D' if c=='DEU' else ''
            extra=' German TL3 physician counts cover ambulatory (KBV-registered) physicians only (national total ~1.5/1000 vs 4.7 practising), so levels are not comparable with other countries; original DE values (2.0/1.3) were also low.' if c=='DEU' else ''
            add(ind,c,round(d[k],2),'per 1,000 population',d['year'],'OECD Regional Statistics - Health care (TL3), aggregated by OECD urban-rural typology','OECD.CFE.EDS:DSD_REG_HEALTH@DF_CARE(2.5) DOC; DSD_REG_DEMO@DF_REGION_TYPE_RURB',U_UR,fl,
                f"Active physicians / population summed over {n} TL3 regions classed {'predominantly urban (PU)' if k=='PU' else 'predominantly rural (PR)'}: {P:,.0f} / {N:,.0f}. {TYPNOTE[c]}{extra} Script scripts/country/urban_rural_physicians.py.")
        else:
            why={'USA':'OECD regional health data for the US exist only at TL2 (states); no TL3 physician data.',
                 'CAN':'OECD regional health data for Canada only at TL2 (provinces).',
                 'GBR':'UK TL3 physician data end in 2009; TL2 ends 2016.',
                 'NLD':'Only TL2 (provinces) physician data in OECD regional database.',
                 'DNK':'Only TL2 physician data in OECD regional database.'}[c]
            add(ind,c,None,'per 1,000 population','','','','',
                '',why+' Not filled to keep one consistent typology (original also NA for GBR, NLD, DNK; original US/CA used national rural-health sources with different urban/rural definitions).')
# ---------------- F4_11 -----------------
for c in C:
    add('F4_11',c,None,'per 1,000 live births ≥1000 g','','','','','',
        'No newer study or official series reports neonatal mortality restricted to live births >=1000 g for these countries. Euro-Peristat reports (2015, 2019, 2021 data) restrict by gestational age (>=24 weeks), not birthweight; Mohangoo et al. 2013 (PLoS One) gives >=1000 g rates only for 2004 data (E&W 1.59, Scotland 1.54, FRA 1.50, NLD 1.96) - older than the original. A US-only value could be computed from CDC WONDER linked birth/infant death files but there is no comparator.')
order=['F4_11','F5_02','F5_03','F5_05','F5_06','F11_09','F11_10']
rows.sort(key=lambda r:(order.index(r['indicator_id']),C.index(r['country'])))
F=['indicator_id','country','value','unit','obs_year','modern_source','dataset_code','url','retrieval_date','flags','notes']
with open(W+'results/country_data.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=F); w.writeheader(); w.writerows(rows)
# audit
def yrs(i):
    ys=sorted({r['obs_year'] for r in rows if r['indicator_id']==i and r['obs_year']}); return ';'.join(ys)
def n(i): return sum(1 for r in rows if r['indicator_id']==i and r['value']!='NA')
spec={x['indicator_id']:x for x in csv.DictReader(open(W+'spec/indicators.csv'))}
A=[
 ('F4_11','UNAVAILABLE','No current source of neonatal mortality excluding <1000 g for these countries.','Neonatal deaths per 1,000 live births >=1000 g','Not updated; gestational-age-restricted (>=24 wk) Euro-Peristat rates exist for European countries only and are a different restriction.','Data rows NA; partial 2004 values in notes.'),
 ('F5_02','CLOSE MODERN EQUIVALENT','OECD Health Statistics DF_PHYS_CAT (9 countries); KFF/Redi-Data May 2026 (USA, original source); MHLW Physician Statistics 2024 (JPN)',
  '(General practitioners + general paediatricians) / all practising physicians (OECD); US adds general internal medicine (KFF); JPN = general internal medicine + paediatrics',
  'Original used heterogeneous national registers (GMC, CMA, Eurostat 2013 image, MBA, MHLW, Socialstyrelsen) incl. internal medicine & geriatrics. OECD/Eurostat no longer separate general internal medicine (Eurostat stopped after 2015), so for OECD countries GIM and geriatrics are counted as specialists (flag D-type limitation); US and JPN include general internal medicine as in the original. Cross-country comparability therefore imperfect.',
  'Numerator uses all Generalist medical practitioners (EMPLGENE) as the original Eurostat category did; this includes non-specialist doctors (e.g. hospital juniors) in DEU, NLD, FRA, AUS - GP-only alternative given in data notes.'),
 ('F5_03','CLOSE MODERN EQUIVALENT','Same as F5_02','100 - F5_02','As F5_02 (complement).',''),
 ('F5_05','CLOSE MODERN EQUIVALENT','OECD Health Statistics DF_REMUN (9 countries); Medscape 2026 (USA); MHLW Survey on Economic Conditions in Health Care 2025 (JPN, combined)',
  'Annual remuneration of GPs, USD PPP current prices (not deflated)','Original mixed national sources (Laugesen & Glied 2011 etc.) inflated to 2017 USD; now OECD standardised series for 9 countries with employment status chosen to match the original per country (see flags); US from Medscape (PCP average); JPN combined physician figure (hospital physicians, salaried). CHE and DNK now available (were NA).',
  'Values in current prices of the obs year; orchestrator to deflate with US CPI. OECD flags: E estimate, D definition differs, B break.'),
 ('F5_06','CLOSE MODERN EQUIVALENT','OECD Health Statistics DF_REMUN (9 countries); Medscape 2026 (USA)','Annual remuneration of specialists, USD PPP current prices (not deflated)',
  'As F5_05. GBR specialist series ends 2020. FRA uses salaried (public hospital) specialists, as the original SIASP source; self-employed FRA specialists earn far more (278k, 2021). JPN NA as in original.',''),
 ('F11_09','CLOSE MODERN EQUIVALENT','OECD Regional Statistics DSD_REG_HEALTH@DF_CARE (TL3 active physicians) aggregated by OECD urban-rural typology (PU)',
  'Physicians per 1,000 population in predominantly urban TL3 regions (sum physicians / sum population)','Original was a patchwork of national sources and definitions; now one OECD typology and source for the 6 countries with TL3 physician data. US and CA (in original) now NA because OECD lacks TL3 data. DEU regional data = ambulatory physicians only (flag D).',
  'Per-region typology not published via SDMX; reconstructed (see notes, scripts/country/build_tl3_typology.py, subset_typology.py, fix_eu_typology.py).'),
 ('F11_10','CLOSE MODERN EQUIVALENT','As F11_09 (PR regions)','Physicians per 1,000 population in predominantly rural TL3 regions','As F11_09.','CHE PR class = only 2 cantons (Jura, Graubuenden); small base.'),
]
with open(W+'results/country_audit.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['indicator_id','status','original_source','modern_source','modern_definition','years_used','n_countries_available','change_vs_2018','notes'])
    for i,st,ms,md,ch,nt in A:
        w.writerow([i,st,spec[i]['orig_source'],ms,md,yrs(i),n(i),ch,nt])
print(len(rows))

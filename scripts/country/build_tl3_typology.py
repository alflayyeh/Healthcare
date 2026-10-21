"""Builds raw/country/tl3_typology.csv: OECD urban-rural TL3 class (PU/IN/PR) per region.
- SWE, CHE: Eurostat/GISCO NUTS-2021 URBN_TYPE (reproduces OECD DF_REGION_TYPE_RURB population totals exactly).
- FRA: GISCO NUTS-2024 URBN_TYPE with Corse-du-Sud (FRM01) IN->PR, the unique single change that reproduces
  OECD totals exactly (also reached from NUTS-2021 prior: Mayotte IN->PU, Drome PR->IN).
- JPN, AUS: reconstructed by exact subset search (scripts/country/subset_typology.py) against OECD PU/IN/PR
  population totals 2022+2023, OECD land area by class, and (JPN) PRR/PRC split; unique solutions.
- DEU: OECD per-region class not recoverable; Eurostat NUTS-2024 urban-rural typology used (flag D)."""
import os
import csv,json
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/raw/country/'
M={1:'PU',2:'IN',3:'PR'}
g={}
for v in ('2021','2024'):
    g[v]={f['properties']['NUTS_ID']:f['properties']['URBN_TYPE'] for f in json.load(open(R+f'gisco_nuts3_{v}.geojson'))['features']}
regs={}
for x in csv.DictReader(open(R+'reg_pop_tl3.csv')):
    if x['TIME_PERIOD']=='2022': regs[x['REF_AREA']]=(x['COUNTRY'],x['Reference area'])
JPN_PU='JPB04,JPD11,JPD12,JPD13,JPD14,JPF23,JPG26,JPG27,JPG28,JPG29,JPH34,JPJ40'.split(',')
JPN_PR='JPB02,JPB03,JPB05,JPB06,JPB07,JPC19,JPC20,JPE18,JPH32,JPH35,JPI39,JPJ41,JPJ45'.split(',')
AUS_PU='AU107,AU111,AU1GS,AU2GM,AU309,AU3GB,AU4GA,AU5GP,AU801'.split(',')
AUS_IN='AU112,AU114,AU201,AU203,AU306,AU308,AU316,AU317,AU318,AU601,AU701'.split(',')
rows=[]
for r,(c,n) in sorted(regs.items()):
    if c in('SWE','CHE'): t=M[g['2021'][r]]; src='GISCO NUTS2021 URBN_TYPE (=OECD exact)'
    elif c=='FRA': t='PR' if r=='FRM01' else M[g['2024'][r]]; src='GISCO NUTS2024 URBN_TYPE, FRM01->PR (=OECD exact)'
    elif c=='DEU': t=M[g['2024'][r]]; src='GISCO NUTS2024 URBN_TYPE (EU typology; OECD class not recoverable)'
    elif c=='JPN': t='PU' if r in JPN_PU else ('PR' if r in JPN_PR else 'IN'); src='reconstructed from OECD aggregates (exact)'
    elif c=='AUS': t='PU' if r in AUS_PU else ('IN' if r in AUS_IN else 'PR'); src='reconstructed from OECD aggregates (exact pop)'
    else: continue
    rows.append((c,r,n,t,src))
with open(R+'tl3_typology.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['country','tl3','name','typology','source']); w.writerows(rows)
print(len(rows))

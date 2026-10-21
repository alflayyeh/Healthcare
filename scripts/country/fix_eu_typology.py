"""For DEU/FRA: start from Eurostat/GISCO URBN_TYPE (NUTS 2021 or 2024) and search for the minimal set
(<=3) of region re-classifications that makes PU/IN/PR population (2022 and 2023) match OECD's
published typology totals exactly; area used as tie-breaker."""
import os
import csv,json,collections,itertools,sys
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/raw/country/'
c=sys.argv[1]; ver=sys.argv[2]
pop=collections.defaultdict(dict); names={}; dens={}
for x in csv.DictReader(open(R+'reg_pop_tl3.csv')):
    if x['COUNTRY']==c: pop[x['REF_AREA']][x['TIME_PERIOD']]=float(x['OBS_VALUE']); names[x['REF_AREA']]=x['Reference area']
for x in csv.DictReader(open(R+'reg_density_tl3.csv')):
    if x['COUNTRY']==c and x['TIME_PERIOD']=='2022' and x['UNIT_MEASURE']=='PS_KM2': dens[x['REF_AREA']]=float(x['OBS_VALUE'])
typ=collections.defaultdict(dict)
for x in csv.DictReader(open(R+'reg_type_rurb_pop.csv')):
    if x['COUNTRY']==c and x['UNIT_MEASURE']=='PS': typ[x['TIME_PERIOD']][x['TERRITORIAL_TYPE']]=float(x['OBS_VALUE'])
ta={}
for x in csv.DictReader(open(R+'reg_type_rurb_area.csv')):
    if x['COUNTRY']==c and x['TIME_PERIOD']=='2022': ta[x['TERRITORIAL_TYPE']]=float(x['OBS_VALUE'])
g={}
for f in json.load(open(R+f'gisco_nuts3_{ver}.geojson'))['features']:
    p=f['properties']; g[p['NUTS_ID']]=p['URBN_TYPE']
M={1:'PU',2:'IN',3:'PR'}; K=['PU','IN','PR']; Y=['2022','2023']
regs=[r for r in pop if '2022' in pop[r]]
cur={r:M.get(g.get(r),None) for r in regs}
print('not in GISCO:',[r for r in regs if cur[r] is None])
for r in regs:
    if cur[r] is None: cur[r]='IN'
def diff(a):
    return {(k,y):typ[y][k]-sum(pop[r].get(y,0) for r in regs if a[r]==k) for k in K for y in Y}
d=diff(cur); print('initial diffs',{k:v for k,v in d.items() if v})
# search up to 3 moves
X={r:{y:pop[r].get(y,0) for y in Y} for r in regs}
def ok(moves):
    dd=dict(d)
    for r,k in moves:
        for y in Y: dd[(cur[r],y)]+=X[r][y]; dd[(k,y)]-=X[r][y]
    return all(abs(v)<0.5 for v in dd.values())
found=[]
cand=[(r,k) for r in regs for k in K if k!=cur[r]]
for n in (1,2,3):
    for combo in itertools.combinations(cand,n):
        if len({r for r,_ in combo})<n: continue
        if ok(combo): found.append(combo)
    if found: break
    if n==2 and len(cand)>400: break
for f in found[:10]:
    a=dict(cur); 
    for r,k in f: a[r]=k
    ae={k:round(sum(pop[r]['2022']/dens[r] for r in regs if a[r]==k)-ta[k]) for k in K}
    print([(r,names[r],cur[r],'->',k) for r,k in f],'area diff',ae)
print('n solutions',len(found))

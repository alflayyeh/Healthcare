"""Exact subset search (meet-in-the-middle) to recover which TL3 regions form OECD's PU and PR
classes for countries with no EU typology (JPN, AUS): find the subset of regions whose populations
sum EXACTLY to OECD's published PR (resp. PU) totals in every available year."""
import os
import csv,collections,sys,itertools
import numpy as np
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/raw/country/'
c=sys.argv[1]; cls=sys.argv[2]; ncand=int(sys.argv[3])
pop=collections.defaultdict(dict); dens={}; names={}
for x in csv.DictReader(open(R+'reg_pop_tl3.csv')):
    if x['COUNTRY']==c: pop[x['REF_AREA']][x['TIME_PERIOD']]=float(x['OBS_VALUE']); names[x['REF_AREA']]=x['Reference area']
for x in csv.DictReader(open(R+'reg_density_tl3.csv')):
    if x['COUNTRY']==c and x['TIME_PERIOD']=='2022' and x['UNIT_MEASURE']=='PS_KM2': dens[x['REF_AREA']]=float(x['OBS_VALUE'])
typ=collections.defaultdict(dict)
for x in csv.DictReader(open(R+'reg_type_rurb_pop.csv')):
    if x['COUNTRY']==c and x['UNIT_MEASURE']=='PS': typ[x['TIME_PERIOD']][x['TERRITORIAL_TYPE']]=float(x['OBS_VALUE'])
regs=[r for r in pop if r in dens]
years=[y for y in sorted(typ) if cls in typ[y] and all(y in pop[r] for r in regs) and y in ('2022','2023')]
print('years',years)
excl=set(sys.argv[4].split(',')) if len(sys.argv)>4 else set()
regs=[r for r in regs if r not in excl]
regs=sorted(regs,key=lambda r:dens[r]*(1 if cls=='PR' else -1))[:ncand]
V=np.array([[pop[r][y] for y in years] for r in regs],dtype=np.int64)
T=np.array([typ[y][cls] for y in years],dtype=np.int64)
h=len(regs)//2
def allsums(M):
    n=len(M); out=np.zeros((1<<n,M.shape[1]),dtype=np.int64)
    for i in range(n):
        out[1<<i:1<<(i+1)]=out[:1<<i]+M[i]
    return out
A=allsums(V[:h]); B=allsums(V[h:])
# hash on first two years
key=lambda M:M[:,0]*1000003+M[:,1] if M.shape[1]>1 else M[:,0]
kb=key(B); idx=collections.defaultdict(list)
order=np.argsort(kb); kbs=kb[order]
need=key(T[None,:]-A)
pos=np.searchsorted(kbs,need)
sols=[]
for i in np.nonzero((pos<len(kbs)) & (kbs[np.minimum(pos,len(kbs)-1)]==need))[0]:
    j=pos[i]
    while j<len(kbs) and kbs[j]==need[i]:
        bj=order[j]
        if np.all(A[i]+B[bj]==T): sols.append((i,bj))
        j+=1
print('solutions',len(sols))
for i,bj in sols[:5]:
    mem=[regs[k] for k in range(h) if i>>k&1]+[regs[h+k] for k in range(len(regs)-h) if bj>>k&1]
    print(sorted((names[m]) for m in mem)); print(','.join(sorted(mem)))
# disambiguate with land area by typology (area_i = pop_i / density_i, 2022)
ta={}
for x in csv.DictReader(open(R+'reg_type_rurb_area.csv')):
    if x['COUNTRY']==c and x['TIME_PERIOD']=='2022': ta[x['TERRITORIAL_TYPE']]=float(x['OBS_VALUE'])
res=[]
for i,bj in sols:
    mem=[regs[k] for k in range(h) if i>>k&1]+[regs[h+k] for k in range(len(regs)-h) if bj>>k&1]
    ar=sum(pop[m]['2022']/dens[m] for m in mem)
    res.append((abs(ar-ta[cls])/ta[cls],','.join(sorted(mem))))
res.sort()
print('target area',ta.get(cls))
for e,m in res[:5]: print(round(100*e,3),'%',m)
if cls=='PR' and 'PRR' in typ['2022']:
    good=[]
    for e,m in res:
        mem=m.split(',')
        ok=False
        for k in range(1<<len(mem)):
            sub=[mem[j] for j in range(len(mem)) if k>>j&1]
            if all(sum(pop[s][y] for s in sub)==typ[y]['PRR'] for y in years): ok=True; break
        if ok: good.append((e,m,sorted(sub)))
    print('PR solutions also splitting exactly into PRR/PRC:',len(good))
    for g in good: print(round(100*g[0],3),'%',g[1],'PRR=',','.join(g[2]))

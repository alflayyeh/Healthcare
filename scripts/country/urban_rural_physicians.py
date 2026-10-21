"""F11_09/F11_10: active physicians per 1,000 population in OECD predominantly urban (PU) vs
predominantly rural (PR) TL3 regions = sum(physicians)/sum(population) over regions of each class,
latest year with complete TL3 coverage. Physicians & rates: OECD DSD_REG_HEALTH@DF_CARE (DOC, PS & 10P3HB);
population implied = PS / rate * 1000 (same source), cross-checked with DF_POP_BROAD."""
import os
import csv,collections,json
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/raw/country/'
typ={}
for x in csv.DictReader(open(R+'tl3_typology.csv')): typ[x['tl3']]=(x['country'],x['typology'])
ps=collections.defaultdict(dict); rt=collections.defaultdict(dict); st=collections.defaultdict(dict)
for x in csv.DictReader(open(R+'reg_care_doc_all.csv')):
    if x['TERRITORIAL_LEVEL']!='TL3' or x['MEASURE']!='DOC': continue
    if x['UNIT_MEASURE']=='PS': ps[x['REF_AREA']][x['TIME_PERIOD']]=float(x['OBS_VALUE']); st[x['REF_AREA']][x['TIME_PERIOD']]=x['OBS_STATUS']
    elif x['UNIT_MEASURE']=='10P3HB': rt[x['REF_AREA']][x['TIME_PERIOD']]=float(x['OBS_VALUE'])
pop=collections.defaultdict(dict)
for x in csv.DictReader(open(R+'reg_pop_tl3.csv')): pop[x['REF_AREA']][x['TIME_PERIOD']]=float(x['OBS_VALUE'])
out={}
for c in ['DEU','FRA','SWE','CHE','JPN','AUS']:
    regs=[r for r,(cc,t) in typ.items() if cc==c and not r.endswith('ZZZ')]  # ZZZ = not regionalised (e.g. AU other territories)
    years=sorted({y for r in regs for y in ps[r]},reverse=True)
    for y in years:
        miss=[r for r in regs if y not in ps[r] or (y not in rt[r] and y not in pop[r])]
        if miss: continue
        res={}
        for k in ('PU','IN','PR'):
            rr=[r for r in regs if typ[r][1]==k]
            if not rr: res[k]=None; continue
            P=sum(ps[r][y] for r in rr)
            N=sum((ps[r][y]/rt[r][y]*1000) if rt[r].get(y) else pop[r][y] for r in rr)
            Nchk=sum(pop[r].get(y,float('nan')) for r in rr)
            res[k]=(P/N*1000,P,N,Nchk,len(rr))
        flags=sorted({st[r][y] for r in regs if st[r].get(y) not in ('A','')})
        out[c]=(y,res,flags); break
    print(c,out[c][0],{k:(round(v[0],2),int(v[1]),int(v[2]),v[4]) if v else None for k,v in out[c][1].items()},out[c][2])
json.dump({c:{'year':v[0],'PU':v[1]['PU'][0] if v[1]['PU'] else None,'PR':v[1]['PR'][0] if v[1]['PR'] else None,
              'detail':{k:(x[1],x[2],x[4]) if x else None for k,x in v[1].items()},'flags':v[2]} for c,v in out.items()},
          open(R+'urban_rural_physicians_result.json','w'),indent=1)

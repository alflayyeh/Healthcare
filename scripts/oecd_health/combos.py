import csv,sys,collections
f=sys.argv[1]; rows=list(csv.DictReader(open(f,encoding='utf-8-sig')))
skip={'REF_AREA','Reference area','TIME_PERIOD','Time period','OBS_VALUE','Observation value','STRUCTURE','STRUCTURE_ID','STRUCTURE_NAME','ACTION','OBS_STATUS','Observation status','UNIT_MULT','Unit multiplier','DECIMALS','Decimals','BASE_PER','Base period','UNIT_MEASURE_STATUS' }
cols=[c for c in rows[0] if c not in skip]
filt=dict(a.split('=') for a in sys.argv[2:])
c=collections.Counter()
for r in rows:
  if all(r[k]==v for k,v in filt.items()):
    c[tuple((k,r[k]) for k in cols if r[k] not in ('','_Z','_T','Not applicable','Total') or k in filt)]+=1
for k,v in sorted(c.items()): print(v,'|'.join(x[1] for x in k))

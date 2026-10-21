import csv,sys,collections
f=sys.argv[1]; rows=list(csv.DictReader(open(f,encoding='utf-8-sig')))
filt=dict(a.split('=',1) for a in sys.argv[2:])
dims=[c for c in rows[0] if c.isupper() and c not in ('STRUCTURE','STRUCTURE_ID','STRUCTURE_NAME','ACTION','REF_AREA','TIME_PERIOD','OBS_VALUE','OBS_STATUS','UNIT_MULT','DECIMALS','FREQ')]
s=collections.defaultdict(dict)
for r in rows:
  if all(r[k]==v for k,v in filt.items()):
    key=tuple(r[d] for d in dims if d not in filt)
    s[(key,r['REF_AREA'])][r['TIME_PERIOD']]=(r['OBS_VALUE'],r['OBS_STATUS'])
for (key,c),d in sorted(s.items()):
  ys=sorted(d)[-4:]
  print('.'.join(key),c,' '.join(f"{y}={d[y][0]}{'('+d[y][1]+')' if d[y][1] not in ('A','') else ''}" for y in ys))

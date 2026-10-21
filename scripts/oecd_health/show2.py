import csv,sys,collections
f=sys.argv[1]; rows=list(csv.DictReader(open(f,encoding='utf-8-sig')))
filt=dict(a.split('=',1) for a in sys.argv[2:])
s=collections.defaultdict(dict)
for r in rows:
  if all(r[k]==v for k,v in filt.items()):
    fl='/'.join(x for x in (r.get('OBS_STATUS',''),r.get('OBS_STATUS2',''),r.get('OBS_STATUS3','')) if x and x!='A')
    s[r['REF_AREA']][r['TIME_PERIOD']]=r['OBS_VALUE']+(f'({fl})' if fl else '')
for c in 'USA GBR DEU SWE FRA NLD CHE DNK CAN JPN AUS'.split():
  d=s.get(c,{}); ys=sorted(d)[-5:]
  print(c,' '.join(f'{y}={d[y]}' for y in ys))

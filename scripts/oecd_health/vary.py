import csv,sys,collections
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8-sig')))
cols=list(rows[0])
for i,c in enumerate(cols):
  if c.isupper() and c not in('OBS_VALUE','TIME_PERIOD','REF_AREA'):
    lab=cols[i+1] if i+1<len(cols) and not cols[i+1].isupper() else c
    u=collections.Counter((r[c],r[lab]) for r in rows)
    if len(u)>1 and len(u)<200: print(c, dict(u) if len(u)<40 else str(len(u))+' values')

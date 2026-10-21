import json,sys,itertools
d=json.load(open(sys.argv[1]))
ids=d['id'];size=d['size']
cats={k:list(sorted(d['dimension'][k]['category']['index'].items(),key=lambda x:x[1])) for k in ids}
vals=d['value'];st=d.get('status',{})
out={}
for i,combo in enumerate(itertools.product(*[cats[k] for k in ids])):
    if str(i) in vals:
        out[tuple(c[0] for c in combo)]=(vals[str(i)],st.get(str(i),''))
import collections
keys=[ids.index(k) for k in ids]
for k,v in sorted(out.items()): print(k,v)

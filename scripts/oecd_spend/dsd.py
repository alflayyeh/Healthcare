import re,sys
s=open(sys.argv[1]).read()
dims=re.findall(r'<structure:Dimension id="([^"]+)"[^>]*position="(\d+)"',s)
print('DIMS',[d for d,p in sorted(dims,key=lambda x:int(x[1]))])
cl={}
for m in re.finditer(r'<structure:Codelist[^>]*id="([^"]+)"[^>]*>(.*?)</structure:Codelist>',s,re.S):
    for c in re.finditer(r'<structure:Code id="([^"]+)"[^>]*>.*?<common:Name xml:lang="en">([^<]+)',m.group(2),re.S):
        cl[c.group(1)]=c.group(2)
for m in re.finditer(r'<common:KeyValue id="([^"]+)"[^>]*>(.*?)</common:KeyValue>',s,re.S):
    vals=re.findall(r'<common:Value>([^<]+)</common:Value>',m.group(2))
    if m.group(1)=='REF_AREA': print('REF_AREA',len(vals)); continue
    print(m.group(1),len(vals),[(v,cl.get(v,'')[:50]) for v in vals[:int(sys.argv[2]) if len(sys.argv)>2 else 60]])

# Parse IDF Diabetes Atlas (11th ed., 2024) country pages -> age-standardised diabetes prevalence 20-79, 2024
import re,html,csv,sys,os
d=sys.argv[1]; out=sys.argv[2]
iso={'australia':'AUS','canada':'CAN','denmark':'DNK','france':'FRA','germany':'DEU','japan':'JPN','netherlands':'NLD','sweden':'SWE','switzerland':'CHE','united-kingdom':'GBR','united-states-of-america':'USA'}
w=csv.writer(open(out,'w',newline=''))
w.writerow(['country','slug','prev_2000','prev_2011','prev_2024','prev_2050','url'])
for slug,c in iso.items():
    t=open(os.path.join(d,slug+'.html'),encoding='utf-8').read()
    t=re.sub(r'<script.*?</script>','',t,flags=re.S); t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(re.sub(r'\s+',' ',t))
    m=re.search(r'Age-standardised prevalence of diabetes, % ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)',t)
    w.writerow([c,slug]+list(m.groups())+['https://diabetesatlas.org/data-by-location/country/%s/'%slug])
    print(c,m.groups())

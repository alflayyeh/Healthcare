"""Decompress the gzipped raw snapshots (raw/**/*.gz) next to themselves so the build scripts can read them."""
import glob, gzip, os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
n = 0
for gz in glob.glob(os.path.join(ROOT, 'raw', '**', '*.gz'), recursive=True):
    out = gz[:-3]
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(gz):
        with gzip.open(gz, 'rb') as a, open(out, 'wb') as b: shutil.copyfileobj(a, b)
        n += 1
print(f'decompressed {n} raw files')

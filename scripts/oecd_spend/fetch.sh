#!/bin/bash
# usage: fetch.sh URL OUTFILE ; retries on 429
url="$1"; out="$2"
for i in 1 2 3 4 5 6; do
  code=$(curl -sS -m 300 -o "$out" -w "%{http_code}" -H "Accept-Encoding: identity" "$url")
  if [ "$code" = "200" ]; then echo "OK $code $(wc -c <"$out") $out"; sleep 2; exit 0; fi
  echo "HTTP $code, retry $i" >&2; head -c 300 "$out" >&2; case $code in 404|400|403) exit 1;; esac; sleep $((i*10))
done
echo "FAILED $url" >&2; exit 1

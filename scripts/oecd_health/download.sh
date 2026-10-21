#!/bin/bash
# Download OECD SDMX data for the 11 countries, 2010+, csvfilewithlabels
cd "$(dirname "$0")/../../raw/oecd_health"
C="USA+GBR+DEU+SWE+FRA+NLD+CHE+DNK+CAN+JPN+AUS"
get() { # dsd df ver ndots
  dots=$(printf '.%.0s' $(seq 1 $4))
  url="https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,$1@$2,$3/${C}${dots}?startPeriod=2008&format=csvfilewithlabels"
  echo "$url" > $2.url
  for i in 1 2 3 4 5; do
    code=$(curl -sS -w '%{http_code}' -o $2.csv "$url")
    [ "$code" = "200" ] && break; echo "$2 $code retry"; sleep 10
  done
  echo "$2 $(wc -l < $2.csv)"; sleep 3
}
get DSD_HEALTH_LVNG DF_HEALTH_LVNG_TC 1.0 6
get DSD_HEALTH_LVNG DF_HEALTH_LVNG_AC 1.0 6
get DSD_HEALTH_LVNG DF_HEALTH_LVNG_BW 1.0 6
get DSD_HEALTH_STAT DF_LE 1.1 12
get DSD_HEALTH_STAT DF_MIM 1.1 12
get DSD_HEALTH_STAT DF_IH_LB 1.1 12
get DSD_HEALTH_PROC DF_HOSP_DISCHARGE 1.2 17
get DSD_HEALTH_PROC DF_DIAG_EXAM 1.2 17
get DSD_HEALTH_PROC DF_SURG_PROC 1.2 17
get DSD_HEALTH_PROC DF_KEY_INDIC 1.2 17
get DSD_HEALTH_PROC DF_HOSP_AV_LENGTH 1.2 17

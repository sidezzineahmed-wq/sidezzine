#!/bin/bash
export REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt
exec python3 /home/user/sidezzine/veille_enrichissement/complement_fiches.py --kit /tmp/claude-0/-home-user-sidezzine/3e421be1-fcd4-5f44-b7d1-e5316c0ec263/scratchpad/kit_m5 --cibles /tmp/claude-0/-home-user-sidezzine/3e421be1-fcd4-5f44-b7d1-e5316c0ec263/scratchpad/v3b/cibles_docs_tout.json --dossier /tmp/claude-0/-home-user-sidezzine/3e421be1-fcd4-5f44-b7d1-e5316c0ec263/scratchpad/compl_docs --paralleles 2 --delai 4 --sans-popup

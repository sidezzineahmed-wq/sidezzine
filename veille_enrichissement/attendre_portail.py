"""Pause pendant une panne du portail : sonde légère (1 GET de la page d'accueil) toutes les 10 min hors minutes 8-24 ;
dès qu'elle répond 200, relance le collecteur (reprise atomique, 2 connexions, >= 4 s). Arrêt de la sonde sur 401/403."""
import json, os, subprocess, sys, time, datetime
SP = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(SP, "compl_vis")
sys.path.insert(0, os.path.join(SP, "kit_m5"))
from veille.client import ClientPMMP, ArretCollecte
CMD = (f"cd {D} && REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt setsid nohup python3 /home/user/sidezzine/veille_enrichissement/complement_fiches.py "
       f"--kit {SP}/kit_m5 --cibles cibles.json --dossier . --delai 4 --paralleles 2 --essais 3 >> run.log 2>&1 < /dev/null &")
T = time.time(); duree = float(sys.argv[1]) if len(sys.argv) > 1 else 560
journal = os.path.join(D, "sondes.jsonl")
while time.time() - T < duree:
    if subprocess.run("pgrep -f '[c]omplement_fiches.py --kit'", shell=True, capture_output=True).returncode == 0:
        print("collecteur actif"); break
    m = datetime.datetime.now(datetime.timezone.utc).minute
    der = [json.loads(l) for l in open(journal)] if os.path.exists(journal) else []
    if not (8 <= m < 24) and (not der or time.time() - der[-1]["t"] >= 600):
        os.environ["REQUESTS_CA_BUNDLE"] = "/root/.ccr/ca-bundle.crt"
        try:
            r = ClientPMMP(delai_min=4.0, reprises=0).get({"page": "entreprise.EntrepriseHome"}); ok, msg = r.status_code == 200, r.status_code
        except ArretCollecte as e:
            ok, msg = False, str(e)[:120]
        open(journal, "a").write(json.dumps({"t": time.time(), "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()[:19], "ok": ok, "msg": str(msg)}) + "\n")
        print(datetime.datetime.now(datetime.timezone.utc).isoformat()[:19], "sonde", ok, msg)
        if "401" in str(msg) or "403" in str(msg):
            print("ARRET 401/403 : aucune relance"); break
        if ok:
            subprocess.run(CMD, shell=True); print("collecteur relancé"); break
    time.sleep(20)

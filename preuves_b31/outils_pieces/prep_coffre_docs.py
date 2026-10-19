"""Publication du coffre (phase pièces) : fiches.json du coffre LIVE relu + relectures v3 (résiduel, résiduel 2, pièces),
ré-analysées par le kit courant ; la lecture la plus récente gagne, lots et inventaire validé gardés ; manifeste live mis à
jour pour les seuls fichiers changés."""
import hashlib, json, os, shutil, subprocess, sys
SP, LIVE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
KIT = f"{SP}/kit_m5"
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
man = json.load(open(f"{LIVE}/manifest.json"))
assert man["fichiers"]["stock/etat/fiches.json"]["sha256"] == hashlib.sha256(open(f"{LIVE}/stock/etat/fiches.json", "rb").read()).hexdigest(), "fiches.json relu ≠ manifeste live"
src = f"{LIVE}/stock/etat/fiches.json"
rap = {}
for n, d in enumerate(("compl_v3res", "compl_v3r2", "compl_docs")):
    dst = f"{OUT}/f_{n}.json"
    r = subprocess.run([sys.executable, "/home/user/sidezzine/veille_enrichissement/integrer_fiches.py", "--fiches", src, "--dossier", f"{SP}/{d}",
                        "--kit", KIT, "--sortie", dst, "--complement", f"{OUT}/complement_{n}.json"], check=True, capture_output=True, text=True)
    rap[d] = json.loads(r.stdout.strip().splitlines()[-1]); src = dst
subprocess.run([sys.executable, f"{SP}/v3/injecter_audit.py", KIT, src, f"{OUT}/f_fin.json", f"{SP}/audit_fiche"], check=True)
F = json.load(open(f"{OUT}/f_fin.json"))
os.makedirs(f"{OUT}/stock/etat")
with open(f"{OUT}/stock/etat/fiches.json", "w", encoding="utf-8") as f:
    json.dump({k: F[k] for k in sorted(F)}, f, ensure_ascii=False, indent=1)
kit = ["LISEZ-MOI.md", "maj_quotidienne.py", "veille/pmmp_fiche.py", "veille/etat.py", "ingestion/enrichi_pmmp.py", "ingestion/test_enrichi_pmmp.py", "tests/test_kit.py", "integrer_releve_pieces.py", "tests/test_releve_pieces.py"]
chg = ["stock/etat/fiches.json"]
for k in kit:
    os.makedirs(os.path.dirname(f"{OUT}/stock/kit/{k}"), exist_ok=True); shutil.copy(f"{KIT}/{k}", f"{OUT}/stock/kit/{k}"); chg.append("stock/kit/" + k)
for p in chg:
    b = open(f"{OUT}/{p}", "rb").read()
    man["fichiers"][p] = {"octets": len(b), "sha256": hashlib.sha256(b).hexdigest()}
man["fichiers"] = dict(sorted(man["fichiers"].items()))
json.dump(man, open(f"{OUT}/manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(rap, open(f"{OUT}/rapport_integration.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({"changes": chg, "fiches": len(F), "integration": {d: {k: v for k, v in r.items() if isinstance(v, int)} for d, r in rap.items()}}, ensure_ascii=False))

"""Ajoute à fiches.json les lectures complètes réelles (pages officielles lues le 19/10 pour l'audit), datées à leur lecture."""
import gzip, hashlib, json, sys
sys.path.insert(0, sys.argv[1])
from veille.pmmp_fiche import lire_fiche, tronquer_contact, fiche_valide
F = json.load(open(sys.argv[2]))
for k, p, lu in (("pmmp:e5w:1041719", "e5w_1041719", "2026-10-19T18:53:31+00:00"), ("pmmp:g3h:1044229", "g3h_1044229", "2026-10-19T18:56:39+00:00")):
    h, coupe = tronquer_contact(gzip.open(f"{sys.argv[4]}/{p}_complet.html.gz", "rt", encoding="utf-8").read())
    f = lire_fiche(h, masquer=True); assert coupe and fiche_valide(f)
    d = {"id": k, "lu_le": lu, "run": "lecture_audit_v3_2026-10-19", "sha256_html_tronque": hashlib.sha256(h.encode()).hexdigest(), "champs": f}
    if F.get(k, {}).get("lots"): d["lots"] = F[k]["lots"]
    if lu > F[k]["lu_le"]:
        F[k] = d
    else:
        print("lecture plus récente déjà présente, gardée :", k)
json.dump(F, open(sys.argv[3], "w"), ensure_ascii=False, indent=1, sort_keys=True)

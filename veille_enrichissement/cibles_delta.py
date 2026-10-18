#!/usr/bin/env python3
"""Cibles résiduelles du complément des fiches, recalculées sur le DERNIER catalogue live (nouvelles arrivées incluses).

  python3 cibles_delta.py --catalogue <catalogue.json live> --fiches <fiches.json du coffre relu> --dossier <complément> --sortie <cibles.json>

Une annonce ouverte est ciblée si, ni le coffre ni le cache du complément n'ont :
  - « fiche »  : une fiche lue (det=false, ou détail seulement hérité d'un ancien catalogue) ;
  - « lots »   : le popup des lots d'une annonce allotie dont la fiche est lue ;
  - « fiche » (qualification) : une fiche du coffre lue par l'ancien parser (sans q_txt) dont une ligne de qualification
    est incomplète (secteur ou qualification manquant) : relue pour ne rien perdre.
Les cibles existantes du dossier sont conservées (reprise : rien de déjà lu n'est relu)."""
import argparse
import glob
import json
import os


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalogue", required=True)
    ap.add_argument("--fiches", required=True)
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--aujourdhui", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args(argv)
    cat = json.load(open(a.catalogue, encoding="utf-8"))
    F = json.load(open(a.fiches, encoding="utf-8"))
    C = {}
    for p in glob.glob(os.path.join(a.dossier, "cache", "*.json")):
        r = json.load(open(p, encoding="utf-8"))
        C[r["id"]] = r
    out, n = {}, {"fiche_non_lue": 0, "detail_herite": 0, "lots": 0, "qualification": 0}
    for x in cat["items"]:
        if x.get("lim") and x["lim"] < a.aujourdhui:
            continue
        k = f"pmmp:{x['o']}:{x['r']}"
        f, c = F.get(k), C.get(k) or {}
        base = {"ref": x["ref"], "lim": x["lim"], "h": x["h"], "prio": 1}
        lue = bool(f) or bool(c.get("fiche"))
        if not lue:
            out[k] = {**base, "besoin": "fiche"}
            n["detail_herite" if x["det"] else "fiche_non_lue"] += 1
            continue
        champs = (c.get("fiche") or {}).get("champs") or (f or {}).get("champs") or {}
        allot = champs.get("allot")
        if (allot or x.get("lots")) and not (c.get("lots") or (f or {}).get("lots")):
            out[k] = {**base, "besoin": "lots", "allot": allot}
            n["lots"] += 1
            continue
        if not c.get("fiche") and f and "q_txt" not in (f.get("champs") or {}) and any(
                not (r.get("s") and r.get("q")) for r in (f.get("champs") or {}).get("q") or []):
            out[k] = {**base, "besoin": "fiche", "prio": 0, "motif": "qualification potentiellement tronquée (ancien parser)"}
            n["qualification"] += 1
    json.dump(out, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps({"cibles": len(out), **n, "annonces_ouvertes": sum(1 for x in cat["items"] if not x.get("lim") or x["lim"] >= a.aujourdhui)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

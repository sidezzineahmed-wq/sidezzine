#!/usr/bin/env python3
"""Fusionne deux états dépliés du collecteur (coffre.py unpack) issus du même coffre de départ, quand un passage horaire a
publié pendant un passage manuel : AUCUNE donnée plus récente n'est perdue. HORS LIGNE.

  python3 fusionner_etats.py --a <état du passage manuel> --b <état déplié du coffre live relu> --sortie <état fusionné>

Règles (par identifiant) :
  - listing : l'observation la plus récente (dernier_vu_listing) fait foi ; premier_vu = le plus ancien ; changements
    réunis (10 derniers) ; un indicateur d'absence posé par un listing COMPLET postérieur à l'autre observation est gardé ;
  - fiches : la lecture la plus récente (lu_le) gagne ; le popup des lots le plus récent (lots.lu_le) est gardé ;
  - couvertures : réunion (un fichier par passage) ;
  - selection.json : par identifiant, le dernier choix le plus récent ;
  - organismes.json : la liste vue le plus récemment.
Rien n'est supprimé, rien n'est inventé."""
import argparse
import glob
import json
import os
import shutil
import sys


def lire(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return d


def ecrire(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def fusion_ligne(x, y):
    """x, y : entrées listing du même identifiant. Renvoie l'entrée fusionnée."""
    if x is None or y is None:
        return dict(x or y)
    rec, anc = (x, y) if (x.get("dernier_vu_listing") or "") >= (y.get("dernier_vu_listing") or "") else (y, x)
    out = dict(rec)
    out["premier_vu"] = min(v for v in (x.get("premier_vu"), y.get("premier_vu")) if v) if (x.get("premier_vu") or y.get("premier_vu")) else None
    ch = {json.dumps(c, sort_keys=True, ensure_ascii=False): c for c in (x.get("changements") or []) + (y.get("changements") or [])}
    if ch:
        out["changements"] = sorted(ch.values(), key=lambda c: c.get("vu_le") or "")[-10:]
    # absence constatée par un listing complet APRÈS la dernière observation de l'autre état : gardée
    if ((anc.get("absences_listing_complet") or 0) and (anc.get("dernier_run_absent") or "") > (rec.get("dernier_run") or "")
            and (anc.get("dernier_run_absent") or "") > (rec.get("dernier_run_absent") or "")):
        out["absences_listing_complet"] = anc["absences_listing_complet"]
        out["dernier_run_absent"] = anc["dernier_run_absent"]
    return out


def fusion_fiche(x, y):
    if x is None or y is None:
        return dict(x or y)
    rec = dict(x if x["lu_le"] >= y["lu_le"] else y)
    lots = [d.get("lots") for d in (x, y) if d.get("lots")]
    if lots:
        rec["lots"] = max(lots, key=lambda l: l.get("lu_le") or "")
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args(argv)
    A, B, S = a.a, a.b, a.sortie
    if os.path.exists(S):
        shutil.rmtree(S)
    os.makedirs(os.path.join(S, "fiches"))
    os.makedirs(os.path.join(S, "couverture"))
    r = {}
    la, lb = lire(os.path.join(A, "listing.json"), {"items": {}}), lire(os.path.join(B, "listing.json"), {"items": {}})
    items = {i: fusion_ligne(la["items"].get(i), lb["items"].get(i)) for i in sorted(set(la["items"]) | set(lb["items"]))}
    r["listing"] = {"a": len(la["items"]), "b": len(lb["items"]), "fusion": len(items),
                    "b_plus_recent": sum(1 for i in items if i in lb["items"] and i in la["items"] and
                                         (lb["items"][i].get("dernier_vu_listing") or "") > (la["items"][i].get("dernier_vu_listing") or ""))}
    ecrire(os.path.join(S, "listing.json"), {**la, "items": items})
    fa = {os.path.basename(p): p for p in glob.glob(os.path.join(A, "fiches", "*.json"))}
    fb = {os.path.basename(p): p for p in glob.glob(os.path.join(B, "fiches", "*.json"))}
    nb_b = 0
    for n in sorted(set(fa) | set(fb)):
        x, y = lire(fa.get(n)) if n in fa else None, lire(fb.get(n)) if n in fb else None
        f = fusion_fiche(x, y)
        nb_b += bool(y and (x is None or y["lu_le"] > x["lu_le"]))
        ecrire(os.path.join(S, "fiches", n), f)
    r["fiches"] = {"a": len(fa), "b": len(fb), "fusion": len(set(fa) | set(fb)), "b_plus_recentes": nb_b}
    for d in (A, B):
        for p in glob.glob(os.path.join(d, "couverture", "*.json")):
            shutil.copy(p, os.path.join(S, "couverture", os.path.basename(p)))
    r["couvertures"] = len(os.listdir(os.path.join(S, "couverture")))
    sa, sb = lire(os.path.join(A, "selection.json"), {"items": {}}), lire(os.path.join(B, "selection.json"), {"items": {}})
    sel = {}
    for i in set(sa["items"]) | set(sb["items"]):
        cand = [s for s in (sa["items"].get(i), sb["items"].get(i)) if s]
        sel[i] = max(cand, key=lambda s: s.get("dernier_choix") or "")
    ecrire(os.path.join(S, "selection.json"), {**sa, "items": dict(sorted(sel.items()))})
    oa, ob = lire(os.path.join(A, "organismes.json")), lire(os.path.join(B, "organismes.json"))
    org = max([o for o in (oa, ob) if o], key=lambda o: o.get("vu_le") or "", default=None)
    if org:
        ecrire(os.path.join(S, "organismes.json"), org)
    print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

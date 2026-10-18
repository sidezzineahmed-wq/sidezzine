#!/usr/bin/env python3
"""Intègre le complément des fiches (cache/ de complement_fiches.py) dans l'état du collecteur du coffre.

Entrées : --fiches  stock/etat/fiches.json RELU du coffre live (jamais une ancienne copie) ;
          --dossier dossier du complément (cache/, echecs/).
Sorties : --sortie  fiches.json fusionné (même format : {id: {id, lu_le, run, sha256_html_tronque, champs[, lots]}}) ;
          --complement referentiel/fiches_complement.json du kit (fiches et popups de lots inaccessibles après --essais).
Règles :
  - fiche : la lecture la plus récente gagne (lu_le) ; une lecture du coffre plus récente n'est jamais remplacée ;
  - lots : datés séparément ; la lecture de popup la plus récente gagne ; rattachés à la fiche du même id ;
  - un popup seul (besoin « lots ») n'est rattaché que si la fiche du coffre existe ;
  - rien n'est supprimé ; aucun champ n'est rempli sans lecture.
Sortie déterministe (tri des clés)."""
import argparse
import glob
import json
import os


def lire(p, d=None):
    if not p:
        return d
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fiches", required=True)
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--essais", type=int, default=3)
    ap.add_argument("--precedent-complement", help="fiches_complement.json actuel du kit (s'il existe)")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--complement", required=True)
    a = ap.parse_args(argv)
    F = lire(a.fiches, {}) or {}
    n = {"fiches_coffre": len(F), "fiche_ajoutee": 0, "fiche_remplacee_plus_recente": 0, "fiche_coffre_plus_recente_gardee": 0,
         "lots_rattaches": 0, "lots_sans_fiche_coffre": 0, "ref_differente_du_catalogue": 0}
    for p in sorted(glob.glob(os.path.join(a.dossier, "cache", "*.json"))):
        r = lire(p)
        k, fi, lo = r["id"], r.get("fiche"), r.get("lots")
        doc = F.get(k)
        if fi:
            nouveau = {"id": k, "lu_le": fi["lu_le"], "run": "complement_eaios_" + fi["lu_le"][:10], "sha256_html_tronque": fi["sha256_html_tronque"],
                       "champs": fi["champs"]}
            if (fi["champs"].get("ref") or "").strip() != (r.get("ref_catalogue") or "").strip():
                n["ref_differente_du_catalogue"] += 1
            if doc is None:
                F[k] = doc = nouveau
                n["fiche_ajoutee"] += 1
            elif fi["lu_le"] > (doc.get("lu_le") or ""):
                if doc.get("lots"):
                    nouveau["lots"] = doc["lots"]
                F[k] = doc = nouveau
                n["fiche_remplacee_plus_recente"] += 1
            else:
                n["fiche_coffre_plus_recente_gardee"] += 1
        if lo and lo.get("statut") in ("lu", "partiel"):
            if doc is None:
                n["lots_sans_fiche_coffre"] += 1
            elif lo["lu_le"] > ((doc.get("lots") or {}).get("lu_le") or ""):
                doc["lots"] = {c: lo[c] for c in ("lu_le", "url", "sha256_html_tronque", "statut", "n", "n_annonce", "lots", "raison") if c in lo}
                n["lots_rattaches"] += 1
    prec = lire(a.precedent_complement, {}) or {}
    fi_inacc, lo_inacc = dict(prec.get("fiches_inaccessibles") or {}), dict(prec.get("lots_inaccessibles") or {})
    for p in sorted(glob.glob(os.path.join(a.dossier, "echecs", "*.json"))):
        e = lire(p)
        if e.get("tentatives", 0) < a.essais:
            continue
        k = e["id"]
        o, r_ = k.split(":")[1:]
        rec = lire(os.path.join(a.dossier, "cache", f"{o}_{r_}.json"))
        info = {c: e.get(c) for c in ("tentatives", "dernier_echec", "raison", "inaccessible")}
        if rec and (rec.get("fiche") or k in F):
            lo_inacc[k] = info
        elif k not in F:
            fi_inacc[k] = info
    for k in list(fi_inacc):
        if k in F:
            fi_inacc.pop(k)
    for k in list(lo_inacc):
        if (F.get(k) or {}).get("lots"):
            lo_inacc.pop(k)
    with open(a.sortie, "w", encoding="utf-8") as f:
        json.dump({k: F[k] for k in sorted(F)}, f, ensure_ascii=False, indent=1)
    comp = {"version": 1, "source": "complément EAIOS des fiches PMMP (fiche + popup « Détail des lots »), essais bornés",
            "regle": "liste des lectures impossibles après essais bornés : valeurs inconnues, jamais remplies",
            "fiches_inaccessibles": {k: fi_inacc[k] for k in sorted(fi_inacc)}, "lots_inaccessibles": {k: lo_inacc[k] for k in sorted(lo_inacc)}}
    with open(a.complement, "w", encoding="utf-8") as f:
        json.dump(comp, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    n.update({"fiches_sortie": len(F), "fiches_inaccessibles": len(fi_inacc), "lots_inaccessibles": len(lo_inacc),
              "fiches_avec_lots": sum(1 for d in F.values() if d.get("lots"))})
    print(json.dumps(n, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

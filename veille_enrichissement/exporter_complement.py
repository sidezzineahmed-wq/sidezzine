#!/usr/bin/env python3
"""Exporte le dossier du complément (cache/ + echecs/) vers referentiel/mode_passation_complement.json du kit collecteur.

statut : « lu » (mode présent), « champ_absent » (fiche lue, élément modePassation vide), « inaccessible » (au moins --essais
échecs, aucune lecture). Les échecs encore réessayables ne sont pas exportés (ni valeur, ni statut). Fusion avec --precedent :
une lecture plus récente gagne ; rien n'est supprimé. Sortie triée, déterministe."""
import argparse
import glob
import json
import os


def charger(dossier, essais):
    out = {}
    for p in sorted(glob.glob(os.path.join(dossier, "cache", "*.json"))):
        r = json.load(open(p, encoding="utf-8"))
        st = r.get("statut") or ("lu" if r.get("mode_passation") else "champ_absent")
        out[r["id"]] = {"statut": st, "v": r.get("mode_passation") if st == "lu" else None, "ref": r.get("ref"),
                        "ref_catalogue": r.get("ref_catalogue"), "lu_le": r["lu_le"], "url": r.get("url"),
                        "sha256_html_tronque": r.get("sha256_html_tronque")}
    for p in sorted(glob.glob(os.path.join(dossier, "echecs", "*.json"))):
        e = json.load(open(p, encoding="utf-8"))
        if e["id"] in out or e.get("tentatives", 0) < essais:
            continue
        out[e["id"]] = {"statut": "inaccessible", "v": None, "tentatives": e["tentatives"], "dernier_echec": e.get("dernier_echec"),
                        "raison": e.get("raison")}
    return out


def fusionner(prec, neuf):
    res = dict(prec)
    for k, v in neuf.items():
        a = res.get(k)
        if a is None or a.get("statut") == "inaccessible" or (v.get("lu_le") or "") > (a.get("lu_le") or ""):
            if not (v["statut"] == "inaccessible" and a and a.get("statut") in ("lu", "champ_absent")):
                res[k] = v
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--essais", type=int, default=3)
    ap.add_argument("--precedent")
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args(argv)
    prec = (json.load(open(a.precedent, encoding="utf-8")).get("par_id") or {}) if a.precedent and os.path.exists(a.precedent) else {}
    par = fusionner(prec, charger(a.dossier, a.essais))
    n = {}
    for v in par.values():
        n[v["statut"]] = n.get(v["statut"], 0) + 1
    doc = {"version": 1, "source": "fiche publique PMMP (EntrepriseDetailConsultation), élément modePassation ; complément EAIOS borné et repris",
           "maj": max([v.get("lu_le") or v.get("dernier_echec") or "" for v in par.values()] or [""]) or None,
           "comptes": dict(sorted(n.items())), "par_id": {k: par[k] for k in sorted(par)}}
    with open(a.sortie, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    print(json.dumps({"sortie": a.sortie, "n": len(par), "comptes": doc["comptes"], "maj": doc["maj"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

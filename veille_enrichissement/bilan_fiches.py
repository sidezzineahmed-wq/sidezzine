#!/usr/bin/env python3
"""Bilan PAR CHAMP des informations de fiche PMMP du catalogue publié (catalogue.json + catalogue_details.json).
Usage : python3 bilan_fiches.py <dossier contenant catalogue.json et catalogue_details.json> [--aujourdhui AAAA-MM-JJ]

Par annonce et par champ, un seul statut :
  connue           valeur publiée sur la fiche lue (annonce non allotie, ou champ de niveau annonce) ;
  zero             estimation/caution publiée à 0 (non exploitable pour l'estimation, à vérifier pour la caution) ;
  non_indiquee     fiche lue, champ vide ou « - » (rien n'est publié : ce n'est ni « non exigé » ni « inconnu ») ;
  par_lot          annonce allotie : valeur portée par les lots ; détaillée en lots_valeur / lots_non_indique / lots_non_affiche ;
  par_lot_partiel  popup lu mais incomplet (moins de lots que « N Lots ») ;
  par_lot_non_lu   annonce allotie dont le popup des lots n'est pas (encore) lu ;
  inaccessible     fiche (ou popup) illisible après essais bornés ;
  non_lue          fiche pas encore lue ;
  non_lue_ancien_collecteur  (visite) fiche lue par une version antérieure du collecteur qui ne lisait pas ce bloc.
Aucun statut n'est déduit d'un autre ; aucun montant n'est sommé."""
import json
import os
import re
import sys

LOT = {"est": "est", "cau": "cau", "tp": "tp", "q": "q", "ag": "ag", "vis": "vis", "reu": "reu", "proto": "proto", "var": "var"}
ANNONCE = ["dom", "ouv", "dep"]
nref = lambda s: re.sub(r"\s+", " ", s or "").strip().upper()
vide = lambda v: v is None or v == [] or v == ""


def bilan(cat, det, auj=None):
    E = (det or {}).get("pmmp_enrichi") or {}
    L = (E.get("lots") or {}).get("par_id") or {}
    LI = (E.get("lots") or {}).get("inaccessibles") or {}
    FI = (E.get("fiches") or {}).get("inaccessibles") or {}
    VNL = set((E.get("fiches") or {}).get("visite_non_lue") or [])
    M = E.get("mode_passation") or {}
    items = [x for x in cat["items"] if not auj or not x.get("lim") or x["lim"] >= auj]
    out = {"annonces": len(items), "det": sum(1 for x in items if x["det"]), "alloties": sum(1 for x in items if x["lots"] or x["allot"]), "champs": {}}

    def add(ch, st, n=1):
        out["champs"].setdefault(ch, {})
        out["champs"][ch][st] = out["champs"][ch].get(st, 0) + n

    for x in items:
        k = f"pmmp:{x['o']}:{x['r']}"
        al = bool(x["lots"] or x["allot"])
        r = L.get(k) if k in L and nref(L[k].get("ref")) == nref(x["ref"]) else None
        for ch in list(LOT) + ANNONCE:
            if not x["det"]:
                add(ch, "inaccessible" if k in FI else "non_lue")
                continue
            if al and ch in LOT:
                if not r:
                    add(ch, "inaccessible" if k in LI else "par_lot_non_lu")
                    continue
                add(ch, "par_lot" if r.get("statut") == "lu" else "par_lot_partiel")
                for l in r.get("lots") or []:
                    v = l.get(LOT[ch])
                    add(ch, "lots_valeur" if not vide(v) else "lots_non_indique" if ch in (l.get("ni") or []) else
                        "lots_non_affiche" if ch in (l.get("na") or []) else "lots_non_indique")
                continue
            v = x.get(ch)
            if ch == "vis" and k in VNL:
                add(ch, "non_lue_ancien_collecteur")  # bloc visite non lu par l'ancienne version : inconnu, pas « non indiquée »
                continue
            add(ch, "zero" if v == 0 and ch in ("est", "cau") else "connue" if not vide(v) else "non_indiquee")
        mp = (M.get("par_id") or {}).get(k)
        add("mode_passation", "connue" if mp and mp.get("v") and nref(mp.get("ref")) == nref(x["ref"]) else
            "non_indiquee" if k in (M.get("absents") or {}) else "inaccessible" if k in (M.get("inaccessibles") or {}) else "non_lue")
        c = ((E.get("classification") or {}).get("par_entite") or {}).get(x["o"])
        add("classification_entite", "connue" if c and c.get("code") else "inconnue")
    for ch, d in out["champs"].items():
        out["champs"][ch] = dict(sorted(d.items()))
    return out


def main():
    dos = sys.argv[1]
    auj = sys.argv[sys.argv.index("--aujourdhui") + 1] if "--aujourdhui" in sys.argv else None
    cat = json.load(open(os.path.join(dos, "catalogue.json"), encoding="utf-8"))
    det = json.load(open(os.path.join(dos, "catalogue_details.json"), encoding="utf-8"))
    print(json.dumps({"maj": cat.get("maj"), **bilan(cat, det, auj)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Construit catalogue.json (format EAIOS, 31 champs) à partir de l'état du kit. Hors ligne : aucune requête.

N'écrit QUE dans le fichier de sortie demandé (par défaut ./sortie/catalogue.json) — jamais dans EAIOS.

Règles :
  - en cours = date limite connue >= aujourd'hui (heure du Maroc) ; une date limite inconnue n'exclut pas ;
  - aucune suppression sur absence : une consultation non revue reste tant que sa date limite n'est pas passée
    (option --exclure-absents-complets N pour écarter celles absentes de N listings COMPLETS consécutifs) ;
  - champs présents à la fois au listing et à la fiche : on prend l'observation la plus récente ;
    si le listing plus récent contredit la fiche, la fiche est signalée « à relire » (jamais re-datée) ;
  - det = true seulement si une fiche a réellement été lue ; sinon tous les champs de fiche sont null / [] ;
  - cls non collectable (filtre « classification » ignoré par le portail) : ancienne valeur conservée pour les IDs
    connus du catalogue EAIOS du 2026-09-26, null explicite pour les nouveaux (comptés dans le rapport) ;
    ent = libellé PMMP de l'organisme.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from veille.etat import Etat, aujourd_hui_maroc, maintenant, _ecrire_json  # noqa: E402
from veille.pmmp_fiche import libelle_seul  # noqa: E402
from veille.schema import CHAMPS, valider_catalogue  # noqa: E402

ICI = os.path.dirname(os.path.abspath(__file__))
SOURCE = "marchespublics.gov.ma, consultations en cours"
COMMUNS = ["ref", "obj", "mo", "cat", "proc", "lim", "h"]
FICHE_SEULE = ["est", "tp", "cau", "q", "ag", "vis", "reu", "var", "allot", "dom", "ouv", "dep", "proto"]


def _espace(s):
    return re.sub(r"\s+", " ", s).strip() if isinstance(s, str) else s


def construire(etat, regions, aujourd_hui=None, exclure_absents=None, cls_heritee=None):
    aujourd_hui = aujourd_hui or aujourd_hui_maroc()
    orgs = etat.organismes().get("organismes", {})
    items, rapport = [], {"a_relire": [], "exclus_date_passee": 0, "exclus_absents": 0,
                          "absents_listing_complet_conserves": [], "sans_fiche": 0, "sans_cls": 0, "lim_inconnue": 0}
    for i, e in sorted(etat.listing["items"].items(), key=lambda kv: (kv[1].get("listing", {}).get("lim") or "9", kv[0])):
        L = e.get("listing") or {}
        fdoc = etat.fiche(i)
        F = (fdoc or {}).get("champs") or {}
        det = bool(fdoc)
        commun = {}
        fiche_plus_recente = det and fdoc["lu_le"] >= (e.get("dernier_vu_listing") or "")
        for k in COMMUNS:
            lv, fv = L.get(k), F.get(k)
            commun[k] = (fv if fv is not None else lv) if fiche_plus_recente else (lv if lv is not None else fv)
            if det and not fiche_plus_recente and lv is not None and fv is not None and _espace(lv) != _espace(fv):
                rapport["a_relire"].append({"id": i, "champ": k, "fiche": fv, "listing": lv, "fiche_lu_le": fdoc["lu_le"],
                                            "listing_vu_le": e.get("dernier_vu_listing")})
        lim = commun["lim"]
        if lim is None:
            rapport["lim_inconnue"] += 1
        elif lim < aujourd_hui:
            rapport["exclus_date_passee"] += 1
            continue
        absn = e.get("absences_listing_complet", 0)
        if absn:
            if exclure_absents and absn >= exclure_absents:
                rapport["exclus_absents"] += 1
                continue
            rapport["absents_listing_complet_conserves"].append({"id": i, "absences": absn})
        ent = orgs.get(e["o"])
        x = {
            "r": e["r"], "o": e["o"], "ref": commun["ref"], "obj": commun["obj"], "mo": commun["mo"],
            "cat": commun["cat"], "proc": commun["proc"], "pub": L.get("pub"), "lim": lim, "h": commun["h"],
            "lx": list(L.get("lx") or []), "nat": bool(L.get("nat")), "etr": list(L.get("etr") or []),
            "lots": bool(L.get("lots")), "det": det, "cls": e.get("cls") or (cls_heritee or {}).get(i), "ent": _espace(ent) if ent else None,
            "env": bool(L.get("env")),
        }
        for k in FICHE_SEULE:
            x[k] = F.get(k) if det else ([] if k in ("q", "dom") else None)
            if libelle_seul(x[k]):  # « Date et heure : » sans date ni lieu (anciennes lectures) : rien de publié
                x[k] = None
        if det and x["q"] is None:
            x["q"] = []
        if det and x["dom"] is None:
            x["dom"] = []
        x["proto"] = x.pop("proto")
        items.append({k: x[k] for k in CHAMPS})
        rapport["sans_fiche"] += (not det)
        if x["cls"] is None:
            rapport["sans_cls"] += 1
            rapport.setdefault("ids_cls_inconnu", []).append(i)
    # dernier passage de listing : date d'observation et total annoncé par le portail
    couv = None
    for nom in reversed(etat.couvertures()):
        with open(os.path.join(etat.d, "couverture", nom), encoding="utf-8") as fh:
            c = json.load(fh)
        if c.get("listing", {}).get("total_annonce") is not None:
            couv = c
            break
    cat = {
        "maj": (couv or {}).get("fin") or maintenant(),
        "source": SOURCE,
        "total_portail": (couv or {}).get("listing", {}).get("total_annonce"),
        "n": len(items),
        "n_details": sum(1 for x in items if x["det"]),
        "regions": regions,
        "items": items,
    }
    rapport["couverture_reference"] = (couv or {}).get("run_id")
    rapport["statut_couverture"] = (couv or {}).get("statut")
    return cat, rapport


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etat", default=os.path.join(ICI, "donnees"))
    ap.add_argument("--sortie", default=os.path.join(ICI, "sortie", "catalogue.json"))
    ap.add_argument("--aujourdhui", help="AAAA-MM-JJ (tests)")
    ap.add_argument("--exclure-absents-complets", type=int, default=None)
    ap.add_argument("--sans-cls-heritee", action="store_true",
                    help="n'applique pas referentiel/cls_heritee_par_id.json (cls hérité des IDs connus) : cls = null partout")
    a = ap.parse_args()
    regions = json.load(open(os.path.join(ICI, "referentiel", "regions.json"), encoding="utf-8"))["regions"]
    etat = Etat(a.etat)
    cls_h = None
    if not a.sans_cls_heritee:
        with open(os.path.join(ICI, "referentiel", "cls_heritee_par_id.json"), encoding="utf-8") as fh:
            cls_h = json.load(fh)["par_id"]
    cat, rapport = construire(etat, regions, a.aujourdhui, a.exclure_absents_complets, cls_h)
    rapport["cls_source"] = "héritée par ID connu (catalogue EAIOS 2026-09-26, non re-vérifiée) ; null pour les nouveaux" if cls_h else "aucune (null)"
    err = valider_catalogue(cat, regions)
    if err:
        print("CATALOGUE INVALIDE :", *err[:20], sep="\n  ")
        sys.exit(2)
    _ecrire_json(a.sortie, cat)
    _ecrire_json(os.path.splitext(a.sortie)[0] + "_rapport.json", rapport)
    print(json.dumps({"sortie": a.sortie, "n": cat["n"], "n_details": cat["n_details"], "total_portail": cat["total_portail"],
                      "statut_couverture": rapport["statut_couverture"], "a_relire": len(rapport["a_relire"]),
                      "sans_cls": rapport["sans_cls"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

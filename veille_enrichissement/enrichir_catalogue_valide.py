#!/usr/bin/env python3
"""Enrichit le DERNIER catalogue valide du coffre avec les fiches relues, quand les passages horaires récents sont PARTIELS
(listing PMMP mouvant : doublon de ligne, total qui bouge pendant la lecture). HORS LIGNE.

  python3 enrichir_catalogue_valide.py --coffre <coffre relu> --kit <kit> --sortie <dossier> [--aujourdhui AAAA-MM-JJ]

Entrées : stock/catalogue_valide.json (dernier listing COMPLET), stock/etat/fiches.json (fiches fusionnées), stock/statut.json.
Sorties : <sortie>/catalogue_valide.json et <sortie>/statut_listing_complet.json (pour ingestion_catalogue.py).
Règles :
  - mêmes identifiants que le catalogue valide : aucun ajout (les annonces vues seulement par un listing partiel attendent un
    passage complet) ; seules les consultations dont la date limite est passée sont retirées (règle de construire_catalogue) ;
  - champs du listing (« maj », total, pub, lx, nat, etr, lots, cls, ent, env) inchangés : le listing partiel n'est jamais repris ;
  - champs de fiche : ceux de la fiche lue (fiches.json), avec la règle de construire_catalogue pour les champs communs
    (ref, obj, mo, cat, proc, lim, h) : la fiche gagne si elle est lue après le listing ;
  - statut_listing_complet.json = statut.json dont « dernier_succes » est « dernier_listing_complet » (le passage qui a produit
    ce catalogue) ; « derniere_tentative » et les erreurs restent ceux du dernier passage réel. Refus si ce passage ne
    correspond pas au catalogue valide."""
import argparse
import json
import os
import sys

COMMUNS = ["ref", "obj", "mo", "cat", "proc", "lim", "h"]
FICHE_SEULE = ["est", "tp", "cau", "q", "ag", "vis", "reu", "var", "allot", "dom", "ouv", "dep", "proto"]


def enrichir(cat, fiches, statut, aujourdhui, libelle_seul):
    lc = statut.get("dernier_listing_complet") or {}
    if lc.get("fin") != cat["maj"] or lc.get("total_annonce") != cat["total_portail"]:
        raise SystemExit(f"refus : catalogue valide (maj {cat['maj']}) ≠ dernier listing complet ({lc.get('fin')})")
    items, r = [], {"n_avant": cat["n"], "exclus_date_passee": 0, "fiche_lue": 0, "sans_fiche": 0, "communs_de_la_fiche": {}}
    for x in cat["items"]:
        k = f"pmmp:{x['o']}:{x['r']}"
        f = fiches.get(k)
        F = (f or {}).get("champs") or {}
        y = dict(x)
        if f:
            if f["lu_le"] >= cat["maj"]:
                for c in COMMUNS:
                    if F.get(c) is not None and F[c] != x[c]:
                        y[c] = F[c]
                        r["communs_de_la_fiche"][c] = r["communs_de_la_fiche"].get(c, 0) + 1
            for c in FICHE_SEULE:
                y[c] = None if libelle_seul(F.get(c)) else F.get(c)
            y["q"] = y["q"] if y["q"] is not None else []
            y["dom"] = y["dom"] if y["dom"] is not None else []
            y["det"] = True
            r["fiche_lue"] += 1
        else:
            r["sans_fiche"] += 1  # rien n'est inventé : le détail du catalogue valide (s'il y en a un) est gardé tel quel
        if y["lim"] and y["lim"] < aujourdhui:
            r["exclus_date_passee"] += 1
            continue
        items.append({c: y[c] for c in x})
    out = {**{c: cat[c] for c in cat if c != "items"}, "n": len(items), "n_details": sum(1 for x in items if x["det"]), "items": items}
    st = {**statut, "dernier_succes": lc}
    r["n"] = out["n"]
    return out, st, r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--coffre", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--aujourdhui")
    a = ap.parse_args(argv)
    sys.path.insert(0, a.kit)
    from veille.etat import aujourd_hui_maroc  # noqa
    from veille.pmmp_fiche import libelle_seul  # noqa
    from veille.schema import valider_catalogue  # noqa
    lire = lambda p: json.load(open(os.path.join(a.coffre, "stock", p), encoding="utf-8"))
    cat, st, r = enrichir(lire("catalogue_valide.json"), lire("etat/fiches.json"), lire("statut.json"),
                          a.aujourdhui or aujourd_hui_maroc(), libelle_seul)
    err = valider_catalogue(cat, cat["regions"])
    if err:
        raise SystemExit("catalogue invalide : " + "; ".join(err[:5]))
    os.makedirs(a.sortie, exist_ok=True)
    json.dump(cat, open(os.path.join(a.sortie, "catalogue_valide.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(st, open(os.path.join(a.sortie, "statut_listing_complet.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

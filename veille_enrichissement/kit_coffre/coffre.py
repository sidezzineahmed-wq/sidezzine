#!/usr/bin/env python3
"""Emballage de l'état du kit pour le coffre (artefact privé) et restitution.

Les artefacts ne servent pas les archives (.zip/.gz) et limitent le nombre de fichiers par version :
l'état est donc stocké en quelques JSON agrégés.

  python coffre.py pack    --etat donnees --sortie coffre_out   # état -> JSON agrégés + statut + manifeste
  python coffre.py unpack  --source coffre_in --etat donnees    # JSON agrégés -> état du kit
  python coffre.py verifier --source coffre_in                  # SHA-256 contre manifest.json

Fichiers du coffre (sous stock/) :
  etat/listing.json, etat/organismes.json, etat/selection.json (journal des choix/échecs de fiches),
  etat/fiches.json (toutes les fiches, par id),
  etat/couvertures_recentes.json (50 dernières), catalogue_valide.json (dernier catalogue issu d'un listing
  COMPLET, jamais remplacé par un passage partiel), catalogue_dernier_passage.json, catalogue_rapport.json,
  statut.json (dernière tentative, dernier succès, erreurs, couverture), manifest.json à la racine.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import sys

MAX_COUV = 50
MAX_ERREURS = 30


def _lire(p, defaut=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut


def _ecrire(p, obj):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=0 if p.endswith("listing.json") else 1)


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def unpack(source, etat):
    s = os.path.join(source, "stock", "etat")
    os.makedirs(os.path.join(etat, "fiches"), exist_ok=True)
    os.makedirs(os.path.join(etat, "couverture"), exist_ok=True)
    for nom in ("listing.json", "organismes.json", "selection.json"):
        if os.path.exists(os.path.join(s, nom)):
            shutil.copy(os.path.join(s, nom), os.path.join(etat, nom))
    fiches = _lire(os.path.join(s, "fiches.json"), {}) or {}
    for i, doc in fiches.items():
        org, ref = i.split(":")[1:]
        _ecrire(os.path.join(etat, "fiches", f"{org}_{ref}.json"), doc)
    for c in _lire(os.path.join(s, "couvertures_recentes.json"), []) or []:
        _ecrire(os.path.join(etat, "couverture", c["run_id"] + ".json"), c)
    return {"fiches": len(fiches)}


def pack(etat, sortie, catalogue=None, rapport=None, source_precedente=None):
    st = os.path.join(sortie, "stock")
    os.makedirs(os.path.join(st, "etat"), exist_ok=True)
    for nom in ("listing.json", "organismes.json", "selection.json"):
        if os.path.exists(os.path.join(etat, nom)):
            shutil.copy(os.path.join(etat, nom), os.path.join(st, "etat", nom))
    fiches = {}
    for p in sorted(glob.glob(os.path.join(etat, "fiches", "*.json"))):
        d = _lire(p)
        fiches[d["id"]] = d
    _ecrire(os.path.join(st, "etat", "fiches.json"), fiches)
    couvs = [_lire(p) for p in sorted(glob.glob(os.path.join(etat, "couverture", "*.json")))][-MAX_COUV:]
    for c in couvs:
        c.pop("journal_http", None) if len(couvs) > 5 and c is not couvs[-1] else None
    _ecrire(os.path.join(st, "etat", "couvertures_recentes.json"), couvs)
    der = couvs[-1] if couvs else None

    prec = os.path.join(source_precedente, "stock") if source_precedente else None
    statut = (_lire(os.path.join(prec, "statut.json")) if prec else None) or {
        "derniere_tentative": None, "dernier_succes": None, "dernier_listing_complet": None, "erreurs": [], "historique": []}
    if der:
        L = der.get("listing", {})
        F = der.get("fiches") or {}
        listing_ok = not der.get("erreur")
        listing_complet = (der.get("statut", "").startswith("LISTING_COMPLET") and listing_ok and bool(L.get("complete")))
        cov = {"run_id": der["run_id"], "debut": der.get("debut"), "fin": der.get("fin"), "statut": der.get("statut"),
               "total_annonce": L.get("total_annonce"), "pages_annoncees": L.get("pages_annoncees"),
               "pages_lues": [p["page"] for p in L.get("pages_lues", [])], "ids_distincts": L.get("ids_distincts"),
               "couverture_pct": round(100 * L["ids_distincts"] / L["total_annonce"], 1) if L.get("total_annonce") and L.get("ids_distincts") is not None else None,
               "stable": L.get("stable"), "raisons_incomplet": L.get("raisons_incomplet"),
               "fiches_lues": len(F.get("lues", [])), "fiches_echecs": len(F.get("echecs", [])),
               "fiches_par_categorie": (F.get("selection") or {}).get("choisies"),
               "nb_requetes": der.get("nb_requetes"),
               "codes_http": sorted({j["code"] for j in der.get("journal_http", [])})}
        statut["derniere_tentative"] = cov
        if listing_ok and L.get("pages_lues"):
            statut["dernier_succes_listing"] = {k: cov[k] for k in ("run_id", "fin", "statut", "total_annonce", "pages_annoncees", "pages_lues", "couverture_pct")}
        if listing_complet:
            statut["dernier_listing_complet"] = statut["dernier_succes_listing"]
        # « dernier_succes » (lu par l'ingestion EAIOS) = le dernier listing COMPLET, celui qui a produit catalogue_valide.json ;
        # un passage PARTIEL ne le remplace jamais (corrige le 19/10 : un partiel l'écrasait et bloquait l'ingestion)
        statut["dernier_succes"] = statut.get("dernier_listing_complet")
        if F.get("lues"):
            statut["derniere_maj_fiches"] = {"run_id": der["run_id"], "fin": der.get("fin"), "lues": len(F["lues"]),
                                             "echecs": len(F.get("echecs", [])), "par_categorie": cov["fiches_par_categorie"],
                                             "files": {k: (F.get("selection") or {}).get(k) for k in ("file_changees", "file_nouvelles", "file_anciennes_eligibles")},
                                             "derniere_lecture": max(x["lu_le"] for x in F["lues"])}
        err = [e for e in (der.get("erreur"), der.get("erreur_fiches")) if e]
        if err:
            statut["erreurs"] = (statut.get("erreurs", []) + [{"run_id": der["run_id"], "erreur": " | ".join(err)[:600]}])[-MAX_ERREURS:]
        statut["historique"] = (statut.get("historique", []) + [{k: cov[k] for k in ("run_id", "statut", "total_annonce", "ids_distincts", "couverture_pct", "fiches_lues")} | {"ok": not err}])[-200:]
        statut["catalogue_valide_mis_a_jour"] = listing_complet
    statut["perimetre"] = ("Annonces de consultation uniquement (fenêtre par défaut du portail). Un listing complet de ces pages "
                           "ne signifie PAS la collecte de tous les types d'annonces PMMP (information, résultats, PV, "
                           "achèvement, résiliation, présentation, bons de commande ne sont pas collectés).")
    statut["maj"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    _ecrire(os.path.join(st, "statut.json"), statut)

    # catalogues : le catalogue « valide » n'est remplacé que par un passage au listing complet sans erreur
    if catalogue and os.path.exists(catalogue):
        shutil.copy(catalogue, os.path.join(st, "catalogue_dernier_passage.json"))
        if der and statut.get("catalogue_valide_mis_a_jour"):
            shutil.copy(catalogue, os.path.join(st, "catalogue_valide.json"))
    if prec and not os.path.exists(os.path.join(st, "catalogue_valide.json")) and os.path.exists(os.path.join(prec, "catalogue_valide.json")):
        shutil.copy(os.path.join(prec, "catalogue_valide.json"), os.path.join(st, "catalogue_valide.json"))
    if der and not statut.get("catalogue_valide_mis_a_jour") and os.path.exists(os.path.join(st, "catalogue_valide.json")):
        # catalogue valide gardé : ses fiches suivent les lectures réelles (aucun identifiant ajouté, listing inchangé)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from construire_catalogue import rafraichir_fiches  # noqa: E402
        cv = _lire(os.path.join(st, "catalogue_valide.json")) or {}
        cv2 = rafraichir_fiches(cv, fiches)[0] if "items" in cv and cv.get("maj") else cv
        if cv2 != cv:
            _ecrire(os.path.join(st, "catalogue_valide.json"), cv2)
    if rapport and os.path.exists(rapport):
        shutil.copy(rapport, os.path.join(st, "catalogue_rapport.json"))
    return manifeste(sortie)


def copier_kit(kit, sortie):
    """Copie les fichiers du kit (sans données, caches ni preuves) sous <sortie>/stock/kit/."""
    n = 0
    for root, dirs, fs in os.walk(kit):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "donnees", "sortie", "preuve_collecte", "donnees_essai", "sortie_essai")]
        for f in fs:
            src = os.path.join(root, f)
            dst = os.path.join(sortie, "stock", "kit", os.path.relpath(src, kit))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
            n += 1
    return n


def manifeste(racine):
    m = {"cree_le": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
         "note": "Coffre d'essai Veille PMMP, hors EAIOS.", "fichiers": {}}
    for p in sorted(glob.glob(os.path.join(racine, "stock", "**", "*"), recursive=True)):
        if os.path.isfile(p) and "__pycache__" not in p:
            rel = os.path.relpath(p, racine).replace(os.sep, "/")
            m["fichiers"][rel] = {"octets": os.path.getsize(p), "sha256": sha(p)}
    _ecrire(os.path.join(racine, "manifest.json"), m)
    return m


def verifier(source):
    m = _lire(os.path.join(source, "manifest.json"))
    res = {"attendus": len(m["fichiers"]), "identiques": 0, "differents": [], "manquants": []}
    for rel, f in m["fichiers"].items():
        p = os.path.join(source, rel)
        if not os.path.exists(p):
            res["manquants"].append(rel)
        elif sha(p) != f["sha256"]:
            res["differents"].append(rel)
        else:
            res["identiques"] += 1
    res["ok"] = not res["differents"] and not res["manquants"]
    return res


TEXTE_BRUT = (".py", ".txt", ".html")


def carte_publication(racine, manifeste_precedent=None):
    """Carte `files` pour l'outil Artifact : chemins du manifeste courant + null pour les chemins disparus.
    Les sources (.py/.txt/.html) partent en text/plain (les archives ne sont pas servies)."""
    m = _lire(os.path.join(racine, "manifest.json"))
    carte = {"manifest.json": os.path.join(racine, "manifest.json")}
    for rel in m["fichiers"]:
        src = os.path.join(racine, rel)
        carte[rel] = {"from": src, "contentType": "text/plain"} if rel.endswith(TEXTE_BRUT) else src
    if manifeste_precedent:
        for rel in (_lire(manifeste_precedent, {}) or {}).get("fichiers", {}):
            if rel not in carte:
                carte[rel] = None
    return carte


def controle(racine, maintenant_iso=None, retard_min=90, listing_max_h=6):
    """Fraîcheur : alerte si la dernière tentative a plus de retard_min minutes, ou si le dernier listing complet
    a plus de listing_max_h heures, ou si la dernière tentative a échoué."""
    st = _lire(os.path.join(racine, "stock", "statut.json"), {}) or {}
    now = dt.datetime.fromisoformat(maintenant_iso) if maintenant_iso else dt.datetime.now(dt.timezone.utc)

    def age(x, cle="fin"):
        v = (x or {}).get(cle)
        return round((now - dt.datetime.fromisoformat(v)).total_seconds() / 60) if v else None
    a_t, a_c = age(st.get("derniere_tentative")), age(st.get("dernier_listing_complet"))
    a_f = age(st.get("derniere_maj_fiches"))
    dern_err = (st.get("historique") or [{}])[-1].get("ok") is False
    motifs = []
    if a_t is None or a_t > retard_min:
        motifs.append(f"dernière tentative il y a {a_t} min (> {retard_min})")
    if a_c is None or a_c > listing_max_h * 60:
        motifs.append(f"dernier listing complet il y a {a_c} min (> {listing_max_h} h)")
    if dern_err:
        motifs.append("dernière tentative en erreur")
    return {"alerte": bool(motifs), "motifs": motifs, "age_derniere_tentative_min": a_t,
            "age_dernier_listing_complet_min": a_c, "age_derniere_maj_fiches_min": a_f}


def resume(racine):
    st = _lire(os.path.join(racine, "stock", "statut.json"), {}) or {}
    d = st.get("derniere_tentative") or {}
    r = {"derniere_tentative": {k: d.get(k) for k in ("run_id", "debut", "fin", "statut", "total_annonce", "pages_annoncees",
                                                     "ids_distincts", "couverture_pct", "pages_lues", "stable", "raisons_incomplet",
                                                     "fiches_lues", "fiches_par_categorie", "nb_requetes", "codes_http")},
         "dernier_succes_listing": (st.get("dernier_succes_listing") or {}).get("run_id"),
         "dernier_listing_complet": (st.get("dernier_listing_complet") or {}).get("run_id"),
         "derniere_maj_fiches": {k: (st.get("derniere_maj_fiches") or {}).get(k) for k in ("run_id", "lues", "derniere_lecture")},
         "catalogue_valide_mis_a_jour": st.get("catalogue_valide_mis_a_jour"),
         "nb_erreurs_enregistrees": len(st.get("erreurs", [])),
         "derniere_erreur": (st.get("erreurs") or [None])[-1],
         "perimetre": "Annonces de consultation seulement ; complet != tous les types d'annonces PMMP"}
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("pack"); a.add_argument("--etat", required=True); a.add_argument("--sortie", required=True)
    a.add_argument("--catalogue"); a.add_argument("--rapport"); a.add_argument("--precedent")
    b = sp.add_parser("unpack"); b.add_argument("--source", required=True); b.add_argument("--etat", required=True)
    c = sp.add_parser("verifier"); c.add_argument("--source", required=True)
    d = sp.add_parser("carte"); d.add_argument("--racine", required=True); d.add_argument("--manifeste-precedent")
    rs = sp.add_parser("resume"); rs.add_argument("--racine", required=True)
    ct = sp.add_parser("controle"); ct.add_argument("--racine", required=True)
    ct.add_argument("--retard-min", type=int, default=90); ct.add_argument("--listing-max-h", type=float, default=6)
    k = sp.add_parser("kit"); k.add_argument("--kit", required=True); k.add_argument("--sortie", required=True)
    x = ap.parse_args()
    if x.cmd == "pack":
        m = pack(x.etat, x.sortie, x.catalogue, x.rapport, x.precedent)
        print(json.dumps({"fichiers": len(m["fichiers"])}))
    elif x.cmd == "unpack":
        print(json.dumps(unpack(x.source, x.etat)))
    elif x.cmd == "carte":
        print(json.dumps(carte_publication(os.path.abspath(x.racine), x.manifeste_precedent), ensure_ascii=False))
    elif x.cmd == "resume":
        print(json.dumps(resume(x.racine), ensure_ascii=True, separators=(",", ":")))
    elif x.cmd == "controle":
        print(json.dumps(controle(x.racine, None, x.retard_min, x.listing_max_h), ensure_ascii=False))
    elif x.cmd == "kit":
        n = copier_kit(x.kit, x.sortie)
        print(json.dumps({"kit_fichiers": n}))
    else:
        r = verifier(x.source)
        print(json.dumps(r, ensure_ascii=False))
        sys.exit(0 if r["ok"] else 3)


if __name__ == "__main__":
    main()

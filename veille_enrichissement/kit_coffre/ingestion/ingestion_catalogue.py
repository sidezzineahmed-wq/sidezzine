#!/usr/bin/env python3
"""Ingestion du catalogue du collecteur Veille PMMP (coffre) dans le fichier publié catalogue.json d'EAIOS. HORS LIGNE.

N'écrit que dans --sortie (dossier local). Ne publie rien : la publication est une étape distincte (voir LISEZ-MOI).

Entrées : catalogue_valide.json et statut.json du coffre du collecteur ; catalogue.json actuellement publié dans EAIOS.
Sorties : catalogue.json (31 champs, même schéma ; consultations du collecteur) ;
          catalogue_details.json (provenance de chaque détail, détails obsolètes conservés à part, et « pmmp_enrichi » :
          mode de passation de la fiche + classification Etat/CL/EEP de l'entité, voir enrichi_pmmp.py) ;
          catalogue_hors_listing.json (consultations de la publication précédente absentes du collecteur, date limite non passée :
          statut INCONNU, jamais présentées comme annulées) ;
          catalogue_etat.json (dernier succès réellement chargé, dernier essai, erreurs, couverture du listing, séparée des fiches) ;
          ingestion_rapport.json ; sauvegarde/<fichier> (copie exacte de chaque fichier publié précédent, retour arrière).

Publication : seuls les fichiers dont les octets changent sont listés dans ingestion_rapport.json « fichiers_a_publier »
(ex. dernier essai échoué avec dernier succès intact : seul catalogue_etat.json change). « inchange » = rien à publier.
Cohérence : catalogue_etat.json et catalogue_hors_listing.json portent catalogue_sha256, le SHA-256 exact du catalogue.json
auquel ils correspondent (la page ne bascule que si les trois concordent).

Règles :
  1. Refus (code 2, rien d'écrit sauf le rapport) si le collecteur n'a pas un dernier SUCCÈS complet correspondant au catalogue
     (statut LISTING_COMPLET…, couverture 100 %, stable, sans erreur), si le schéma est invalide, ou si le nombre de
     consultations s'effondre par rapport à la publication précédente encore ouverte (garde-fou contre un remplacement par un
     instantané partiel ; --accepter-baisse pour lever après examen humain).
  2. Ensemble des consultations = celui du collecteur (toutes les consultations nationales, sans filtre de score, de région
     ni de dossiers). Les consultations de l'ancien catalogue absentes du collecteur sont RETIRÉES du fichier publié et listées
     (date passée / absentes du portail) ; aucune donnée métier EAIOS (dossiers, suivi, pièces) n'est touchée : elles vivent
     dans la base, pas dans ce fichier.
  3. Détails séparés : si le collecteur n'a pas (encore) lu la fiche (det=false) mais que l'ancien catalogue avait un détail
     pour la MÊME consultation et que les champs d'identification (ref, obj, mo, lim, h) n'ont pas changé, le détail précédent est
     conservé et sa provenance (date de l'ancien catalogue) est inscrite dans catalogue_details.json. Les valeurs du listing
     récent gagnent toujours. Si l'annonce a été modifiée, le détail ancien n'est PAS repris dans catalogue.json (det=false
     jusqu'à une nouvelle lecture) : il est gardé dans catalogue_details.json « obsoletes », daté, avec les champs changés.
  4. Idempotent : même entrée → mêmes octets ; si le résultat est identique au catalogue publié, le rapport dit « inchangé ».
"""
import argparse
import datetime
import hashlib
import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lieux import Lieux  # noqa: E402
from enrichi_pmmp import enrichir  # noqa: E402

CHAMPS = ["r", "o", "ref", "obj", "mo", "cat", "proc", "pub", "lim", "h", "lx", "nat", "etr", "lots",
          "det", "cls", "ent", "env", "est", "tp", "cau", "q", "ag", "vis", "reu", "var", "allot", "dom",
          "ouv", "dep", "proto"]
FICHE_SEULE = ["est", "tp", "cau", "q", "ag", "vis", "reu", "var", "allot", "dom", "ouv", "dep", "proto"]
IDENT = ["ref", "obj", "mo", "lim", "h", "cat", "proc", "lots", "lx", "etr"]  # si l'un change (lieux normalisés), l'ancien détail est obsolète
SUIVIS = ["ref", "obj", "mo", "cat", "proc", "pub", "lim", "h", "lx", "nat", "etr", "lots", "cls", "ent", "env"]
STATUT_COMPLET = "LISTING_COMPLET_ANNONCES_DE_CONSULTATION_FENETRE_PAR_DEFAUT"
BAISSE_MAX = 0.10


class Refus(Exception):
    pass


FICHIERS = ("catalogue.json", "catalogue_details.json", "catalogue_hors_listing.json", "catalogue_etat.json")
TZ_MAROC = ZoneInfo("Africa/Casablanca")
REFERENTIEL_CLASSIFICATION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "referentiel", "classification_entites.json")


def jour_maroc(instant=None):
    """Jour civil au Maroc (fuseau Africa/Casablanca, y compris le passage à UTC+0 pendant le Ramadan)."""
    t = instant or datetime.datetime.now(datetime.timezone.utc)
    return t.astimezone(TZ_MAROC).date().isoformat()


def prov_lecture(fiches, k, snapshot):
    """Provenance d'un détail lu par le collecteur : date de lecture RÉELLE (fiches.json, lu_le) si connue ; sinon rien
    n'est inventé : lecture inconnue, seule la date du catalogue source est donnée."""
    f = (fiches or {}).get(k) or {}
    if f.get("lu_le"):
        return {"source": "collecteur", "lu_le": f["lu_le"], "run": f.get("run")}
    return {"source": "collecteur", "lu_le": None, "snapshot_maj": snapshot, "note": "date de lecture réelle inconnue"}


def octets_json(d):
    return (json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def cle(x):
    return f"pmmp:{x['o']}:{x['r']}"


def verifier_source(cat, statut):
    s = statut.get("dernier_succes") or {}
    t = statut.get("derniere_tentative") or {}
    if s.get("statut") != STATUT_COMPLET or s.get("couverture_pct") != 100.0:
        raise Refus("aucun dernier succès complet du collecteur (statut %r)" % s.get("statut"))
    if statut.get("catalogue_valide_mis_a_jour") is not True and t.get("run_id") == s.get("run_id"):
        raise Refus("le collecteur n'a pas validé ce catalogue")
    if cat.get("maj") != s.get("fin"):
        raise Refus("catalogue_valide (maj %r) ne correspond pas au dernier succès (%r)" % (cat.get("maj"), s.get("fin")))
    if cat.get("total_portail") != s.get("total_annonce"):
        raise Refus("total_portail du catalogue différent du total du dernier succès")
    if len(s.get("pages_lues") or []) != s.get("pages_annoncees"):
        raise Refus("pages lues != pages annoncées")


def verifier_schema(cat):
    err = []
    for k in ("maj", "source", "total_portail", "n", "n_details", "regions", "items"):
        if k not in cat:
            err.append("clé racine manquante " + k)
    if err:
        return err
    if cat["n"] != len(cat["items"]):
        err.append("n != len(items)")
    vus = set()
    for x in cat["items"]:
        if list(x.keys()) != CHAMPS:
            err.append("31 champs attendus pour %s:%s" % (x.get("o"), x.get("r")))
            continue
        if cle(x) in vus:
            err.append("doublon " + cle(x))
        vus.add(cle(x))
        if not x["det"] and any(x[k] not in (None, []) for k in FICHE_SEULE):
            err.append("champs de fiche sans det pour " + cle(x))
    if cat["n_details"] != sum(1 for x in cat["items"] if x["det"]):
        err.append("n_details incohérent")
    return err


def ingerer(nouveau, statut, precedent, aujourdhui, details_precedents=None, accepter_baisse=False, hors_precedents=None, fiches=None,
            referentiel_classification=None):
    verifier_source(nouveau, statut)
    err = verifier_schema(nouveau)
    if err:
        raise Refus("catalogue du collecteur invalide : " + "; ".join(err[:5]))
    prev = {cle(x): x for x in (precedent or {}).get("items", [])}
    prov_prec = (details_precedents or {}).get("par_id", {})
    date_prec = (precedent or {}).get("maj")
    ouverts_prec = sum(1 for x in prev.values() if x.get("lim") and x["lim"] >= aujourdhui)
    if ouverts_prec and len(nouveau["items"]) < (1 - BAISSE_MAX) * ouverts_prec and not accepter_baisse:
        raise Refus(f"baisse suspecte : {len(nouveau['items'])} consultations contre {ouverts_prec} encore ouvertes dans la publication précédente")
    items, prov, obsoletes = [], {}, dict((details_precedents or {}).get("obsoletes", {}))
    lieux, rap_lieux = Lieux(nouveau["regions"]), {}
    r = {"nouveaux": [], "modifies": {}, "retires_date_passee": 0, "hors_listing_statut_inconnu": [], "details_collecteur": 0,
         "details_herites": 0, "details_non_repris_champs_changes": 0, "sans_detail": 0}
    for x in nouveau["items"]:
        k = cle(x)
        y = dict(x)
        y["lx"], y["etr"] = lieux.normaliser(x["lx"], x["etr"], rap_lieux)  # libellés administratifs -> codes canoniques
        x = y
        p = prev.get(k)
        if p is None:
            r["nouveaux"].append(k)
        else:
            ch = [f for f in SUIVIS if p.get(f) != x.get(f)]
            if ch:
                r["modifies"][k] = ch
        if x["det"]:
            prov[k] = prov_lecture(fiches, k, nouveau["maj"])
            r["details_collecteur"] += 1
        elif p is not None and p.get("det"):
            changes = [f for f in IDENT if p.get(f) != x.get(f)]
            if not changes:
                for f in FICHE_SEULE:
                    y[f] = p.get(f)
                y["det"] = True
                prov[k] = prov_prec.get(k) or {"source": "catalogue_precedent", "lu_le": None, "snapshot_maj": date_prec,
                                               "note": "date de lecture réelle inconnue : seule la date du catalogue source est connue"}
                r["details_herites"] += 1
            else:
                r["details_non_repris_champs_changes"] += 1
                r["sans_detail"] += 1
                obsoletes[k] = {"provenance": prov_prec.get(k) or {"source": "catalogue_precedent", "lu_le": None, "snapshot_maj": date_prec},
                                "champs_changes": changes, "detail": {f: p.get(f) for f in FICHE_SEULE}}
        else:
            r["sans_detail"] += 1
        items.append({f: y[f] for f in CHAMPS})
    cles_nouv = {cle(x) for x in nouveau["items"]}
    hp = {cle(x): x for x in (hors_precedents or {}).get("items", [])}
    depuis_prec = (hors_precedents or {}).get("absent_depuis", {})
    r["reapparues"] = sorted(k for k in hp if k in cles_nouv)
    hors, depuis = [], {}
    for k in sorted(set(prev) | set(hp)):
        if k in cles_nouv:
            continue
        p = prev.get(k) or hp[k]
        if p.get("lim") and p["lim"] < aujourdhui:
            r["retires_date_passee"] += 1
            continue
        r["hors_listing_statut_inconnu"].append({"id": k, "lim": p.get("lim")})
        hors.append({f: p.get(f) for f in CHAMPS})
        depuis[k] = depuis_prec.get(k) or nouveau["maj"]   # premier listing complet où elle manquait
    for k in list(obsoletes):
        if k not in cles_nouv:
            obsoletes.pop(k)
        elif any(x["det"] for x in nouveau["items"] if cle(x) == k):
            obsoletes.pop(k)  # relu par le collecteur : l'ancien détail n'a plus lieu d'être
    cat = {"maj": nouveau["maj"], "source": nouveau["source"], "total_portail": nouveau["total_portail"], "n": len(items),
           "n_details": sum(1 for x in items if x["det"]), "regions": nouveau["regions"], "items": items}
    err = verifier_schema(cat)
    if err:
        raise Refus("résultat invalide : " + "; ".join(err[:5]))
    s, t = statut["dernier_succes"], statut.get("derniere_tentative") or {}
    absents_conserves = len(items) - s["total_annonce"]
    r["couverture"] = {
        "derniere_tentative": {k: t.get(k) for k in ("run_id", "fin", "statut", "couverture_pct")},
        "dernier_succes": {**{k: s.get(k) for k in ("run_id", "fin", "statut", "total_annonce", "pages_annoncees", "couverture_pct")},
                           "pages_lues": len(s.get("pages_lues") or [])},
        "consultations_publiees": len(items),
        "au_dernier_listing": s["total_annonce"],
        "absentes_du_dernier_listing_conservees": absents_conserves,
        "explication": "consultations publiées = annonces du dernier listing complet + consultations absentes de ce listing "
                       "mais dont la date limite n'est pas passée (le collecteur ne supprime jamais sur simple absence)",
        "perimetre": statut.get("perimetre"),
    }
    r["nouveaux_n"], r["modifies_n"] = len(r["nouveaux"]), len(r["modifies"])
    r["lieux"] = {"normalises": len(rap_lieux.get("lieux_normalises", {})), "table": rap_lieux.get("lieux_normalises", {}),
                  "a_verifier_ambigus": sorted(rap_lieux.get("lieux_ambigus", {})), "a_verifier_non_reconnus": sorted(rap_lieux.get("lieu_marocain_non_reconnu", {}))}
    csha = sha(octets_json(cat))
    details = {"maj": nouveau["maj"], "catalogue_sha256": csha, "par_id": {k: prov[k] for k in sorted(prov)},
               "obsoletes": {k: obsoletes[k] for k in sorted(obsoletes)},
               # enrichissement PMMP joint (mode de passation de la fiche, classification Etat/CL/EEP de l'entité) : voir enrichi_pmmp.py
               "pmmp_enrichi": enrichir(items, fiches, referentiel_classification, (details_precedents or {}).get("pmmp_enrichi"))}
    hors_listing = {"maj": nouveau["maj"], "catalogue_sha256": csha, "statut": "inconnu",
                    "explication": "absentes du dernier listing complet du collecteur alors que leur date limite n'est pas passée ; "
                                   "aucune preuve d'annulation : ne pas les présenter comme annulées",
                    "absent_depuis": {k: depuis[k] for k in sorted(depuis)},
                    "items": sorted(hors, key=lambda x: (x.get("lim") or "", cle(x)))}
    etat = {"maj": nouveau["maj"], "catalogue_sha256": csha,
            "cadence": "collecte horaire des « Annonces de consultation » du portail ; la page relit ces fichiers périodiquement : "
                       "ce n'est pas du temps réel",
            "listing": r["couverture"],
            "fiches": {"avec_detail": cat["n_details"], "detail_du_collecteur": r["details_collecteur"],
                       "detail_du_collecteur_lecture_connue": sum(1 for v in prov.values() if v["source"] == "collecteur" and v.get("lu_le")),
                       "derniere_lecture_reelle": max((v["lu_le"] for v in prov.values() if v.get("lu_le")), default=None),
                       "detail_herite_date": r["details_herites"],
                       "detail_herite_sources": sorted({v.get("snapshot_maj") or "" for v in prov.values() if v["source"] != "collecteur"} - {""}),
                       "sans_detail": r["sans_detail"]},
            "erreurs_derniere_tentative": statut.get("erreurs") or []}
    return cat, details, r, hors_listing, etat


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalogue-valide", required=True)
    ap.add_argument("--statut", required=True)
    ap.add_argument("--precedent", required=True, help="catalogue.json actuellement publié dans EAIOS")
    ap.add_argument("--details-precedents", help="catalogue_details.json publié (s'il existe)")
    ap.add_argument("--hors-precedents", help="catalogue_hors_listing.json publié (s'il existe)")
    ap.add_argument("--etat-precedent", help="catalogue_etat.json publié (s'il existe)")
    ap.add_argument("--fiches", help="stock/etat/fiches.json du collecteur (dates de lecture réelles)")
    ap.add_argument("--referentiel-classification", default=REFERENTIEL_CLASSIFICATION,
                    help="relevé officiel Etat/CL/EEP par entité (défaut : referentiel/classification_entites.json du kit)")
    ap.add_argument("--aujourdhui", help="AAAA-MM-JJ ; défaut : jour civil Africa/Casablanca")
    ap.add_argument("--accepter-baisse", action="store_true")
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args(argv)
    lire = lambda p: json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else None
    brut = lambda p: open(p, "rb").read() if p and os.path.exists(p) else None
    auj = a.aujourdhui or jour_maroc()
    prec_octets = open(a.precedent, "rb").read()
    os.makedirs(os.path.join(a.sortie, "sauvegarde"), exist_ok=True)
    try:
        cat, details, r, hors, etat = ingerer(lire(a.catalogue_valide), lire(a.statut), json.loads(prec_octets), auj,
                                              lire(a.details_precedents), a.accepter_baisse, lire(a.hors_precedents), lire(a.fiches),
                                              lire(a.referentiel_classification))
    except Refus as e:
        open(os.path.join(a.sortie, "ingestion_rapport.json"), "wb").write(octets_json({"etat": "refus", "motif": str(e)}))
        print(json.dumps({"etat": "refus", "motif": str(e)}, ensure_ascii=False))
        return 2
    sorties = dict(zip(FICHIERS, (octets_json(cat), octets_json(details), octets_json(hors), octets_json(etat))))
    precedents = dict(zip(FICHIERS, (prec_octets, brut(a.details_precedents), brut(a.hors_precedents), brut(a.etat_precedent))))
    a_publier = [n for n in FICHIERS if precedents[n] is None or sha(precedents[n]) != sha(sorties[n])]
    r.update({"etat": "pret" if a_publier else "inchange", "fichiers_a_publier": a_publier,
              "sha256": {n: sha(sorties[n]) for n in FICHIERS}, "catalogue_sha256": sha(sorties["catalogue.json"]),
              "octets": len(sorties["catalogue.json"]), "precedent_sha256": sha(prec_octets),
              "precedent_maj": json.loads(prec_octets).get("maj"), "aujourdhui": auj})
    for n in FICHIERS:
        if precedents[n] is not None:
            open(os.path.join(a.sortie, "sauvegarde", n), "wb").write(precedents[n])
        open(os.path.join(a.sortie, n), "wb").write(sorties[n])
    open(os.path.join(a.sortie, "ingestion_rapport.json"), "wb").write(octets_json(r))
    print(json.dumps({k: r[k] for k in ("etat", "fichiers_a_publier", "catalogue_sha256", "nouveaux_n", "modifies_n", "retires_date_passee", "details_collecteur",
                                        "details_herites", "sans_detail")} | {"hors_listing_statut_inconnu": len(r["hors_listing_statut_inconnu"]),
                                                                                "couverture": r["couverture"]["consultations_publiees"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

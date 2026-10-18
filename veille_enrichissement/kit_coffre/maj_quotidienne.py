#!/usr/bin/env python3
"""Passage MANUEL de veille PMMP (catalogue des consultations en cours). Aucune planification ici.

Exemples :
  python maj_quotidienne.py --max-pages 1 --fiches 5            # petite collecte (essai)
  python maj_quotidienne.py --fiches 50                          # listing complet + 50 fiches
  python construire_catalogue.py                                 # puis construction hors ligne

Portail public uniquement : pas de login, pas de compte, pas de secret, pas de contournement.
Débit : >= 3 s (+ gigue) entre requêtes ; arrêt immédiat sur 401/403 ou page inattendue.
"""
import argparse
import hashlib
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from veille.client import ArretCollecte, ClientPMMP, texte  # noqa: E402
from veille.etat import Etat, aujourd_hui_maroc, maintenant  # noqa: E402
from veille.pmmp_fiche import PARAMS, fiche_valide, lire_fiche, tronquer_contact  # noqa: E402
from veille.pmmp_lots import PARAMS_LOTS, lire_popup  # noqa: E402
from veille.pmmp_listing import CollecteListing, lignes, lire_ligne, total_et_pages  # noqa: E402
from veille.schema import make_id, split_id  # noqa: E402

ICI = os.path.dirname(os.path.abspath(__file__))

FAMILLES_HORS_PERIMETRE = [
    "Bons de commande / avis d'achat (rubrique distincte du portail, non sondée par ce kit)",
    "Consultations annulées (non distinguées : une consultation disparue n'est PAS marquée annulée)",
    "Rectificatifs / avis modificatifs en tant que tels (seul l'effet visible au listing est constaté, ex. report de date)",
    "Pièces du DCE (téléchargement non effectué par ce kit)",
    "Détail par lot : lu dans le popup « Détail des lots » (clé « lots » de la fiche) ; est/cau/tp/q/ag de la fiche restent null pour les consultations alloties (valeurs par lot, jamais sommées)",
    "Consultations hors fenêtre de recherche par défaut (date limite > +6 mois ou mise en ligne > 6 mois)",
]


def charger_ref():
    reg = json.load(open(os.path.join(ICI, "referentiel", "regions.json"), encoding="utf-8"))["regions"]
    alias = json.load(open(os.path.join(ICI, "referentiel", "alias_lieux.json"), encoding="utf-8"))
    alias = {k: v for k, v in alias.items() if not k.startswith("_")}
    return reg, {p for v in reg.values() for p, _ in v}, alias


def passe_listing(cl, etat, run_id, provinces, alias, max_pages, classification, snapshots, couv_passe):
    """Une recherche parcourue page par page. Le nombre de pages vient du portail (nombrePageTop), jamais d'une
    constante. Si le total ou le nombre de pages change pendant le parcours, ou si les lignes lues ne couvrent pas
    exactement le total annoncé, la passe est marquée incomplète (PARTIEL). classification doit rester None."""
    vu_le = maintenant()
    h, _ = cl.rechercher(classification=classification)
    tp = total_et_pages(h)
    couv_passe.update({"classification": classification, "total_annonce": tp["total"], "debut": vu_le})
    if tp["total"] is None:
        raise ArretCollecte("nombre de résultats introuvable : page inattendue")
    if tp["total"] == 0:
        couv_passe.update({"pages_annoncees": 0, "pages_lues": [], "lignes_lues": 0, "ids_distincts": 0,
                           "complete": True, "stable": True, "fin": maintenant()})
        return set()
    h = cl.taille_500(h)
    tp = total_et_pages(h)
    pages_init, total_init = tp["pages"], tp["total"]
    couv_passe.update({"pages_annoncees": pages_init, "taille_page": tp["taille_page"], "total_annonce": total_init})
    if tp["taille_page"] != 500:
        raise ArretCollecte("passage à 500 lignes/page non confirmé par le portail")
    if not pages_init:
        raise ArretCollecte("nombre de pages introuvable : page inattendue")
    ids, pages_lues, nlignes, empreintes, vus = [], [], 0, set(), []
    n = 1
    while True:
        if tp["page"] != n:
            raise ArretCollecte(f"page demandée {n}, portail affiche {tp['page']}")
        vus.append({"page": n, "total": tp["total"], "pages": tp["pages"]})
        rows = lignes(h)
        page_ids = []
        for rw in rows:
            x = lire_ligne(rw, provinces, alias)
            i = etat.enregistrer_ligne(x, vu_le, run_id) if classification is None else make_id(x["o"], x["r"])
            page_ids.append(i)
        emp = tuple(page_ids)
        if emp in empreintes:
            raise ArretCollecte(f"page {n} identique à une page déjà lue : pagination non effective")
        empreintes.add(emp)
        ids += page_ids
        nlignes += len(rows)
        pages_lues.append({"page": n, "lignes": len(rows)})
        if snapshots:
            etat.snapshot(run_id, f"listing_{classification or 'tous'}_p{n:02d}", h)
        cible = max(pages_init, tp["pages"] or 0)  # si le portail annonce plus de pages, on lit quand même la suite
        if n >= cible or (max_pages and n >= max_pages):
            break
        n += 1
        h = cl.page(h, n)
        tp = total_et_pages(h)
    stable = all(v["total"] == total_init and v["pages"] == pages_init for v in vus)
    nd = len(set(ids))
    couv_passe.update({"pages_lues": pages_lues, "lignes_lues": nlignes, "ids_distincts": nd,
                       "pagination_verifiee": len(pages_lues) > 1, "fin": maintenant(),
                       "compteurs_vus_par_page": vus, "stable": stable})
    raisons = []
    if not stable:
        raisons.append("total ou nombre de pages modifié pendant le parcours")
    if len(pages_lues) != pages_init:
        raisons.append(f"{len(pages_lues)} pages lues sur {pages_init} annoncées")
    if nd != total_init or nlignes != total_init:
        raisons.append(f"{nd} identifiants distincts / {nlignes} lignes pour {total_init} annoncés")
    couv_passe["complete"] = not raisons
    couv_passe["raisons_incomplet"] = raisons
    return set(ids)


CHAMPS_CHANGEMENT = ("lim", "h", "ref", "obj", "proc", "cat")


def _norm(v):
    return " ".join(str(v).split())


def _change_apres_lecture(e, F, lu_le):
    """Vrai seulement si le listing a CHANGÉ après la lecture de la fiche (entrée `changements` postérieure à lu_le
    touchant un champ suivi) ET si la valeur actuelle du listing diffère encore de la fiche. Un simple écart permanent
    entre listing et fiche (format, troncature) ne relance donc pas la même fiche à chaque passage."""
    L = e.get("listing", {})
    champs = {k for c in e.get("changements", []) if (c.get("vu_le") or "") > lu_le for k in (c.get("diff") or {})}
    return any(k in champs and L.get(k) is not None and F.get(k) is not None and _norm(L[k]) != _norm(F[k])
               for k in CHAMPS_CHANGEMENT)


def choisir_fiches(etat, ids_run, n, relire_anciennes=True, aujourd_hui=None, age_min_h=24, maintenant_iso=None,
                   pause_echec_h=6, pause_echec_max_h=48):
    """Sélection tournante des fiches à lire, par PRIORITÉ STRICTE :
      1. changees : fiches dont le listing a changé (date/heure limite, objet, référence…) APRÈS leur dernière lecture,
         la lecture la plus ancienne d'abord ;
      2. nouvelles : jamais lues ; d'abord jamais tentées, puis les plus récemment apparues, puis la date limite la plus proche ;
      3. anciennes : lues (ou tentées) il y a au moins age_min_h heures, la plus ancienne activité d'abord.
    Le journal etat.selection (persisté dans selection.json) garde pour chaque id la date du dernier choix et les
    échecs : une fiche en échec est mise en pause (6 h, doublée à chaque échec, max 48 h) et ne bloque pas la tête de
    file ; une fiche choisie récemment ne revient pas avant age_min_h. Les consultations à date limite passée sont ignorées."""
    import datetime as _dt
    aujourd_hui = aujourd_hui or aujourd_hui_maroc()
    now = _dt.datetime.fromisoformat(maintenant_iso or maintenant())
    seuil = (now - _dt.timedelta(hours=age_min_h)).isoformat()
    sel = getattr(etat, "selection", {"items": {}})["items"]

    def en_pause(s):
        k = s.get("echecs_consecutifs") or 0
        if not k or not s.get("dernier_echec"):
            return False
        h = min(pause_echec_max_h, pause_echec_h * 2 ** (k - 1))
        return s["dernier_echec"] > (now - _dt.timedelta(hours=h)).isoformat()

    changees, nouvelles, anciennes, en_pause_n = [], [], [], 0
    for i in ids_run:
        e = etat.listing["items"][i]
        L = e.get("listing", {})
        if L.get("lim") and L["lim"] < aujourd_hui:
            continue
        s = sel.get(i, {})
        if en_pause(s):
            en_pause_n += 1
            continue
        f = etat.fiche(i)
        if f is None:
            nouvelles.append((1 if s.get("tentatives") else 0, -_ts(e.get("premier_vu") or ""), L.get("lim") or "9999", i))
            continue
        F = f.get("champs", {})
        activite = max(f["lu_le"], s.get("dernier_choix") or "")
        if _change_apres_lecture(e, F, f["lu_le"]):
            changees.append((f["lu_le"], i))
        elif relire_anciennes and activite <= seuil:
            anciennes.append((activite, i))
    changees.sort()
    nouvelles.sort()
    anciennes.sort()
    files = {"changees": [i for _, i in changees], "nouvelles": [t[-1] for t in nouvelles], "anciennes": [i for _, i in anciennes]}
    choix, reste = {}, n
    for k in ("changees", "nouvelles", "anciennes"):
        choix[k] = files[k][:max(reste, 0)]
        reste -= len(choix[k])
    ordre = choix["changees"] + choix["nouvelles"] + choix["anciennes"]
    stats = {"regle": "priorite_stricte changees>nouvelles>anciennes", "file_changees": len(files["changees"]),
             "file_nouvelles": len(files["nouvelles"]), "file_anciennes_eligibles": len(files["anciennes"]),
             "en_pause_apres_echec": en_pause_n,
             "choisies": {k: len(v) for k, v in choix.items()}, "categorie": {i: k for k, v in choix.items() for i in v}}
    return ordre, stats


def _ts(iso):
    import datetime as _dt
    try:
        return _dt.datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0


def lire_lots_fiche(client, org, ref, f, precedent, res):
    """Popup « Détail des lots » d'une fiche allotie, lu dans le même passage. Échec (hors 401/403) : la lecture précédente
    du popup est conservée telle quelle (avec sa propre date) ; aucune valeur n'est inventée."""
    try:
        r = client.get(PARAMS_LOTS(ref, org))
        h, _ = tronquer_contact(texte(r))
        out = lire_popup(h, org, ref, f.get("allot"))
        if out["statut"] in ("lu", "partiel"):
            res.setdefault("lots_lus", 0)
            res["lots_lus"] += 1
            return {"lu_le": maintenant(), "url": r.url[:300], "sha256_html_tronque": hashlib.sha256(h.encode()).hexdigest(), **out}
        res.setdefault("lots_echecs", []).append({"id": make_id(org, ref), "raison": out.get("raison")})
    except ArretCollecte as e:
        if "HTTP 401" in str(e) or "HTTP 403" in str(e):
            raise
        res.setdefault("lots_echecs", []).append({"id": make_id(org, ref), "raison": str(e)[:200]})
    except Exception as e:
        res.setdefault("lots_echecs", []).append({"id": make_id(org, ref), "raison": repr(e)[:200]})
    return precedent


def lire_fiches(client, etat, run_id, ids, snapshots, masquer):
    res = {"demandees": len(ids), "lues": [], "echecs": []}
    for i in ids:
        org, ref = split_id(i)
        try:
            r = client.get(PARAMS(ref, org))
            h, coupe = tronquer_contact(texte(r))
            f = lire_fiche(h, masquer=masquer)
            if not fiche_valide(f):
                res["echecs"].append({"id": i, "raison": "page sans référence/objet"})
                etat.noter_tentative(i, maintenant(), run_id, False, "page sans référence/objet")
                continue
            lu_le = maintenant()
            lots = lire_lots_fiche(client, org, ref, f, (etat.fiche(i) or {}).get("lots"), res) if f.get("allot") else None
            etat.enregistrer_fiche(i, f, lu_le, run_id, hashlib.sha256(h.encode()).hexdigest(), lots)
            etat.noter_tentative(i, lu_le, run_id, True)
            if snapshots:
                etat.snapshot(run_id, f"fiche_{org}_{ref}", h)
            res["lues"].append({"id": i, "lu_le": lu_le, "contact_coupe": coupe})
        except ArretCollecte:
            raise
        except Exception as e:  # une fiche illisible n'arrête pas les autres
            res["echecs"].append({"id": i, "raison": repr(e)[:200]})
            etat.noter_tentative(i, maintenant(), run_id, False, repr(e))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etat", default=os.path.join(ICI, "donnees"))
    ap.add_argument("--max-pages", type=int, default=0, help="0 = toutes les pages annoncées")
    ap.add_argument("--fiches", type=int, default=0, help="nombre max de fiches lues ce passage")
    ap.add_argument("--sans-relecture", action="store_true", help="ne relit jamais une fiche déjà lue sauf si le listing l'a contredite")
    ap.add_argument("--age-min-relecture-h", type=float, default=24.0)
    ap.add_argument("--delai", type=float, default=3.0)
    ap.add_argument("--sans-snapshots", action="store_true")
    ap.add_argument("--ne-pas-masquer-coordonnees", action="store_true")
    a = ap.parse_args()

    reg, provinces, alias = charger_ref()
    etat = Etat(a.etat)
    run_id = maintenant().replace(":", "").replace("+0000", "Z")
    journal = []
    client = ClientPMMP(delai_min=a.delai, journal=journal.append)
    couv = {"run_id": run_id, "debut": maintenant(), "mode": "manuel", "outil": "veille_kit maj_quotidienne",
            "parametres": vars(a), "listing": {}, "fiches": None}
    statut_err = None
    erreur_fiches = None
    try:
        cl = CollecteListing(client)
        cl.ouvrir()
        etat.sauver_organismes(cl.organismes, maintenant())
        couv["fenetre_recherche"] = cl.fenetre
        couv["types_annonce_portail"] = cl.types_annonce
        ids = passe_listing(cl, etat, run_id, provinces, alias, a.max_pages, None, not a.sans_snapshots, couv["listing"])
        couv["listing"]["total_annonce"] = couv["listing"].get("total_annonce")
        if couv["listing"].get("complete"):
            couv["listing"]["absents_marques"] = etat.marquer_absents_listing_complet(ids, run_id)
        etat.sauver_listing()
        if a.fiches:
            choix, stats = choisir_fiches(etat, ids, a.fiches, not a.sans_relecture, age_min_h=a.age_min_relecture_h)
            try:
                couv["fiches"] = lire_fiches(client, etat, run_id, choix, not a.sans_snapshots, not a.ne_pas_masquer_coordonnees)
            except ArretCollecte as e:
                couv["fiches"] = {"demandees": len(choix), "lues": [], "echecs": [], "arret": str(e)}
                erreur_fiches = f"ARRET fiches: {e}"
            couv["fiches"]["selection"] = stats
    except ArretCollecte as e:
        statut_err = f"ARRET: {e}"
    except Exception:
        statut_err = "ERREUR: " + traceback.format_exc()[-800:]
    finally:
        etat.sauver_listing()
        etat.sauver_selection()
        L = couv["listing"]
        complet = bool(L.get("complete")) and not statut_err
        if erreur_fiches:
            couv["erreur_fiches"] = erreur_fiches
        couv["statut"] = ("LISTING_COMPLET_ANNONCES_DE_CONSULTATION_FENETRE_PAR_DEFAUT" if complet else "PARTIEL")
        if statut_err:
            couv["erreur"] = statut_err
        couv["familles"] = {
            "couvertes": ["Annonce de consultation (tous types de procédure, toutes catégories), fenêtre par défaut du portail"
                          + ("" if complet else " — PARTIELLEMENT ce passage")],
            "types_annonce_portail_non_collectes": [t for v, t in couv.get("types_annonce_portail", []) if v != "3"],
            "hors_perimetre_du_kit": FAMILLES_HORS_PERIMETRE,
            "cls": ("non collectée : le filtre « classification » de la recherche avancée est ignoré par le portail "
                    "(constaté le 2026-10-02 : même total filtré et non filtré). construire_catalogue.py conserve l'ancienne "
                    "valeur pour les IDs connus et met null pour les nouveaux"),
        }
        couv["nb_requetes"] = client.nb_requetes
        couv["journal_http"] = journal
        couv["fin"] = maintenant()
        etat.enregistrer_couverture(run_id, couv)
        print(json.dumps({"run_id": run_id, "statut": couv["statut"], "total_annonce": L.get("total_annonce"),
                          "pages_annoncees": L.get("pages_annoncees"), "lignes_lues": L.get("lignes_lues"),
                          "ids_distincts": L.get("ids_distincts"), "raisons_incomplet": L.get("raisons_incomplet"),
                          "pages_lues": [p["page"] for p in L.get("pages_lues", [])],
                          "fiches_lues": len((couv["fiches"] or {}).get("lues", [])), "nb_requetes": client.nb_requetes,
                          "erreur": statut_err, "erreur_fiches": erreur_fiches}, ensure_ascii=False))
        if statut_err or erreur_fiches:
            sys.exit(1)


if __name__ == "__main__":
    main()

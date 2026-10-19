#!/usr/bin/env python3
"""Passage MANUEL de veille PMMP (catalogue des consultations en cours). Aucune planification ici.

Exemples :
  python maj_quotidienne.py --max-pages 1 --fiches 5            # petite collecte (essai)
  python maj_quotidienne.py --fiches 50                          # listing complet + 50 fiches
  python construire_catalogue.py                                 # puis construction hors ligne

Portail public uniquement : pas de login, pas de compte, pas de secret, pas de contournement.
Débit : >= 4 s (+ gigue) entre requêtes, une seule connexion ; arrêt immédiat sur 401/403 ou page inattendue.
"""
import argparse
import hashlib
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from veille.client import ArretCollecte, ClientPMMP, texte  # noqa: E402
from veille.etat import Etat, _ecrire_json, aujourd_hui_maroc, maintenant  # noqa: E402
from veille.pmmp_fiche import PARAMS, fiche_valide, lire_fiche, tronquer_contact  # noqa: E402
from veille.pmmp_lots import PARAMS_LOTS, lire_popup  # noqa: E402
from veille.pmmp_listing import (CATEGORIES, TAILLE_PAGE, CollecteListing, date_portail, lignes, lire_ligne,  # noqa: E402
                                 total_et_pages)
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


def planifier_partitions(etat, du, au, cible=400):
    """Intervalles de dates limites contigus et disjoints couvrant exactement [du, au], d'après la répartition des dates
    limites déjà connues (estimation seulement : chaque partition est recomptée sur le portail et redécoupée si besoin)."""
    import collections
    import datetime as _dt
    n = collections.Counter()
    for e in etat.listing["items"].values():
        lim = (e.get("listing") or {}).get("lim")
        try:
            d = _dt.date.fromisoformat(lim) if lim else None
        except ValueError:
            d = None
        if d and du <= d <= au:
            n[d] += 1
    plan, debut, acc, d, un = [], du, 0, du, _dt.timedelta(days=1)
    while d <= au:
        if acc and acc + n[d] > cible:
            plan.append((debut, d - un))
            debut, acc = d, 0
        acc += n[d]
        d += un
    plan.append((debut, au))
    return plan


def _lire_partition(cl, h, t, du, au, cat, provinces, alias):
    """Une partition de ≤ 500 résultats lue en UNE réponse (sans pagination). Renvoie (lignes {id: ligne}, total annoncé
    par la réponse lue, anomalies). Anomalie = ce qui empêche de prouver la partition (jamais corrigé en silence)."""
    total = t["total"]
    if total > 10:  # la page 1 par défaut ne montre que 10 lignes
        h = cl.taille_500(h)
        t2 = total_et_pages(h)
        if t2["taille_page"] != TAILLE_PAGE:
            raise ArretCollecte("passage à 500 lignes/page non confirmé par le portail")
        total = t2["total"]
    rows = [lire_ligne(rw, provinces, alias) for rw in lignes(h)]
    ids = [make_id(x["o"], x["r"]) for x in rows]
    anomalies = []
    if total is None:
        anomalies.append("compteur absent de la réponse lue")
    elif len(rows) != total:
        anomalies.append(f"{len(rows)} lignes pour {total} annoncés")
    if len(set(ids)) != len(ids):
        anomalies.append(f"{len(ids) - len(set(ids))} doublon(s) dans la partition")
    hors = [i for i, x in zip(ids, rows) if not x["lim"] or not (du.isoformat() <= x["lim"] <= au.isoformat())]
    if hors:
        anomalies.append(f"{len(hors)} ligne(s) hors bornes de date limite : {hors[:5]}")
    if cat and any(x["cat"] != CATEGORIES[cat] for x in rows):
        anomalies.append("ligne(s) d'une autre catégorie que le filtre")
    return dict(zip(ids, rows)), total, anomalies, h


def _cle(du, au, cat=None, proc=None):
    return f"{du.isoformat()}..{au.isoformat()}" + (f"#{CATEGORIES[cat]}" if cat else "") + (f"#proc{proc}" if proc else "")


def lectures_precedentes(etat, maintenant_iso=None, age_max_h=3.0):
    """Dernière lecture de chaque partition par le passage partitionné précédent, reconstruite EXACTEMENT depuis l'état :
    une partition lue à l'instant lu_le par le passage run contient les identifiants dont la dernière observation est
    (run, lu_le) et dont la date limite (et la catégorie) relèvent de ses bornes. Un identifiant revu ensuite dans une autre partition (date limite modifiée) n'y figure plus : la partition
    sera alors relue. Plus vieille que age_max_h : ignorée (aucune confirmation sur une lecture ancienne)."""
    import datetime as _dt
    now = _dt.datetime.fromisoformat(maintenant_iso or maintenant())
    for nom in reversed(etat.couvertures()):
        with open(os.path.join(etat.d, "couverture", nom), encoding="utf-8") as fh:
            c = json.load(fh)
        L = c.get("listing") or {}
        if not str(L.get("mode", "")).startswith("partitions"):
            continue
        pages = [p for p in L.get("pages_lues") or [] if p.get("lu_le") and p.get("partition")]
        if not pages:
            return {}
        par_instant = {}
        for i, e in etat.listing["items"].items():
            if e.get("dernier_run") == c["run_id"]:
                par_instant.setdefault(e.get("dernier_vu_listing"), []).append((i, e.get("listing") or {}))
        out = {}
        for p in pages:
            morceaux = p["partition"].split("#")
            if any(m.startswith("proc") for m in morceaux[1:]):
                continue  # sous-partition par procédure : libellé du listing ≠ code du filtre, relue dans le passage
            if (now - _dt.datetime.fromisoformat(p["lu_le"])).total_seconds() > age_max_h * 3600:
                continue
            a, b = morceaux[0].split("..")
            cat = morceaux[1] if len(morceaux) > 1 else None
            # même instant ET bornes de la partition (deux partitions lues dans la même seconde restent distinctes)
            ids = {i for i, L in par_instant.get(p["lu_le"], []) if L.get("lim") and a <= L["lim"] <= b and (cat is None or L.get("cat") == cat)}
            out[p["partition"]] = {"ids": ids, "total": p.get("total"), "lu_le": p["lu_le"], "run": c["run_id"]}
        return out
    return {}


def _plan_depuis_precedent(prec, du, au):
    """Bornes des partitions précédentes si elles couvrent exactement [du, au] (contiguës, sans trou) ; sinon None."""
    import datetime as _dt
    bornes = []
    for cle in prec:
        if "#" in cle:
            return None  # sous-partitions : on redécoupe
        a, b = cle.split("..")
        bornes.append((_dt.date.fromisoformat(a), _dt.date.fromisoformat(b)))
    bornes.sort()
    if not bornes or bornes[0][0] != du or bornes[-1][1] != au:
        return None
    if any(b + _dt.timedelta(days=1) != a for (_, b), (a, _) in zip(bornes, bornes[1:])):
        return None
    return bornes


def passe_partitionnee(cl, etat, run_id, provinces, alias, couv_passe, snapshots=False, cible=400, max_iterations=8,
                       precedent=None):
    """Listing COMPLET vérifiable malgré la pagination instable et un portail qui bouge pendant la lecture.

    Fenêtre FIXÉE une fois pour tout le passage : les bornes « date limite entre / et » du formulaire officiel lu à
    l'ouverture (cl.fenetre) sont envoyées explicitement à CHAQUE requête, total global compris.
    Partitions officielles disjointes : date limite par intervalle de jours (bornes inclusives vérifiées ligne à ligne),
    puis catégorie, puis type de procédure pour un jour trop chargé. Une partition n'est acceptée que lue en UNE réponse
    de ≤ 500 lignes ; aucune pagination n'est jamais retenue ; une partition indivisible > 500 rend le passage PARTIEL.
    Preuve d'identité par partition : une partition est CONFIRMÉE quand deux lectures consécutives donnent exactement les
    mêmes identifiants et le même total (la première peut être la dernière lecture du passage partitionné précédent, de
    moins de 3 h). Seules les partitions non confirmées sont relues (au plus max_iterations fois).
    Contrôle final, encadré par deux totaux globaux : chaque partition est RECOMPTÉE (page de 10 lignes) ; une partition
    dont le compte diffère de son total confirmé perd sa confirmation et est relue. Complet SEULEMENT si toutes les
    partitions sont confirmées, tous les comptes égalent les totaux confirmés (aucun écart toléré), somme des partitions =
    identifiants distincts = total global du DÉBUT du contrôle (instant de référence ; la variation du total ensuite est
    enregistrée à part et relève du passage suivant), aucun identifiant dans deux partitions,
    aucune anomalie, et, pour chaque jour subdivisé, somme des sous-partitions = total du jour. Sinon PARTIEL avec les
    raisons (aucune absence marquée, dernier catalogue valide conservé).
    Limite assumée : un ajout ET une suppression dans une même partition après sa dernière lecture (compte inchangé)
    ne sont vus qu'au passage suivant, comme pour tout instantané non atomique."""
    import datetime as _dt
    import time as _time
    debut = maintenant()
    du, au = date_portail(cl.fenetre["dateMiseEnLigneStart"]), date_portail(cl.fenetre["dateMiseEnLigneEnd"])
    procedures = list(getattr(cl, "procedures", []) or [])
    totaux = []
    prec = precedent if precedent is not None else lectures_precedentes(etat)

    def total_global(moment):
        _, t = cl.partition(du, au)
        if t["total"] is None:
            raise ArretCollecte("nombre de résultats introuvable : page inattendue")
        totaux.append({"moment": moment, "quand": maintenant(), "total": t["total"]})
        return t["total"]

    couv_passe.update({"mode": "partitions_date_limite_confirmees", "debut": debut, "classification": None,
                       "fenetre_date_limite": [du.isoformat(), au.isoformat()],
                       "fenetre_fixee_a_l_ouverture": {k: cl.fenetre.get(k) for k in (
                           "dateMiseEnLigneStart", "dateMiseEnLigneEnd", "dateMiseEnLigneCalculeStart", "dateMiseEnLigneCalculeEnd")}})
    nreq0, oct0, t0 = cl.c.nb_requetes, getattr(cl.c, "octets_recus", 0), _time.monotonic()
    feuilles, parents, subdivisions, controles, phase = {}, {}, [], [], ["decoupage"]
    etat_d = getattr(etat, "d", None)

    def progres():
        """Point de reprise lisible (écriture atomique) : avancement réel du passage en cours, pour le suivi."""
        if not etat_d:
            return
        _ecrire_json(os.path.join(etat_d, "progression_listing.json"), {
            "run_id": run_id, "phase": phase[0], "maj": maintenant(), "depuis_s": round(_time.monotonic() - t0),
            "partitions": len(feuilles), "confirmees": sum(1 for f in feuilles.values() if f.get("confirmee")),
            "lectures": sum(f.get("lectures", 0) for f in feuilles.values()),
            "requetes": cl.c.nb_requetes - nreq0, "octets_recus": getattr(cl.c, "octets_recus", 0) - oct0,
            "totaux_globaux": totaux, "controles": [{k: r[k] for k in ("controle", "total_avant", "total_apres", "raisons")} for r in controles]})

    def lire(f, h, t):
        if t["total"] > TAILLE_PAGE:
            f.update({"total": t["total"], "ids_prec": f.get("ids"), "ids": set(), "confirmee": False,
                      "anomalies": [f"{t['total']} résultats > {TAILLE_PAGE} : partition indivisible, jamais lue par pagination"]})
            return
        rows, total, anom, hl = _lire_partition(cl, h, t, f["du"], f["au"], f["cat"], provinces, alias)
        lu_le = maintenant()
        for x in rows.values():
            etat.enregistrer_ligne(x, lu_le, run_id)
        if snapshots and hl:
            etat.snapshot(run_id, "partition_" + f["cle"].replace("#", "_").replace("..", "_"), hl)
        avant = {"ids": f.get("ids"), "total": f.get("total"), "lu_le": f.get("lu_le")}
        ids = set(rows)
        conf = (not anom and avant["ids"] is not None and avant["ids"] == ids and avant["total"] == total == len(ids))
        f.update({"ids": ids, "total": total, "lu_le": lu_le, "anomalies": anom, "lectures": f.get("lectures", 0) + 1,
                  "confirmee": conf, "confirmation": {"lectures": [avant["lu_le"], lu_le], "identiques": True} if conf else None})
        if anom:  # trace de toute anomalie, même résolue par une relecture
            f.setdefault("anomalies_vues", []).append({"partition": f["cle"], "lecture": f["lectures"], "anomalies": anom})
        if avant["ids"] is not None and not conf:
            f["changements_vus"] = f.get("changements_vus", 0) + 1
        progres()

    try:
        t_initial = total_global("initial")
        couv_passe["total_annonce"] = t_initial
        # 1. découpage (bornes du passage précédent si elles couvrent exactement la fenêtre) et première lecture
        plan = _plan_depuis_precedent(prec, du, au) or planifier_partitions(etat, du, au, cible)
        file = [(a, b, None, None) for a, b in plan]
        while file:
            a, b, cat, proc = file.pop(0)
            h, t = cl.partition(a, b, cat, proc)
            if t["total"] is None:
                raise ArretCollecte(f"compteur introuvable pour la partition {_cle(a, b, cat, proc)}")
            sous = None
            if t["total"] > TAILLE_PAGE:
                if b > a:
                    m = a + (b - a) // 2
                    file[:0] = [(a, m, cat, proc), (m + _dt.timedelta(days=1), b, cat, proc)]
                    continue
                if cat is None:
                    sous = [(a, a, c, None) for c in CATEGORIES]
                elif proc is None and procedures:
                    sous = [(a, a, cat, p) for p in procedures]
            if sous:
                cle = _cle(a, b, cat, proc)
                parents[cle] = {"du": a, "au": b, "cat": cat, "proc": proc, "total": t["total"], "enfants": [_cle(*s) for s in sous]}
                subdivisions.append({"partition": cle, "total": t["total"], "par": "categorie" if cat is None else "procedure"})
                file[:0] = sous
                continue
            cle = _cle(a, b, cat, proc)
            p0 = prec.get(cle) or {}
            feuilles[cle] = {"cle": cle, "du": a, "au": b, "cat": cat, "proc": proc, "ids": p0.get("ids"), "total": p0.get("total"),
                             "lu_le": p0.get("lu_le"), "lecture_precedente": p0.get("run")}
            lire(feuilles[cle], h, t)

        # 2. relecture des seules partitions non confirmées, puis contrôle final encadré
        phase[0] = "confirmation"
        dernier = None
        for it in range(1, max_iterations + 1):
            for cle in sorted(c for c, f in feuilles.items() if not f["confirmee"]):
                f = feuilles[cle]
                h, t = cl.partition(f["du"], f["au"], f["cat"], f["proc"])
                if t["total"] is None:
                    raise ArretCollecte(f"compteur introuvable pour la partition {cle}")
                lire(f, h, t)
            if not all(f["confirmee"] for f in feuilles.values()) and it < max_iterations:
                continue
            phase[0] = f"controle_{it}"
            t_avant = total_global(f"avant_controle_{it}")
            toutes_confirmees_avant = all(f["confirmee"] for f in feuilles.values())
            comptes = {}
            for cle, f in sorted(feuilles.items()):
                _, t = cl.partition(f["du"], f["au"], f["cat"], f["proc"])
                comptes[cle] = t["total"]
                if t["total"] != f["total"]:
                    f["confirmee"] = False
            for cle, p in parents.items():
                _, t = cl.partition(p["du"], p["au"], p["cat"], p["proc"])
                p["total_controle"] = t["total"]
            t_apres = total_global(f"apres_controle_{it}")
            occ = {}
            for cle, f in feuilles.items():
                for i in f["ids"]:
                    occ.setdefault(i, []).append(cle)
            doublons = sorted(i for i, c in occ.items() if len(c) > 1)
            somme = sum(f["total"] or 0 for f in feuilles.values())
            non_conf = sorted(c for c, f in feuilles.items() if not f["confirmee"])
            raisons = []
            # instant de référence = DÉBUT du contrôle, seul instantané prouvable : chaque partition, confirmée par deux lectures
            # identiques avant ce début, est recomptée après lui avec un compte ÉGAL à son total confirmé ; son état au début
            # est donc sa lecture confirmée (sauf ajout + retrait dans la même partition, limite assumée) ; somme = total du
            # début prouve que les partitions couvrent tout. Aucun écart de compte n'est toléré (une hausse globale ne date pas
            # un ajout : le portail ne publie que le jour de mise en ligne) ; la variation du total après le début est
            # seulement enregistrée à part (publications_apres_reference), jamais incluse ni prise pour preuve.
            ecarts = {c: (comptes[c] or 0) - (feuilles[c]["total"] or 0) for c in comptes if comptes[c] != feuilles[c]["total"]}
            reference = "debut_controle" if (somme == t_avant and not ecarts and toutes_confirmees_avant) else None
            if somme != t_avant:
                raisons.append(f"somme des partitions confirmées {somme} ≠ total global du début du contrôle {t_avant}")
            if len(occ) != somme:
                raisons.append(f"{len(occ)} identifiants distincts pour {somme} lignes des partitions")
            if doublons:
                raisons.append(f"{len(doublons)} identifiant(s) dans deux partitions (date limite modifiée) : " + ", ".join(doublons[:5]))
            if non_conf:
                raisons.append(f"{len(non_conf)} partition(s) non confirmée(s) (deux lectures différentes, ou compte modifié au "
                               "contrôle) : " + ", ".join(non_conf[:6]))
            for cle, p in parents.items():
                s = sum(feuilles[e]["total"] or 0 for e in p["enfants"] if e in feuilles) + sum(
                    parents[e].get("total_controle") or 0 for e in p["enfants"] if e in parents)
                if s != p["total_controle"]:
                    raisons.append(f"sous-partitions de {cle} : {s} ≠ {p['total_controle']} (valeur de catégorie/procédure inconnue ou hors liste)")
            for cle, f in sorted(feuilles.items()):
                if f["anomalies"]:
                    raisons.append(f"partition {cle} : " + " ; ".join(f["anomalies"]))
            dernier = {"controle": it, "total_avant": t_avant, "total_apres": t_apres, "somme_partitions": somme,
                       "ecarts_de_compte": ecarts, "instant_reference": reference, "total_reference": t_avant if reference else None,
                       "publications_apres_reference": t_apres - t_avant,
                       "ids_distincts": len(occ), "comptes_differents": sorted(c for c in comptes if comptes[c] != feuilles[c]["total"]),
                       "non_confirmees": non_conf, "doublons_inter_partitions": doublons[:20], "raisons": raisons}
            controles.append(dernier)
            progres()
            if not raisons:
                break
            # doublon inter-partitions : les partitions concernées sont relues (la date limite a changé entre deux lectures)
            for i in doublons:
                for c in occ[i]:
                    feuilles[c]["confirmee"] = False
    except ArretCollecte as e:
        # interruption (réseau, 401/403, budget de temps) : ce qui a été lu est décrit, rien n'est conclu
        lues = sorted((f for f in feuilles.values() if f.get("lu_le") and f.get("lectures")), key=lambda f: (f["du"], f["cat"] or "", f["proc"] or ""))
        couv_passe.update({"complete": False, "interrompu": str(e)[:300], "fin": maintenant(),
                           "pages_annoncees": None, "ids_distincts": None, "totaux_globaux": totaux,
                           # lectures réelles faites avant l'arrêt : amorce du passage suivant (jamais une preuve de complétude)
                           "pages_lues": [{"page": k + 1, "partition": f["cle"], "lignes": len(f["ids"] or ()), "total": f["total"],
                                           "lu_le": f["lu_le"], "lectures": f["lectures"], "confirmee": f.get("confirmee")}
                                          for k, f in enumerate(lues)],
                           "partitions_lues_avant_arret": len(feuilles), "controles": controles,
                           "requetes_listing": cl.c.nb_requetes - nreq0, "octets_recus": getattr(cl.c, "octets_recus", 0) - oct0,
                           "raisons_incomplet": [f"passage interrompu : {str(e)[:200]}"]})
        phase[0] = "interrompu"
        progres()
        raise
    phase[0] = "fini"
    progres()
    if dernier is None:
        dernier = {"total_avant": None, "total_apres": None, "raisons": ["aucun contrôle final (itérations épuisées)"]}
    ids = set().union(*[f["ids"] for f in feuilles.values()]) if feuilles else set()
    ordre = sorted(feuilles.values(), key=lambda f: (f["du"], f["cat"] or "", f["proc"] or ""))
    couv_passe.update({
        "total_annonce": dernier.get("total_reference") or dernier["total_apres"], "pages_annoncees": len(feuilles), "taille_page": TAILLE_PAGE,
        "instant_reference": dernier.get("instant_reference"), "total_reference": dernier.get("total_reference"),
        "total_global_apres_controle": dernier["total_apres"], "publications_apres_reference": dernier.get("publications_apres_reference"),
        "pages_lues": [{"page": k + 1, "partition": f["cle"], "lignes": len(f["ids"]), "total": f["total"], "lu_le": f.get("lu_le"),
                        "lectures": f.get("lectures", 0), "confirmee": f["confirmee"], "confirmation": f.get("confirmation"),
                        "lecture_precedente": f.get("lecture_precedente"), "changements_vus": f.get("changements_vus", 0)}
                       for k, f in enumerate(ordre)],
        "lignes_lues": sum(len(f["ids"]) for f in feuilles.values()), "ids_distincts": len(ids),
        "subdivisions": subdivisions, "totaux_globaux": totaux, "controles": controles,
        "requetes_listing": cl.c.nb_requetes - nreq0, "octets_recus": getattr(cl.c, "octets_recus", 0) - oct0,
        "duree_listing_s": round(_time.monotonic() - t0), "stable": dernier["total_avant"] == dernier["total_apres"],
        "anomalies_vues": [a for f in ordre for a in f.get("anomalies_vues", [])],
        "complete": not dernier["raisons"], "raisons_incomplet": dernier["raisons"], "fin": maintenant(),
        "preuve": "fenêtre fixée à l'ouverture ; partitions disjointes (date limite, catégorie, procédure) lues chacune en une "
                  "réponse ≤ 500 ; chaque partition confirmée par deux lectures consécutives identiques ; contrôle final : "
                  "recomptage de chaque partition après le début du contrôle (compte = total confirmé, aucun écart), somme = distincts = "
                  "total global du début du contrôle (instant de référence). Limite : un "
                  "ajout+suppression dans une même partition après sa dernière lecture n'est vu qu'au passage suivant"})
    return ids


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
                   pause_echec_h=6, pause_echec_max_h=48, nouvelles_max=0, pieces_max=0):
    """Sélection tournante des fiches à lire, par PRIORITÉ STRICTE :
      1. changees : fiches dont le listing a changé (date/heure limite, objet, référence…) APRÈS leur dernière lecture,
         la lecture la plus ancienne d'abord ;
      2. nouvelles : jamais lues ; d'abord jamais tentées, puis les plus récemment apparues, puis la date limite la plus proche ;
      3. anciennes : lues (ou tentées) il y a au moins age_min_h heures ; d'abord celles dont les pièces publiées ne sont
         pas encore lues (reliquat des lectures antérieures au lecteur v3), puis la plus ancienne activité d'abord.
    Le journal etat.selection (persisté dans selection.json) garde pour chaque id la date du dernier choix et les
    échecs : une fiche en échec est mise en pause (6 h, doublée à chaque échec, max 48 h) et ne bloque pas la tête de
    file ; une fiche choisie récemment ne revient pas avant age_min_h. Les consultations à date limite passée sont ignorées.
    nouvelles_max > 0 : les nouvelles sans fiche passent AVANT toute relecture (au plus nouvelles_max), puis les n places
    vont aux changées puis aux anciennes : une annonce publiée n'attend pas sa fiche derrière des relectures (constat réel
    du 19/10 : 30 puis 124 nouvelles en attente pour 1 place par passage). Plafond et budget de temps sont des limites :
    le reliquat (au-delà du plafond, ou non lu faute de temps) est compté et reste en tête de file au passage suivant."""
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
            # reliquat borné : parmi les relectures, d'abord les fiches dont les pièces publiées ne sont pas encore lues
            anciennes.append((0 if "docs" not in (F.get("blocs_lus") or []) else 1, activite, i))
    changees.sort()
    nouvelles.sort()
    anciennes.sort()
    files = {"changees": [i for _, i in changees], "nouvelles": [t[-1] for t in nouvelles], "anciennes": [t[-1] for t in anciennes]}
    choix, reste = {}, n
    for k in ("changees", "nouvelles", "anciennes"):
        choix[k] = files[k][:max(reste, 0)]
        reste -= len(choix[k])
    if nouvelles_max > 0:
        # nouvelles sans fiche d'abord (plafond honnête), puis les n places pour les relectures changées / anciennes ;
        # pieces_max > 0 : file dédiée « pièces publiées pas encore lues » (lectures antérieures au lecteur v3), APRÈS les
        # nouvelles et les changées, AVANT les relectures ordinaires ; le budget de temps arrête la file (reliquat mesuré)
        choix["nouvelles"] = files["nouvelles"][:nouvelles_max]
        choix["changees"] = files["changees"][:n]
        pieces = [t[-1] for t in anciennes if t[0] == 0]
        choix["pieces"] = pieces[:pieces_max] if pieces_max > 0 else []
        pris = set(choix["pieces"])
        choix["anciennes"] = [i for i in files["anciennes"] if i not in pris][:max(n - len(choix["changees"]), 0)]
        ordre = choix["nouvelles"] + choix["changees"] + choix["pieces"] + choix["anciennes"]
    else:
        ordre = choix["changees"] + choix["nouvelles"] + choix["anciennes"]
    stats = {"regle": (f"nouvelles (max {nouvelles_max}) > changees > pieces non lues (max {pieces_max}) > anciennes (n={n})" if nouvelles_max and pieces_max
                       else f"nouvelles (max {nouvelles_max}) > changees > anciennes (n={n})" if nouvelles_max
                       else "priorite_stricte changees>nouvelles>anciennes"),
             "reliquat_nouvelles_plafond": max(len(files["nouvelles"]) - len(choix["nouvelles"]), 0),
             "file_changees": len(files["changees"]),
             "file_nouvelles": len(files["nouvelles"]), "file_anciennes_eligibles": len(files["anciennes"]),
             "en_pause_apres_echec": en_pause_n,
             "reliquat_pieces_non_lues_eligibles": sum(1 for t in anciennes if t[0] == 0),
             "reliquat_pieces_apres_choix": max(sum(1 for t in anciennes if t[0] == 0) - len(choix.get("pieces") or []), 0),
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
        except ArretCollecte as e:
            if "HTTP 401" in str(e) or "HTTP 403" in str(e):
                raise  # refus du portail : arrêt immédiat de tout le passage
            res["arret"] = str(e)[:300]  # budget / réseau : les fiches déjà lues restent comptées (elles sont enregistrées)
            return res
        except Exception as e:  # une fiche illisible n'arrête pas les autres
            res["echecs"].append({"id": i, "raison": repr(e)[:200]})
            etat.noter_tentative(i, maintenant(), run_id, False, repr(e))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etat", default=os.path.join(ICI, "donnees"))
    ap.add_argument("--max-pages", type=int, default=0, help="0 = toutes les pages annoncées")
    ap.add_argument("--fiches", type=int, default=0, help="nombre max de fiches lues ce passage")
    ap.add_argument("--fiches-nouvelles-max", type=int, default=150,
                    help="en plus de --fiches : toutes les annonces nouvelles sans fiche (au plus N) sont lues ce passage, dans le budget "
                         "de temps (0 = comportement d'avant : les nouvelles n'ont que les places restantes de --fiches)")
    ap.add_argument("--sans-relecture", action="store_true", help="ne relit jamais une fiche déjà lue sauf si le listing l'a contredite")
    ap.add_argument("--age-min-relecture-h", type=float, default=24.0)
    ap.add_argument("--delai", type=float, default=4.0, help="secondes entre requêtes ; jamais moins de 4 (rythme convenu)")
    ap.add_argument("--fiches-pieces-max", type=int, default=60,
                    help="après les nouvelles et les changées : au plus N fiches dont les pièces publiées ne sont pas encore lues "
                         "(reprise bornée du reliquat, dans le budget de temps ; 0 = désactivé)")
    ap.add_argument("--budget-s", type=float, default=1200.0,
                    help="durée maximale du passage (listing + fiches) ; au-delà aucune requête n'est envoyée et le passage "
                         "se termine PARTIEL en écrivant sa couverture (la tâche horaire coupe à 1500 s)")
    ap.add_argument("--listing-pagine", action="store_true",
                    help="ancien parcours page par page (sans partitions) : sensible à la pagination instable du portail")
    ap.add_argument("--sans-snapshots", action="store_true")
    ap.add_argument("--ne-pas-masquer-coordonnees", action="store_true")
    a = ap.parse_args()

    reg, provinces, alias = charger_ref()
    etat = Etat(a.etat)
    run_id = maintenant().replace(":", "").replace("+0000", "Z")
    journal = []
    client = ClientPMMP(delai_min=max(a.delai, 4.0), journal=journal.append)
    import time as _time
    t_depart = _time.monotonic()
    reserve_fiches = min(240.0, a.budget_s / 5) if (a.budget_s and a.fiches) else 0.0
    if a.budget_s:
        client.echeance = t_depart + a.budget_s - reserve_fiches  # le listing laisse du temps aux fiches
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
        if a.listing_pagine or a.max_pages:
            ids = passe_listing(cl, etat, run_id, provinces, alias, a.max_pages, None, not a.sans_snapshots, couv["listing"])
        else:
            try:
                ids = passe_partitionnee(cl, etat, run_id, provinces, alias, couv["listing"], not a.sans_snapshots)
            except ArretCollecte as e:
                if "budget de temps" not in str(e):
                    raise  # 401/403, réseau : arrêt de tout le passage
                # budget du listing atteint : passage PARTIEL (rien n'est conclu), mais les fiches gardent leur réserve
                statut_err = f"ARRET: {e}"
                ids = {i for i, x in etat.listing["items"].items() if x.get("dernier_run") == run_id}
        couv["listing"]["total_annonce"] = couv["listing"].get("total_annonce")
        if couv["listing"].get("complete"):
            couv["listing"]["absents_marques"] = etat.marquer_absents_listing_complet(ids, run_id)
        etat.sauver_listing()
        if a.budget_s:
            client.echeance = t_depart + a.budget_s  # fiches : jusqu'au budget complet
        if a.fiches:
            choix, stats = choisir_fiches(etat, ids, a.fiches, not a.sans_relecture, age_min_h=a.age_min_relecture_h,
                                          nouvelles_max=a.fiches_nouvelles_max, pieces_max=a.fiches_pieces_max)
            couv["fiches"] = lire_fiches(client, etat, run_id, choix, not a.sans_snapshots, not a.ne_pas_masquer_coordonnees)
            faites = {x["id"] for x in couv["fiches"]["lues"]} | {x["id"] for x in couv["fiches"]["echecs"]}
            couv["fiches"]["reliquat"] = {  # mesurable : ce qui reste pour le passage suivant (aucune fiche marquée tentée)
                "nouvelles_non_lues_budget": sum(1 for i in choix if i not in faites and stats["categorie"].get(i) == "nouvelles"),
                "relectures_non_faites_budget": sum(1 for i in choix if i not in faites and stats["categorie"].get(i) != "nouvelles"),
                "nouvelles_au_dela_du_plafond": stats["reliquat_nouvelles_plafond"]}
            if couv["fiches"].get("arret"):
                erreur_fiches = f"ARRET fiches: {couv['fiches']['arret']}"
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
        couv["octets_recus"] = client.octets_recus
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

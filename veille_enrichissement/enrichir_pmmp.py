#!/usr/bin/env python3
"""Enrichissement PMMP du catalogue EAIOS : classification officielle Etat / CL / EEP et mode de passation.

Produit catalogue_pmmp_enrichi.json, fichier JOINT au catalogue (clé pmmp:<org>:<ref>, ou code d'entité publique) :
le schéma à 31 champs de catalogue.json et l'ingestion horaire ne changent pas ; ce fichier n'est pas touché par
l'ingestion horaire (qui ne republie que les quatre fichiers catalogue*.json).

Sources (toutes publiques, sans compte) — vérifiées le 2026-10-18 sur
https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons= :
  * Classification « Etat/CL/EEP » : liste ctl0$CONTENU_PAGE$AdvancedSearch$classification (1 Etat, 2 Collectivité
    locale, 3 Etablissement public). C'est un TActiveDropDownList PRADO : son rappel (PRADO_CALLBACK_TARGET) renvoie la
    liste officielle des entités publiques (organismesNames) de cette classification. Contrôle : la recherche avancée
    filtrée (type_rechercheEntite=exact + classification) renvoie des totaux qui partitionnent le total non filtré, et
    chaque annonce renvoyée appartient à une entité de la même classification.
    -> La classification est celle de l'ENTITÉ PUBLIQUE (organisme PMMP). Une annonce hérite de la classification de son
       entité (rattachement unique : orgAcronyme de l'annonce). Entité absente ou présente dans plusieurs listes = inconnue.
       Aucune déduction par le nom (Commune, SA, Ministère…), aucune reprise de l'ancien champ cls.
  * Mode de passation : élément modePassation de la fiche publique (EntrepriseDetailConsultation), affiché après la
    procédure (« Procédure : Appel d'offres ouvert | Sur offre de prix »). Lu par le collecteur (fiches.json, champ
    mode_passation, lu_le réel) ou par un complément borné (même analyseur, contacts tronqués avant analyse).
    Distinct de la procédure. NB : dans le formulaire de recherche, la liste libellée « Mode de passation »
    (procedureType) contient les procédures : ses codes sont relevés ici comme identifiants PMMP des procédures.

Règles : une valeur relevée n'est jamais supprimée par une construction ultérieure (la plus récente lecture gagne) ;
une annonce sans lecture reste inconnue (jamais « Sur offre de prix » par défaut) ; la jointure n'est utilisée par la page
que si la référence lue concorde avec celle du catalogue. Idempotent : mêmes entrées -> mêmes octets.
"""
import argparse
import datetime
import glob
import hashlib
import html as _html
import json
import os
import re
import sys

URL_RECHERCHE = "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons="
P_RECH = "ctl0$CONTENU_PAGE$AdvancedSearch$"
CLASSIFICATIONS = {"1": "Etat", "2": "Collectivité locale", "3": "Etablissement public"}
VERSION = 1


def maintenant():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def _esp(s):
    return re.sub(r"\s+", " ", _html.unescape(s or "")).strip()


def options_select(h, nom):
    """Options (valeur, libellé brut normalisé en espaces) d'un <select name="...$nom">, ou None si absent."""
    m = re.search(r'<select[^>]*name="[^"]*\$' + re.escape(nom) + r'"[^>]*>(.*?)</select>', h, re.S)
    if not m:
        return None
    return [(v, _esp(re.sub(r"<[^>]+>", "", t))) for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', m.group(1), re.S)]


def classification_selectionnee(h):
    o = re.search(r'<select[^>]*\$classification"[^>]*>(.*?)</select>', h, re.S)
    m = re.search(r'<option selected="selected" value="(\d)"', o.group(1)) if o else None
    return m.group(1) if m else None


def entites_par_classification(rappels):
    """rappels = {code: html du rappel PRADO} pour '0' (toutes) et '1','2','3'.
    Renvoie (par_entite, controle). par_entite = {org: {"code","libelle","entite"}} ; une entité présente dans plusieurs
    listes ou dans aucune est exclue (inconnue) et listée dans controle."""
    listes, libelles = {}, {}
    for code, h in rappels.items():
        if classification_selectionnee(h) != code:
            raise ValueError(f"rappel {code} : la classification renvoyée ne correspond pas")
        opts = options_select(h, "organismesNames")
        if opts is None:
            raise ValueError(f"rappel {code} : liste des entités publiques absente")
        listes[code] = {v for v, _ in opts if v != "0"}
        libelles.update({v: t for v, t in opts if v != "0"})
    toutes = listes.get("0")
    vu = {}
    for code in ("1", "2", "3"):
        for org in listes.get(code, ()):
            vu.setdefault(org, []).append(code)
    ambigues = sorted(o for o, c in vu.items() if len(c) > 1)
    sans = sorted((toutes or set()) - set(vu))
    par_entite = {o: {"code": c[0], "libelle": CLASSIFICATIONS[c[0]], "entite": libelles.get(o)}
                  for o, c in sorted(vu.items()) if len(c) == 1}
    controle = {"entites_toutes": len(toutes or ()), "par_classification": {c: len(listes.get(c, ())) for c in ("1", "2", "3")},
                "ambigues": ambigues, "sans_classification": sans,
                "partition_exacte": bool(toutes) and not ambigues and not sans and set(vu) == toutes}
    return par_entite, controle


def procedures_formulaire(h):
    opts = options_select(h, "procedureType") or []
    return {t: v for v, t in opts if v != "0"}


# ---------------------------------------------------------------- relevé en ligne (borné)
def relever(kit, sortie, delai=4.0):
    """Relevé officiel borné : 1 GET + 4 rappels + 3 recherches filtrées (+ pages 500 pour CL et EEP). Utilise le client
    du kit collecteur (débit, arrêt 401/403). Écrit releve_classification.json et les réponses brutes utiles."""
    sys.path.insert(0, kit)
    from veille.client import ClientPMMP  # noqa
    from veille.html_outils import formulaire  # noqa
    from veille.pmmp_listing import CollecteListing, lignes, total_et_pages  # noqa
    import time
    os.makedirs(sortie, exist_ok=True)
    journal = []
    c = ClientPMMP(delai_min=delai, journal=journal.append)
    debut = maintenant()
    L = CollecteListing(c)
    h0 = L.ouvrir()
    rappels = {}
    for code in ("0", "1", "2", "3"):
        d = formulaire(h0)
        d[P_RECH + "type_rechercheEntite"] = "exact"
        d[P_RECH + "classification"] = code
        d["PRADO_CALLBACK_TARGET"] = P_RECH + "classification"
        d["PRADO_CALLBACK_PARAMETER"] = "null"
        c._attendre()
        r = c.s.post(L.url, data=d, timeout=c.timeout)
        c._dernier = time.monotonic()
        c.nb_requetes += 1
        journal.append({"m": "POST rappel classification=" + code, "url": r.url[:200], "code": r.status_code, "octets": len(r.content)})
        if r.status_code != 200:
            raise RuntimeError(f"rappel classification {code} : HTTP {r.status_code}")
        rappels[code] = r.content.decode("utf-8", "replace")
    par_entite, controle = entites_par_classification(rappels)
    ids = lambda h: [(re.search(r'\$orgCons"[^>]*value="([^"]*)"', x).group(1), re.search(r'\$refCons"[^>]*value="(\d+)"', x).group(1)) for x in lignes(h)]
    filtres = {}
    h, _ = L.rechercher()
    filtres["toutes"] = {"total": total_et_pages(h)["total"]}
    for code in ("3", "2", "1"):
        h, _ = L.rechercher(classification=code, fenetre={"type_rechercheEntite": "exact"})
        t = total_et_pages(h)
        res = {"total": t["total"]}
        if code != "1" and t["total"] and t["total"] <= 1500:
            h = L.taille_500(h)
            t = total_et_pages(h)
            I = ids(h)
            for n in range(2, (t["pages"] or 1) + 1):
                h = L.page(h, n)
                I += ids(h)
            I = sorted(set(I))
            res.update({"ids_lus": len(I), "incoherents": sorted(f"pmmp:{o}:{r}" for o, r in I if (par_entite.get(o) or {}).get("code") != code)})
        filtres[code] = res
    s = sum(filtres[c]["total"] or 0 for c in ("1", "2", "3"))
    rel = {"version": VERSION, "debut": debut, "fin": maintenant(), "url": L.url, "fenetre_recherche": L.fenetre,
           "methode": "rappel PRADO de la liste « Etat/CL/EEP » (classification) -> liste officielle organismesNames ; "
                      "contrôle par la recherche avancée filtrée (type_rechercheEntite=exact)",
           "valeurs": CLASSIFICATIONS, "par_entite": par_entite, "controle_listes": controle,
           "controle_recherche": {"totaux": filtres, "somme_classes": s, "partition_totaux": s == filtres["toutes"]["total"]},
           "procedures_formulaire": {"champ": P_RECH + "procedureType", "libelle_formulaire": "Mode de passation",
                                     "codes": procedures_formulaire(h0)},
           "requetes": journal}
    json.dump(rel, open(os.path.join(sortie, "releve_classification.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return rel


def completer_mode(kit, catalogue, fiches, cache, maximum, aujourdhui, delai=4.0):
    """Complément borné et repris : lit la fiche publique des annonces ouvertes sans mode connu (date limite la plus
    proche d'abord), au plus `maximum`, et garde seulement mode_passation / proc / ref / lu_le / sha256 du HTML tronqué."""
    sys.path.insert(0, kit)
    from veille.client import ArretCollecte, ClientPMMP, texte  # noqa
    from veille.pmmp_fiche import PARAMS, fiche_valide, lire_fiche, tronquer_contact  # noqa
    os.makedirs(cache, exist_ok=True)
    F = fiches or {}
    deja = lambda o, r: os.path.exists(os.path.join(cache, f"{o}_{r}.json"))
    cand = [x for x in catalogue["items"] if (x.get("lim") or "9") >= aujourdhui
            and not ((F.get(f"pmmp:{x['o']}:{x['r']}") or {}).get("champs") or {}).get("mode_passation") and not deja(x["o"], x["r"])]
    cand.sort(key=lambda x: (x.get("lim") or "9", x.get("h") or "", x["o"], x["r"]))
    c = ClientPMMP(delai_min=delai)
    lues = echecs = 0
    for x in cand[:maximum]:
        try:
            r = c.get(PARAMS(x["r"], x["o"]))
            h, coupe = tronquer_contact(texte(r))
            f = lire_fiche(h, masquer=True)
            if not fiche_valide(f):
                echecs += 1
                continue
            rec = {"id": f"pmmp:{x['o']}:{x['r']}", "lu_le": maintenant(), "url": r.url[:300], "mode_passation": f.get("mode_passation"),
                   "proc": f.get("proc"), "ref": f.get("ref"), "ref_catalogue": x.get("ref"), "contact_coupe": coupe,
                   "sha256_html_tronque": hashlib.sha256(h.encode()).hexdigest()}
            json.dump(rec, open(os.path.join(cache, f"{x['o']}_{x['r']}.json"), "w", encoding="utf-8"), ensure_ascii=False)
            lues += 1
        except ArretCollecte:
            break
        except Exception:
            echecs += 1
    return {"candidats": len(cand), "lues": lues, "echecs": echecs, "requetes": c.nb_requetes}


# ---------------------------------------------------------------- construction hors ligne
def octets_json(d):
    return (json.dumps(d, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def construire(catalogue, releve, fiches=None, complements=None, precedent=None, catalogue_sha=None, source_fiches=None):
    """Assemble le fichier joint. Aucune requête. N'écrase jamais une lecture plus récente ; ne supprime rien."""
    items = catalogue["items"]
    cles = {f"pmmp:{x['o']}:{x['r']}": x for x in items}
    # --- mode de passation par annonce
    prev = ((precedent or {}).get("mode_passation") or {}).get("par_id") or {}
    par_id = {k: dict(v) for k, v in prev.items()}

    def proposer(k, rec):
        if not rec.get("v"):
            return
        a = par_id.get(k)
        if a is None or (rec.get("lu_le") or "") > (a.get("lu_le") or ""):
            par_id[k] = rec

    for k, f in sorted((fiches or {}).items()):
        ch = f.get("champs") or {}
        proposer(k, {"v": ch.get("mode_passation"), "proc": ch.get("proc"), "ref": ch.get("ref"), "lu_le": f.get("lu_le"),
                     "run": f.get("run"), "source": "collecteur", "sha256_html_tronque": f.get("sha256_html_tronque")})
    for rec in sorted(complements or [], key=lambda r: r["id"]):
        proposer(rec["id"], {"v": rec.get("mode_passation"), "proc": rec.get("proc"), "ref": rec.get("ref"), "lu_le": rec.get("lu_le"),
                             "url": rec.get("url"), "source": "complement_eaios", "sha256_html_tronque": rec.get("sha256_html_tronque")})
    norm = lambda s: re.sub(r"\s+", " ", s or "").strip().upper()
    cat_ok = {k: v for k, v in par_id.items() if k in cles and norm(v.get("ref")) == norm(cles[k].get("ref"))}
    discord = sorted(k for k, v in par_id.items() if k in cles and norm(v.get("ref")) != norm(cles[k].get("ref")))
    valeurs = {}
    for v in cat_ok.values():
        valeurs[v["v"]] = valeurs.get(v["v"], 0) + 1
    # --- classification par entité
    pe = releve["par_entite"]
    orgs = sorted({x["o"] for x in items})
    inconnues = [o for o in orgs if o not in pe]
    n_cls = {}
    for x in items:
        c = (pe.get(x["o"]) or {}).get("code") or "inconnu"
        n_cls[c] = n_cls.get(c, 0) + 1
    # --- procédures : codes PMMP
    codes = releve.get("procedures_formulaire", {}).get("codes", {})
    procs = sorted({x.get("proc") for x in items if x.get("proc")})
    lus = [v.get("lu_le") for v in par_id.values() if v.get("lu_le")]
    out = {
        "version": VERSION,
        "maj": max([releve.get("fin") or ""] + lus),
        "catalogue_sha256": catalogue_sha,
        "catalogue_maj": catalogue.get("maj"),
        "jointure": "annonce : pmmp:<org>:<ref> (orgAcronyme, refConsultation) ; entité : code PMMP <org>",
        "classification": {
            "nom": "Etat/CL/EEP (classification PMMP de l'entité publique)",
            "valeurs": CLASSIFICATIONS,
            "source": {"url": releve.get("url"), "releve_debut": releve.get("debut"), "releve_fin": releve.get("fin"),
                       "methode": releve.get("methode"), "controle_listes": releve.get("controle_listes"),
                       "controle_recherche": releve.get("controle_recherche")},
            "regle": "une annonce hérite de la classification de son entité publique (rattachement unique orgAcronyme) ; "
                     "entité absente ou ambiguë = inconnue ; jamais déduite du nom de l'acheteur",
            "par_entite": pe,
            "couverture": {"annonces": len(items), "par_code": dict(sorted(n_cls.items())), "entites_catalogue": len(orgs),
                           "entites_inconnues": inconnues},
        },
        "mode_passation": {
            "nom": "Mode de passation (fiche PMMP, élément modePassation, distinct de la procédure)",
            "source": {"element": "ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_modePassation",
                       "page": "index.php?page=entreprise.EntrepriseDetailConsultation&refConsultation=<ref>&orgAcronyme=<org>",
                       "fiches_collecteur": source_fiches},
            "regle": "lecture réelle datée par annonce ; la plus récente gagne ; jointure utilisée seulement si la référence lue "
                     "concorde avec le catalogue ; sans lecture = inconnu",
            "par_id": {k: par_id[k] for k in sorted(par_id)},
            "couverture": {"annonces": len(items), "connues": len(cat_ok), "inconnues": len(items) - len(cat_ok),
                           "pct": round(100 * len(cat_ok) / len(items), 1) if items else 0, "valeurs": dict(sorted(valeurs.items())),
                           "reference_discordante": discord,
                           "lues_hors_catalogue_conservees": sum(1 for k in par_id if k not in cles)},
        },
        "procedures": {"nom": "Procédure (type de procédure PMMP)",
                       "source": {"url": releve.get("url"), "champ": (releve.get("procedures_formulaire") or {}).get("champ"),
                                  "libelle_formulaire": "Mode de passation (libellé du formulaire de recherche ; valeurs = procédures)",
                                  "releve_fin": releve.get("fin")},
                       "codes": codes, "catalogue_sans_code": [p for p in procs if p not in codes]},
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a1 = sp.add_parser("releve", help="relevé officiel borné (réseau)")
    a1.add_argument("--kit", required=True, help="dossier stock/kit du collecteur (client, listing)")
    a1.add_argument("--sortie", required=True)
    a1.add_argument("--delai", type=float, default=4.0)
    a2 = sp.add_parser("completer", help="complément borné du mode de passation (réseau)")
    a2.add_argument("--kit", required=True)
    a2.add_argument("--catalogue", required=True)
    a2.add_argument("--fiches")
    a2.add_argument("--cache", required=True)
    a2.add_argument("--max", type=int, default=100)
    a2.add_argument("--aujourdhui", required=True)
    a3 = sp.add_parser("construire", help="construction hors ligne du fichier joint")
    a3.add_argument("--catalogue", required=True)
    a3.add_argument("--releve", required=True)
    a3.add_argument("--fiches", help="stock/etat/fiches.json du collecteur")
    a3.add_argument("--complement", help="dossier cache du complément")
    a3.add_argument("--precedent", help="catalogue_pmmp_enrichi.json publié")
    a3.add_argument("--sortie", required=True)
    a = ap.parse_args(argv)
    lire = lambda p: json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else None
    if a.cmd == "releve":
        r = relever(a.kit, a.sortie, a.delai)
        print(json.dumps({"partition": r["controle_listes"]["partition_exacte"], "totaux": r["controle_recherche"]}, ensure_ascii=False))
        return 0 if r["controle_listes"]["partition_exacte"] and r["controle_recherche"]["partition_totaux"] else 2
    if a.cmd == "completer":
        print(json.dumps(completer_mode(a.kit, lire(a.catalogue), lire(a.fiches), a.cache, a.max, a.aujourdhui), ensure_ascii=False))
        return 0
    cat_b = open(a.catalogue, "rb").read()
    rel = lire(a.releve)
    if not (rel["controle_listes"]["partition_exacte"] and rel["controle_recherche"]["partition_totaux"]):
        print(json.dumps({"etat": "refus", "motif": "relevé de classification non vérifié"}, ensure_ascii=False))
        return 2
    fiches = lire(a.fiches)
    comp = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(a.complement, "*.json")))] if a.complement else []
    src = {"sha256": hashlib.sha256(open(a.fiches, "rb").read()).hexdigest(), "n": len(fiches)} if fiches is not None else None
    out = construire(json.loads(cat_b), rel, fiches, comp, lire(a.precedent), hashlib.sha256(cat_b).hexdigest(), src)
    b = octets_json(out)
    prec = open(a.precedent, "rb").read() if a.precedent and os.path.exists(a.precedent) else None
    open(a.sortie, "wb").write(b)
    print(json.dumps({"etat": "inchange" if prec == b else "pret", "sha256": hashlib.sha256(b).hexdigest(), "octets": len(b),
                      "classification": out["classification"]["couverture"], "mode": {k: v for k, v in out["mode_passation"]["couverture"].items() if k != "reference_discordante"}
                      | {"reference_discordante": len(out["mode_passation"]["couverture"]["reference_discordante"])}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

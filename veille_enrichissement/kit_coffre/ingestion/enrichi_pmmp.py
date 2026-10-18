"""Enrichissement PMMP joint au catalogue (clé « pmmp_enrichi » de catalogue_details.json). HORS LIGNE, déterministe.

Deux champs officiels, DISTINCTS :
  * Mode de passation : élément modePassation de la fiche publique (« Procédure : Appel d'offres ouvert | Sur offre de prix »),
    lu par le collecteur (fiches.json, champ mode_passation, lu_le réel). Distinct de la procédure. Par annonce : la lecture la
    plus récente gagne ; une valeur déjà publiée n'est jamais perdue (reprise depuis la publication précédente, même si la
    fiche n'est plus dans fiches.json) ; la page ne l'utilise que si la référence lue = référence du catalogue.
  * Classification « Etat/CL/EEP » : classification PMMP de l'ENTITÉ PUBLIQUE (referentiel/classification_entites.json,
    relevé officiel : rappel de la liste « Etat/CL/EEP » du formulaire de recherche, contrôlé par la recherche filtrée).
    Une annonce hérite de son entité (orgAcronyme) ; entité absente ou ambiguë = inconnue ; aucune déduction par le nom.
Les codes PMMP des procédures (liste du formulaire libellée « Mode de passation », dont les valeurs sont les procédures) sont
repris du même relevé. Aucune date « maintenant » : mêmes entrées -> mêmes octets.
"""
import re

CLASSIFICATIONS = {"1": "Etat", "2": "Collectivité locale", "3": "Etablissement public"}


def _nref(s):
    return re.sub(r"\s+", " ", s or "").strip().upper()


def _plus_recent(a, b):
    return b if a is None or (b.get("lu_le") or "") > (a.get("lu_le") or "") else a


def enrichir(items, fiches=None, referentiel=None, precedent=None):
    """items : consultations du catalogue publié ; fiches : fiches.json du collecteur ; referentiel : relevé officiel de
    classification ; precedent : « pmmp_enrichi » de la publication précédente (ou None)."""
    precedent = precedent or {}
    par_id = {k: dict(v) for k, v in ((precedent.get("mode_passation") or {}).get("par_id") or {}).items() if v.get("v")}
    for k, f in sorted((fiches or {}).items()):
        ch = (f or {}).get("champs") or {}
        if ch.get("mode_passation") and f.get("lu_le"):
            par_id[k] = _plus_recent(par_id.get(k), {"v": ch["mode_passation"], "ref": ch.get("ref"), "lu_le": f["lu_le"],
                                                      "run": f.get("run"), "source": "collecteur"})
    cles = {f"pmmp:{x['o']}:{x['r']}": x for x in items}
    connues, valeurs, discord = 0, {}, []
    for k, x in cles.items():
        v = par_id.get(k)
        if not v:
            continue
        if _nref(v.get("ref")) != _nref(x.get("ref")):
            discord.append(k)
            continue
        connues += 1
        valeurs[v["v"]] = valeurs.get(v["v"], 0) + 1
    if referentiel:
        cls = {"nom": "Etat/CL/EEP (classification PMMP de l'entité publique)", "valeurs": CLASSIFICATIONS,
               "source": {k: referentiel.get(k) for k in ("url", "debut", "fin", "methode", "controle_listes", "controle_recherche")},
               "regle": "une annonce hérite de la classification de son entité publique (rattachement unique orgAcronyme) ; "
                        "entité absente ou ambiguë = inconnue ; jamais déduite du nom de l'acheteur",
               "par_entite": referentiel.get("par_entite") or {}}
        procs = {"codes": (referentiel.get("procedures_formulaire") or {}).get("codes") or {},
                 "source": {"url": referentiel.get("url"), "champ": (referentiel.get("procedures_formulaire") or {}).get("champ"),
                            "libelle_formulaire": "Mode de passation (libellé du formulaire de recherche PMMP ; valeurs = procédures)",
                            "fin": referentiel.get("fin")}}
    else:  # référentiel absent : la classification publiée précédemment est conservée telle quelle
        cls = {k: v for k, v in (precedent.get("classification") or {}).items() if k != "couverture"} or None
        procs = precedent.get("procedures")
    pe = (cls or {}).get("par_entite") or {}
    n_cls = {}
    for x in items:
        c = (pe.get(x["o"]) or {}).get("code") or "inconnu"
        n_cls[c] = n_cls.get(c, 0) + 1
    out = {"version": 1, "jointure": "annonce : pmmp:<org>:<ref> ; entité : code PMMP <org>",
           "mode_passation": {"nom": "Mode de passation (fiche PMMP, élément modePassation ; distinct de la procédure)",
                              "source": {"element": "ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_modePassation",
                                         "page": "index.php?page=entreprise.EntrepriseDetailConsultation&refConsultation=<ref>&orgAcronyme=<org>"},
                              "regle": "lecture réelle datée par annonce, la plus récente gagne ; utilisée seulement si la référence lue "
                                       "concorde avec le catalogue ; sans lecture = non renseigné",
                              "par_id": {k: par_id[k] for k in sorted(par_id)},
                              "couverture": {"annonces": len(items), "connues": connues, "inconnues": len(items) - connues,
                                             "pct": round(100 * connues / len(items), 1) if items else 0.0,
                                             "valeurs": dict(sorted(valeurs.items())), "reference_discordante": sorted(discord),
                                             "lues_hors_catalogue_conservees": sum(1 for k in par_id if k not in cles)}}}
    if cls:
        out["classification"] = dict(cls, couverture={"annonces": len(items), "par_code": dict(sorted(n_cls.items())),
                                                      "entites_inconnues": sorted({x["o"] for x in items if x["o"] not in pe})})
    if procs:
        out["procedures"] = procs
    lus = [v.get("lu_le") for v in par_id.values() if v.get("lu_le")]
    out["maj"] = max([((cls or {}).get("source") or {}).get("fin") or ""] + lus) or None
    return out

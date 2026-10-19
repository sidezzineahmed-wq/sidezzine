"""Enrichissement PMMP joint au catalogue (clé « pmmp_enrichi » de catalogue_details.json). HORS LIGNE, déterministe.

Deux champs officiels, DISTINCTS :
  * Mode de passation : élément modePassation de la fiche publique (« Procédure : Appel d'offres ouvert | Sur offre de prix »),
    lu par le collecteur (fiches.json, champ mode_passation, lu_le réel). Distinct de la procédure. Par annonce : la lecture la
    plus récente gagne ; une valeur déjà publiée n'est jamais perdue (reprise depuis la publication précédente, même si la
    fiche n'est plus dans fiches.json) ; la page ne l'utilise que si la référence lue = référence du catalogue.
  * Classification « Etat/CL/EEP » : classification PMMP de l'ENTITÉ PUBLIQUE (referentiel/classification_entites.json,
    relevé officiel : rappel de la liste « Etat/CL/EEP » du formulaire de recherche, contrôlé par la recherche filtrée).
    Une annonce hérite de son entité (orgAcronyme) ; entité absente ou ambiguë = inconnue ; aucune déduction par le nom.
  * Détail par lot : popup public « Détail des lots » d'une consultation allotie (commun.PopUpDetailLots), lu par le
    collecteur dans le même passage que la fiche (fiches.json, clé « lots » : statut lu / partiel, lu_le, lots[]). Valeurs
    PAR LOT telles que publiées (estimation TTC, caution, TPE/PME, qualifications, agréments, visites…), jamais sommées ni
    aplaties ; « ni » = non indiqué par l'acheteur (« - »), « na » = bloc non affiché. La lecture la plus récente gagne ;
    une lecture déjà publiée est conservée ; la page ne l'utilise que si la référence de la fiche concorde.
  * Compléments de fiche (lecteur v3) : adresse de retrait, prix des plans, prospectus / échantillons (date et texte publiés,
    distincts de la remise des plis), contact administratif PUBLIÉ dans la fiche, pièces publiées (liens publics PMMP, aucun
    fichier joint). Statut PAR BLOC : « lu » (valeur publiée, None = « - »), « non_publie » (page lue jusqu'au-delà du bloc,
    bloc absent), « non_lu » (lecture antérieure ou page coupée avant le bloc : jamais « non publié »). Date de lecture réelle
    (lu_le) conservée ; une ré-analyse hors ligne du HTML déjà lu est datée à part (reanalyse_le, version_parseur).
Les codes PMMP des procédures (liste du formulaire libellée « Mode de passation », dont les valeurs sont les procédures) sont
repris du même relevé. Aucune date « maintenant » : mêmes entrées -> mêmes octets.
"""
import re

CLASSIFICATIONS = {"1": "Etat", "2": "Collectivité locale", "3": "Etablissement public"}


def _nref(s):
    return re.sub(r"\s+", " ", s or "").strip().upper()


def _plus_recent(a, b):
    return b if a is None or (b.get("lu_le") or "") > (a.get("lu_le") or "") else a


CHAMPS_LOT = ("num", "intitule", "cat", "description", "est", "est_libelle", "cau", "tp", "q", "ag", "vis", "reu", "proto", "var",
              "env", "autres", "ni", "na")


def _lots(items, fiches, precedent, complement_fiches):
    """Section « lots » : détail par lot des consultations alloties."""
    prec = (precedent or {}).get("lots") or {}
    par_id = {k: dict(v) for k, v in (prec.get("par_id") or {}).items()}
    inacc = {k: dict(v) for k, v in (prec.get("inaccessibles") or {}).items()}
    for k, f in sorted((fiches or {}).items()):
        L = (f or {}).get("lots")
        if not L or not L.get("lu_le") or L.get("statut") not in ("lu", "partiel"):
            continue
        rec = {"lu_le": L["lu_le"], "statut": L["statut"], "n": L.get("n"), "n_annonce": L.get("n_annonce"),
               "ref": ((f.get("champs") or {}).get("ref")), "url": L.get("url"),
               "lots": [{c: x[c] for c in CHAMPS_LOT if c in x and not (c == "description" and x.get(c) == x.get("intitule"))}
                        for x in L.get("lots") or []]}
        par_id[k] = _plus_recent(par_id.get(k), rec)
    for k, c in sorted(((complement_fiches or {}).get("lots_inaccessibles") or {}).items()):
        if k not in par_id:
            inacc[k] = c
    cles = {f"pmmp:{x['o']}:{x['r']}": x for x in items}
    for d in (par_id, inacc):  # consultations closes ou retirées : rien à garder (le popup n'a de sens que pour l'annonce ouverte)
        for k in list(d):
            if k not in cles:
                d.pop(k)
    for k in list(inacc):
        if k in par_id:
            inacc.pop(k)
    alloties = [k for k, x in cles.items() if x.get("lots") or x.get("allot")]
    lus = [k for k in alloties if k in par_id and _nref(par_id[k].get("ref")) == _nref(cles[k].get("ref"))]
    return {"nom": "Détail par lot (popup PMMP « Détail des lots »)",
            "source": {"page": "index.php?page=commun.PopUpDetailLots&orgAccronyme=<org>&refConsultation=<ref>&lang=fr"},
            "regle": "valeurs par lot telles que publiées, jamais sommées ni aplaties ; ni = non indiqué (« - »), na = bloc non affiché ; "
                     "utilisées seulement si la référence de la fiche concorde avec le catalogue",
            "par_id": {k: par_id[k] for k in sorted(par_id)}, "inaccessibles": {k: inacc[k] for k in sorted(inacc)},
            "couverture": {"alloties": len(alloties), "lues": sum(1 for k in lus if par_id[k]["statut"] == "lu"),
                           "partielles": sum(1 for k in lus if par_id[k]["statut"] == "partiel"),
                           "inaccessibles": sum(1 for k in alloties if k not in lus and k in inacc),
                           "non_lues": sum(1 for k in alloties if k not in lus and k not in inacc),
                           "lots": sum(len(par_id[k]["lots"]) for k in lus)}}


CHAMPS_V3 = ("type_annonce", "ret", "prix_plans", "ech_date", "ech_txt", "contact", "docs")
BLOCS_V3 = ("retrait", "prix_plans", "echantillons", "contact", "docs")


def statuts_blocs(ch):
    """Statut de chaque bloc v3 d'une fiche lue : lu / non_publie / non_lu (voir docstring du module)."""
    if "blocs_lus" not in (ch or {}):
        return {b: "non_lu" for b in BLOCS_V3}  # champs analysés par un lecteur antérieur : blocs jamais extraits
    lus = set(ch["blocs_lus"])
    au_dela = "docs" in lus  # page lue jusqu'aux pièces, donc au-delà du contact
    st = {b: "lu" if b in lus else "non_publie" for b in ("retrait", "prix_plans", "echantillons")}
    st["contact"] = "lu" if "contact" in lus else "non_publie" if au_dela else "non_lu"
    st["docs"] = "lu" if au_dela else "non_lu"
    return st


def _cle_lecture(v):
    return (v.get("lu_le") or "", v.get("reanalyse_le") or "")


def _complements(items, fiches, precedent):
    """Section « complements_fiche » : blocs v3 par annonce, avec statut par bloc et provenance."""
    prec = ((precedent or {}).get("complements_fiche") or {}).get("par_id") or {}
    par_id = {k: dict(v) for k, v in prec.items()}
    for k, f in sorted((fiches or {}).items()):
        ch = (f or {}).get("champs") or {}
        if not f or not f.get("lu_le") or "blocs_lus" not in ch:
            continue
        rec = {"ref": ch.get("ref"), "lu_le": f["lu_le"], "run": f.get("run"), "version_lecture": ch.get("version_lecture")}
        for c in ("reanalyse_le", "version_parseur", "version_lecture_initiale"):
            if f.get(c) is not None:
                rec[c] = f[c]
        rec["statuts"] = statuts_blocs(ch)
        org_ref = k.split(":", 1)[1]
        if rec["statuts"]["docs"] == "lu" and (ch.get("page_id") != org_ref if ch.get("docs") == [] or ch.get("page_id") else False):
            # pièces (et surtout « aucune pièce ») d'une page dont le formulaire désigne une autre consultation, ou vide
            # sans contexte de page prouvé : non lues
            rec["statuts"]["docs"] = "non_lu"
            rec["identite_pieces"] = "non_prouvee"
            ch = {c: v for c, v in ch.items() if c not in ("docs", "docs_preuve")}
        if ch.get("sources_blocs"):
            rec["sources_blocs"] = ch["sources_blocs"]  # ex. contact relu dans l'état de la page déjà reçue
        for c in CHAMPS_V3 + ("docs_preuve", "docs_lu_le", "docs_source"):
            if ch.get(c) is not None:
                rec[c] = ch[c]
        a = par_id.get(k)
        if a is None or _cle_lecture(rec) >= _cle_lecture(a):
            par_id[k] = rec
    cles = {f"pmmp:{x['o']}:{x['r']}": x for x in items}
    for k in list(par_id):
        if k not in cles:
            par_id.pop(k)
    ok = {k for k, v in par_id.items() if _nref(v.get("ref")) == _nref(cles[k].get("ref"))}
    cov = {}
    for b in BLOCS_V3:
        n = {"lu": 0, "non_publie": 0, "non_lu": 0}
        for k in cles:
            n[par_id[k]["statuts"][b] if k in ok else "non_lu"] += 1
        cov[b] = n
    cov["avec_valeur"] = {c: sum(1 for k in ok if par_id[k].get(c) is not None) for c in CHAMPS_V3}
    cov["docs_detail"] = {"avec_pieces": sum(1 for k in ok if par_id[k].get("docs")),
                          "aucune_piece_confirmee": sum(1 for k in ok if par_id[k].get("docs") == []),
                          "preuves": {p: sum(1 for k in ok if par_id[k].get("docs_preuve") == p and par_id[k]["statuts"]["docs"] == "lu")
                                      for p in sorted({par_id[k].get("docs_preuve") for k in ok if par_id[k].get("docs_preuve")})},
                          "inventaire_date_propre": sum(1 for k in ok if par_id[k].get("docs_lu_le"))}
    cov["reference_discordante"] = sorted(set(par_id) - ok)
    cov["reanalyses_hors_ligne"] = sum(1 for k in ok if par_id[k].get("reanalyse_le"))
    cov["contact_etat_de_page"] = sum(1 for k in ok if (par_id[k].get("sources_blocs") or {}).get("contact") == "etat_de_page")
    return {"nom": "Compléments de fiche PMMP (retrait, plans, prospectus/échantillons, contact publié, pièces)",
            "source": {"page": "index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=<ref>&orgAcronyme=<org>",
                       "portail": "https://www.marchespublics.gov.ma/"},
            "regle": "statut par bloc : lu (valeur publiée ; absente = « - » publié), non_publie (page lue au-delà du bloc, bloc "
                     "absent), non_lu (lecture antérieure ou page coupée avant le bloc) ; contact = coordonnées professionnelles "
                     "publiées dans le bloc administratif de la fiche, rien de l'espace entreprise ; pièces = liens publics PMMP du "
                     "même identifiant, aucun fichier joint ; lu_le = lecture réelle, reanalyse_le = ré-analyse hors ligne du même HTML ; "
                     "utilisé seulement si la référence lue concorde avec le catalogue",
            "par_id": {k: par_id[k] for k in sorted(par_id)}, "couverture": cov}


def enrichir(items, fiches=None, referentiel=None, precedent=None, complement=None, complement_fiches=None):
    """items : consultations du catalogue publié ; fiches : fiches.json du collecteur ; referentiel : relevé officiel de
    classification ; precedent : « pmmp_enrichi » de la publication précédente (ou None) ; complement :
    referentiel/mode_passation_complement.json du kit (lectures du complément EAIOS : statut lu / champ_absent / inaccessible).
    Une valeur n'existe QUE si une lecture réelle l'a vue ; « champ absent » (fiche lue, élément vide) et « inaccessible »
    (fiche illisible après essais bornés) sont comptés à part et ne donnent jamais de valeur."""
    precedent = precedent or {}
    pm = precedent.get("mode_passation") or {}
    par_id = {k: dict(v) for k, v in (pm.get("par_id") or {}).items() if v.get("v")}
    absents = {k: dict(v) for k, v in (pm.get("absents") or {}).items()}
    inacc = {k: dict(v) for k, v in (pm.get("inaccessibles") or {}).items()}

    def lecture(k, rec, vide):
        if vide:
            absents[k] = _plus_recent(absents.get(k), rec)
        else:
            par_id[k] = _plus_recent(par_id.get(k), rec)
            inacc.pop(k, None)

    for k, f in sorted((fiches or {}).items()):
        ch = (f or {}).get("champs") or {}
        if f and f.get("lu_le") and "mode_passation" in ch:
            lecture(k, {"v": ch.get("mode_passation"), "ref": ch.get("ref"), "lu_le": f["lu_le"], "run": f.get("run"), "source": "collecteur"},
                    not ch.get("mode_passation"))
    for k, c in sorted(((complement or {}).get("par_id") or {}).items()):
        if c.get("statut") in ("lu", "champ_absent") and c.get("lu_le"):
            lecture(k, {"v": c.get("v"), "ref": c.get("ref"), "lu_le": c["lu_le"], "url": c.get("url"), "source": "complement_eaios"},
                    c["statut"] == "champ_absent" or not c.get("v"))
        elif c.get("statut") == "inaccessible" and k not in par_id:
            inacc[k] = {k2: c.get(k2) for k2 in ("tentatives", "dernier_echec", "raison", "url") if c.get(k2) is not None}
    for k in list(absents):  # une valeur lue plus récemment l'emporte sur un « champ absent » plus ancien
        if k in par_id and (par_id[k].get("lu_le") or "") >= (absents[k].get("lu_le") or ""):
            absents.pop(k)
    for k in list(inacc):
        if k in par_id or k in absents:
            inacc.pop(k)
    cles = {f"pmmp:{x['o']}:{x['r']}": x for x in items}
    connues, valeurs, discord = 0, {}, []
    n_abs = sum(1 for k, x in cles.items() if k not in par_id and k in absents and _nref(absents[k].get("ref")) == _nref(x.get("ref")))
    n_inacc = sum(1 for k in cles if k not in par_id and k not in absents and k in inacc)
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
                              "absents": {k: absents[k] for k in sorted(absents)},
                              "inaccessibles": {k: inacc[k] for k in sorted(inacc)},
                              "couverture": {"annonces": len(items), "connues": connues, "inconnues": len(items) - connues,
                                             "champ_absent": n_abs, "inaccessibles": n_inacc,
                                             "non_lues": len(items) - connues - n_abs - n_inacc - len(discord),
                                             "pct": round(100 * connues / len(items), 1) if items else 0.0,
                                             "valeurs": dict(sorted(valeurs.items())), "reference_discordante": sorted(discord),
                                             "lues_hors_catalogue_conservees": sum(1 for k in par_id if k not in cles)}}}
    if cls:
        out["classification"] = dict(cls, couverture={"annonces": len(items), "par_code": dict(sorted(n_cls.items())),
                                                      "entites_inconnues": sorted({x["o"] for x in items if x["o"] not in pe})})
    if procs:
        out["procedures"] = procs
    out["lots"] = _lots(items, fiches, precedent, complement_fiches)
    out["complements_fiche"] = _complements(items, fiches, precedent)
    fi = {k: v for k, v in sorted(((complement_fiches or {}).get("fiches_inaccessibles") or {}).items())
          if k in cles and not cles[k]["det"]}
    vnl = sorted(k for k, x in cles.items() if x.get("det") and k in (fiches or {})
                 and ((fiches[k] or {}).get("champs") or {}).get("version_lecture", 1) < 2)
    out["fiches"] = {"inaccessibles": fi, "regle": "fiche PMMP illisible après essais bornés : champs de fiche inconnus (jamais remplis)",
                     "visite_non_lue": vnl,
                     "regle_visite": "fiche lue par une version du collecteur antérieure à version_lecture 2 : bloc « Visites des lieux » "
                                     "non lu ; la visite est inconnue (jamais « non indiquée ») jusqu'à la prochaine lecture"}
    lus = [v.get("lu_le") for v in par_id.values() if v.get("lu_le")] + [v.get("lu_le") for v in out["lots"]["par_id"].values() if v.get("lu_le")] + \
        [v.get("lu_le") for v in out["complements_fiche"]["par_id"].values() if v.get("lu_le")]
    out["maj"] = max([((cls or {}).get("source") or {}).get("fin") or ""] + lus) or None
    return out

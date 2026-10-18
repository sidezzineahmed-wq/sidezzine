"""Fiche publique d'une consultation PMMP (EntrepriseDetailConsultation), sans login.

Le bloc « Contact Administratif » (nom, e-mail, téléphone d'agents) n'est JAMAIS lu ni conservé :
le HTML est tronqué avant ce bloc dès la réception, avant toute analyse ou sauvegarde.
"""
import re

from .html_outils import date_iso, masquer_coordonnees, montant, nettoyer, vide_portail

PARAMS = lambda r, o: {"page": "entreprise.EntrepriseDetailConsultation", "refConsultation": r, "orgAcronyme": o}
PFX = "ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_"
# 2 (18/10/2026) : visites lues (sous-bloc panelRepeaterVisitesLieux), qualification par position, lignes publiées gardées.
# Une fiche sans ce champ a été lue par une version antérieure : sa visite des lieux n'a PAS été lue (inconnue, pas « non indiquée »).
VERSION_LECTURE = 2
DEBUT_CONTACT = re.compile(r'<div id="ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_panelCont\w*Administratif"|Contact Administratif', re.I)


def tronquer_contact(h):
    """Coupe tout à partir du bloc Contact Administratif. Renvoie (html_tronqué, coupé?)."""
    m = DEBUT_CONTACT.search(h)
    if not m:
        return h, False
    return h[: m.start()], True


def _id(h, suffixe, balise="span"):
    m = re.search(r'id="' + PFX + suffixe + r'"[^>]*>(.*?)</' + balise + ">", h, re.S)
    return m.group(1) if m else None


def _txt(h, suffixe, balise="span"):
    v = nettoyer(_id(h, suffixe, balise))
    return None if vide_portail(v) else v


def _li(h, suffixe):
    brut = _id(h, suffixe)
    if brut is None:
        return []
    items = [nettoyer(x) for x in re.findall(r"<li>(.*?)</li>", brut, re.S)]
    items = [x for x in items if x and not vide_portail(x)]
    if not items:
        v = nettoyer(brut)
        items = [] if vide_portail(v) else [v]
    return items


def _panel_visible(h, suffixe):
    m = re.search(r'id="' + PFX + suffixe + r'"[^>]*style="([^"]*)"', h)
    return m is None or "none" not in m.group(1).replace(" ", "")


def _bloc_panel(h, panel):
    """Texte du contenu d'un panneau « line » (après l'intitulé), ou None."""
    # le bloc s'arrête au panneau SUIVANT, pas à son propre sous-bloc (« panelRepeaterVisitesLieux » contient les visites)
    m = re.search(r'id="' + PFX + panel + r'"[^>]*>(.*?)(?=<div id="' + PFX + r'panel(?!Repeater)|<span class="spacer-small"|$)', h, re.S)
    if not m:
        return None
    corps = re.sub(r'<div class="intitule-240 bold">.*?</div>', "", m.group(1), count=1, flags=re.S)
    corps = re.sub(r"<script.*?</script>", "", corps, flags=re.S)
    v = nettoyer(corps)
    v = re.sub(r"\s+,", ",", v) if v else v  # « 28/10/2026 11:00 , lieu » (balises retirées) -> « 28/10/2026 11:00, lieu »
    # « Date et heure : » seul (libellé sans date ni adresse, cas des consultations alloties) = rien de publié
    if vide_portail(nettoyer(re.sub(r'<span id="' + PFX + r'label\w*"[^>]*>.*?</span>', "", corps, flags=re.S))):
        return None
    return None if vide_portail(v) else v


LIBELLES_SEULS = re.compile(r"^\s*Date et heure(?: limite)?\s*:?\s*$", re.I)


def libelle_seul(v):
    """Vrai pour une ancienne valeur réduite au libellé du portail (« Date et heure : ») : aucune donnée publiée."""
    return isinstance(v, str) and bool(LIBELLES_SEULS.match(v))


CODE_LETTRES = re.compile(r"^([A-Z]\d*(?:\.\d+)*)\s*-\s*(.*)$")  # « B- … », « B.3- … », « Y1- … » (jamais un mot : « RECHERCHE-DEVELOPPEMENT »)
CODE_CHIFFRES = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s*-\s*|\s+|(?=[^\d\s.]))(.*)$")  # « 2 Travaux », « 2.2 Sans objet. », « 10.1.Travaux »


def _code(p):
    """(code, libellé) d'un segment ; code None si le segment n'est que du texte (ex. « ETUDES GEOTECHNIQUES »)."""
    m = CODE_LETTRES.match(p) or CODE_CHIFFRES.match(p)
    if m:
        return m.group(1), m.group(2).strip() or None
    return None, p.strip() or None


def lire_qualification(ligne):
    """Ligne publiée « Système / Secteur / Qualification / Classe N » -> {m,s,sl,q,ql,c}, PAR POSITION :
    1er segment (sans code) = système ; dernier « Classe … » = classe ; entre les deux, 1er = secteur, 2e = qualification
    (segments suivants éventuels ajoutés au libellé de la qualification). Codes réels gardés tels que publiés
    (« B », « B.3 », « Y », « Y1 », « 2.2 », « 10.1 ») ; un segment sans code garde son texte (libellé, code None).
    Un seul segment : avec point = qualification, sinon secteur. Les parties absentes restent None (rien n'est deviné)."""
    parts = [p.strip() for p in ligne.split(" / ") if p.strip()]
    out = {"m": None, "s": None, "sl": None, "q": None, "ql": None, "c": None}
    if parts and re.match(r"(?i)^classe\s+(.+)$", parts[-1]):
        out["c"] = re.match(r"(?i)^classe\s+(.+)$", parts.pop()).group(1).strip()
    if parts and _code(parts[0])[0] is None and len(parts) >= 1 and (len(parts) > 1 or not parts[0].isupper()):
        out["m"] = parts.pop(0)
    mid = [_code(p) for p in parts]
    if len(mid) >= 2:
        (out["s"], out["sl"]), (out["q"], out["ql"]) = mid[0], mid[1]
        if len(mid) > 2:
            out["ql"] = " / ".join(x for x in [out["ql"]] + [((c + " ") if c else "") + (l or "") for c, l in mid[2:]] if x)
    elif mid:
        c, l = mid[0]
        if c and "." in c:
            out["q"], out["ql"] = c, l
        else:
            out["s"], out["sl"] = c, l
    return out


def lire_fiche(h_tronque, masquer=True):
    """Champs de fiche du schéma catalogue. Une information absente vaut None (ou [] pour les listes)."""
    h = h_tronque
    lim = h_ = None
    dl = _txt(h, "dateHeureLimiteRemisePlis")
    if dl:
        m = re.match(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", dl)
        if m:
            lim, h_ = date_iso(m.group(1)), m.group(2)
    acheteur = _txt(h, "entiteAchat")
    mo = acheteur.split(" - ", 1)[1].strip() if acheteur and " - " in acheteur else acheteur
    proc = _txt(h, "typeProcedure")
    nb_lots = _txt(h, "nbrLots")
    lien_lots = nettoyer(_id(h, "linkDetailLots", "a"))
    allot = nb_lots or (None if vide_portail(lien_lots) else lien_lots)
    lieux = _txt(h, "lieuxExecutionSuite") or _txt(h, "lieuxExecutions")

    # zones « référentiel » : Estimation (montant), TPE/PME (radio)
    est = None
    tp = None
    for titre, val in re.findall(r'_titre">([^<]*)</span>.*?_label\w+"[^>]*>([^<]*)</span>', h, re.S):
        t = nettoyer(titre) or ""
        if t.startswith("Estimation"):
            est = montant(val)
        elif t.startswith("Réservé à la TPE"):
            v = (nettoyer(val) or "").lower()
            tp = True if v == "oui" else False if v == "non" else None

    non_alloti_visible = _panel_visible(h, "panelConsultationNonAlotti")
    cau = montant(_txt(h, "cautionProvisoire")) if non_alloti_visible else None
    q_txt = _li(h, "qualification")
    q = [lire_qualification(x) for x in q_txt]
    ag_l = _li(h, "agrements")
    ag = " ; ".join(ag_l) if ag_l else None
    proto = _bloc_panel(h, "panelEchantillons")
    reu = _bloc_panel(h, "panelReunion")
    vis = _bloc_panel(h, "panelVisitesLieux")
    var_txt = (_txt(h, "varianteValeur") or "").lower()
    var = True if var_txt == "oui" else False if var_txt == "non" else None
    dom = _li(h, "domainesActivite")
    ouv = _txt(h, "lieuOuverturePlis")
    dep = _txt(h, "adresseDepotOffres")
    if masquer:
        vis, reu, proto = masquer_coordonnees(vis), masquer_coordonnees(reu), masquer_coordonnees(proto)
    return {
        "ref": _txt(h, "reference"), "obj": _txt(h, "objet"), "mo": mo, "acheteur_code": acheteur.split(" - ", 1)[0] if acheteur and " - " in acheteur else None,
        "type_annonce": _txt(h, "annonce"), "proc": proc, "mode_passation": (_txt(h, "modePassation") or "").lstrip("| ").strip() or None,
        "cat": _txt(h, "categoriePrincipale"), "lim": lim, "h": h_, "lieux_fiche": lieux,
        "est": est, "tp": tp, "cau": cau, "q": q, "q_txt": q_txt, "ag": ag, "vis": vis, "reu": reu, "var": var,
        "allot": allot, "dom": dom, "ouv": ouv, "dep": dep, "proto": proto,
        "version_lecture": VERSION_LECTURE,
    }


def fiche_valide(f):
    """Garde-fou : une page sans référence ni objet n'est pas une fiche (erreur, page de contrôle…)."""
    return bool(f.get("ref") and f.get("obj"))

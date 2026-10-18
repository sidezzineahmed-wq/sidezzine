"""Popup public « Détail des lots » d'une consultation allotie PMMP (commun.PopUpDetailLots), sans login.

Une consultation allotie publie estimation, caution, qualifications, agréments, visites, TPE/PME… PAR LOT dans ce popup
(la fiche principale les laisse vides). Chaque lot est lu tel que publié, sans aplatir ni sommer :
  - valeur publiée -> champ renseigné (montants en float, tels que publiés : l'estimation reste TTC, aucune conversion) ;
  - « - » ou vide sur un bloc affiché -> nom du champ dans « ni » (non indiqué par l'acheteur) ;
  - bloc absent ou masqué (display:none) -> nom du champ dans « na » (non affiché par le portail).
Identité : l'action du formulaire du popup doit porter la même organisation et la même consultation que la demande.
Coordonnées (téléphones, e-mails) masquées dans les textes libres.
"""
import re

from .html_outils import masquer_coordonnees, montant, nettoyer, vide_portail
from .pmmp_fiche import lire_qualification

# le portail écrit « orgAccronyme » (deux c) dans ce lien
PARAMS_LOTS = lambda r, o: {"page": "commun.PopUpDetailLots", "orgAccronyme": o, "refConsultation": r, "lang": "fr"}
CHAMPS_LOT = ("est", "cau", "q", "ag", "proto", "reu", "vis", "var", "env", "tp")


def _bloc_lot(h):
    """[(ctl, html du lot)] dans l'ordre de la page."""
    fin = h.find("Fin Bloc Detail Lots")
    corps = h if fin < 0 else h[:fin]
    pos = [m.start() for m in re.finditer(r"<!--\s*Debut Lot\b[^>]*-->", corps)]
    out = []
    for a, b in zip(pos, pos[1:] + [len(corps)]):
        s = corps[a:b]
        m = re.search(r"repeaterLots_ctl(\d+)_", s)
        if m:
            out.append((m.group(1), s))
    return out


def _span(s, pfx, suffixe):
    m = re.search(r'id="' + pfx + suffixe + r'"[^>]*>(.*?)</span>', s, re.S)
    return m.group(1) if m else None


def _panel(s, pfx, nom):
    """(present, visible, html du panneau jusqu'au panneau suivant)"""
    m = re.search(r'<div id="' + pfx + nom + r'"([^>]*)>', s)
    if not m:
        return False, False, None
    visible = "none" not in re.sub(r"\s", "", (re.search(r'style="([^"]*)"', m.group(1)) or [None, ""])[1])
    reste = s[m.end():]
    n = re.search(r'<div id="' + pfx + r'panel(?!PasVisite|RepeaterVisite|BlocConsEnv)|<!--\s*(?:Fin|Debut) ', reste)
    return True, visible, reste[: n.start()] if n else reste


def _texte_panel(corps):
    corps = re.sub(r"<script.*?</script>", "", corps or "", flags=re.S)
    corps = re.sub(r'<div class="intitule-bloc[^"]*">.*?</div>', "", corps, count=1, flags=re.S)
    v = nettoyer(corps)
    return None if vide_portail(v) else v


def _liste(brut):
    if brut is None:
        return None
    items = [nettoyer(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", brut, re.S)]
    items = [x for x in items if x and not vide_portail(x)]
    if not items:
        v = nettoyer(brut)
        items = [] if vide_portail(v) else [v]
    return items


def _apres_intitule(s, libelle):
    m = re.search(r"<span>" + libelle + r"</span>\s*:\s*</div>\s*<div class=\"content-bloc[^\"]*\">(.*?)</div>", s, re.S)
    return nettoyer(m.group(1)) if m else None


def lire_lots(h, masquer=True):
    """Liste des lots du popup, dans l'ordre publié. Chaque lot : num, intitule, cat, description, est/est_brut/est_libelle,
    cau, q (lignes {m,s,sl,q,ql,c}), ag (liste), proto, reu, vis, var, env, tp, autres (zones référentiel non reconnues),
    ni (non indiqué), na (non affiché)."""
    lots = []
    for ctl, s in _bloc_lot(h):
        pfx = f"ctl0_CONTENU_PAGE_repeaterLots_ctl{ctl}_"
        L = {"num": None, "intitule": None, "cat": None, "description": None, "ni": [], "na": []}
        m = re.search(r"<span>Lot</span>\s*([^<:]+?)\s*:", s)
        L["num"] = m.group(1).strip() if m else None
        m = re.search(r'<div class="d-flex"[^>]*>(.*?)<div id="' + pfx + r'panelConsEnvIcone', s, re.S) or \
            re.search(r'</span>\s*</div>\s*<div class="content-bloc[^"]*">(.*?)</div>', s, re.S)
        L["intitule"] = nettoyer(m.group(1)) if m else None
        L["cat"] = _apres_intitule(s, "Catégorie")
        L["description"] = _apres_intitule(s, "Description")
        # zones référentiel (texte : estimation ; radio : TPE/PME)
        autres = []
        for kind in ("ZoneText", "Radio"):
            for n, titre in re.findall(r'id="' + pfx + r'idRef\w*?_RepeaterReferentiel' + kind + r'_ctl(\d+)_titre">(.*?)</span>', s, re.S):
                t = nettoyer(titre) or ""
                val = nettoyer(_span(s, pfx, r'idRef\w*?_RepeaterReferentiel' + kind + "_ctl" + n + "_labelReferentiel" + kind))
                if t.startswith("Estimation"):
                    if vide_portail(val):
                        L["ni"].append("est")
                    else:
                        L["est"], L["est_brut"], L["est_libelle"] = montant(val), val, t
                elif t.startswith("Réservé à la TPE"):
                    v = (val or "").strip().lower()
                    if v in ("oui", "non"):
                        L["tp"] = v == "oui"
                    else:
                        L["ni"].append("tp")
                elif t:
                    autres.append({"titre": t, "valeur": None if vide_portail(val) else val})
        # le nom du référentiel peut varier : on cherche aussi le motif générique si rien n'a été vu
        if "est" not in L and "est" not in L["ni"]:
            L["na"].append("est")
        if "tp" not in L and "tp" not in L["ni"]:
            L["na"].append("tp")
        if autres:
            L["autres"] = autres
        blocs = [("cau", "panelCautionProvisoire", "cautionProvisoire"), ("q", "panelQualification", "qualification"),
                 ("ag", "panelAgrements", "agrements"), ("proto", "panelEchantillons", None), ("reu", "panelReunion", None),
                 ("vis", "panelVisitesLieux", None), ("var", "panelVariante", "varianteValeur"), ("env", "panelConsEnv", "consEnvValeur")]
        for k, panel, span in blocs:
            present, visible, corps = _panel(s, pfx, panel)
            if not present or not visible:
                L["na"].append(k)
                continue
            if k == "q":
                v = _liste(_span(s, pfx, span))
                v = [lire_qualification(x) for x in v] if v else None
            elif k == "ag":
                v = _liste(_span(s, pfx, span)) or None
            elif k == "cau":
                brut = nettoyer(_span(s, pfx, span))
                v = None if vide_portail(brut) else montant(brut)
                if v is not None:
                    L["cau_brut"] = brut
            elif k in ("var",):
                t = (nettoyer(_span(s, pfx, span)) or "").lower()
                v = True if t == "oui" else False if t == "non" else None
            elif k == "env":
                t = nettoyer(_span(s, pfx, span))
                v = None if vide_portail(t) else t
            else:
                v = _texte_panel(corps)
                if v and masquer:
                    v = masquer_coordonnees(v)
            if v is None:
                L["ni"].append(k)
            else:
                L[k] = v
        lots.append(L)
    return lots


def identite_popup(h, o, r):
    """Vrai si la page est bien le popup des lots de (o, r) : action du formulaire et titre."""
    act = re.search(r'<form[^>]*action="([^"]*)"', h)
    a = (act.group(1) if act else "").replace("&amp;", "&")
    return ("PopUpDetailLots" in a and f"orgAccronyme={o}&" in a + "&" and f"refConsultation={r}&" in a + "&"
            and "Descriptif des lots" in h)


def nb_lots_annonce(allot):
    """« 3 Lots » -> 3 ; None si illisible."""
    m = re.match(r"\s*(\d+)\s*Lot", allot or "", re.I)
    return int(m.group(1)) if m else None


def lire_popup(h, o, r, allot=None, masquer=True):
    """Résultat complet d'une lecture : {statut, n, n_annonce, lots}. statut : « lu » (tous les lots annoncés lus),
    « partiel » (moins de lots que « N Lots » de la fiche, ou bloc illisible), « inaccessible » (pas le bon popup)."""
    if not identite_popup(h, o, r):
        return {"statut": "inaccessible", "raison": "popup sans identité attendue", "lots": []}
    lots = lire_lots(h, masquer=masquer)
    na = nb_lots_annonce(allot)
    nums = [x["num"] for x in lots]
    ok = bool(lots) and (na is None or na == len(lots)) and all(nums) and len(set(nums)) == len(nums)
    return {"statut": "lu" if ok else "partiel", "n": len(lots), "n_annonce": na, "lots": lots,
            **({} if ok else {"raison": f"{len(lots)} lot(s) lisible(s) pour {na} annoncé(s)"})}

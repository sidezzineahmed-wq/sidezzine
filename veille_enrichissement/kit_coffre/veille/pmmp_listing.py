"""Listing public PMMP des « Annonces de consultation » (recherche avancée, sans login).

Mécanisme vérifié (02/10/2026) :
  GET  index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons
  POST même URL, formulaire PRADO + lancerRecherche          -> page 1 (10 lignes) + nombreElement
  POST listePageSizeTop=500 (PRADO_POSTBACK_TARGET = ce champ) -> 500 lignes / page, nombrePageTop
  POST numPageTop=n + DefaultButtonTop                         -> page n (vérifié par la collecte réelle)
Le filtre « classification » (Etat / Collectivité locale / Etablissement public) est IGNORÉ par le portail
(constaté le 2026-10-02 : total identique filtré / non filtré, même avec l'autopostback) : cls n'est pas collectée.
Fenêtre par défaut du portail : date limite entre aujourd'hui et +6 mois, mise en ligne entre -6 mois et
aujourd'hui, type d'annonce = « Annonce de consultation ». Les valeurs utilisées sont enregistrées dans la
couverture de chaque passage.

Pagination instable (constaté les 18/10 12:14 et 19/10 10:14, 11:15, 12:24 : total stable, lignes = total, mais 1 à 2
identifiants lus deux fois, donc autant de consultations jamais vues) : le tri du portail (catégorie, publication,
référence, objet, organisme, date limite) n'a pas de clé unique, l'ordre change d'une requête à l'autre. Les
partitions officielles vérifiées le 19/10/2026 sur le portail réel : le critère « date limite de remise des plis
entre / et » (dateMiseEnLigneStart/End, jj/mm/aaaa) est inclusif au jour et additif (19/10 : 182, 20/10 : 356,
19–20/10 : 538) ; une partition de ≤ 500 résultats se lit en UNE réponse (500 lignes/page), toutes ses lignes ont une
date limite dans la partition ; le critère « catégorie » (1 Travaux, 2 Fournitures, 3 Services) sert de
sous-partition d'un jour trop chargé.
"""
import datetime as _dt
import re

from .html_outils import date_iso, formulaire, nettoyer, options

P_RECH = "ctl0$CONTENU_PAGE$AdvancedSearch$"
P_RES = "ctl0$CONTENU_PAGE$resultSearch$"
PARAMS_RECHERCHE = {"page": "entreprise.EntrepriseAdvancedSearch", "searchAnnCons": ""}
CLASSIFICATIONS = {"1": "Etat", "2": "Collectivité locale", "3": "Etablissement public"}
CATEGORIES = {"1": "Travaux", "2": "Fournitures", "3": "Services"}
TAILLE_PAGE = 500


def date_portail(s):
    """« jj/mm/aaaa » du formulaire -> date."""
    j, m, a = s.split("/")
    return _dt.date(int(a), int(m), int(j))


def portail_date(d):
    return d.strftime("%d/%m/%Y")


def _span(row, suffixe):
    m = re.search(r'id="[^"]*_' + suffixe + r'"[^>]*>(.*?)</(?:span|div)>', row, re.S)
    return nettoyer(m.group(1)) if m else None


def total_et_pages(h):
    n = re.search(r'id="ctl0_CONTENU_PAGE_resultSearch_nombreElement"[^>]*>\s*(\d+)', h)
    p = re.search(r'id="ctl0_CONTENU_PAGE_resultSearch_nombrePageTop"[^>]*>\s*(\d+)', h)
    num = re.search(r'name="ctl0\$CONTENU_PAGE\$resultSearch\$numPageTop"[^>]*value="(\d+)"', h)
    taille = re.search(r'listePageSizeTop".*?<option selected="selected" value="(\d+)"', h, re.S)
    return {
        "total": int(n.group(1)) if n else None,
        "pages": int(p.group(1)) if p else None,
        "page": int(num.group(1)) if num else None,
        "taille_page": int(taille.group(1)) if taille else None,
    }


def lignes(h):
    """Découpe la page de résultats en lignes de consultation (une par refCons)."""
    morceaux = h.split("<tr class=")
    return [m for m in morceaux[1:] if re.search(r'\$refCons"[^>]*value="\d+"', m)]


def lire_ligne(row, referentiel_provinces, alias=None):
    alias = alias or {}
    r = re.search(r'\$refCons"[^>]*value="(\d+)"', row).group(1)
    o = re.search(r'\$orgCons"[^>]*value="([^"]*)"', row).group(1)
    proc = None
    m = re.search(r'_panelBlocTypesProc"[^>]*>(.*?)</div>\s*</div>', row, re.S)
    if m:
        proc = nettoyer(m.group(1))
    cat = _span(row, "panelBlocCategorie")
    pub = None
    m = re.search(r'_panelBlocCategorie"[^>]*>.*?</div>\s*<div>\s*(\d{2}/\d{2}/\d{4})', row, re.S)
    if m:
        pub = date_iso(m.group(1))
    ref = _span(row, "reference")
    obj = None
    m = re.search(r'_infosBullesObjet"[^>]*>\s*<div>(.*?)</div>', row, re.S)
    if m:
        obj = nettoyer(m.group(1))
    if not obj:
        m = re.search(r'_panelBlocObjet"[^>]*>(.*?)<span', row, re.S)
        obj = nettoyer(re.sub(r"<strong>.*?</strong>", "", m.group(1), flags=re.S)) if m else None
    mo = None
    m = re.search(r'_panelBlocDenomination"[^>]*>(.*?)</div>', row, re.S)
    if m:
        mo = nettoyer(re.sub(r"<strong>.*?</strong>", "", m.group(1), flags=re.S))
    # lieux : info-bulle complète « MAROC, TETOUAN, FAHS-ANJRA » ; repli sur le bloc visible
    lieux_txt = None
    m = re.search(r'_infosLieuExecution" class="info-bulle"><div>(.*?)</div>', row, re.S)
    if m:
        lieux_txt = nettoyer(m.group(1))
    lieux = [x.strip() for x in (lieux_txt or "").split(",") if x.strip()]
    if not lieux:
        m = re.search(r'_panelBlocLieuxExec"[^>]*>(.*?)<div class="bloc-info-bulle"', row, re.S)
        if m:
            lieux = [x for x in [nettoyer(t) for t in re.split(r"<br\s*/?>", m.group(1))] if x]
    nat = any(x.upper() == "MAROC" for x in lieux)
    lieux_sans_pays = []
    for x in lieux:
        if x.upper() == "MAROC":
            continue
        x = alias.get(x, x)
        if x not in lieux_sans_pays:
            lieux_sans_pays.append(x)
    lx = [x for x in lieux_sans_pays if x in referentiel_provinces]
    etr = [x for x in lieux_sans_pays if x not in referentiel_provinces]
    lim = h = None
    m = re.search(r'headers="cons_dateEnd".*?<div class="cloture-line">\s*(\d{2}/\d{2}/\d{4})\s*<br\s*/?>\s*(\d{2}:\d{2})', row, re.S)
    if m:
        lim, h = date_iso(m.group(1)), m.group(2)
    m = re.search(r'picto-details\.gif"\s+style="([^"]*)"', row)
    lots = bool(m) and "none" not in m.group(1)
    # le bloc logoConsEnv n'existe que pour les consultations signalées « dispositions environnementales »
    env = "_logoConsEnv\"" in row
    return {
        "r": r, "o": o, "ref": ref, "obj": obj, "mo": mo, "cat": cat, "proc": proc, "pub": pub,
        "lim": lim, "h": h, "lx": lx, "nat": nat, "etr": etr, "lots": lots, "env": env,
        "lieux_portail": lieux,
    }


class CollecteListing:
    """Pilote une recherche « Annonces de consultation » ; n'écrit rien, renvoie des pages HTML brutes."""

    def __init__(self, client):
        self.c = client
        self.url = None
        self.h = None
        self.fenetre = None
        self.organismes = {}
        self.types_annonce = []
        self.procedures = []

    def ouvrir(self):
        r = self.c.get(PARAMS_RECHERCHE)
        self.url, self.h = r.url, r.content.decode("utf-8", "replace")
        f = formulaire(self.h)
        self.fenetre = {k: f.get(P_RECH + k) for k in (
            "dateMiseEnLigneStart", "dateMiseEnLigneEnd", "dateMiseEnLigneCalculeStart", "dateMiseEnLigneCalculeEnd",
            "annonceType", "classification", "categorie", "procedureType", "organismesNames")}
        self.fenetre["_libelles"] = {
            "dateMiseEnLigneStart/End": "Date limite de remise des plis : entre / et",
            "dateMiseEnLigneCalculeStart/End": "Date de mise en ligne : entre / et",
        }
        self.organismes = {v: t for v, t in options(self.h, "organismesNames") if v != "0"}
        self.types_annonce = [(v, t) for v, t in options(self.h, "annonceType") if v != "0"]
        self.procedures = [v for v, t in options(self.h, "procedureType") if v != "0"]
        return self.h

    def rechercher(self, classification=None, fenetre=None):
        """Lance la recherche (formulaire par défaut, éventuellement filtré par classification)."""
        if self.h is None:
            self.ouvrir()
        d = formulaire(self.h)
        if classification:
            d[P_RECH + "classification"] = classification
        for k, v in (fenetre or {}).items():
            d[P_RECH + k] = v
        d[P_RECH + "lancerRecherche"] = "Lancer la recherche"
        r = self.c.post(self.url, d)
        h = r.content.decode("utf-8", "replace")
        self.url_res = r.url
        return h, d

    def taille_500(self, h):
        d = formulaire(h)
        d[P_RES + "listePageSizeTop"] = "500"
        d["PRADO_POSTBACK_TARGET"] = P_RES + "listePageSizeTop"
        r = self.c.post(self.url_res, d)
        return r.content.decode("utf-8", "replace")

    def partition(self, du, au, categorie=None, procedure=None):
        """Recherche officielle restreinte à une date limite entre du et au (dates incluses) et, au besoin, à une
        catégorie et un type de procédure. Renvoie (html de la page 1, compteurs). Le reste du formulaire (mise en ligne,
        type d'annonce) garde les valeurs lues à l'ouverture (fenêtre fixée pour tout le passage)."""
        f = {"dateMiseEnLigneStart": portail_date(du), "dateMiseEnLigneEnd": portail_date(au)}
        for k in ("dateMiseEnLigneCalculeStart", "dateMiseEnLigneCalculeEnd"):
            if (self.fenetre or {}).get(k):
                f[k] = self.fenetre[k]
        if categorie:
            f["categorie"] = categorie
        if procedure:
            f["procedureType"] = procedure
        h, _ = self.rechercher(fenetre=f)
        return h, total_et_pages(h)

    def page(self, h, n):
        d = formulaire(h)
        d[P_RES + "numPageTop"] = str(n)
        d[P_RES + "DefaultButtonTop"] = ""
        d["PRADO_POSTBACK_TARGET"] = P_RES + "DefaultButtonTop"
        r = self.c.post(self.url_res, d)
        return r.content.decode("utf-8", "replace")

"""Copie canonique des conditions générales servies en HTML (PMMP, page commun.ConditionsUtilisation) — algorithme versionné.

Constat (05/10/2026) : la page des conditions (PRADO, ~48 Ko) était hachée octet pour octet ; ses octets portent un état de
page, des attributs de session, des scripts et un bandeau date/heure hors du contenu. Relevé DOM officiel : une section
UNIQUE div#main-part.main-part contient l'intégralité des « Conditions d'utilisation » et des « Pré-requis techniques »
(rubriques rubrique_1, rubrique_2… et leurs paragraphes) ; le bandeau date/heure est hors de cette section.

Algorithme ALGO (cg-v3) pour un document HTML :
  - décodage STRICT : encodage déclaré (en-tête HTTP et/ou <meta charset>), connu, concordant ; octet invalide : REFUS ;
  - document complet (balise </html> finale) ; section : exactement UN élément d'id « main-part », de balise div, de classe
    « main-part », fermé ; elle doit contenir les rubriques rubrique_1 puis rubrique_2 (une fois chacune, chacune avec du
    contenu) et les titres observés « Conditions d'utilisation » et « Pré-requis techniques » ; sinon REFUS (page d'erreur,
    section vide, incomplète ou tronquée) — aucune empreinte de repli ;
  - conservé, dans l'ordre : TOUT le texte de la section, y compris le contenu replié ou masqué (aucun CSS n'est évalué :
    une clause cachée compte comme une clause affichée), les repères de rubrique (§ rubrique_N), la cible COMPLÈTE des
    liens et des images (schéma, hôte, port, chemin, paramètres, ancre), le texte alternatif des images ;
  - paramètres d'URL : seuls les paramètres TECHNIQUES de la liste étroite PARAMS_TECHNIQUES sont retirés ; un paramètre
    au nom évoquant un secret (MOTIF_SECRET) n'apparaît que par l'empreinte de sa valeur (jamais la valeur) ; tous les
    autres (document, revision, lang, v…) sont conservés tels quels ;
  - exclu : <script>, <style>, <noscript>, <template>, les autres attributs, les commentaires, les valeurs de champs ;
  - copie canonique = lignes normalisées (NFC, espaces) jointes par « \\n » ; empreinte = SHA-256 de cette copie.
Document non HTML (PDF…) : SHA-256 des octets complets, inchangé."""
import hashlib
import re
import unicodedata
from html.parser import HTMLParser
import codecs
from urllib.parse import parse_qsl, urlparse

ALGO = "cg-v3"   # cg-v2 (commit 9dc0413) n'a jamais été déployé
PARAMS_TECHNIQUES = {"phpsessid", "jsessionid", "prado_pagestate", "prado_postback_target", "prado_postback_parameter",
                     "prado_callback_target", "prado_callback_parameter"}
MOTIF_SECRET = re.compile(r"token|jeton|secret|session|sid|csrf|nonce|auth|key|signature|sig|pass", re.I)
TITRES = ("Conditions d'utilisation", "Pré-requis techniques")
EXCLUS = {"script", "style", "noscript", "template"}
BLOCS = {"address", "article", "aside", "blockquote", "br", "caption", "dd", "div", "dl", "dt", "fieldset", "figcaption", "figure",
         "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "label", "legend", "li", "main", "nav", "ol", "p",
         "pre", "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul", "details", "summary", "option", "button"}
RUBRIQUE = re.compile(r"^rubrique_\d+$")


class ExtractionRefusee(ValueError):
    pass


def _norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def _h(v):
    return "#empreinte:" + hashlib.sha256(v.encode()).hexdigest()[:16]


def cible(href):
    """Cible d'un lien ou d'une image, sémantique complète : schéma, hôte, port, chemin, paramètres (ordre d'origine), ancre.
    Retirés : paramètres de PARAMS_TECHNIQUES et « ;jsessionid=… » du chemin. Nom évoquant un secret : valeur remplacée par
    son empreinte. Schémas javascript:/data: : empreinte seulement."""
    href = (href or "").strip()
    if not href:
        return ""
    u = urlparse(href)
    if u.scheme.lower() in ("javascript", "data"):
        return u.scheme.lower() + ":" + _h(href)
    chemin = re.sub(r";jsessionid=[^/?#]*", "", u.path, flags=re.I)
    params = []
    for k, v in parse_qsl(u.query, keep_blank_values=True):
        if k.lower() in PARAMS_TECHNIQUES:
            continue
        params.append(f"{k}={_h(v) if MOTIF_SECRET.search(k) else v}")
    ident = (_h(u.netloc.rsplit("@", 1)[0]) + "@") if "@" in u.netloc else ""   # identifiants dans l'URL : empreinte, jamais la valeur
    reseau = ((u.scheme + ":" if u.scheme else "") + ("//" + ident + (u.hostname or "") + (f":{u.port}" if u.port else "") if u.netloc else ""))
    return reseau + chemin + ("?" + "&".join(params) if params else "") + (f"#{u.fragment}" if u.fragment else "")


class _Section(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.trouvees, self.formes, self.prof, self.exclus, self.buf, self.lignes, self.liens = 0, [], 0, [], [], [], []

    def _vider(self):
        s = _norm("".join(self.buf))
        if s:
            self.lignes.append(s)
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id") == "main-part":
            self.trouvees += 1
            self.formes.append((tag, "main-part" in (a.get("class") or "").split()))
            if self.trouvees == 1 and tag == "div":
                self.prof = 1
                return
        if not self.prof:
            return
        if tag == "div":
            self.prof += 1
        if tag in EXCLUS:
            self.exclus.append(tag)
            return
        if self.exclus:
            return
        if tag in BLOCS:
            self._vider()
        if RUBRIQUE.match(a.get("id") or ""):
            self._vider()
            self.lignes.append("§ " + a["id"])
        if tag == "a":
            self.liens.append(cible(a.get("href")))
        elif tag == "img":
            self._img(a)

    def _img(self, a):
        self.buf.append(f" [image : {_norm(a.get('alt') or '')} ({cible(a.get('src'))})] ")

    def handle_startendtag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id") == "main-part":
            self.trouvees += 1
            self.formes.append((tag, False))
        if not self.prof or self.exclus:
            return
        if tag in BLOCS:
            self._vider()
        if tag == "img":
            self._img(a)

    def handle_endtag(self, tag):
        if not self.prof:
            return
        if tag in self.exclus:
            del self.exclus[len(self.exclus) - 1 - self.exclus[::-1].index(tag):]
            return
        if self.exclus:
            return
        if tag == "a" and self.liens:
            c = self.liens.pop()
            if c:
                self.buf.append(f" [→ {c}]")
        if tag in BLOCS:
            self._vider()
        if tag == "div":
            self.prof -= 1
            if not self.prof:
                self._vider()

    def handle_data(self, data):
        if self.prof and not self.exclus:
            self.buf.append(data)


def canonique(html):
    """Copie canonique (texte) de la section des conditions ; ExtractionRefusee si la section est introuvable ou ambiguë."""
    p = _Section()
    p.feed(html)
    p.close()
    if p.trouvees != 1:
        raise ExtractionRefusee(f"section des conditions #main-part {'absente' if not p.trouvees else f'ambiguë ({p.trouvees})'}")
    if p.formes[0] != ("div", True):
        raise ExtractionRefusee("section #main-part de forme inattendue (div.main-part attendu)")
    if p.prof:
        raise ExtractionRefusee("section #main-part non fermée")
    if not p.lignes:
        raise ExtractionRefusee("section #main-part sans texte")
    _structure(p.lignes)
    return "\n".join(p.lignes)


def _cle(s):
    return unicodedata.normalize("NFC", s).replace("\u2019", "'").casefold()


def _structure(lignes):
    """Structure observée de la page des conditions : rubrique_1 puis rubrique_2, une fois chacune, chacune avec un contenu
    autre que son titre, et les deux titres attendus ; sinon (page d'erreur, section incomplète) refus."""
    rub = [i for i, x in enumerate(lignes) if x.startswith("§ rubrique_")]
    noms = [lignes[i][2:] for i in rub]
    for r in ("rubrique_1", "rubrique_2"):
        if noms.count(r) != 1:
            raise ExtractionRefusee(f"section incomplète : {r} {'absente' if not noms.count(r) else 'en double'}")
    if noms.index("rubrique_1") > noms.index("rubrique_2"):
        raise ExtractionRefusee("section inattendue : rubrique_2 avant rubrique_1")
    cles = [_cle(x) for x in lignes]
    for t in TITRES:
        if _cle(t) not in cles:
            raise ExtractionRefusee(f"section incomplète : titre « {t} » absent")
    titres = {_cle(t) for t in TITRES}
    for k, i in enumerate(rub):
        bloc = lignes[i + 1:(rub[k + 1] if k + 1 < len(rub) else len(lignes))]
        if not [x for x in bloc if _cle(x) not in titres]:
            raise ExtractionRefusee(f"section incomplète : {noms[k]} sans contenu")


def decoder(corps, content_type):
    """Décodage STRICT : encodage déclaré (en-tête et/ou <meta>), connu et concordant ; document complet. Sinon refus."""
    def nom(x):
        try:
            return codecs.lookup(x).name
        except LookupError:
            raise ExtractionRefusee(f"encodage inconnu : {x}") from None
    m = re.search(r"charset=[\"']?([\w.:-]+)", content_type or "", re.I)
    entete = nom(m.group(1)) if m else None
    mm = re.search(rb"<meta[^>]+charset=[\"']?([\w.:-]+)", corps[:4096], re.I)
    meta = nom(mm.group(1).decode("ascii")) if mm else None
    if entete and meta and entete != meta:
        raise ExtractionRefusee(f"encodages contradictoires (en-tête {entete}, page {meta})")
    enc = entete or meta
    if not enc:
        raise ExtractionRefusee("encodage non déclaré")
    try:
        html = corps.decode(enc)
    except UnicodeDecodeError as x:
        raise ExtractionRefusee(f"octets invalides pour {enc} (position {x.start})") from None
    if not re.search(r"</html\s*>\s*(<!--.*?-->\s*)*$", html, re.I | re.S):
        raise ExtractionRefusee("document tronqué (balise </html> finale absente)")
    return html


def empreinte(texte):
    return hashlib.sha256(texte.encode()).hexdigest()


def differences(avant, apres, max_lignes=200):
    """Lignes retirées (-) et ajoutées (+) entre deux copies canoniques, pour décision humaine."""
    import difflib
    d = [x for x in difflib.unified_diff((avant or "").split("\n"), (apres or "").split("\n"), "validee", "lue", n=1, lineterm="")]
    return d[:max_lignes] + ([f"… {len(d) - max_lignes} lignes de plus"] if len(d) > max_lignes else [])

"""Copie canonique des conditions générales servies en HTML (PMMP, page commun.ConditionsUtilisation) — algorithme versionné.

Constat (05/10/2026) : la page des conditions (PRADO, ~48 Ko) était hachée octet pour octet ; ses octets portent un état de
page, des attributs de session, des scripts et un bandeau date/heure hors du contenu. Relevé DOM officiel : une section
UNIQUE div#main-part.main-part contient l'intégralité des « Conditions d'utilisation » et des « Pré-requis techniques »
(rubriques rubrique_1, rubrique_2… et leurs paragraphes) ; le bandeau date/heure est hors de cette section.

Algorithme ALGO (cg-v2) pour un document HTML :
  - section : exactement UN élément d'id « main-part », de balise div, de classe « main-part » ; absente, multiple, d'une autre
    forme ou sans texte : REFUS (aucune empreinte de repli) ;
  - conservé, dans l'ordre : TOUT le texte de la section, y compris le contenu replié ou masqué (aucun CSS n'est évalué :
    une clause cachée compte comme une clause affichée), les repères de rubrique (§ rubrique_N), la cible des liens
    (chemin, paramètre « page » et ancre uniquement : aucun autre paramètre d'URL, donc aucun jeton de session), les
    images (texte alternatif et chemin) ;
  - exclu : <script>, <style>, <noscript>, <template>, tous les attributs hors ceux cités, les commentaires, les valeurs
    de champs (aucune valeur de <input> n'est lue) ;
  - copie canonique = lignes normalisées (NFC, espaces) jointes par « \\n » ; empreinte = SHA-256 de cette copie.
Document non HTML (PDF…) : SHA-256 des octets complets, inchangé."""
import hashlib
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

ALGO = "cg-v2"
EXCLUS = {"script", "style", "noscript", "template"}
BLOCS = {"address", "article", "aside", "blockquote", "br", "caption", "dd", "div", "dl", "dt", "fieldset", "figcaption", "figure",
         "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "label", "legend", "li", "main", "nav", "ol", "p",
         "pre", "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul", "details", "summary", "option", "button"}
RUBRIQUE = re.compile(r"^rubrique_\d+$")


class ExtractionRefusee(ValueError):
    pass


def _norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def cible(href):
    """Cible significative d'un lien, sans jeton : hôte éventuel, chemin, paramètre « page », ancre."""
    href = (href or "").strip()
    if not href:
        return ""
    if href.lower().startswith(("javascript:", "data:")):
        return "action"
    if href.startswith("#"):
        return href
    u = urlparse(href)
    if u.scheme == "mailto":
        return "mailto:" + u.path
    page = parse_qs(u.query).get("page")
    return (u.hostname or "") + u.path + (f"?page={page[0]}" if page else "") + (f"#{u.fragment}" if u.fragment else "")


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
    return "\n".join(p.lignes)


def empreinte(texte):
    return hashlib.sha256(texte.encode()).hexdigest()


def charset(content_type):
    m = re.search(r"charset=([\w-]+)", content_type or "", re.I)
    return m.group(1) if m else "utf-8"


def differences(avant, apres, max_lignes=200):
    """Lignes retirées (-) et ajoutées (+) entre deux copies canoniques, pour décision humaine."""
    import difflib
    d = [x for x in difflib.unified_diff((avant or "").split("\n"), (apres or "").split("\n"), "validee", "lue", n=1, lineterm="")]
    return d[:max_lignes] + ([f"… {len(d) - max_lignes} lignes de plus"] if len(d) > max_lignes else [])

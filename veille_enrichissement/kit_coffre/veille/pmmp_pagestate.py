"""Lecture PASSIVE et bornée de l'état de page PRADO (champ caché PRADO_PAGESTATE) d'une fiche PMMP déjà reçue.

But : relire HORS LIGNE, dans une page authentique déjà lue et conservée (coupée avant le contact par l'ancien lecteur), le
seul contact administratif PUBLIÉ dans le résumé de la consultation (nom / service, e-mail, téléphone, télécopieur).

Sécurité : aucun eval, pickle ni unserialize ; aucune classe instanciée, aucun arbre de valeurs construit. Décodage base64
strict puis zlib plafonné ; un parcours structurel borné SAUTE les valeurs (longueurs déclarées vérifiées) pour situer les
clés ; seules des chaînes placées sous des chemins publics exacts du composant de résumé sont lues. Rien d'autre de l'état
n'est lu, gardé ni republié (ni compte, ni jeton, ni zone entreprise, ni état brut).

Refus (None, « non encore lu ») : état absent / trop grand / illisible ; structure globale non conforme (préfixe
d'empreinte de 40 hex puis une seule racine couvrant tout l'état) ; structure inattendue ; clé absente ou multiple ;
référence ou objet de l'état ≠ ceux affichés dans la même page ; contexte de page (formulaire) d'une autre consultation ;
panneau du contact invisible ; valeur gabarit (@@@@).

Pièces de la consultation : NON lues depuis l'état. La visibilité de chaque lien (<li style="display:…">) est rendue par le
gabarit HTML et ne figure pas dans l'état ; un libellé ou un lien de l'état ne prouve donc pas une pièce publiée."""
import base64
import binascii
import re
import zlib

MAX_B64 = 2_000_000
MAX_ETAT = 4_000_000
MAX_PROF = 64
MAX_PAS = 3_000_000
_STATE = re.compile(r'id="PRADO_PAGESTATE" value="([A-Za-z0-9+/=]*)"')
_FORM = re.compile(r'<form[^>]*\saction="[^"]*?refConsultation=([^"&]+)&amp;orgAcronyme=([^"&]+)"')
RESUME = "idEntrepriseConsultationSummary"


class EtatInvalide(Exception):
    pass


def decoder(h):
    """Octets de l'état de page, ou None (absent, multiple, trop grand, base64 / zlib invalide, flux incomplet)."""
    ms = _STATE.findall(h or "")
    if len(ms) != 1 or not ms[0] or len(ms[0]) > MAX_B64:
        return None
    try:
        d = zlib.decompressobj()
        b = d.decompress(base64.b64decode(ms[0], validate=True), MAX_ETAT)
        if d.unconsumed_tail or not d.eof or d.unused_data:
            return None
        return b
    except (binascii.Error, ValueError, zlib.error):
        return None


_ENT = re.compile(rb"(-?\d{1,19});")
_NB = re.compile(rb"(\d{1,7})")


class _Parcours:
    """Saute les valeurs sérialisées sans les construire (compte de pas et profondeur bornés)."""

    def __init__(self, b):
        self.b, self.pas = b, 0

    def _n(self, i):
        m = _NB.match(self.b, i)
        if not m:
            raise EtatInvalide("longueur")
        return int(m.group(1)), m.end()

    def chaine(self, i):
        if self.b[i:i + 2] != b"s:":
            raise EtatInvalide("chaîne attendue")
        n, j = self._n(i + 2)
        if self.b[j:j + 2] != b':"' or self.b[j + 2 + n:j + 4 + n] != b'";':
            raise EtatInvalide("longueur de chaîne")
        return self.b[j + 2:j + 2 + n], j + 4 + n

    def cle(self, i):
        """Clé de tableau : (bytes ou int, fin)."""
        if self.b[i:i + 2] == b"i:":
            m = _ENT.match(self.b, i + 2)
            if not m:
                raise EtatInvalide("clé entière")
            return int(m.group(1)), m.end()
        return self.chaine(i)

    def fin(self, i, prof=0):
        self.pas += 1
        if prof > MAX_PROF or self.pas > MAX_PAS:
            raise EtatInvalide("trop profond / trop long")
        b, t = self.b, self.b[i:i + 2]
        if t == b"N;":
            return i + 2
        if t == b"b:":
            if b[i + 2:i + 4] not in (b"0;", b"1;"):
                raise EtatInvalide("booléen")
            return i + 4
        if t == b"i:":
            m = _ENT.match(b, i + 2)
            if not m:
                raise EtatInvalide("entier")
            return m.end()
        if t == b"d:":
            m = re.compile(rb"[-0-9.EeINFA]{1,40};").match(b, i + 2)
            if not m:
                raise EtatInvalide("décimal")
            return m.end()
        if t == b"s:":
            return self.chaine(i)[1]
        if t in (b"a:", b"O:"):
            return self.enfants(i, prof)[1]
        raise EtatInvalide("type non pris en charge")

    def enfants(self, i, prof=0):
        """Tableau (a:) ou propriétés d'objet (O:, lues comme données, jamais instanciées) : ([(clé, début, fin)], fin)."""
        b = self.b
        if b[i:i + 2] == b"O:":
            n, j = self._n(i + 2)
            if b[j:j + 2] != b':"' or b[j + 2 + n:j + 4 + n] != b'":':
                raise EtatInvalide("objet")
            m = _NB.match(b, j + 4 + n)  # nombre de propriétés
            if not m:
                raise EtatInvalide("objet")
            k, j = int(m.group(1)), m.end()
        elif b[i:i + 2] == b"a:":
            k, j = self._n(i + 2)
        else:
            raise EtatInvalide("tableau attendu")
        if b[j:j + 2] != b":{":
            raise EtatInvalide("tableau")
        j += 2
        out = []
        for _ in range(k):
            c, j = self.cle(j)
            f = self.fin(j, prof + 1)
            out.append((c, j, f))
            j = f
        if b[j:j + 1] != b"}":
            raise EtatInvalide("fin de tableau")
        return out, j + 1


def _fils(p, i, nom):
    """Valeur (début, fin) du fils direct nommé ; None si absent ou présent plusieurs fois."""
    nom = nom.encode() if isinstance(nom, str) else nom
    L = [(d, f) for c, d, f in p.enfants(i)[0] if c == nom]
    return L[0] if len(L) == 1 else None


def _texte(p, i):
    """Contrôle WebControl : a:1:{i:0;a:1:{s:4:"Text";s:..}} (exactement) -> texte."""
    E = p.enfants(i)[0]
    if len(E) != 1 or E[0][0] != 0:
        return None
    F = p.enfants(E[0][1])[0]
    if len(F) != 1 or F[0][0] != b"Text" or p.b[F[0][1]:F[0][1] + 2] != b"s:":
        return None
    try:
        return p.chaine(F[0][1])[0].decode("utf-8")
    except UnicodeDecodeError:
        return None


def _resume(p, b):
    """Valeur du composant de résumé : clé exacte présente une seule fois dans tout l'état, valeur tableau."""
    k = b's:%d:"%s";' % (len(RESUME), RESUME.encode())
    if b.count(k) != 1:
        return None
    i = b.find(k) + len(k)
    return i if b[i:i + 2] == b"a:" else None


def _trouver(p, i, nom, prof=0):
    """Toutes les positions de valeur de la clé nom dans le sous-arbre i (bornées)."""
    out = []
    if p.b[i:i + 2] not in (b"a:", b"O:") or prof > 12:
        return out
    for c, d, _f in p.enfants(i)[0]:
        if c == nom:
            out.append(d)
        out += _trouver(p, d, nom, prof + 1)
    return out


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _val(t):
    t = _norm(t)
    return None if t in ("", "-") else t


def contexte_page(h):
    """(ref, org) de l'action du formulaire de la page ; None si absent ou multiple."""
    L = set(_FORM.findall(h or ""))
    return next(iter(L)) if len(L) == 1 else None


def lire_contact(h, org, ref, ref_page, objet_page):
    """Contact publié relu dans l'état de la page h de la consultation (org, ref) : (dict, None) ou (None, motif)."""
    if contexte_page(h) != (str(ref), org):
        return None, "contexte de page d'une autre consultation ou absent"
    b = decoder(h)
    if b is None:
        return None, "état de page absent, multiple, trop grand ou illisible"
    p = _Parcours(b)
    try:
        # préfixe d'empreinte PRADO (40 hex, non vérifiable sans la clé du portail) puis UNE racine qui couvre tout l'état
        if not re.fullmatch(rb"[0-9a-f]{40}", b[:40]) or p.fin(40) != len(b):
            return None, "structure globale de l'état invalide (tronquée ou inattendue)"
        R = _resume(p, b)
        if R is None:
            return None, "composant de résumé absent ou multiple"
        ident = {}
        for k in ("reference", "objet"):
            L = _trouver(p, R, k.encode())
            if len(L) != 1:
                return None, f"clé {k} absente ou multiple dans le résumé"
            ident[k] = _texte(p, L[0])
        if not (ident["reference"] and ident["objet"] and _norm(ident["reference"]) == _norm(ref_page)
                and _norm(ident["objet"]) == _norm(objet_page)):
            return None, "référence / objet de l'état différents de la page"
        L = _trouver(p, R, b"panelContcatAdministratif")
        if len(L) != 1:
            return None, "panneau du contact absent ou multiple dans le résumé"
        P = L[0]
        props = _fils(p, P, 0)
        if props and b'"Visible";b:0;' in b[props[0]:props[1]]:
            return None, "panneau du contact invisible"
        c = _fils(p, P, "contactAdministratif")
        d = _fils(p, P, "blocDetailContactAdministratif")
        if not c or not d:
            return None, "structure du contact inattendue"
        out = {"nom": _texte(p, c[0])}
        for k, n in (("email", "email"), ("telephone", "tel"), ("telecopieur", "fax")):
            f = _fils(p, d[0], k)
            if not f:
                return None, "structure du contact inattendue"
            out[n] = _texte(p, f[0])
    except EtatInvalide as e:
        return None, f"état invalide ({e})"
    if any(v is None for v in out.values()):
        return None, "valeur de contact illisible"
    if any("@@@@" in v for v in out.values()):
        return None, "contact gabarit (@@@@)"
    return {k: _val(v) for k, v in out.items()}, None

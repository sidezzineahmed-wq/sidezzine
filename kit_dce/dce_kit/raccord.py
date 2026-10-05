"""Raccord manifest du kit -> stockage Drive : reconstitue l'archive ZIP BINAIRE à partir de sa copie texte base64.

Constat (05/10/2026, passage r20261005171636) : « telecharger » range l'archive d'origine en texte base64
(manifest.zip.fichier_local = base64/<nom>.b64.txt, chemin relatif) ; ce fichier était passé tel quel à
« drive_adapter stocker-dce », qui attend un ZIP binaire → ErreurIntegrite (archive illisible). Aucun refus de sécurité.

zip_binaire(manifest, racine, sortie) :
  - chemin : un fichier_local relatif est résolu par rapport au dossier du manifest, puis par rapport à la racine ; les
    candidats existants doivent désigner UN seul fichier ; son chemin réel (liens résolus) doit rester sous la racine ;
  - décodage STRICT : texte ASCII, alphabet base64 standard seulement (aucun caractère hors alphabet, aucun retour à la
    ligne interne), remplissage canonique (réencodage identique) ; seuls des blancs aux extrémités sont tolérés ;
  - vérifications AVANT toute écriture : taille et SHA-256 égaux à ceux du manifest, archive ZIP valide (zipcheck :
    signature, CRC, chemins, limites) ;
  - écriture : sous la racine seulement, fichier neuf (jamais d'écrasement d'un fichier différent), atomique, relu et
    revérifié. Aucun accès réseau, aucune écriture hors de la racine."""
import base64
import binascii
import hashlib
import json
import os
import re
import tempfile

from .zipcheck import ZipInvalide, inspecter


class RaccordInvalide(ValueError):
    pass


def _sous(chemin, racine):
    r = os.path.realpath(racine)
    c = os.path.realpath(chemin)
    return c == r or c.startswith(r + os.sep)


def _dossier_sous(dossier, racine):
    """Le chemin réel que prendrait `dossier` (existant ou à créer) est-il sous la racine ? Rien n'est créé : le plus
    proche ancêtre existant est résolu (liens compris), les composants absents lui sont ajoutés tels quels."""
    d, reste = os.path.abspath(dossier), []
    while not os.path.lexists(d):
        d, nom = os.path.split(d)
        if not nom:
            return False
        reste.insert(0, nom)
    if not os.path.isdir(d):
        return False
    return _sous(os.path.join(os.path.realpath(d), *reste), racine)


def _sha_fichier(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def resoudre(fichier_local, manifest, racine):
    """Chemin réel UNIQUE du fichier désigné par le manifest, sous la racine ; sinon RaccordInvalide."""
    if not isinstance(fichier_local, str) or not fichier_local.strip() or "\x00" in fichier_local:
        raise RaccordInvalide("manifest : fichier_local de l'archive absent")
    if os.path.isabs(fichier_local):
        bases = [""]
    else:
        bases = [os.path.dirname(os.path.abspath(manifest)), os.path.abspath(racine)]
    trouves = []
    for b in bases:
        c = os.path.realpath(os.path.join(b, fichier_local))
        if os.path.isfile(c) and c not in trouves:
            trouves.append(c)
    if not trouves:
        raise RaccordInvalide(f"archive base64 introuvable : {fichier_local}")
    if len(trouves) > 1:
        raise RaccordInvalide(f"chemin ambigu : {fichier_local} désigne plusieurs fichiers")
    if not _sous(trouves[0], racine):
        raise RaccordInvalide(f"archive base64 hors de la racine de travail : {fichier_local}")
    return trouves[0]


def decoder_strict(texte_octets, taille_max):
    if len(texte_octets) > (taille_max // 3 + 1) * 4 + 16:
        raise RaccordInvalide("texte base64 au-delà de la taille autorisée")
    try:
        t = texte_octets.decode("ascii")
    except UnicodeDecodeError:
        raise RaccordInvalide("texte base64 non ASCII") from None
    t = t.strip(" \t\r\n")
    if not t or len(t) % 4 or not re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", t):
        raise RaccordInvalide("texte base64 invalide (alphabet, longueur ou remplissage)")
    try:
        d = base64.b64decode(t, validate=True)
    except binascii.Error:
        raise RaccordInvalide("texte base64 invalide") from None
    if base64.b64encode(d).decode("ascii") != t:
        raise RaccordInvalide("texte base64 non canonique")
    return d


def zip_binaire(manifest, racine, sortie, zip_max=200 * 2**20):
    racine = os.path.abspath(racine)
    if not os.path.isdir(racine):
        raise RaccordInvalide("racine de travail absente")
    if not _sous(manifest, racine):
        raise RaccordInvalide("manifest hors de la racine de travail")
    try:
        with open(manifest, encoding="utf-8") as f:
            m = json.load(f)
        z = m["zip"]
        nom, taille, sha = z["nom"], z["taille"], z["sha256"]
    except (OSError, ValueError, KeyError, TypeError):
        raise RaccordInvalide("manifest illisible ou sans archive") from None
    if z.get("depot") != "texte_base64":
        raise RaccordInvalide(f"dépôt de l'archive inattendu : {z.get('depot')}")
    if not isinstance(taille, int) or isinstance(taille, bool) or taille <= 0 or not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
        raise RaccordInvalide("manifest : taille ou SHA-256 de l'archive invalide")
    if not isinstance(nom, str) or not nom.lower().endswith(".zip"):
        raise RaccordInvalide("manifest : nom d'archive inattendu")
    src = resoudre(z.get("fichier_local"), manifest, racine)
    with open(src, "rb") as f:
        octets = decoder_strict(f.read(), zip_max)
    if len(octets) != taille:
        raise RaccordInvalide(f"taille décodée {len(octets)} ≠ manifest {taille}")
    if hashlib.sha256(octets).hexdigest() != sha:
        raise RaccordInvalide("SHA-256 décodé différent du manifest")
    try:
        inv = inspecter(octets, zip_max=zip_max)
    except ZipInvalide as e:
        raise RaccordInvalide(f"archive invalide : {e}") from None
    sortie = os.path.abspath(sortie)
    dossier = os.path.dirname(sortie)
    if not _dossier_sous(dossier, racine) or os.path.islink(sortie):   # contrôle AVANT toute création
        raise RaccordInvalide("sortie hors de la racine de travail")
    os.makedirs(dossier, exist_ok=True)
    if not _sous(dossier, racine):                                      # recontrôle après création (chemin réel)
        raise RaccordInvalide("sortie hors de la racine de travail")
    if os.path.exists(sortie):
        if not os.path.isfile(sortie) or _sha_fichier(sortie) != sha:
            raise RaccordInvalide("un autre fichier existe déjà à l'emplacement de sortie : rien n'est écrasé")
    else:
        fd, tmp = tempfile.mkstemp(dir=dossier, prefix=".raccord-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(octets)
            os.replace(tmp, sortie)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
    if os.path.getsize(sortie) != taille or _sha_fichier(sortie) != sha:
        raise RaccordInvalide("archive écrite non conforme à la relecture")
    return {"etat": "ok", "zip": sortie, "nom": nom, "taille": taille, "sha256": sha, "entrees": len(inv["entrees"]),
            "source": os.path.relpath(src, racine)}

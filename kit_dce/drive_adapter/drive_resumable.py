"""Adaptateur Google Drive API v3 (bibliothèque standard uniquement), NON ACTIVÉ par défaut.

- Envoi « resumable » depuis un CHEMIN LOCAL, par morceaux (multiples de 256 Kio), reprise après interruption réseau ou après
  arrêt du processus (fichier d'état local, droits 0600), nombre de tentatives borné.
- Téléchargement en flux vers un fichier temporaire, contrôle de la taille et du SHA-256 attendu, renommage atomique ; un
  fichier dont l'empreinte diffère est supprimé et refusé.
- Identifiants OAuth de l'utilisateur, lus dans l'environnement (DCE_GDRIVE_CLIENT_ID, DCE_GDRIVE_CLIENT_SECRET,
  DCE_GDRIVE_REFRESH_TOKEN), portée drive.file. Le jeton d'accès reste en mémoire ; aucun jeton, secret ni identifiant de
  session d'envoi n'est écrit dans les journaux ou les messages d'erreur.
- N'utilise ni ne lit le connecteur Google Drive de claude.ai."""
import hashlib
import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

PORTEE = "https://www.googleapis.com/auth/drive.file"
URLS = {"jeton": "https://oauth2.googleapis.com/token",
        "envoi": "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,name,size,appProperties",
        "fichier": "https://www.googleapis.com/drive/v3/files/{id}?alt=media",
        "api": "https://www.googleapis.com/drive/v3/files",
        "maj": "https://www.googleapis.com/upload/drive/v3/files/{id}?uploadType=media&fields=id,name,size,md5Checksum,appProperties"}
CHAMPS = "id,name,size,md5Checksum,mimeType,parents,appProperties"
_ID = re.compile(r"[A-Za-z0-9_-]{10,200}")
VARIABLES = ("DCE_GDRIVE_CLIENT_ID", "DCE_GDRIVE_CLIENT_SECRET", "DCE_GDRIVE_REFRESH_TOKEN")
UNITE = 256 * 1024
log = logging.getLogger("drive_adapter")


class ErreurDrive(RuntimeError):
    pass


class ErreurConfig(ErreurDrive):
    pass


class ErreurAuth(ErreurDrive):
    pass


class ErreurIntegrite(ErreurDrive):
    pass


class _Masque(logging.Filter):
    """Masque tout ce qui ressemble à un jeton ou à un identifiant de session d'envoi, par sécurité supplémentaire."""
    MOTIFS = [re.compile(r"(Bearer\s+)[^\s\"']+"), re.compile(r"((?:access|refresh)_token[\"'=:\s]+)[^\s\"'&,}]+"),
              re.compile(r"(upload_id=)[^\s&\"']+"), re.compile(r"(client_secret[\"'=:\s]+)[^\s\"'&,}]+")]

    def filter(self, rec):
        msg = rec.getMessage()
        for m in self.MOTIFS:
            msg = m.sub(r"\1[masqué]", msg)
        rec.msg, rec.args = msg, ()
        return True


log.addFilter(_Masque())


def sha256_fichier(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _url_permise(u, tests_locaux):
    p = urllib.parse.urlparse(u)
    return p.scheme == "https" or (tests_locaux and p.scheme == "http" and p.hostname == "127.0.0.1")


class Drive:
    def __init__(self, env=None, urls=None, morceau=8 * 1024 * 1024, essais=5, pause_s=1.0, tests_locaux=False, ouvrir=None, auth="oauth", horloge=time.time):
        """auth="oauth" : identifiants OAuth lus dans l'environnement ; auth="proxy" : l'adaptateur n'envoie AUCUN identifiant
        (un identifiant d'API de l'environnement cloud est censé être ajouté par le proxy ; voir ACTIVATION.md, non vérifié) ;
        auth="proxy_oauth" : renouvellement OAuth dont les secrets (client_id, client_secret, refresh_token) sont ajoutés au corps
        de POST /token par le proxy de l'environnement (identifiant d'API de type « Body parameter ») ; l'adaptateur n'envoie que
        grant_type=refresh_token et ne lit aucun secret. Le jeton d'accès obtenu reste en mémoire."""
        env = os.environ if env is None else env
        if auth not in ("oauth", "proxy", "proxy_oauth"):
            raise ErreurConfig("mode d'authentification inconnu")
        self.auth = auth
        if auth == "oauth":
            manquantes = [v for v in VARIABLES if not env.get(v)]
            if manquantes:
                raise ErreurConfig("identifiants Google Drive absents : " + ", ".join(manquantes) + " (à fournir par l'utilisateur, voir ACTIVATION.md)")
            self._id, self._secret, self._refresh = (env[v] for v in VARIABLES)
        self.urls = {**URLS, **(urls or {})}
        for u in self.urls.values():
            if not _url_permise(u.split("{")[0], tests_locaux):
                raise ErreurConfig("adresse non https refusée")
        if morceau % UNITE:
            raise ErreurConfig("taille de morceau : multiple de 256 Kio exigé par l'API")
        self.morceau, self.essais, self.pause_s = morceau, essais, pause_s
        self._ouvrir = ouvrir or urllib.request.build_opener(_SansRedirection).open
        self._acces, self._expire, self._horloge = None, 0.0, horloge

    # ---- jeton d'accès (mémoire seulement) ----
    def _jeton(self, renouveler=False):
        if self._acces and not renouveler and self._horloge() < self._expire:
            return self._acces
        if self.auth == "proxy_oauth":  # le proxy ajoute client_id, client_secret et refresh_token depuis son coffre
            corps = urllib.parse.urlencode({"grant_type": "refresh_token"}).encode()
        else:
            corps = urllib.parse.urlencode({"client_id": self._id, "client_secret": self._secret, "refresh_token": self._refresh, "grant_type": "refresh_token"}).encode()
        try:
            with self._ouvrir(urllib.request.Request(self.urls["jeton"], data=corps, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=60) as r:
                d = json.loads(r.read())
        except urllib.error.HTTPError as e:
            e.close()
            if self.auth == "proxy_oauth":
                raise ErreurAuth(f"renouvellement du jeton refusé (HTTP {e.code}) : vérifiez l'identifiant d'API « Body parameter » de l'environnement (hôte oauth2.googleapis.com, chemin /token) et le refresh token ; rien n'a été envoyé") from None
            raise ErreurAuth(f"renouvellement du jeton refusé par Google (HTTP {e.code}) : vérifiez DCE_GDRIVE_REFRESH_TOKEN et le client OAuth ; rien n'a été envoyé") from None
        if not d.get("access_token"):
            raise ErreurAuth("réponse de jeton sans jeton d'accès")
        if PORTEE not in d.get("scope", PORTEE):
            raise ErreurAuth("le jeton n'a pas la portée drive.file")
        self._acces = d["access_token"]
        self._expire = self._horloge() + max(0, int(d.get("expires_in", 3600)) - 60)  # renouvelé une minute avant l'expiration
        return self._acces

    def _requete(self, url, methode, corps=None, entetes=None, auth=True):
        """Une requête, avec un seul renouvellement de jeton sur 401. Renvoie (statut, en-têtes, réponse)."""
        for tour in (0, 1):
            h = dict(entetes or {})
            if auth and self.auth == "proxy":
                auth = False
                proxy = True
            else:
                proxy = False
            if auth:
                h["Authorization"] = "Bearer " + self._jeton(renouveler=bool(tour))
            try:
                r = self._ouvrir(urllib.request.Request(url, data=corps, method=methode, headers=h), timeout=120)
                return r.status, r.headers, r
            except urllib.error.HTTPError as e:
                if e.code != 308:
                    e.close()
                if e.code == 401 and auth and tour == 0:
                    log.info("jeton d'accès refusé (401) : un seul renouvellement")
                    continue
                if e.code == 308:
                    return 308, e.headers, e
                if e.code == 401 and proxy:
                    raise ErreurAuth("accès refusé (HTTP 401) : aucun identifiant ajouté par le proxy pour cet hôte ; vérifiez l'identifiant d'API de l'environnement") from None
                if e.code == 401:
                    raise ErreurAuth("accès refusé par Google après renouvellement du jeton (HTTP 401)") from None
                if e.code == 403:
                    raise ErreurAuth("accès interdit (HTTP 403) : portée drive.file insuffisante pour ce fichier, ou quota") from None
                raise
        raise ErreurAuth("accès refusé")

    # ---- envoi resumable ----
    def envoyer(self, chemin, nom, parent=None, type_mime="application/octet-stream", etat=None, apres_morceau=None, proprietes=None):
        taille, sha = os.path.getsize(chemin), sha256_fichier(chemin)
        st = self._lire_etat(etat, chemin, taille, sha)
        if st:
            session, offset = st["session"], self._statut(st["session"], taille)
            if isinstance(offset, dict):
                return self._terminer(offset, taille, sha, etat)
            log.info("reprise d'un envoi interrompu à l'octet %d / %d", offset, taille)
        else:
            meta = {"name": nom, "mimeType": type_mime, "appProperties": {**(proprietes or {}), "sha256": sha}}
            if parent:
                meta["parents"] = [parent]
            s, h, r0 = self._requete(self.urls["envoi"], "POST", json.dumps(meta).encode(),
                                     {"Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": type_mime, "X-Upload-Content-Length": str(taille)})
            r0.close()
            session, offset = h.get("Location"), 0
            if not session or not _url_permise(session, self.urls["envoi"].startswith("http://127.0.0.1")):
                raise ErreurDrive("session d'envoi absente ou non https")
            self._ecrire_etat(etat, {"session": session, "chemin": os.path.abspath(chemin), "taille": taille, "sha256": sha})
        echecs = 0
        with open(chemin, "rb") as f:
            while True:
                f.seek(offset)
                bloc = f.read(self.morceau)
                fin = offset + len(bloc) - 1
                try:
                    s, h, r = self._requete(session, "PUT", bloc, {"Content-Length": str(len(bloc)), "Content-Range": f"bytes {offset}-{fin}/{taille}"})
                except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
                    if isinstance(e, urllib.error.HTTPError) and e.code < 500:
                        raise ErreurDrive(f"envoi refusé (HTTP {e.code})") from None
                    echecs += 1
                    if echecs > self.essais:
                        raise ErreurDrive(f"envoi interrompu {echecs} fois : abandon, reprise possible avec le fichier d'état") from None
                    log.info("morceau interrompu (%s) : interrogation de l'état puis reprise", type(e).__name__)
                    time.sleep(self.pause_s * echecs)
                    offset = self._statut(session, taille)
                    if isinstance(offset, dict):
                        return self._terminer(offset, taille, sha, etat)
                    continue
                if s == 308:
                    r.close()
                    offset = self._offset(h)
                    if apres_morceau:
                        apres_morceau(offset)
                    continue
                if s in (200, 201):
                    with r:
                        return self._terminer(json.loads(r.read()), taille, sha, etat)
                raise ErreurDrive(f"réponse inattendue à l'envoi (HTTP {s})")

    def _terminer(self, d, taille, sha, etat):
        if int(d.get("size", -1)) != taille or (d.get("appProperties") or {}).get("sha256") != sha:
            raise ErreurIntegrite("Drive annonce une taille ou une empreinte différente de celle envoyée")
        self._effacer_etat(etat)
        return {"id": d["id"], "nom": d.get("name"), "taille": taille, "sha256": sha}

    # ---- appels JSON de l'API (dossiers, recherche, fiche, mise à jour du contenu) ----
    def _json(self, url, methode="GET", corps=None, entetes=None):
        h = dict(entetes or {})
        if corps is not None and not isinstance(corps, bytes):
            corps, h["Content-Type"] = json.dumps(corps).encode(), "application/json; charset=UTF-8"
        try:
            s, _, r = self._requete(url, methode, corps, h)
        except urllib.error.HTTPError as e:
            raise ErreurDrive(f"appel Drive refusé (HTTP {e.code})") from None
        with r:
            return json.loads(r.read() or b"{}")

    def chercher(self, q):
        """Recherche (portée drive.file : seulement les fichiers créés par cette application)."""
        url = self.urls["api"] + "?" + urllib.parse.urlencode({"q": q, "fields": "files(" + CHAMPS + ")", "pageSize": "100", "spaces": "drive"})
        return self._json(url).get("files", [])

    def fiche(self, fichier_id):
        if not _ID.fullmatch(fichier_id or ""):
            raise ErreurDrive("identifiant de fichier Drive invalide")
        return self._json(self.urls["api"] + "/" + fichier_id + "?" + urllib.parse.urlencode({"fields": CHAMPS}))

    def creer_dossier(self, nom, parent=None, proprietes=None):
        meta = {"name": nom, "mimeType": "application/vnd.google-apps.folder", "appProperties": proprietes or {}}
        if parent:
            meta["parents"] = [parent]
        return self._json(self.urls["api"] + "?" + urllib.parse.urlencode({"fields": CHAMPS}), "POST", meta)

    def maj_contenu(self, fichier_id, octets, type_mime="application/json"):
        """Remplace le contenu d'un petit fichier appartenant à l'application (manifeste)."""
        if not _ID.fullmatch(fichier_id or ""):
            raise ErreurDrive("identifiant de fichier Drive invalide")
        return self._json(self.urls["maj"].format(id=fichier_id), "PATCH", octets, {"Content-Type": type_mime})

    def lire_octets(self, fichier_id, maximum=1 << 20):
        """Lecture en mémoire d'un PETIT fichier (manifeste), bornée."""
        if not _ID.fullmatch(fichier_id or ""):
            raise ErreurDrive("identifiant de fichier Drive invalide")
        s, _, r = self._requete(self.urls["fichier"].format(id=fichier_id), "GET")
        with r:
            b = r.read(maximum + 1)
        if len(b) > maximum:
            raise ErreurDrive("fichier trop grand pour une lecture en mémoire")
        return b

    def _statut(self, session, taille):
        s, h, r = self._requete(session, "PUT", b"", {"Content-Length": "0", "Content-Range": f"bytes */{taille}"})
        if s == 308:
            r.close()
        if s in (200, 201):
            return json.loads(r.read())  # envoi déjà complet : fiche du fichier
        if s == 308:
            return self._offset(h)
        raise ErreurDrive(f"état de l'envoi illisible (HTTP {s})")

    @staticmethod
    def _offset(h):
        m = re.match(r"bytes=0-(\d+)$", (h.get("Range") or "").strip())
        return int(m.group(1)) + 1 if m else 0

    # ---- état local de reprise (droits 0600, contient l'adresse de session : ne pas partager) ----
    @staticmethod
    def _lire_etat(etat, chemin, taille, sha):
        if not etat or not os.path.exists(etat):
            return None
        with open(etat) as f:
            d = json.load(f)
        if (d.get("chemin"), d.get("taille"), d.get("sha256")) != (os.path.abspath(chemin), taille, sha):
            raise ErreurDrive("fichier d'état d'un autre envoi : supprimez-le ou choisissez un autre chemin d'état")
        return d

    @staticmethod
    def _ecrire_etat(etat, d):
        if not etat:
            return
        fd = os.open(etat, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(d, f)

    @staticmethod
    def _effacer_etat(etat):
        if etat and os.path.exists(etat):
            os.remove(etat)

    # ---- téléchargement en flux avec contrôle d'intégrité ----
    def recuperer(self, fichier_id, sortie, sha256_attendu, taille_attendue=None):
        if not _ID.fullmatch(fichier_id or ""):
            raise ErreurDrive("identifiant de fichier Drive invalide")
        tmp = sortie + ".partiel"
        h, n = hashlib.sha256(), 0
        try:
            s, _, r = self._requete(self.urls["fichier"].format(id=fichier_id), "GET")
            with r, open(tmp, "wb") as f:
                for b in iter(lambda: r.read(1 << 20), b""):
                    f.write(b)
                    h.update(b)
                    n += len(b)
            if (taille_attendue is not None and n != taille_attendue) or h.hexdigest() != sha256_attendu:
                raise ErreurIntegrite(f"fichier reçu différent de l'attendu ({n} octets, empreinte {h.hexdigest()[:12]}…) : refusé")
            os.replace(tmp, sortie)
            return {"id": fichier_id, "taille": n, "sha256": h.hexdigest()}
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)


class _SansRedirection(urllib.request.HTTPRedirectHandler):
    """L'API répond 308 « Resume Incomplete » sans redirection : ne jamais suivre de redirection (évite d'emporter le jeton)."""
    def redirect_request(self, *a, **k):
        return None

"""Stockage privé et durable d'un DCE déjà acquis, dans le Google Drive du compte autorisé (portée drive.file).

Arborescence créée par l'application (aucun partage, aucun changement de droits) :
    EAIOS_DCE_PRIVE/                      dossier racine (appProperties eaios_type=racine)
        DCE_<ref>/                        un dossier par consultation (eaios_type=dossier, eaios_ref=<ref>)
            <archive d'origine>.zip       eaios_role=archive
            <chaque document du ZIP>      eaios_role=document, eaios_chemin=<chemin dans le ZIP>
            eaios_dce_manifeste_<ref>.json   manifeste lu par la page (via le connecteur) et par la routine (via l'adaptateur)

Le manifeste porte l'historique horodaté des statuts (UTC) :
    demande -> acquis -> stockage -> stocke -> verifie      (ou echec, avec un motif sans secret)
et, pour chaque fichier : nom, chemin, rôle, taille, SHA-256, MD5 et identifiant Drive. Un identifiant Drive n'est PAS une
adresse de téléchargement : le contenu ne se lit qu'avec un accès authentifié au compte propriétaire.

Idempotent : un fichier déjà présent dans le dossier avec le même SHA-256 et la même taille n'est pas renvoyé ; une reprise
après une session neuve repart du manifeste."""
import datetime
import hashlib
import io
import json
import os
import re
import tempfile
import time
import zipfile

from .drive_resumable import ErreurDrive, ErreurIntegrite, sha256_fichier

RACINE = "EAIOS_DCE_PRIVE"
DOSSIER = "application/vnd.google-apps.folder"
ETATS = ("demande", "acquis", "stockage", "stocke", "verifie", "echec")
TYPES = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         ".doc": "application/msword", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
         ".xls": "application/vnd.ms-excel", ".odt": "application/vnd.oasis.opendocument.text", ".txt": "text/plain",
         ".zip": "application/zip", ".rtf": "application/rtf"}
LIMITES = {"entrees": 300, "total": 300 * 1024 * 1024, "entree": 150 * 1024 * 1024, "ratio": 200}


def slug(ref):
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", str(ref or "")).strip("._-")
    if not s or len(s) > 80:
        raise ErreurDrive("référence de consultation invalide")
    return s


def _q(v):
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


def _maintenant(horloge):
    return datetime.datetime.fromtimestamp(horloge(), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _md5(chemin):
    h = hashlib.md5()
    with open(chemin, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _court(v, octets=100):
    """appProperties : clé + valeur limitées à 124 octets UTF-8 ; la valeur est tronquée sans couper un caractère."""
    return str(v).encode("utf-8")[:octets].decode("utf-8", "ignore")


def type_de(nom):
    return TYPES.get(os.path.splitext(nom.lower())[1], "application/octet-stream")


def entrees_zip(chemin):
    """Liste contrôlée des entrées (fichiers) d'une archive ; refuse chemins absolus, remontées, archives piégées."""
    try:
        z = zipfile.ZipFile(chemin)
    except zipfile.BadZipFile:
        raise ErreurIntegrite("archive ZIP illisible") from None
    with z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        if len(infos) > LIMITES["entrees"]:
            raise ErreurIntegrite("archive : trop d'entrées")
        total = 0
        for i in infos:
            n = i.filename.replace("\\", "/")
            if n.startswith("/") or ".." in n.split("/") or re.match(r"^[A-Za-z]:", n):
                raise ErreurIntegrite("archive : chemin d'entrée refusé")
            if i.file_size > LIMITES["entree"] or (i.compress_size and i.file_size / i.compress_size > LIMITES["ratio"]):
                raise ErreurIntegrite("archive : entrée trop grande ou trop compressée")
            total += i.file_size
        if total > LIMITES["total"]:
            raise ErreurIntegrite("archive : taille décompressée excessive")
        return [i.filename for i in infos]


class StockageDCE:
    def __init__(self, drive, horloge=time.time, racine=RACINE):
        self.d, self.horloge, self.nom_racine = drive, horloge, racine

    # ---- dossiers ----
    def _trouver(self, q):
        r = self.d.chercher(q + " and trashed = false")
        return r[0] if r else None

    def racine(self, creer=True):
        q = f"name = {_q(self.nom_racine)} and mimeType = '{DOSSIER}' and appProperties has {{ key='eaios_type' and value='racine' }}"
        f = self._trouver(q)
        if f or not creer:
            return f
        return self.d.creer_dossier(self.nom_racine, None, {"eaios_type": "racine"})

    def dossier(self, ref, creer=True):
        s, rac = slug(ref), self.racine(creer)
        if not rac:
            return None
        q = (f"{_q(rac['id'])} in parents and mimeType = '{DOSSIER}' and appProperties has {{ key='eaios_type' and value='dossier' }}"
             f" and appProperties has {{ key='eaios_ref' and value={_q(s)} }}")
        f = self._trouver(q)
        if f or not creer:
            return f
        return self.d.creer_dossier("DCE_" + s, rac["id"], {"eaios_type": "dossier", "eaios_ref": s})

    # ---- manifeste ----
    def nom_manifeste(self, ref):
        return f"eaios_dce_manifeste_{slug(ref)}.json"

    def _fiche_manifeste(self, dossier_id, ref):
        q = (f"{_q(dossier_id)} in parents and name = {_q(self.nom_manifeste(ref))}"
             " and appProperties has { key='eaios_type' and value='manifeste' }")
        return self._trouver(q)

    def lire_manifeste(self, ref):
        """Pour la routine après une session neuve : None si rien n'a encore été rangé pour cette référence."""
        dos = self.dossier(ref, creer=False)
        if not dos:
            return None
        f = self._fiche_manifeste(dos["id"], ref)
        if not f:
            return None
        m = json.loads(self.d.lire_octets(f["id"]))
        if m.get("format") != "eaios.dce.manifeste/1" or m.get("ref") != slug(ref):
            raise ErreurIntegrite("manifeste Drive inattendu")
        m["_id"] = f["id"]
        return m

    def lister_manifestes(self):
        """Toutes les consultations rangées (reprise de la routine)."""
        return [{"id": f["id"], "ref": (f.get("appProperties") or {}).get("eaios_ref")}
                for f in self.d.chercher("appProperties has { key='eaios_type' and value='manifeste' } and trashed = false")]

    def _ecrire(self, m):
        corps = json.dumps({k: v for k, v in m.items() if not k.startswith("_")}, ensure_ascii=False, indent=1).encode("utf-8")
        if m.get("_id"):
            self.d.maj_contenu(m["_id"], corps)
            return m
        with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as t:
            t.write(corps)
        try:
            r = self.d.envoyer(t.name, self.nom_manifeste(m["ref"]), m["dossier_id"], "application/json",
                               proprietes={"eaios_type": "manifeste", "eaios_ref": m["ref"]})
        finally:
            os.remove(t.name)
        m["_id"] = r["id"]
        return m

    def statut(self, m, etat, detail=None, le=None):
        if etat not in ETATS:
            raise ErreurDrive("statut inconnu")
        e = {"etat": etat, "le": le or _maintenant(self.horloge)}
        if detail:
            e["detail"] = str(detail)[:300]
        m["statut"], m["maj"] = etat, e["le"]
        m.setdefault("historique", []).append(e)
        return self._ecrire(m)

    def ouvrir(self, ref, demande_le=None, source=None):
        """Crée (ou reprend) le dossier et le manifeste d'une consultation."""
        s = slug(ref)
        dos = self.dossier(s)
        m = self.lire_manifeste(s)
        if m:
            return m
        m = {"format": "eaios.dce.manifeste/1", "ref": s, "dossier_id": dos["id"], "source": source or {}, "fichiers": [],
             "historique": []}
        return self.statut(m, "demande", "demande enregistrée dans EAIOS" if demande_le else None, le=demande_le)

    # ---- rangement ----
    def _deja(self, m, sha, taille, role, chemin):
        for f in m["fichiers"]:
            if f["sha256"] == sha and f["taille"] == taille and f["role"] == role and f.get("chemin") == chemin:
                return f
        q = (f"{_q(m['dossier_id'])} in parents and appProperties has {{ key='sha256' and value={_q(sha)} }}"
             f" and appProperties has {{ key='eaios_role' and value={_q(role)} }}")
        for f in self.d.chercher(q + " and trashed = false"):
            if int(f.get("size", -1)) == taille and (f.get("appProperties") or {}).get("eaios_chemin", "") == _court(chemin or ""):
                return {"drive_id": f["id"]}
        return None

    def _ranger(self, m, chemin_local, nom, role, chemin_zip, etat_dir):
        taille, sha, md5 = os.path.getsize(chemin_local), sha256_fichier(chemin_local), _md5(chemin_local)
        exist = self._deja(m, sha, taille, role, chemin_zip)
        if exist and exist.get("nom"):
            return exist
        if exist:
            fid = exist["drive_id"]
        else:
            props = {"eaios_type": "fichier", "eaios_ref": m["ref"], "eaios_role": role}
            if chemin_zip:
                props["eaios_chemin"] = _court(chemin_zip)
            etat = os.path.join(etat_dir, hashlib.sha256((role + (chemin_zip or nom)).encode()).hexdigest()[:16] + ".etat") if etat_dir else None
            fid = self.d.envoyer(chemin_local, nom, m["dossier_id"], type_de(nom), etat, proprietes=props)["id"]
        f = {"nom": nom, "chemin": chemin_zip, "role": role, "type": os.path.splitext(nom)[1].lstrip(".").lower() or "bin",
             "mime": type_de(nom), "taille": taille, "sha256": sha, "md5": md5, "drive_id": fid}
        m["fichiers"] = [x for x in m["fichiers"] if not (x["role"] == role and x.get("chemin") == chemin_zip)] + [f]
        return f

    def stocker(self, ref, zip_chemin, demande_le=None, source=None, etat_dir=None):
        """ZIP d'origine + chaque document extrait, puis vérification. Renvoie le manifeste final."""
        m = self.ouvrir(ref, demande_le, source)
        try:
            noms = entrees_zip(zip_chemin)
            m["archive"] = {"nom": os.path.basename(zip_chemin), "taille": os.path.getsize(zip_chemin), "sha256": sha256_fichier(zip_chemin), "entrees": len(noms)}
            if m["statut"] in ("demande", "echec"):
                self.statut(m, "acquis", f"archive de {m['archive']['taille']} octets, {len(noms)} entrées")
            self.statut(m, "stockage")
            self._ranger(m, zip_chemin, m["archive"]["nom"], "archive", None, etat_dir)
            with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(zip_chemin) as z:
                for i, n in enumerate(noms):
                    loc = os.path.join(tmp, f"{i:04d}")
                    with z.open(n) as src, open(loc, "wb") as dst:
                        for b in iter(lambda: src.read(1 << 20), b""):
                            dst.write(b)
                    self._ranger(m, loc, os.path.basename(n.replace("\\", "/")) or f"entree_{i}", "document", n, etat_dir)
            self.statut(m, "stocke", f"{len(m['fichiers'])} fichiers rangés")
            self.verifier(m)
            return self.statut(m, "verifie", "taille, SHA-256 (propriété) et MD5 (calculé par Drive) concordants")
        except ErreurDrive as e:
            try:
                self.statut(m, "echec", f"{type(e).__name__}: {e}")
            except ErreurDrive:
                pass
            raise

    def verifier(self, m):
        """Contrôle côté Drive sans retélécharger : taille, MD5 calculé par Google, SHA-256 inscrit à l'envoi, dossier parent."""
        for f in m["fichiers"]:
            d = self.d.fiche(f["drive_id"])
            if (int(d.get("size", -1)) != f["taille"] or d.get("md5Checksum") != f["md5"]
                    or (d.get("appProperties") or {}).get("sha256") != f["sha256"] or m["dossier_id"] not in (d.get("parents") or [])):
                raise ErreurIntegrite(f"fichier rangé non conforme : {f['nom']}")
        return True

    def relire(self, m, sortie_dir):
        """Preuve de récupération complète : retélécharge chaque fichier et contrôle taille + SHA-256."""
        os.makedirs(sortie_dir, exist_ok=True)
        r = []
        for i, f in enumerate(m["fichiers"]):
            x = self.d.recuperer(f["drive_id"], os.path.join(sortie_dir, f"{i:04d}_{f['sha256'][:12]}"), f["sha256"], f["taille"])
            r.append({"nom": f["nom"], "taille": x["taille"], "sha256_identique": x["sha256"] == f["sha256"]})
        return r

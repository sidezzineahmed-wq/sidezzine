"""Confiance TLS du navigateur dans l'environnement cloud (mode « proxy_ccr ») — sans désactiver aucune vérification.

Constat : le proxy de sortie de l'environnement re-termine TLS (/root/.ccr/README.md). Chromium (Linux) ne lit pas
SSL_CERT_FILE mais le magasin NSS $HOME/.pki/nssdb, trouvé vide. Ce module prépare, pour UN lancement, un magasin NSS
temporaire ne contenant QUE l'autorité officielle de l'environnement, puis le supprime.

Garde-fous (revue du 2026-10-04) :
  - aucun PEM arbitraire : seul /root/.ccr/agent-proxy-ca.crt, octet pour octet identique à /root/.ccr/system-trust.ca.pem,
    d'empreinte SHA-256 de fichier égale à la valeur REVUE, et cité par /root/.ccr/README.md ; toute différence (rotation
    future comprise) = arrêt « confiance », à revoir humainement ;
  - magasin créé SOUS la racine de travail fournie (jamais sous /tmp) ; nettoyage garanti (try/finally) même si certutil,
    le lancement ou la fermeture échouent ;
  - aucun message brut de certutil n'est remonté (seulement le code de retour) ;
  - aucune option d'ignorance d'erreur TLS n'est jamais passée au navigateur.
"""
import hashlib
import os
import shutil
import subprocess
import tempfile

CA_OFFICIELLE = "/root/.ccr/agent-proxy-ca.crt"
CA_SYSTEME = "/root/.ccr/system-trust.ca.pem"
README = "/root/.ccr/README.md"
SHA_REVUE = "70f9315129c67bf82e0a0dadc984adee41331f6b67096f653bb34479e0c0080b"
MODES = ("", "proxy_ccr")
INTERDITS = ("/tmp",)   # racines refusées pour le magasin temporaire (la routine interdit /tmp)


class ErreurConfiance(RuntimeError):
    pass


def verifier_ca(ca=CA_OFFICIELLE, systeme=CA_SYSTEME, readme=README, sha_revue=SHA_REVUE):
    try:
        b, s, r = open(ca, "rb").read(), open(systeme, "rb").read(), open(readme, encoding="utf-8", errors="replace").read()
    except OSError:
        raise ErreurConfiance("autorité officielle de l'environnement introuvable : arrêt, à revoir") from None
    if b != s:
        raise ErreurConfiance("l'autorité du proxy diffère de la confiance système de l'environnement : arrêt, à revoir")
    if hashlib.sha256(b).hexdigest() != sha_revue:
        raise ErreurConfiance("empreinte de l'autorité différente de la valeur revue (rotation ?) : arrêt, nouvelle revue requise")
    if os.path.basename(ca) not in r or "re-terminated" not in r:
        raise ErreurConfiance("le README de l'environnement ne documente pas cette autorité : arrêt, à revoir")
    return ca


def preparer_magasin(racine, ca, executer=subprocess.run, certutil=None):
    """Crée <racine>/nss_XXXX/.pki/nssdb avec la seule autorité `ca` (C,,). Rend le HOME temporaire. Nettoie en cas d'échec."""
    if not racine:
        raise ErreurConfiance("racine de travail absente : magasin NSS non préparé")
    racine = os.path.realpath(racine)
    if not os.path.isdir(racine):
        raise ErreurConfiance("racine de travail absente : magasin NSS non préparé")
    if any(racine == p or racine.startswith(p + "/") for p in INTERDITS):
        raise ErreurConfiance("racine de travail sous /tmp refusée")
    outil = certutil or shutil.which("certutil")
    if not outil:
        raise ErreurConfiance("certutil (paquet libnss3-tools) absent : magasin NSS impossible à préparer")
    home = tempfile.mkdtemp(prefix="nss_", dir=racine)
    try:
        db = os.path.join(home, ".pki", "nssdb")
        os.makedirs(db)
        for args in (["-N", "--empty-password"], ["-A", "-n", "ccr-agent-proxy", "-t", "C,,", "-i", ca]):
            r = executer([outil, *args, "-d", "sql:" + db], capture_output=True, text=True, timeout=60)
            if r.returncode:
                raise ErreurConfiance(f"certutil a échoué (code {r.returncode}) : magasin NSS non préparé")
        return home
    except BaseException:
        shutil.rmtree(home, ignore_errors=True)
        raise


def nettoyer(home):
    if home:
        shutil.rmtree(home, ignore_errors=True)

"""Commandes du kit DCE pour une tâche cloud FINIE (aucun serveur permanent). Chaque commande écrit un JSON d'état.

  verifier-env                       Playwright importable et Chromium lançable (page vide locale, aucun réseau).
  ouvrir     --ref --org --sortie    Ouvre la page DCE, vérifie ref/org, lit les CG. NE REMPLIT RIEN, NE COCHE RIEN,
                                     NE SOUMET RIEN. État « attente_validation_CG ».
  telecharger --ref --org --validation v.json --sortie DIR
                                     Exige la validation HUMAINE de CE téléchargement (phrase exacte + empreinte des CG
                                     présentées, récente). Recharge la page, refuse si les CG diffèrent, saisit
                                     l'identité de l'exploitant (variables d'environnement), soumet, capture l'archive.
  preparer   --zip F --sortie DIR    Contrôle l'archive et prépare le retour : PDF tels quels, autres fichiers et archive
                                     d'origine en texte base64, manifest.json avec les empreintes SHA-256.

401/403, page de contrôle ou CAPTCHA : état « echec », code de sortie 2, AUCUNE nouvelle tentative."""
import argparse
import asyncio
import base64
import datetime
import hashlib
import json
import os
import re
import sys

from .config import Config, ConfigInvalide
from .navigateur import NavigateurPlaywright, Refus
from .zipcheck import ZipInvalide, inspecter

PHRASE = "J'accepte les conditions générales du portail pour ce téléchargement"


def maintenant():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ecrire(chemin, d):
    os.makedirs(os.path.dirname(os.path.abspath(chemin)), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def _nom_sur(nom, pris):
    base = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", nom).strip() or "fichier"
    n, i = base, 2
    while n.lower() in pris:
        r, e = os.path.splitext(base)
        n, i = f"{r} ({i}){e}", i + 1
    pris.add(n.lower())
    return n


def preparer(octets, nom_zip, sortie, zip_max=200 * 2**20):
    """Archive -> fichiers prêts au dépôt : PDF (dépôt direct), autres et archive d'origine en base64 (dépôt texte)."""
    import io
    import zipfile
    inv = inspecter(octets, zip_max=zip_max)
    z = zipfile.ZipFile(io.BytesIO(octets))
    os.makedirs(os.path.join(sortie, "fichiers"), exist_ok=True)
    os.makedirs(os.path.join(sortie, "base64"), exist_ok=True)
    pris, fichiers = set(), []
    for e in inv["entrees"]:
        d = z.read(e["chemin"])
        nom = _nom_sur(e["nom"], pris)
        f = {k: e[k] for k in ("nom", "chemin", "taille", "sha256", "type")}
        if e["type"] == "pdf":
            p = os.path.join(sortie, "fichiers", nom)
            open(p, "wb").write(d)
            f.update(depot="pdf", fichier_local=p)
        else:
            p = os.path.join(sortie, "base64", nom + ".b64.txt")
            open(p, "w").write(base64.b64encode(d).decode())
            f.update(depot="texte_base64", fichier_local=p)
        fichiers.append(f)
    nz = _nom_sur(nom_zip or "DCE.zip", set())
    pz = os.path.join(sortie, "base64", nz + ".b64.txt")
    open(pz, "w").write(base64.b64encode(octets).decode())
    m = {"zip": {"nom": nz, "taille": inv["taille"], "sha256": inv["sha256"], "depot": "texte_base64", "fichier_local": pz},
         "fichiers": fichiers, "prepare_le": maintenant()}
    ecrire(os.path.join(sortie, "manifest.json"), m)
    return m


def lire_validation(chemin, ref, org, validite_h):
    v = json.load(open(chemin, encoding="utf-8"))
    if v.get("phrase") != PHRASE:
        raise Refus("validation", "validation humaine absente : la phrase exacte n'a pas été confirmée")
    if (v.get("ref"), v.get("org")) != (ref, org):
        raise Refus("validation", "la validation concerne une autre consultation")
    if not v.get("empreinte") or not v.get("par"):
        raise Refus("validation", "validation incomplète (empreinte des CG, auteur)")
    try:
        le = datetime.datetime.strptime(v.get("le", ""), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        raise Refus("validation", "date de validation illisible")
    age = (datetime.datetime.now(datetime.timezone.utc) - le).total_seconds()
    if age < 0 or age > validite_h * 3600:
        raise Refus("validation", f"validation expirée (plus de {validite_h} h) : nouvelle validation humaine requise")
    return v


async def _ouvrir(c, a):
    nav = NavigateurPlaywright(c)
    try:
        i = await nav.ouvrir(a.ref, a.org, a.reference_attendue)
        return {"etat": "attente_validation_CG", "ref": a.ref, "org": a.org, "url": i.url, "le": maintenant(),
                "cg": {"texte": i.texte, "lien": i.lien_cg, "empreinte": i.empreinte, "portee": i.portee}, "phrase_requise": PHRASE}
    finally:
        await nav.fermer()


async def _telecharger(c, a, v):
    nav = NavigateurPlaywright(c)
    try:
        octets, nom, url = await nav.telecharger(a.ref, a.org, c.identite, v["empreinte"], a.reference_attendue)
    finally:
        await nav.fermer()
    m = preparer(octets, nom, a.sortie, c.zip_max)
    return {"etat": "pret", "ref": a.ref, "org": a.org, "source": url, "cg_valide_par": v["par"], "cg_valide_le": v["le"],
            "manifest": os.path.join(a.sortie, "manifest.json"), "zip_sha256": m["zip"]["sha256"], "le": maintenant()}


async def _verifier_env():
    import playwright
    from importlib.metadata import version
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.set_content("<p id=x>ok</p>")
        txt = await pg.inner_text("#x")
        v = b.version
        await b.close()
    return {"etat": "ok" if txt == "ok" else "echec", "python": sys.version.split()[0], "playwright": version("playwright"), "chromium": v}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dce_tache.py")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("verifier-env")
    for n in ("ouvrir", "telecharger"):
        p = sp.add_parser(n)
        p.add_argument("--ref", required=True)
        p.add_argument("--org", required=True)
        p.add_argument("--reference-attendue")
        p.add_argument("--config")
        p.add_argument("--etat", required=True, help="fichier JSON d'état écrit par la commande")
        if n == "telecharger":
            p.add_argument("--validation", required=True)
            p.add_argument("--sortie", required=True)
    p = sp.add_parser("preparer")
    p.add_argument("--zip", required=True)
    p.add_argument("--sortie", required=True)
    p = sp.add_parser("planifier")
    p.add_argument("--file", required=True, help="JSON {doc_id: document} ou répertoire de <doc_id>.json lus par ArtifactData")
    p.add_argument("--dossiers-autorises", required=True)
    p.add_argument("--run", required=True)
    p.add_argument("--max-actions", type=int, default=1)
    p.add_argument("--sortie", required=True)
    p = sp.add_parser("resultat")
    for o in ("--id", "--demande", "--etat", "--run", "--sortie"):
        p.add_argument(o, required=True)
    for o in ("--registre", "--manifest", "--depots"):
        p.add_argument(o)
    a = ap.parse_args(argv)
    if a.cmd in ("planifier", "resultat"):
        from . import cycle
        return cycle.main_planifier(a) if a.cmd == "planifier" else cycle.main_resultat(a)
    try:
        if a.cmd == "verifier-env":
            r = asyncio.run(_verifier_env())
            print(json.dumps(r, ensure_ascii=False))
            return 0 if r["etat"] == "ok" else 1
        if a.cmd == "preparer":
            m = preparer(open(a.zip, "rb").read(), os.path.basename(a.zip), a.sortie)
            print(json.dumps({"etat": "ok", "zip_sha256": m["zip"]["sha256"], "fichiers": len(m["fichiers"])}, ensure_ascii=False))
            return 0
        c = Config.charger(a.config, identite_requise=(a.cmd == "telecharger"))
        if a.cmd == "ouvrir":
            r = asyncio.run(_ouvrir(c, a))
        else:
            v = lire_validation(a.validation, a.ref, a.org, c.cg_validite_h)
            r = asyncio.run(_telecharger(c, a, v))
    except Refus as e:
        r = {"etat": "echec", "code": e.code, "motif": e.motif, "le": maintenant()}
    except (ZipInvalide, ConfigInvalide) as e:
        r = {"etat": "echec", "code": type(e).__name__, "motif": str(e), "le": maintenant()}
    if getattr(a, "etat", None):
        ecrire(a.etat, {**r, "ref": getattr(a, "ref", None), "org": getattr(a, "org", None)})
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r["etat"] != "echec" else 2

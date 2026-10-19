#!/usr/bin/env python3
"""Intègre dans l'état du collecteur le RELEVÉ DES PIÈCES publié dans le dépôt (checkpoint durable du relevé ponctuel),
AVANT les relectures réseau du passage horaire. Données seulement : aucun code du dépôt n'est exécuté.

  python3 integrer_releve_pieces.py --etat W/etat --depot W/depot [--rapport W/releve_pieces.json]

Le dépôt est un clone de la branche publiée ; on lit <depot>/veille_enrichissement/releve_pieces/index.json et ses lots
(SHA-256 vérifié pour chaque lot). Chaque entrée = inventaire PUBLIC normalisé d'une consultation (type, libellé, taille,
lien relatif PMMP du même identifiant), sa preuve, l'identité de la page lue (page_id), sa date de lecture réelle.

Règles :
  - entrée validée strictement (identifiant, organisme / référence, page_id identique, types et liens du même identifiant,
    « aucune pièce » seulement avec une preuve officielle) ; sinon ignorée et comptée avec son motif ;
  - appliquée seulement si la fiche existe dans l'état avec la MÊME référence, et si son inventaire actuel est absent ou plus
    ancien que l'entrée : jamais une lecture plus récente écrasée ;
  - la date de la fiche (lu_le) ne change pas : l'inventaire porte sa propre date (docs_lu_le) et sa source
    (docs_source = "releve_pieces") ;
  - idempotent (relancer ne change rien)."""
import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from veille.etat import Etat, _ecrire_json  # noqa: E402

SOUS_DOSSIER = os.path.join("veille_enrichissement", "releve_pieces")
TYPES = {"reglement", "dce", "complement", "avis"}
PREUVES_VIDE = {"bloc_aucune_piece", "liens_officiels_tous_masques"}
PAGES = {"entreprise.EntrepriseDemandeTelechargementDce", "entreprise.EntrepriseDownloadReglement", "entreprise.EntrepriseDownloadComplement",
         "entreprise.EntrepriseDownloadAvisJAL", "entreprise.ExtraitPV"}
ID = re.compile(r"^pmmp:([a-z0-9]{2,8}):(\d{1,10})$")


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip().upper()


def valider(e):
    """Motif de refus, ou None si l'entrée est valide."""
    m = ID.match(str(e.get("id") or ""))
    if not m or e.get("org") != m.group(1) or str(e.get("ref_consultation")) != m.group(2):
        return "identifiant"
    if e.get("page_id") != f"{m.group(1)}:{m.group(2)}":
        return "page_id"
    if not isinstance(e.get("lu_le"), str) or not re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d", e["lu_le"]):
        return "lu_le"
    docs, preuve = e.get("docs"), e.get("docs_preuve")
    if not isinstance(docs, list) or len(docs) > 30:
        return "docs"
    if not docs and preuve not in PREUVES_VIDE:
        return "vide_sans_preuve"
    if docs and preuve != "liens_visibles":
        return "preuve"
    for d in docs:
        if not isinstance(d, dict) or d.get("type") not in TYPES or not isinstance(d.get("libelle"), str) or not d["libelle"].strip():
            return "piece"
        if len(d["libelle"]) > 300 or (d.get("taille") is not None and not re.match(r"^[\d.,]+\s*[KMG]?o$", str(d["taille"]))):
            return "piece"
        u = d.get("url")
        if u is not None:
            if not isinstance(u, str) or not u.startswith("index.php?page=") or len(u) > 400:
                return "lien"
            page = re.match(r"index\.php\?page=([\w.]+)", u).group(1)
            if page not in PAGES:
                return "lien"
            q = dict(re.findall(r"[?&](refConsultation|orgAcronyme|reference)=([^&]*)", u))
            ref_lien = q.get("refConsultation")
            if ref_lien is None and "reference" in q:  # règlement / complément : reference = base64 de la référence
                try:
                    ref_lien = base64.b64decode(q["reference"], validate=True).decode("ascii")
                except (binascii.Error, ValueError, UnicodeDecodeError):
                    return "lien"
            if ref_lien != m.group(2) or q.get("orgAcronyme") != m.group(1):
                return "lien_autre_consultation"
    return None


def charger(depot, rapport):
    base = os.path.join(depot, SOUS_DOSSIER)
    idx = json.load(open(os.path.join(base, "index.json"), encoding="utf-8"))
    entrees = []
    for lot in idx.get("lots") or []:
        p = os.path.join(base, os.path.basename(lot["fichier"]))
        b = open(p, "rb").read()
        if hashlib.sha256(b).hexdigest() != lot.get("sha256"):
            rapport["lots_refuses_sha"].append(lot["fichier"])
            continue
        doc = json.loads(b.decode("utf-8"))
        entrees += doc.get("entrees") or []
        rapport["lots_lus"] += 1
    return idx, entrees


def appliquer(etat, entrees, rapport):
    meilleures = {}
    for e in entrees:  # par identifiant, la lecture la plus récente du relevé
        mot = valider(e)
        if mot:
            rapport["ignorees"][mot] = rapport["ignorees"].get(mot, 0) + 1
            continue
        a = meilleures.get(e["id"])
        if a is None or e["lu_le"] > a["lu_le"]:
            meilleures[e["id"]] = e
    for i, e in sorted(meilleures.items()):
        f = etat.fiche(i)
        if f is None:
            rapport["ignorees"]["fiche_absente"] = rapport["ignorees"].get("fiche_absente", 0) + 1
            continue
        ch = f.get("champs") or {}
        if _norm(ch.get("ref")) != _norm(e.get("reference")):
            rapport["ignorees"]["reference_differente"] = rapport["ignorees"].get("reference_differente", 0) + 1
            continue
        actuel = (ch.get("docs_lu_le") or f.get("lu_le") or "") if "docs" in (ch.get("blocs_lus") or []) else ""
        if actuel >= e["lu_le"]:
            rapport["deja_a_jour_ou_plus_recent"] += 1
            continue
        ch = dict(ch)
        ch["docs"], ch["docs_preuve"], ch["docs_lu_le"], ch["docs_source"] = e["docs"], e["docs_preuve"], e["lu_le"], "releve_pieces"
        ch["blocs_lus"] = sorted(set(ch.get("blocs_lus") or []) | {"docs"})
        f = dict(f, champs=ch)
        _ecrire_json(etat.chemin_fiche(i), f)
        rapport["appliquees"] += 1
        rapport["vides_confirmes" if not e["docs"] else "avec_pieces"] += 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etat", required=True)
    ap.add_argument("--depot", required=True)
    ap.add_argument("--rapport")
    a = ap.parse_args(argv)
    r = {"commit": None, "lots_lus": 0, "lots_refuses_sha": [], "entrees": 0, "appliquees": 0, "avec_pieces": 0,
         "vides_confirmes": 0, "deja_a_jour_ou_plus_recent": 0, "ignorees": {}}
    try:
        r["commit"] = subprocess.run(["git", "-C", a.depot, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip() or None
    except Exception:
        pass
    try:
        idx, entrees = charger(a.depot, r)
    except FileNotFoundError:
        r["erreur"] = "relevé absent du dépôt"
        entrees = []
    r["entrees"] = len(entrees)
    appliquer(Etat(a.etat), entrees, r)
    if a.rapport:
        _ecrire_json(a.rapport, r)
    print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

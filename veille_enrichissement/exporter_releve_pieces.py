#!/usr/bin/env python3
"""Exporte le relevé ponctuel des pièces (cache/ et brut/ de complement_fiches.py) en CHECKPOINT DURABLE dans le dépôt :
veille_enrichissement/releve_pieces/lot_NNNN.json + index.json, commités et poussés par lots (ex. 100) puis au final.
Le passage horaire du collecteur les intègre avant ses relectures réseau (kit : integrer_releve_pieces.py).

  python3 exporter_releve_pieces.py --dossier <compl_docs> --kit <kit> --depot <racine du dépôt> [--lot 100]
                                    [--boucle 60 --pid <pid du relevé>] [--sans-push]

Données PUBLIQUES normalisées seulement (aucun HTML, aucun état de page, aucune donnée de compte) : par consultation lue,
id / org / ref_consultation / reference (telle que lue) / page_id (formulaire de la page) / lu_le (lecture réelle) /
docs (type, libellé, taille, lien relatif PMMP) / docs_preuve / version_lecture / lecteur_sha256 (lecteur utilisé) /
html_sha256 (empreinte du HTML lu, conservé hors dépôt). Le HTML conservé est RÉ-ANALYSÉ par le lecteur courant (SHA
vérifié) : les règles strictes de lecture s'appliquent. Une page dont le bloc des pièces n'est pas lisible n'est PAS
exportée (pas « aucune pièce ») ; elle est comptée dans index.json (non_lus, par motif)."""
import argparse
import glob
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time

SOUS = os.path.join("veille_enrichissement", "releve_pieces")


def lire(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return d


def ecrire(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")
    os.replace(tmp, p)


def git(depot, *args, ok=(0,)):
    r = subprocess.run(["git", "-C", depot, *args], capture_output=True, text=True, timeout=120)
    if r.returncode not in ok:
        raise RuntimeError(f"git {' '.join(args)} : {r.stderr.strip()[:300]}")
    return r.stdout.strip()


def pousser(depot, message, essais=4):
    git(depot, "add", "--", SOUS)
    if not git(depot, "diff", "--cached", "--name-only", "--", SOUS):
        return False
    git(depot, "commit", "-q", "-m", message, "--", SOUS)
    branche = git(depot, "rev-parse", "--abbrev-ref", "HEAD")
    for k in range(essais):
        try:
            git(depot, "push", "-q", "-u", "origin", branche)
            return True
        except RuntimeError:
            time.sleep(2 ** (k + 1))
    raise RuntimeError("push impossible après essais")


def cycle(a, lire_fiche, version, lecteur_sha, forcer=False):
    base = os.path.join(a.depot, SOUS)
    os.makedirs(base, exist_ok=True)
    idx = lire(os.path.join(base, "index.json")) or {"version": 1, "lots": [], "ids": {}, "non_lus": {}}
    deja = idx["ids"]
    nouvelles, non_lus = [], dict(idx.get("non_lus") or {})
    for p in sorted(glob.glob(os.path.join(a.dossier, "cache", "*.json"))):
        rec = lire(p) or {}
        fi, k = rec.get("fiche"), rec.get("id")
        if not fi or not k or deja.get(k) == fi.get("lu_le"):
            continue
        o, r = k.split(":")[1:]
        b = os.path.join(a.dossier, "brut", f"{o}_{r}_fiche.html.gz")
        if not os.path.exists(b):
            continue
        h = gzip.open(b, "rt", encoding="utf-8", newline="").read()
        sha = hashlib.sha256(h.encode()).hexdigest()
        if sha != fi.get("sha256_html_tronque"):
            continue
        ch = lire_fiche(h, masquer=True)
        if ch.get("docs") is None:
            non_lus[k] = ch.get("docs_preuve") or "non_lu"
            deja[k] = fi["lu_le"]
            continue
        non_lus.pop(k, None)
        nouvelles.append({"id": k, "org": o, "ref_consultation": r, "reference": ch.get("ref"), "page_id": ch.get("page_id"),
                          "lu_le": fi["lu_le"], "docs": ch["docs"], "docs_preuve": ch["docs_preuve"],
                          "version_lecture": version, "lecteur_sha256": lecteur_sha, "html_sha256": sha})
    nouvelles.sort(key=lambda e: (e["lu_le"], e["id"]))
    pousse = 0
    while nouvelles and (len(nouvelles) >= a.lot or forcer):
        part, nouvelles = nouvelles[:a.lot], nouvelles[a.lot:]
        n = len(idx["lots"]) + 1
        nom = f"lot_{n:04d}.json"
        ecrire(os.path.join(base, nom), {"version": 1, "entrees": part})
        b = open(os.path.join(base, nom), "rb").read()
        idx["lots"].append({"fichier": nom, "sha256": hashlib.sha256(b).hexdigest(), "n": len(part),
                            "premier": part[0]["lu_le"], "dernier": part[-1]["lu_le"]})
        for e in part:
            deja[e["id"]] = e["lu_le"]
        pousse += len(part)
    if pousse or non_lus != idx.get("non_lus"):
        idx["non_lus"] = non_lus
        idx["total_entrees"] = sum(l["n"] for l in idx["lots"])
        idx["maj"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        idx["regle"] = ("inventaires publics des pièces (liens visibles ; « aucune pièce » seulement avec preuve officielle) ; "
                        "aucun HTML ni état de page ; intégrés par le kit (integrer_releve_pieces.py) sans écraser une lecture plus récente")
        ecrire(os.path.join(base, "index.json"), idx)
        if not a.sans_push:
            pousser(a.depot, f"Relevé des pièces PMMP : {idx['total_entrees']} inventaires ({len(non_lus)} non lisibles)\n\n"
                             "Checkpoint durable (données publiques normalisées), intégré par le passage horaire.")
    return pousse, len(nouvelles)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--depot", required=True)
    ap.add_argument("--lot", type=int, default=100)
    ap.add_argument("--boucle", type=int, default=0, help="secondes entre deux cycles (0 = un seul cycle, tout est poussé)")
    ap.add_argument("--pid", type=int, help="processus du relevé : à sa fin, dernier cycle forcé puis arrêt")
    ap.add_argument("--sans-push", action="store_true")
    a = ap.parse_args(argv)
    sys.path.insert(0, a.kit)
    from veille.pmmp_fiche import VERSION_LECTURE, lire_fiche  # noqa: E402
    lecteur_sha = hashlib.sha256(open(os.path.join(a.kit, "veille", "pmmp_fiche.py"), "rb").read()).hexdigest()
    if not a.boucle:
        print(json.dumps(dict(zip(("exportees", "en_attente"), cycle(a, lire_fiche, VERSION_LECTURE, lecteur_sha, forcer=True)))))
        return 0
    while True:
        vivant = a.pid is None or os.path.exists(f"/proc/{a.pid}")
        try:
            n, reste = cycle(a, lire_fiche, VERSION_LECTURE, lecteur_sha, forcer=not vivant)
            print(json.dumps({"t": time.strftime("%H:%M:%S", time.gmtime()), "exportees": n, "en_attente": reste}), flush=True)
        except Exception as e:  # le relevé continue ; le cycle suivant réessaie
            print(json.dumps({"t": time.strftime("%H:%M:%S", time.gmtime()), "erreur": repr(e)[:300]}), flush=True)
        if not vivant:
            return 0
        time.sleep(a.boucle)


if __name__ == "__main__":
    sys.exit(main())

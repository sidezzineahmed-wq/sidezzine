#!/usr/bin/env python3
"""Ré-analyse HORS LIGNE, avec le lecteur de fiche du kit, du HTML de fiche DÉJÀ LU et conservé (brut/ des compléments) :
aucune requête. Sert à extraire les blocs que l'ancien lecteur n'extrayait pas (retrait, prix des plans, prospectus /
échantillons) sans relire le portail.

  python3 reanalyser_fiches.py --fiches <stock/etat/fiches.json relu du coffre live> --brut <dossier brut/> [--brut ...]
                               --kit <kit à jour> --sortie <fiches.json ré-analysé> [--rapport <rapport.json>]

Règles :
  - seule une fiche dont le HTML conservé a EXACTEMENT le SHA-256 enregistré (sha256_html_tronque) est ré-analysée ;
  - la date réelle de lecture (lu_le), le passage (run), le SHA et le popup des lots ne changent jamais ; la ré-analyse est
    datée à part (reanalyse_le) avec version_parseur et version_lecture_initiale ;
  - le HTML conservé a été coupé avant le contact par l'ancien lecteur : contact et pièces restent « non lus » (le lecteur
    ne voit pas leurs blocs) ; ils viendront d'une vraie relecture ;
  - une fiche déjà analysée par le lecteur courant ou plus récent n'est pas touchée ; référence différente = non touchée ;
  - aucune ligne de qualification perdue : si le nouveau lecteur en perd une, l'ancienne liste est gardée (listé)."""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import sys

from integrer_fiches import lire, q_conserve


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fiches", required=True)
    ap.add_argument("--brut", action="append", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--rapport")
    ap.add_argument("--maintenant", help="date de ré-analyse (tests)")
    a = ap.parse_args(argv)
    sys.path.insert(0, a.kit)
    from veille.pmmp_fiche import VERSION_LECTURE, lire_fiche  # noqa: E402
    now = a.maintenant or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    F = lire(a.fiches, {}) or {}
    n = {"fiches": len(F), "reanalysees": 0, "deja_a_jour": 0, "sans_html": 0, "sha_different": 0, "ref_differente": 0,
         "q_garde_ancien": [], "champs_changes": {}}
    for k in sorted(F):
        doc = F[k]
        ch0 = doc.get("champs") or {}
        if ch0.get("version_lecture", 1) >= VERSION_LECTURE:
            n["deja_a_jour"] += 1
            continue
        o, r = k.split(":")[1:]
        h, vu = None, False
        for d in a.brut:
            p = os.path.join(d, f"{o}_{r}_fiche.html.gz")
            if not os.path.exists(p):
                continue
            vu = True
            t = gzip.open(p, "rt", encoding="utf-8", newline="").read()
            if hashlib.sha256(t.encode()).hexdigest() == doc.get("sha256_html_tronque"):
                h = t
                break
        if h is None:
            n["sha_different" if vu else "sans_html"] += 1
            continue
        ch = lire_fiche(h, masquer=True)
        if (ch.get("ref") or "").strip() != (ch0.get("ref") or "").strip():
            n["ref_differente"] += 1
            continue
        if not q_conserve(ch0.get("q"), ch.get("q")):
            n["q_garde_ancien"].append(k)
            ch["q"], ch["q_txt"] = ch0.get("q"), ch0.get("q_txt")
        for c in sorted(set(ch) | set(ch0)):
            if c not in ("version_lecture", "blocs_lus") and ch.get(c) != ch0.get(c):
                n["champs_changes"][c] = n["champs_changes"].get(c, 0) + 1
        doc["champs"] = ch
        doc["reanalyse_le"] = now
        doc["version_parseur"] = VERSION_LECTURE
        doc["version_lecture_initiale"] = ch0.get("version_lecture", 1)
        n["reanalysees"] += 1
    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    with open(a.sortie, "w", encoding="utf-8") as f:
        json.dump(F, f, ensure_ascii=False, indent=1, sort_keys=True)
    n["champs_changes"] = dict(sorted(n["champs_changes"].items()))
    if a.rapport:
        with open(a.rapport, "w", encoding="utf-8") as f:
            json.dump(n, f, ensure_ascii=False, indent=1)
    print(json.dumps({c: (len(v) if isinstance(v, list) else v) for c, v in n.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

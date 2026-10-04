"""python -m drive_adapter verifier-config | envoyer --chemin F --nom N [--parent ID] [--etat E] | recuperer --id ID --sortie F --sha256 H [--taille N]
                        | stocker-dce --ref R --zip F [--demande-le ISO] [--etat-dir D] | etat-dce --ref R | lister-dce
Imprime une ligne JSON ; code 0 si succès, 2 sinon. N'affiche jamais de jeton ni d'identifiant secret."""
import argparse
import json
import os
import sys

from .dce_stockage import StockageDCE
from .drive_resumable import VARIABLES, Drive, ErreurDrive


def _resume(m):
    """Sortie sans identifiant Drive de dossier ni de manifeste : statut, horodatages, fichiers (nom, taille, empreinte, id)."""
    if not m:
        return {"statut": None}
    return {"ref": m["ref"], "statut": m["statut"], "maj": m.get("maj"), "historique": m.get("historique", []), "archive": m.get("archive"),
            "fichiers": [{k: f[k] for k in ("nom", "chemin", "role", "taille", "sha256", "drive_id")} for f in m.get("fichiers", [])]}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="drive_adapter")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("verifier-config")
    e = sp.add_parser("envoyer")
    e.add_argument("--chemin", required=True)
    e.add_argument("--nom", required=True)
    e.add_argument("--parent")
    e.add_argument("--type", default="application/octet-stream")
    e.add_argument("--etat")
    g = sp.add_parser("recuperer")
    g.add_argument("--id", required=True)
    g.add_argument("--sortie", required=True)
    g.add_argument("--sha256", required=True)
    g.add_argument("--taille", type=int)
    k = sp.add_parser("stocker-dce")
    k.add_argument("--ref", required=True)
    k.add_argument("--zip", required=True)
    k.add_argument("--demande-le")
    k.add_argument("--etat-dir")
    t = sp.add_parser("etat-dce")
    t.add_argument("--ref", required=True)
    sp.add_parser("lister-dce")
    a = ap.parse_args(argv)
    try:
        mode = os.environ.get("DCE_GDRIVE_AUTH", "oauth")
        if a.cmd == "verifier-config":
            if mode == "proxy_oauth":
                print(json.dumps({"etat": "a_verifier", "mode": mode, "motif": "secrets dans le coffre du proxy : invisibles depuis la session ; seul un premier renouvellement réel les confirme"}, ensure_ascii=False))
                return 0
            r = {v: ("présente" if os.environ.get(v) else "absente") for v in VARIABLES}
            print(json.dumps({"etat": "ok" if all(x == "présente" for x in r.values()) else "incomplet", "variables": r}, ensure_ascii=False))
            return 0 if all(x == "présente" for x in r.values()) else 2
        d = Drive(auth=mode)
        if a.cmd in ("stocker-dce", "etat-dce", "lister-dce"):
            s = StockageDCE(d)
            r = (_resume(s.stocker(a.ref, a.zip, a.demande_le, None, a.etat_dir)) if a.cmd == "stocker-dce"
                 else _resume(s.lire_manifeste(a.ref)) if a.cmd == "etat-dce" else {"consultations": s.lister_manifestes()})
            print(json.dumps({"etat": "ok", **r}, ensure_ascii=False))
            return 0
        r = d.envoyer(a.chemin, a.nom, a.parent, a.type, a.etat) if a.cmd == "envoyer" else d.recuperer(a.id, a.sortie, a.sha256, a.taille)
        print(json.dumps({"etat": "ok", **r}, ensure_ascii=False))
        return 0
    except ErreurDrive as e:
        print(json.dumps({"etat": "echec", "type": type(e).__name__, "motif": str(e)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())

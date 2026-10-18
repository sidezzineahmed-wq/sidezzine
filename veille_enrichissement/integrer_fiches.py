#!/usr/bin/env python3
"""Intègre le complément des fiches (cache/ de complement_fiches.py) dans l'état du collecteur du coffre.

Entrées : --fiches  stock/etat/fiches.json RELU du coffre live (jamais une ancienne copie) ;
          --dossier dossier du complément (cache/, echecs/).
Sorties : --sortie  fiches.json fusionné (même format : {id: {id, lu_le, run, sha256_html_tronque, champs[, lots]}}) ;
          --complement referentiel/fiches_complement.json du kit (fiches et popups de lots inaccessibles après --essais).
Règles :
  - fiche : la lecture la plus récente gagne (lu_le) ; une lecture du coffre plus récente n'est jamais remplacée ;
  - lots : datés séparément ; la lecture de popup la plus récente gagne ; rattachés à la fiche du même id ;
  - un popup seul (besoin « lots ») n'est rattaché que si la fiche du coffre existe ;
  - rien n'est supprimé ; aucun champ n'est rempli sans lecture.
Sortie déterministe (tri des clés)."""
import argparse
import glob
import json
import os


def lire(p, d=None):
    if not p:
        return d
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return d


def q_conserve(ancien, nouveau):
    """Vrai si chaque ligne de qualification ancienne retrouve TOUTES ses valeurs non nulles dans une même ligne nouvelle
    (ex. ancien secteur « Y1 » = nouvelle qualification « Y1 » de la ligne Y / Y1) : un reparse ne perd rien."""
    vals = lambda r: {str(v) for v in r.values() if v not in (None, "")}
    return all(any(vals(o) <= vals(n) for n in nouveau or []) for o in ancien or [])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fiches", required=True)
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--essais", type=int, default=3)
    ap.add_argument("--precedent-complement", help="fiches_complement.json actuel du kit (s'il existe)")
    ap.add_argument("--kit", help="kit à jour : champs et lots RE-CALCULÉS depuis brut/ (HTML tronqué conservé, SHA vérifié), sans requête")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--complement", required=True)
    a = ap.parse_args(argv)
    F = lire(a.fiches, {}) or {}
    n = {"fiches_coffre": len(F), "fiche_ajoutee": 0, "fiche_remplacee_plus_recente": 0, "fiche_coffre_plus_recente_gardee": 0,
         "lots_rattaches": 0, "lots_sans_fiche_coffre": 0, "ref_differente_du_catalogue": 0}
    if a.kit:
        import gzip
        import hashlib
        import sys
        sys.path.insert(0, a.kit)
        from veille.pmmp_fiche import lire_fiche  # noqa
        from veille.pmmp_lots import lire_popup  # noqa
        n.update({"reparse_fiches": 0, "reparse_lots": 0, "reparse_sha_ko": 0, "reparse_change": 0})

        def brut(o, r_, nom, sha):
            p = os.path.join(a.dossier, "brut", f"{o}_{r_}_{nom}.html.gz")
            if not os.path.exists(p):
                return None
            h = gzip.open(p, "rt", encoding="utf-8", newline="").read()
            if hashlib.sha256(h.encode()).hexdigest() != sha:
                n["reparse_sha_ko"] += 1
                return None
            return h
    for p in sorted(glob.glob(os.path.join(a.dossier, "cache", "*.json"))):
        r = lire(p)
        k, fi, lo = r["id"], r.get("fiche"), r.get("lots")
        if a.kit:
            o, r_ = k.split(":")[1:]
            h = fi and brut(o, r_, "fiche", fi["sha256_html_tronque"])
            if h:
                ch = lire_fiche(h, masquer=True)
                if not q_conserve(fi["champs"].get("q"), ch.get("q")):
                    n.setdefault("reparse_q_garde_ancien", []).append(k)  # jamais de perte : l'ancienne lecture est gardée
                    ch["q"] = fi["champs"].get("q")
                n["reparse_change"] += ch != fi["champs"]
                fi["champs"] = ch
                n["reparse_fiches"] += 1
            h = lo and brut(o, r_, "lots", lo["sha256_html_tronque"])
            if h:
                ancien_lots = lo
                allot = (fi or {}).get("champs", {}).get("allot") or r.get("allot") or (F.get(k) or {}).get("champs", {}).get("allot")
                res = lire_popup(h, o, r_, allot)
                if res["statut"] in ("lu", "partiel") and len(res["lots"]) >= len(ancien_lots.get("lots") or []) and all(
                        q_conserve(o.get("q"), nl.get("q")) for o, nl in zip(ancien_lots.get("lots") or [], res["lots"])):
                    lo = {**{c: lo[c] for c in ("lu_le", "url", "sha256_html_tronque")}, **res}
                    n["reparse_lots"] += 1
        doc = F.get(k)
        if fi:
            nouveau = {"id": k, "lu_le": fi["lu_le"], "run": "complement_eaios_" + fi["lu_le"][:10], "sha256_html_tronque": fi["sha256_html_tronque"],
                       "champs": fi["champs"]}
            if (fi["champs"].get("ref") or "").strip() != (r.get("ref_catalogue") or "").strip():
                n["ref_differente_du_catalogue"] += 1
            if doc is None:
                F[k] = doc = nouveau
                n["fiche_ajoutee"] += 1
            elif fi["lu_le"] == doc.get("lu_le") and fi["sha256_html_tronque"] == doc.get("sha256_html_tronque"):
                # même lecture (même date, même HTML) : seuls les champs re-analysés par le parser à jour changent
                if not q_conserve((doc.get("champs") or {}).get("q"), fi["champs"].get("q")):
                    n.setdefault("reanalyse_q_garde_ancien", []).append(k)
                    fi["champs"]["q"] = (doc.get("champs") or {}).get("q")
                doc["champs"] = fi["champs"]
                n["meme_lecture_reanalysee"] = n.get("meme_lecture_reanalysee", 0) + 1
            elif fi["lu_le"] > (doc.get("lu_le") or ""):
                if not q_conserve((doc.get("champs") or {}).get("q"), fi["champs"].get("q")):
                    n.setdefault("relecture_q_differente", []).append(k)  # nouvelle lecture réelle : elle fait foi, l'écart est listé
                if doc.get("lots"):
                    nouveau["lots"] = doc["lots"]
                F[k] = doc = nouveau
                n["fiche_remplacee_plus_recente"] += 1
            else:
                n["fiche_coffre_plus_recente_gardee"] += 1
        if lo and lo.get("statut") in ("lu", "partiel"):
            if doc is None:
                n["lots_sans_fiche_coffre"] += 1
            elif lo["lu_le"] > ((doc.get("lots") or {}).get("lu_le") or ""):
                doc["lots"] = {c: lo[c] for c in ("lu_le", "url", "sha256_html_tronque", "statut", "n", "n_annonce", "lots", "raison") if c in lo}
                n["lots_rattaches"] += 1
    prec = lire(a.precedent_complement, {}) or {}
    fi_inacc, lo_inacc = dict(prec.get("fiches_inaccessibles") or {}), dict(prec.get("lots_inaccessibles") or {})
    for p in sorted(glob.glob(os.path.join(a.dossier, "echecs", "*.json"))):
        e = lire(p)
        if e.get("tentatives", 0) < a.essais:
            continue
        k = e["id"]
        o, r_ = k.split(":")[1:]
        rec = lire(os.path.join(a.dossier, "cache", f"{o}_{r_}.json"))
        info = {c: e.get(c) for c in ("tentatives", "dernier_echec", "raison", "inaccessible")}
        if rec and (rec.get("fiche") or k in F):
            lo_inacc[k] = info
        elif k not in F:
            fi_inacc[k] = info
    for k in list(fi_inacc):
        if k in F:
            fi_inacc.pop(k)
    for k in list(lo_inacc):
        if (F.get(k) or {}).get("lots"):
            lo_inacc.pop(k)
    with open(a.sortie, "w", encoding="utf-8") as f:
        json.dump({k: F[k] for k in sorted(F)}, f, ensure_ascii=False, indent=1)
    comp = {"version": 1, "source": "complément EAIOS des fiches PMMP (fiche + popup « Détail des lots »), essais bornés",
            "regle": "liste des lectures impossibles après essais bornés : valeurs inconnues, jamais remplies",
            "fiches_inaccessibles": {k: fi_inacc[k] for k in sorted(fi_inacc)}, "lots_inaccessibles": {k: lo_inacc[k] for k in sorted(lo_inacc)}}
    with open(a.complement, "w", encoding="utf-8") as f:
        json.dump(comp, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    n.update({"fiches_sortie": len(F), "fiches_inaccessibles": len(fi_inacc), "lots_inaccessibles": len(lo_inacc),
              "fiches_avec_lots": sum(1 for d in F.values() if d.get("lots"))})
    print(json.dumps(n, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

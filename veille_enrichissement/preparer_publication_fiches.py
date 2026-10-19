#!/usr/bin/env python3
"""Prépare la publication du complément des fiches, à partir d'une relecture COMPLÈTE et vérifiée du coffre live.

  python3 preparer_publication_fiches.py --coffre-in <relu> --dossier <complément> --kit <kit à jour> --sortie <out>

1. copie <relu> -> <out> ; remplace stock/kit par le kit à jour (référentiels du kit relu gardés s'ils diffèrent) ;
2. intègre le complément (integrer_fiches.py, re-analyse hors ligne avec garde anti-perte) -> stock/etat/fiches.json et
   stock/kit/referentiel/fiches_complement.json ;
3. reconstruit stock/catalogue_valide.json avec construire_catalogue.py du kit à jour sur l'état relu + fiches fusionnées
   (même listing, même date de passage : seul le détail change) ; refus si « maj » ≠ dernier succès du statut ;
4. manifeste, contrôle (coffre.py verifier), carte de publication (coffre.py carte).
statut.json, listing, couvertures et catalogue_dernier_passage.json ne sont PAS modifiés (aucun faux passage)."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def run(*cmd):
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True)
    if r.returncode not in (0,):
        raise SystemExit(f"échec {cmd[0]} : {r.stdout[-800:]} {r.stderr[-800:]}")
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--coffre-in", required=True)
    ap.add_argument("--dossier", required=True, action="append", help="dossier(s) du complément, intégrés dans l'ordre")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--aujourdhui")
    ap.add_argument("--garder-catalogue-valide", action="store_true",
                    help="dernier passage non complet : catalogue_valide.json du coffre relu gardé tel quel (le passage horaire "
                         "suivant au listing complet le reconstruit avec les fiches fusionnées) ; seul fiches.json change")
    a = ap.parse_args(argv)
    IN, OUT = os.path.abspath(a.coffre_in), os.path.abspath(a.sortie)
    v = json.loads(run(os.path.join(IN, "stock", "kit", "coffre.py"), "verifier", "--source", IN))
    assert v["ok"], v
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(IN, OUT)
    rapport = {"coffre_relu": {"manifest_cree_le": json.load(open(os.path.join(IN, "manifest.json")))["cree_le"], "fichiers": v["attendus"]}}
    # 2. kit à jour ; les référentiels de données du kit relu priment (aucune régression du mode, de la classification…)
    K = os.path.join(OUT, "stock", "kit")
    ref_relu = {f: sha(os.path.join(IN, "stock", "kit", "referentiel", f)) for f in os.listdir(os.path.join(IN, "stock", "kit", "referentiel"))}
    shutil.rmtree(K)
    run(os.path.join(a.kit, "coffre.py"), "kit", "--kit", a.kit, "--sortie", OUT)
    for f in ref_relu:
        if sha(os.path.join(K, "referentiel", f)) != ref_relu[f]:
            shutil.copy(os.path.join(IN, "stock", "kit", "referentiel", f), os.path.join(K, "referentiel", f))
            rapport.setdefault("referentiels_relus_gardes", []).append(f)
    src, prec_c = os.path.join(IN, "stock", "etat", "fiches.json"), os.path.join(IN, "stock", "kit", "referentiel", "fiches_complement.json")
    rapport["integration"] = []
    for i, dos in enumerate(a.dossier):
        dst, comp = os.path.join(OUT, "stock", "etat", f"_fiches_{i}.json"), os.path.join(OUT, f"_comp_{i}.json")
        rapport["integration"].append({"dossier": dos, **json.loads(run(os.path.join(ICI, "integrer_fiches.py"), "--fiches", src, "--dossier", dos,
                                                                        "--kit", a.kit, "--precedent-complement", prec_c, "--sortie", dst, "--complement", comp))})
        src, prec_c = dst, comp
    shutil.move(src, os.path.join(OUT, "stock", "etat", "fiches.json"))
    shutil.move(prec_c, os.path.join(K, "referentiel", "fiches_complement.json"))
    for f in os.listdir(os.path.join(OUT, "stock", "etat")):
        if f.startswith("_fiches_"):
            os.remove(os.path.join(OUT, "stock", "etat", f))
    for f in os.listdir(OUT):
        if f.startswith("_comp_"):
            os.remove(os.path.join(OUT, f))
    if a.garder_catalogue_valide:
        rapport["catalogue_valide"] = "gardé tel quel (dernier passage non complet)"
    else:
        # 3. catalogue valide reconstruit (même listing, fiches fusionnées)
        E = os.path.join(OUT, "_etat")
        run(os.path.join(K, "coffre.py"), "unpack", "--source", OUT, "--etat", E)
        cat_p = os.path.join(OUT, "_sortie", "catalogue.json")
        run(os.path.join(K, "construire_catalogue.py"), "--etat", E, "--sortie", cat_p, *(["--aujourdhui", a.aujourdhui] if a.aujourdhui else []))
        cat, st = json.load(open(cat_p)), json.load(open(os.path.join(OUT, "stock", "statut.json")))
        ancien = json.load(open(os.path.join(IN, "stock", "catalogue_valide.json")))
        assert cat["maj"] == st["dernier_succes"]["fin"] == ancien["maj"], (cat["maj"], st["dernier_succes"]["fin"], ancien["maj"])
        assert cat["total_portail"] == ancien["total_portail"]
        shutil.copy(cat_p, os.path.join(OUT, "stock", "catalogue_valide.json"))
        rapport["catalogue_valide"] = {"maj": cat["maj"], "n": cat["n"], "n_details_avant": ancien["n_details"], "n_details": cat["n_details"],
                                       "n_avant": ancien["n"]}
        shutil.rmtree(E)
        shutil.rmtree(os.path.join(OUT, "_sortie"))
    # 4. manifeste et contrôle
    sys.path.insert(0, K)
    import coffre  # noqa
    coffre.manifeste(OUT)
    v2 = coffre.verifier(OUT)
    assert v2["ok"], v2
    carte = coffre.carte_publication(OUT, os.path.join(IN, "manifest.json"))
    json.dump(carte, open(os.path.join(os.path.dirname(OUT), "carte_" + os.path.basename(OUT) + ".json"), "w"), ensure_ascii=False)
    m0, m1 = json.load(open(os.path.join(IN, "manifest.json")))["fichiers"], json.load(open(os.path.join(OUT, "manifest.json")))["fichiers"]
    rapport["changes"] = sorted(k for k in m1 if k not in m0 or m0[k]["sha256"] != m1[k]["sha256"])
    rapport["retires"] = sorted(k for k in m0 if k not in m1)
    print(json.dumps(rapport, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

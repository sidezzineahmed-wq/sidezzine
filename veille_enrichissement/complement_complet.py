#!/usr/bin/env python3
"""Complément COMPLET du « Mode de passation » (élément modePassation de la fiche publique PMMP), durable et reprenable.

Cible : toutes les annonces de --cibles (liste d'identifiants pmmp:<org>:<ref> avec la référence du catalogue) sans mode connu.
Lecture publique sans compte, client du kit collecteur (>= --delai s + gigue ; arrêt définitif sur 401/403 : rien n'est contourné).
Le bloc « Contact administratif » est coupé AVANT analyse ; seuls mode_passation, proc, ref, lu_le, url, sha256 sont gardés.

Points de reprise (écriture atomique, un fichier par fiche) :
  cache/<org>_<ref>.json   lecture réussie : statut "lu" (mode présent) ou "champ_absent" (fiche lue, élément vide) ;
  echecs/<org>_<ref>.json  tentatives échouées (réseau, page sans référence/objet = "inaccessible") : au plus --essais par
                           fiche, attente croissante entre passes ; au-delà : irréductible, listé, jamais rempli.
  etat.json                avancement (relu au redémarrage : aucune fiche déjà lue n'est relue).
Fenêtre de courtoisie : pause pendant les minutes --pause-debut..--pause-fin de chaque heure (passage horaire du collecteur).
"""
import argparse
import datetime
import hashlib
import json
import os
import random
import sys
import time

now = lambda: datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def ecrire(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, p)


def lire(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--cibles", required=True, help="JSON {id: {ref, lim, h}}")
    ap.add_argument("--dossier", required=True, help="dossier du complément (cache/, echecs/, etat.json)")
    ap.add_argument("--delai", type=float, default=4.0)
    ap.add_argument("--essais", type=int, default=3)
    ap.add_argument("--pause-debut", type=int, default=10)
    ap.add_argument("--pause-fin", type=int, default=22)
    a = ap.parse_args(argv)
    sys.path.insert(0, a.kit)
    from veille.client import ArretCollecte, ClientPMMP, texte  # noqa
    from veille.pmmp_fiche import PARAMS, fiche_valide, lire_fiche, tronquer_contact  # noqa
    C, E = os.path.join(a.dossier, "cache"), os.path.join(a.dossier, "echecs")
    os.makedirs(C, exist_ok=True)
    os.makedirs(E, exist_ok=True)
    cibles = lire(a.cibles)
    pe = os.path.join(a.dossier, "etat.json")
    etat = lire(pe, {}) or {}
    etat.update({"debut_session": now(), "cibles": len(cibles), "arret": None})
    client = ClientPMMP(delai_min=a.delai)
    passe = 0
    while True:
        passe += 1
        restant = []
        for k, v in sorted(cibles.items(), key=lambda kv: (kv[1].get("lim") or "9", kv[1].get("h") or "", kv[0])):
            o, r = k.split(":")[1:]
            if os.path.exists(os.path.join(C, f"{o}_{r}.json")):
                continue
            ech = lire(os.path.join(E, f"{o}_{r}.json"), {}) or {}
            if ech.get("tentatives", 0) >= a.essais:
                continue
            restant.append((k, o, r, v, ech))
        etat.update({"passe": passe, "restant_passe": len(restant), "maj": now()})
        ecrire(pe, etat)
        if not restant:
            break
        consecutifs = 0
        for k, o, r, v, ech in restant:
            while a.pause_debut <= datetime.datetime.now(datetime.timezone.utc).minute < a.pause_fin:
                etat["en_pause"] = now()
                ecrire(pe, etat)
                time.sleep(30)
            if ech.get("prochain_essai_apres") and ech["prochain_essai_apres"] > now():
                continue
            try:
                rep = client.get(PARAMS(r, o))
                h, coupe = tronquer_contact(texte(rep))
                f = lire_fiche(h, masquer=True)
                lu = now()
                if not fiche_valide(f):
                    raise ValueError("inaccessible : page sans référence ni objet")
                mp = f.get("mode_passation")
                ecrire(os.path.join(C, f"{o}_{r}.json"), {
                    "id": k, "lu_le": lu, "url": rep.url[:300], "statut": "lu" if mp else "champ_absent", "mode_passation": mp,
                    "proc": f.get("proc"), "ref": f.get("ref"), "ref_catalogue": v.get("ref"), "contact_coupe": coupe,
                    "sha256_html_tronque": hashlib.sha256(h.encode()).hexdigest()})
                if os.path.exists(os.path.join(E, f"{o}_{r}.json")):
                    os.remove(os.path.join(E, f"{o}_{r}.json"))
                consecutifs = 0
                etat["lues_session"] = etat.get("lues_session", 0) + 1
            except ArretCollecte as e:
                if "HTTP 401" not in str(e) and "HTTP 403" not in str(e):  # réseau / 5xx épuisés : échec compté, on continue
                    n = ech.get("tentatives", 0) + 1
                    ech.update({"id": k, "tentatives": n, "dernier_echec": now(), "raison": str(e)[:240], "inaccessible": False,
                                "prochain_essai_apres": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10 * n)).replace(microsecond=0).isoformat()})
                    ecrire(os.path.join(E, f"{o}_{r}.json"), ech)
                    consecutifs += 1
                    if consecutifs >= 3:
                        attente = min(900, 60 * 2 ** min(consecutifs - 3, 4)) + random.uniform(0, 15)
                        etat["recul"] = {"depuis": now(), "secondes": round(attente)}
                        ecrire(pe, etat)
                        time.sleep(attente)
                    continue
                etat.update({"arret": f"{now()} {e}"})
                ecrire(pe, etat)
                print(json.dumps({"ARRET": str(e)}, ensure_ascii=False), flush=True)
                return 3
            except Exception as e:
                n = ech.get("tentatives", 0) + 1
                ech.update({"id": k, "tentatives": n, "dernier_echec": now(), "raison": repr(e)[:240],
                            "inaccessible": "inaccessible" in repr(e),
                            "prochain_essai_apres": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10 * n)).replace(microsecond=0).isoformat()})
                ecrire(os.path.join(E, f"{o}_{r}.json"), ech)
                consecutifs += 1
                if consecutifs >= 5:  # portail instable : recul croissant, puis on continue
                    attente = min(900, 60 * 2 ** min(consecutifs - 5, 4)) + random.uniform(0, 15)
                    etat["recul"] = {"depuis": now(), "secondes": round(attente)}
                    ecrire(pe, etat)
                    time.sleep(attente)
            etat["maj"] = now()
            ecrire(pe, etat)
        # passe suivante : seulement les échecs à réessayer (attente déjà inscrite)
        if all((lire(os.path.join(E, f"{o}_{r}.json"), {}) or {}).get("tentatives", 0) >= a.essais or os.path.exists(os.path.join(C, f"{o}_{r}.json"))
               for k, o, r, v, e in restant):
            continue
        time.sleep(60)
    etat.update({"fin": now()})
    ecrire(pe, etat)
    print(json.dumps({"fin": etat["fin"], "lues_session": etat.get("lues_session", 0)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

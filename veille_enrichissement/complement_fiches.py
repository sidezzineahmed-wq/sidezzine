#!/usr/bin/env python3
"""Complément COMPLET des fiches PMMP : une lecture alimente TOUS les champs de fiche (estimation, caution, TPE/PME,
qualifications, agréments, visites, réunion, échantillons, variante, domaines, lieux d'ouverture/dépôt, mode de passation…)
et, pour une consultation allotie, le popup public « Détail des lots » lu dans le même passage (valeurs PAR LOT).

Cibles (--cibles, JSON {id: {ref, lim, h, besoin, allot}}) :
  besoin « fiche »  fiche jamais lue par le collecteur (ou détail seulement hérité) : fiche, puis popup si elle est allotie ;
  besoin « lots »   fiche déjà lue et allotie : popup seul (aucune relecture de la fiche).
Lecture publique sans compte, client du kit (arrêt définitif sur 401/403 : rien n'est contourné). Le bloc « Contact
administratif » est coupé AVANT analyse et avant toute sauvegarde ; les coordonnées des textes libres sont masquées.

Ordonnanceur (identique au complément du mode de passation) : au plus --paralleles connexions (1 ou 2), départs globalement
espacés d'au moins --delai s (+ gigue), un seul fil écrit ; pause pendant les minutes --pause-debut..--pause-fin de chaque
heure (passage horaire du collecteur) ; recul croissant après 3 échecs consécutifs.
Points de reprise (écriture atomique, un fichier par consultation) :
  cache/<org>_<ref>.json    lecture : fiche (champs complets, lu_le, url, sha256) et lots (statut, lu_le, url, lots…) ;
  brut/<org>_<ref>_{fiche,lots}.html.gz  HTML tronqué (sans contact) : toute correction du parser se rejoue SANS requête ;
  echecs/<org>_<ref>.json   tentatives échouées (au plus --essais ; au-delà : irréductible, listé, jamais rempli) ;
  etat.json                 avancement (relu au redémarrage : rien de déjà lu n'est relu).
"""
import argparse
import datetime
import gzip
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


def ecrire_gz(p, texte):
    tmp = p + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        f.write(texte)
    os.replace(tmp, p)


def lire(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return d


def termine(rec, besoin):
    """Vrai si plus rien n'est à lire pour cette cible."""
    if not rec:
        return False
    if besoin == "fiche" and not rec.get("fiche"):
        return False
    lots = rec.get("lots")
    return not rec.get("allotie") or bool(lots and lots.get("statut") in ("lu", "partiel"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--cibles", required=True)
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--delai", type=float, default=4.0)
    ap.add_argument("--essais", type=int, default=3)
    ap.add_argument("--paralleles", type=int, default=1)
    ap.add_argument("--pause-debut", type=int, default=10)
    ap.add_argument("--pause-fin", type=int, default=22)
    ap.add_argument("--attente-echec-min", type=float, default=10.0, help="attente avant nouvel essai : N x tentatives minutes")
    a = ap.parse_args(argv)
    if not 1 <= a.paralleles <= 2:
        ap.error("--paralleles : 1 ou 2")
    sys.path.insert(0, a.kit)
    from veille.client import ArretCollecte, ClientPMMP, texte  # noqa
    from veille.pmmp_fiche import PARAMS, fiche_valide, lire_fiche, tronquer_contact  # noqa
    from veille.pmmp_lots import PARAMS_LOTS, lire_popup  # noqa
    C, E, B = (os.path.join(a.dossier, x) for x in ("cache", "echecs", "brut"))
    for d in (C, E, B):
        os.makedirs(d, exist_ok=True)
    cibles = lire(a.cibles)
    pe = os.path.join(a.dossier, "etat.json")
    etat = lire(pe, {}) or {}
    etat.update({"debut_session": now(), "cibles": len(cibles), "arret": None})
    import concurrent.futures as cf
    import threading
    verrou, dernier_depart, locaux = threading.Lock(), [0.0], threading.local()

    def depart():
        with verrou:
            reste = dernier_depart[0] + a.delai + random.uniform(0, 1.0) - time.monotonic()
            if reste > 0:
                time.sleep(reste)
            dernier_depart[0] = time.monotonic()

    def get(params):
        if not hasattr(locaux, "c"):
            locaux.c = ClientPMMP(delai_min=a.delai)
        depart()
        rep = locaux.c.get(params)
        h, coupe = tronquer_contact(texte(rep))
        return rep.url, h, coupe

    def charger(k, o, r, v, rec):
        """Lit ce qui manque (fiche puis popup). Ne lève pas : renvoie (kind, rec_maj, err)."""
        rec = dict(rec or {"id": k, "ref_catalogue": v.get("ref")})
        brut = {}
        try:
            if v.get("besoin") == "fiche" and not rec.get("fiche"):
                url, h, coupe = get(PARAMS(r, o))
                f = lire_fiche(h, masquer=True)
                if not fiche_valide(f):
                    return "inacc", rec, "fiche : page sans référence ni objet", brut
                brut["fiche"] = h
                rec["fiche"] = {"lu_le": now(), "url": url[:300], "contact_coupe": coupe,
                                "sha256_html_tronque": hashlib.sha256(h.encode()).hexdigest(), "champs": f}
                rec["allotie"] = bool(f.get("allot"))
                rec["allot"] = f.get("allot")
            elif "allotie" not in rec:
                rec["allotie"], rec["allot"] = True, v.get("allot")
            if rec.get("allotie") and not (rec.get("lots") or {}).get("statut") in ("lu", "partiel"):
                url, h, coupe = get(PARAMS_LOTS(r, o))
                res = lire_popup(h, o, r, rec.get("allot"))
                if res["statut"] == "inaccessible":
                    return "inacc", rec, "lots : " + res.get("raison", "popup inattendu"), brut
                brut["lots"] = h
                rec["lots"] = {"lu_le": now(), "url": url[:300], "sha256_html_tronque": hashlib.sha256(h.encode()).hexdigest(), **res}
            return "ok", rec, None, brut
        except ArretCollecte as e:
            kind = "arret" if ("HTTP 401" in str(e) or "HTTP 403" in str(e)) else "reseau"
            return kind, rec, str(e), brut
        except Exception as e:
            return "err", rec, repr(e), brut

    def echec(o, r, k, raison, inacc):
        p = os.path.join(E, f"{o}_{r}.json")
        ech = lire(p, {}) or {}
        n = ech.get("tentatives", 0) + 1
        ech.update({"id": k, "tentatives": n, "dernier_echec": now(), "raison": raison[:240], "inaccessible": inacc,
                    "prochain_essai_apres": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=a.attente_echec_min * n)).replace(microsecond=0).isoformat()})
        ecrire(p, ech)

    pool = cf.ThreadPoolExecutor(max_workers=a.paralleles)
    passe = 0
    try:
        while True:
            passe += 1
            restant = []
            for k, v in sorted(cibles.items(), key=lambda kv: (kv[1].get("prio", 9), kv[1].get("lim") or "9", kv[1].get("h") or "", kv[0])):
                o, r = k.split(":")[1:]
                rec = lire(os.path.join(C, f"{o}_{r}.json"))
                if termine(rec, v.get("besoin")):
                    continue
                ech = lire(os.path.join(E, f"{o}_{r}.json"), {}) or {}
                if ech.get("tentatives", 0) >= a.essais:
                    continue
                restant.append((k, o, r, v, rec, ech))
            etat.update({"passe": passe, "restant_passe": len(restant), "maj": now(), "paralleles": a.paralleles})
            ecrire(pe, etat)
            if not restant:
                break
            consecutifs, arret, en_cours, file = 0, None, {}, list(restant)
            while (file or en_cours) and not arret:
                while file and len(en_cours) < a.paralleles:
                    while a.pause_debut <= datetime.datetime.now(datetime.timezone.utc).minute < a.pause_fin and not en_cours:
                        etat["en_pause"] = now()
                        ecrire(pe, etat)
                        time.sleep(30)
                    if a.pause_debut <= datetime.datetime.now(datetime.timezone.utc).minute < a.pause_fin:
                        break
                    k, o, r, v, rec, ech = file.pop(0)
                    if ech.get("prochain_essai_apres") and ech["prochain_essai_apres"] > now():
                        continue
                    en_cours[pool.submit(charger, k, o, r, v, rec)] = (k, o, r)
                if not en_cours:
                    continue
                fait, _ = cf.wait(list(en_cours), return_when=cf.FIRST_COMPLETED)
                for fu in fait:
                    k, o, r = en_cours.pop(fu)
                    kind, rec, err, brut = fu.result()
                    for nom, h in brut.items():
                        ecrire_gz(os.path.join(B, f"{o}_{r}_{nom}.html.gz"), h)
                    if rec.get("fiche") or rec.get("lots"):
                        ecrire(os.path.join(C, f"{o}_{r}.json"), rec)  # une lecture réussie est gardée même si la suite échoue
                    if kind == "ok":
                        if os.path.exists(os.path.join(E, f"{o}_{r}.json")):
                            os.remove(os.path.join(E, f"{o}_{r}.json"))
                        consecutifs = 0
                        etat["lues_session"] = etat.get("lues_session", 0) + 1
                    elif kind == "arret":
                        arret = err
                    else:
                        echec(o, r, k, err, kind == "inacc")
                        consecutifs += 1
                    if consecutifs >= 3:
                        cf.wait(list(en_cours))
                        attente = min(900, 60 * 2 ** min(consecutifs - 3, 4)) + random.uniform(0, 15)
                        etat["recul"] = {"depuis": now(), "secondes": round(attente)}
                        ecrire(pe, etat)
                        time.sleep(attente)
                etat["maj"] = now()
                ecrire(pe, etat)
            if arret:
                etat["arret"] = f"{now()} {arret}"
                ecrire(pe, etat)
                print(json.dumps({"ARRET": str(arret)}, ensure_ascii=False), flush=True)
                return 3
            time.sleep(5 if a.delai < 3 else 60)
    finally:
        pool.shutdown(wait=True)
    etat["fin"] = now()
    ecrire(pe, etat)
    print(json.dumps({"fin": etat["fin"], "lues_session": etat.get("lues_session", 0)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

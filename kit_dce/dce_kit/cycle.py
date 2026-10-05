"""Cycle d'une tâche cloud FINIE autour d'une file de demandes DCE gardée dans la base d'un artefact (aucun serveur).

La tâche (Claude) fait seule les appels d'outils : lecture de la file et écritures par ArtifactData, dépôt des fichiers par
Artifact (asset). Ce module ne fait AUCUN appel réseau : il décide (planifier) puis traduit un résultat en écritures
(resultat), toutes épinglées sur la version lue (if_version) pour qu'une modification concurrente fasse échouer le lot
au lieu d'être écrasée.

File  : collection `dce_demande`, un document par dossier :
  {ao_id, ref, org, reference_attendue?, etat, demande_par, demande_le,
   cg?: {texte, lien, empreinte, portee, algo, doc_sha256, canonique?, lue_le},
   validation?: {phrase, empreinte, par, le},            <- écrite par un HUMAIN depuis la page, jamais par la tâche
   tache?: {run, jusqu}, erreur?: {code, motif, le}, resultat?: {...}, maj}
États : demandee -> ouverture -> attente_validation_CG -> (humain) cg_validees -> telechargement -> pret | echec | expiree | annulee
Registre : collection `dcef`, document <ao_id> : {fichiers: {dce_N | dceo_N | dcezip_N: {...}}, lots: [...], dossier, maj}.
La tâche n'écrit JAMAIS le document du dossier lui-même : la page fusionne le registre à l'affichage."""
import datetime
import hashlib
import json
import os

from .cg_texte import ALGO
from .tache import PHRASE

BAIL_MIN = 45                 # une tâche bloquée libère la demande après ce délai
ATTENTE_CG_H = 72             # une demande en attente de validation humaine expire
VALIDITE_CG_H = 24            # une validation humaine non utilisée expire
BASE_CLE = 1000               # numéros de clés réservés aux dépôts de la tâche (les dépôts manuels prennent les plus petits)


def _t(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None


def _iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _version(doc):
    return doc.get("__version") or doc.get("version")


def _ecr(op, coll, did, data, version):
    w = {"op": op, "collection": coll, "doc_id": did, "data": data}
    if version:
        w["if_version"] = version
    return w


def validation_ok(d, maintenant):
    v, cg = d.get("validation") or {}, d.get("cg") or {}
    le = _t(v.get("le"))
    if v.get("phrase") != PHRASE or not v.get("par") or not cg.get("empreinte") or v.get("empreinte") != cg.get("empreinte"):
        return False, "validation humaine absente ou ne correspondant pas aux CG présentées"
    if not le or le > maintenant or (maintenant - le).total_seconds() > VALIDITE_CG_H * 3600:
        return False, f"validation humaine expirée (plus de {VALIDITE_CG_H} h)"
    return True, ""


def planifier(demandes, dossiers_autorises, run, maintenant=None, max_actions=1):
    """demandes : {doc_id: document (avec sa version)}. Rend {actions, ecritures, ignorees}. Au plus `max_actions` navigation
    par passage ; les écritures prennent le bail AVANT toute navigation (lot épinglé : si un autre passage l'a pris, il échoue)."""
    maintenant = maintenant or datetime.datetime.now(datetime.timezone.utc)
    actions, ecritures, ignorees = [], [], []
    for did, d in sorted(demandes.items(), key=lambda x: x[1].get("demande_le") or ""):
        ver, etat = _version(d), d.get("etat")
        if d.get("ao_id") != did or did not in dossiers_autorises:
            ignorees.append({"id": did, "motif": "dossier non autorisé pour la tâche (essai : dossiers de test uniquement)"})
            continue
        bail = d.get("tache") or {}
        if bail.get("jusqu") and (_t(bail["jusqu"]) or maintenant) > maintenant:
            ignorees.append({"id": did, "motif": f"déjà prise par le passage {bail.get('run')}"})
            continue
        if etat in ("ouverture", "telechargement"):      # bail échu : la tâche précédente s'est arrêtée en route
            ecritures.append(_ecr("update", "dce_demande", did, {"etat": "echec", "tache": None, "maj": _iso(maintenant),
                              "erreur": {"code": "interrompu", "motif": "passage précédent interrompu ; rien n'est retenté automatiquement", "le": _iso(maintenant)}}, ver))
            continue
        if etat == "attente_validation_CG":
            lue = _t((d.get("cg") or {}).get("lue_le"))
            if lue and (maintenant - lue).total_seconds() > ATTENTE_CG_H * 3600:
                ecritures.append(_ecr("update", "dce_demande", did, {"etat": "expiree", "maj": _iso(maintenant)}, ver))
            continue
        if len(actions) >= max_actions or etat not in ("demandee", "cg_validees"):
            continue
        if etat == "cg_validees" and (d.get("cg") or {}).get("algo") != ALGO:
            # aucune migration : les CG ont été lues par un autre algorithme et leurs octets ne sont pas conservés
            ecritures.append(_ecr("update", "dce_demande", did, {"etat": "echec", "tache": None, "maj": _iso(maintenant), "erreur": {"code": "cg_algo",
                              "motif": f"CG lues avec un autre algorithme ({(d.get('cg') or {}).get('algo') or 'antérieur, octets bruts'}) que {ALGO} : "
                                       "les octets anciens n'étant pas conservés, l'équivalence du consentement n'est pas prouvée ; "
                                       "nouvelle demande (ouverture) et nouvelle validation humaine requises", "le": _iso(maintenant)}}, ver))
            continue
        if etat == "cg_validees":
            ok, motif = validation_ok(d, maintenant)
            if not ok:
                ecritures.append(_ecr("update", "dce_demande", did, {"etat": "attente_validation_CG", "maj": _iso(maintenant),
                                  "validation": None, "erreur": {"code": "validation", "motif": motif, "le": _iso(maintenant)}}, ver))
                continue
        suivant = "ouverture" if etat == "demandee" else "telechargement"
        bail = {"run": run, "jusqu": _iso(maintenant + datetime.timedelta(minutes=BAIL_MIN))}
        ecritures.append(_ecr("update", "dce_demande", did, {"etat": suivant, "tache": bail, "maj": _iso(maintenant)}, ver))
        a = {"id": did, "commande": "ouvrir" if etat == "demandee" else "telecharger", "ref": d["ref"], "org": d["org"],
             "reference_attendue": d.get("reference_attendue")}
        if etat == "cg_validees":
            v = d["validation"]
            a["validation"] = {"ref": d["ref"], "org": d["org"], "phrase": v["phrase"], "empreinte": v["empreinte"], "par": v["par"], "le": v["le"]}
            # CG PRÉSENTÉES lors de la validation (texte, lien, algorithme, copie canonique) : pour rapporter un éventuel changement
            # ligne à ligne ; ce n'est jamais une validation ni une empreinte de remplacement
            a["validation"]["cg"] = {k: d["cg"][k] for k in ("texte", "lien", "algo", "canonique") if k in d["cg"]}
        actions.append(a)
    return {"run": run, "le": _iso(maintenant), "actions": actions, "ecritures": ecritures, "ignorees": ignorees}


def empreinte_contenu(manifest):
    """Empreinte du CONTENU (ensemble des SHA-256 des fichiers), indépendante des octets du ZIP : un portail qui régénère
    l'archive à chaque téléchargement (horodatages) produit un autre ZIP pour le même dossier."""
    return hashlib.sha256("\n".join(sorted(f["sha256"] for f in manifest["fichiers"])).encode()).hexdigest()


def _cle(prefixe, pris):
    n = BASE_CLE
    while f"{prefixe}_{n}" in pris:
        n += 1
    pris.add(f"{prefixe}_{n}")
    return f"{prefixe}_{n}"


def resultat(did, demande, etat, run, registre=None, manifest=None, depots=None, maintenant=None, drive=None):
    """Traduit l'état écrit par une commande du kit en écritures épinglées. `depots` : {fichier_local: asset_id} rendu par
    les dépôts Artifact ; chaque fichier du manifest doit y figurer, sinon rien n'est rattaché (pas de succès partiel).
    `drive` (au lieu de `depots`) : résumé rendu par « python -m drive_adapter stocker-dce » ; le dossier n'est marqué prêt que si
    Drive a vérifié TOUS les fichiers du manifest (même SHA-256 et taille) ; aucune entrée d'asset n'est écrite dans dcef."""
    maintenant = maintenant or datetime.datetime.now(datetime.timezone.utc)
    m_iso, ver = _iso(maintenant), _version(demande)
    if (demande.get("tache") or {}).get("run") != run:
        raise ValueError("cette demande n'est pas tenue par ce passage : aucune écriture")
    fin = {"tache": None, "maj": m_iso}
    if etat.get("etat") == "echec":
        return [_ecr("update", "dce_demande", did, {**fin, "etat": "echec", "erreur": {"code": etat.get("code"), "motif": etat.get("motif"), "le": m_iso}}, ver)]
    if etat.get("etat") == "attente_validation_CG":
        cg = {**etat["cg"], "lue_le": m_iso}
        return [_ecr("update", "dce_demande", did, {**fin, "etat": "attente_validation_CG", "cg": cg, "validation": None, "erreur": None}, ver)]
    if etat.get("etat") != "pret":
        raise ValueError(f"état inattendu : {etat.get('etat')}")
    registre = registre or {}
    lots = registre.get("lots") or []
    contenu = empreinte_contenu(manifest)
    if any((l.get("zip") or {}).get("sha256") == manifest["zip"]["sha256"] or l.get("contenu") == contenu for l in lots):
        return [_ecr("update", "dce_demande", did, {**fin, "etat": "pret", "erreur": None,
                     "resultat": {"zip_sha256": manifest["zip"]["sha256"], "contenu": contenu, "deja_importe": True, "cles": [], "le": m_iso}}, ver)]
    if drive is not None:
        return [_resultat_drive(did, manifest, drive, contenu, fin, m_iso, ver, demande)]
    depots = depots or {}
    manquants = [f["nom"] for f in manifest["fichiers"] + [manifest["zip"]] if not depots.get(f["fichier_local"])]
    if manquants:
        return [_ecr("update", "dce_demande", did, {**fin, "etat": "echec", "erreur": {"code": "depot",
                     "motif": "dépôt incomplet, rien n'est rattaché : " + ", ".join(manquants[:10]), "le": m_iso}}, ver)]
    pris, nouveaux, src, lot = set(registre.get("fichiers") or {}), {}, "PMMP via la tâche cloud", "c" + run
    for f in manifest["fichiers"]:
        commun = {"id": depots[f["fichier_local"]], "nom": f["nom"], "taille": f["taille"], "sha256": f["sha256"], "chemin": f["chemin"], "source": src, "lot": lot, "le": m_iso}
        if f["depot"] == "pdf":
            nouveaux[_cle("dce", pris)] = {**commun, "type": "pdf"}
        else:
            ext = os.path.splitext(f["nom"])[1].lstrip(".").lower() or "fichier"
            nouveaux[_cle("dceo", pris)] = {**commun, "type": ext, "enc": "base64"}
    z = manifest["zip"]
    nouveaux[_cle("dcezip", pris)] = {"id": depots[z["fichier_local"]], "nom": z["nom"], "taille": z["taille"], "sha256": z["sha256"], "type": "zip",
                                      "mime": "application/zip", "enc": "base64", "source": src, "lot": lot, "le": m_iso}
    lot_rec = {"lot": lot, "le": m_iso, "par": "tache:" + run, "zip": {"nom": z["nom"], "sha256": z["sha256"], "taille": z["taille"], "conserve": True},
               "contenu": contenu, "cles": list(nouveaux), "rejets": []}
    rv = _version(registre)
    reg = ({"fichiers": nouveaux, "lots": lots + [lot_rec], "maj": m_iso} if rv
           else {"fichiers": nouveaux, "lots": [lot_rec], "dossier": did, "maj": m_iso})
    return [_ecr("update" if rv else "set", "dcef", did, reg, rv),
            _ecr("update", "dce_demande", did, {**fin, "etat": "pret", "erreur": None,
                 "resultat": {"zip_sha256": z["sha256"], "contenu": contenu, "deja_importe": False, "cles": list(nouveaux), "valide_par": (demande.get("validation") or {}).get("par"), "le": m_iso}}, ver)]


def _resultat_drive(did, manifest, drive, contenu, fin, m_iso, ver, demande):
    ranges = {(f.get("sha256"), f.get("taille")) for f in drive.get("fichiers") or []}
    attendus = manifest["fichiers"] + [manifest["zip"]]
    manquants = [f["nom"] for f in attendus if (f["sha256"], f["taille"]) not in ranges]
    if drive.get("statut") != "verifie" or manquants:
        motif = "stockage Drive non vérifié" if drive.get("statut") != "verifie" else "absents du Drive : " + ", ".join(manquants[:10])
        return _ecr("update", "dce_demande", did, {**fin, "etat": "echec", "erreur": {"code": "stockage", "motif": motif, "le": m_iso}}, ver)
    z = manifest["zip"]
    return _ecr("update", "dce_demande", did, {**fin, "etat": "pret", "erreur": None, "resultat": {
        "stockage": "drive", "ref": drive.get("ref"), "verifie_le": drive.get("maj"), "fichiers": len(attendus),
        "zip_sha256": z["sha256"], "contenu": contenu, "deja_importe": False, "cles": [],
        "valide_par": (demande.get("validation") or {}).get("par"), "le": m_iso}}, ver)


def reprise_stockage(did, demande, manifest, drive, zip_sha256_attendu, run, dossiers_autorises, maintenant=None):
    """Reprise du STOCKAGE SEUL après un passage dont le téléchargement a réussi mais dont le stockage Drive a échoué
    (dce_demande : etat « echec », code « stockage »). L'état « pret » du passage ayant été remplacé par l'état d'échec,
    l'archive est désignée par son SHA-256 relevé dans ce passage (zip_sha256_attendu), qui doit être celui du manifest
    et de l'archive rangée dans Drive.
    Aucune navigation, aucun téléchargement, aucune CG lue ni acceptée : `validation` et `cg` ne sont ni lues pour décider
    ni réécrites. Pas de bail : « resultat » exige le bail du passage (tache.run), libéré par l'échec ; la reprise est UNE
    écriture épinglée (if_version) sur la version lue, et planifier ne prend jamais une demande en « echec ».
    L'échec d'origine est conservé (resultat.reprise.echec_precedent) : rien n'est effacé de l'historique."""
    maintenant = maintenant or datetime.datetime.now(datetime.timezone.utc)
    m_iso, ver = _iso(maintenant), _version(demande)
    err = demande.get("erreur") or {}
    if not ver:
        raise ValueError("version de la demande inconnue : aucune écriture non épinglée")
    if demande.get("ao_id") != did or did not in dossiers_autorises:
        raise ValueError("dossier non autorisé pour la tâche")
    if demande.get("etat") != "echec" or err.get("code") != "stockage":
        raise ValueError(f"reprise refusée : la demande n'est pas en échec de stockage (etat {demande.get('etat')}, code {err.get('code')})")
    bail = demande.get("tache") or {}
    if bail.get("jusqu") and (_t(bail["jusqu"]) or maintenant) > maintenant:
        raise ValueError(f"reprise refusée : demande tenue par le passage {bail.get('run')}")
    z = manifest["zip"]
    if not zip_sha256_attendu or zip_sha256_attendu != z["sha256"]:
        raise ValueError("reprise refusée : le manifest ne correspond pas à l'archive du téléchargement d'origine")
    if drive.get("ref") != did:
        raise ValueError("reprise refusée : le stockage Drive concerne une autre consultation")
    if (drive.get("archive") or {}).get("sha256") != z["sha256"]:
        raise ValueError("reprise refusée : l'archive rangée dans Drive n'est pas celle du manifest")
    w = _resultat_drive(did, manifest, drive, empreinte_contenu(manifest), {"tache": None, "maj": m_iso}, m_iso, ver, demande)
    if w["data"]["etat"] != "pret":
        return w   # stockage toujours non vérifié : nouvel échec daté, l'ancien reste dans le journal du passage
    w["data"]["resultat"]["reprise"] = {"run": run, "le": m_iso, "echec_precedent": err, "zip_sha256": z["sha256"],
                                        "nature": "stockage seul, octets du téléchargement d'origine, aucun accès au portail"}
    return w


def _lire(p):
    if not p:
        return None
    if os.path.isdir(p):
        return {os.path.splitext(n)[0]: json.load(open(os.path.join(p, n), encoding="utf-8")) for n in sorted(os.listdir(p)) if n.endswith(".json")}
    return json.load(open(p, encoding="utf-8"))


def main_planifier(a):
    dem = _lire(a.file)
    for did, v in (_lire(a.versions) or {}).items():
        if did in dem:
            dem[did]["__version"] = int(v)
    for did, d in dem.items():
        if not _version(d):
            raise SystemExit(f"version inconnue pour dce_demande/{did} : passez --versions (aucune écriture non épinglée)")
    autorises = set(x for x in a.dossiers_autorises.split(",") if x)
    p = planifier(dem, autorises, a.run, max_actions=a.max_actions)
    json.dump(p, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for act in p["actions"]:
        if act.get("validation"):
            json.dump(act["validation"], open(os.path.join(os.path.dirname(os.path.abspath(a.sortie)), f"validation_{act['id']}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps({"actions": len(p["actions"]), "ecritures": len(p["ecritures"]), "ignorees": len(p["ignorees"])}, ensure_ascii=False))
    return 0


def main_resultat(a):
    dem, reg = _lire(a.demande), _lire(a.registre)
    if a.version_demande:
        dem["__version"] = a.version_demande
    if reg is not None and a.version_registre:
        reg["__version"] = a.version_registre
    if not _version(dem) or (reg is not None and not _version(reg)):
        raise SystemExit("version inconnue (demande ou registre) : aucune écriture non épinglée")
    w = resultat(a.id, dem, _lire(a.etat), a.run, registre=reg, manifest=_lire(a.manifest), depots=_lire(a.depots), drive=_lire(getattr(a, "drive", None)))
    json.dump(w, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"ecritures": len(w), "etat": w[-1]["data"].get("etat")}, ensure_ascii=False))
    return 0


def main_reprise(a):
    dem = _lire(a.demande)
    if a.version_demande:
        dem["__version"] = a.version_demande
    w = reprise_stockage(a.id, dem, _lire(a.manifest), _lire(a.drive), a.zip_sha256, a.run,
                         set(x for x in a.dossiers_autorises.split(",") if x))
    json.dump([w], open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"ecritures": 1, "etat": w["data"].get("etat")}, ensure_ascii=False))
    return 0

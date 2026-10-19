"""État persistant du kit, en fichiers JSON dans un dossier choisi (par défaut ./donnees).

Trois registres SÉPARÉS, jamais confondus :
  listing.json         dernier listing : par id, champs vus dans le listing + premier_vu / dernier_vu_listing
                       (+ cls et date de la passe par classification qui l'a établi)
  couverture/<run>.json ce que chaque passage a réellement couvert (annoncé vs lu, partiel, familles)
  fiches/<org>_<ref>.json dernière lecture de fiche : champs + lu_le (date de la lecture réelle)

Règles :
  - une fiche n'est réécrite QUE par une nouvelle lecture réelle de cette fiche (lu_le = date de cette lecture) ;
    un passage de listing ne touche jamais aux fichiers fiches ;
  - aucune suppression : une consultation absente d'un listing reste dans l'état ; seul un listing
    COMPLET incrémente absences_listing_complet (indicateur, pas suppression).
"""
import datetime as dt
import gzip
import json
import os
import tempfile

from .schema import make_id

TZ_MAROC = dt.timezone(dt.timedelta(hours=1))  # Africa/Casablanca (UTC+1 hors Ramadan) — date du jour métier


def maintenant():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def aujourd_hui_maroc():
    return dt.datetime.now(TZ_MAROC).date().isoformat()


def _ecrire_json(chemin, obj):
    os.makedirs(os.path.dirname(chemin) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(chemin) or ".", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, chemin)  # écriture atomique


def _lire_json(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut


CHAMPS_LISTING = ["ref", "obj", "mo", "cat", "proc", "pub", "lim", "h", "lx", "nat", "etr", "lots", "env", "lieux_portail"]


def garder_pieces(champs, precedent):
    """Une lecture qui n'a PAS lu le bloc des pièces (section absente ou illisible) garde l'inventaire déjà validé de la
    lecture précédente, avec sa propre date (docs_lu_le). Une lecture qui l'a lu fait foi (même vide confirmé)."""
    pc = (precedent or {}).get("champs") or {}
    if "docs" in (champs.get("blocs_lus") or []) or "docs" not in (pc.get("blocs_lus") or []):
        return champs
    out = dict(champs)
    out["docs"], out["docs_preuve"] = pc.get("docs"), pc.get("docs_preuve")
    out["docs_lu_le"] = pc.get("docs_lu_le") or precedent.get("lu_le")
    out["blocs_lus"] = sorted(set(out.get("blocs_lus") or []) | {"docs"})
    return out


class Etat:
    def __init__(self, dossier):
        self.d = dossier
        os.makedirs(os.path.join(dossier, "fiches"), exist_ok=True)
        os.makedirs(os.path.join(dossier, "couverture"), exist_ok=True)
        os.makedirs(os.path.join(dossier, "snapshots"), exist_ok=True)
        self.p_listing = os.path.join(dossier, "listing.json")
        self.p_organismes = os.path.join(dossier, "organismes.json")
        self.p_selection = os.path.join(dossier, "selection.json")
        self.listing = _lire_json(self.p_listing, {"version": 1, "items": {}})
        self.selection = _lire_json(self.p_selection, {"version": 1, "items": {}})

    # ---------- journal de sélection des fiches (persiste entre passages) ----------
    def noter_tentative(self, i, quand, run_id, ok, raison=None):
        """Enregistre chaque tentative de lecture de fiche (réussie ou non). Ne touche jamais au fichier fiche."""
        s = self.selection["items"].setdefault(i, {"tentatives": 0, "echecs_consecutifs": 0})
        s["tentatives"] = s.get("tentatives", 0) + 1
        s["dernier_choix"], s["dernier_run"] = quand, run_id
        if ok:
            s["echecs_consecutifs"], s["dernier_echec"], s["raison_echec"] = 0, None, None
        else:
            s["echecs_consecutifs"] = s.get("echecs_consecutifs", 0) + 1
            s["dernier_echec"], s["raison_echec"] = quand, (raison or "")[:200]

    def sauver_selection(self):
        _ecrire_json(self.p_selection, self.selection)

    # ---------- dernier listing ----------
    def enregistrer_ligne(self, ligne, vu_le, run_id):
        i = make_id(ligne["o"], ligne["r"])
        e = self.listing["items"].get(i)
        champs = {k: ligne[k] for k in CHAMPS_LISTING}
        if e is None:
            e = {"id": i, "r": ligne["r"], "o": ligne["o"], "premier_vu": vu_le, "premier_run": run_id,
                 "cls": None, "cls_vu_le": None, "absences_listing_complet": 0}
            self.listing["items"][i] = e
        if e.get("listing") and e["listing"] != champs:
            # trace minimale des changements constatés (ex. report de date limite)
            diff = {k: [e["listing"].get(k), champs[k]] for k in CHAMPS_LISTING if e["listing"].get(k) != champs[k]}
            e.setdefault("changements", []).append({"vu_le": vu_le, "run": run_id, "diff": diff})
            e["changements"] = e["changements"][-10:]
        e["listing"] = champs
        e["dernier_vu_listing"] = vu_le
        e["dernier_run"] = run_id
        e["absences_listing_complet"] = 0
        return i

    def enregistrer_cls(self, i, cls, vu_le):
        e = self.listing["items"].get(i)
        if e is not None:
            e["cls"], e["cls_vu_le"] = cls, vu_le

    def marquer_absents_listing_complet(self, ids_vus, run_id):
        """N'est appelé QUE si la couverture du passage est complète. Ne supprime rien."""
        n = 0
        for i, e in self.listing["items"].items():
            if i not in ids_vus:
                e["absences_listing_complet"] = e.get("absences_listing_complet", 0) + 1
                e["dernier_run_absent"] = run_id
                n += 1
        return n

    def sauver_listing(self):
        _ecrire_json(self.p_listing, self.listing)

    def sauver_organismes(self, organismes, vu_le):
        _ecrire_json(self.p_organismes, {"vu_le": vu_le, "organismes": organismes})

    def organismes(self):
        return _lire_json(self.p_organismes, {"vu_le": None, "organismes": {}})

    # ---------- dernière lecture de fiche ----------
    def chemin_fiche(self, i):
        org, ref = i.split(":")[1:]
        return os.path.join(self.d, "fiches", f"{org}_{ref}.json")

    def fiche(self, i):
        return _lire_json(self.chemin_fiche(i), None)

    def enregistrer_fiche(self, i, champs, lu_le, run_id, sha256_html, lots=None):
        """Appelé uniquement après une lecture HTTP réelle et valide de la fiche. lots : lecture du popup « Détail des lots »
        (datée séparément) ; None = pas de popup lu ce passage."""
        champs = garder_pieces(champs, self.fiche(i))
        doc = {"id": i, "lu_le": lu_le, "run": run_id, "sha256_html_tronque": sha256_html, "champs": champs}
        if lots is not None:
            doc["lots"] = lots
        _ecrire_json(self.chemin_fiche(i), doc)

    # ---------- couverture ----------
    def enregistrer_couverture(self, run_id, couverture):
        _ecrire_json(os.path.join(self.d, "couverture", f"{run_id}.json"), couverture)

    def couvertures(self):
        p = os.path.join(self.d, "couverture")
        return sorted(os.listdir(p))

    # ---------- snapshots publics bruts ----------
    def snapshot(self, run_id, nom, texte):
        p = os.path.join(self.d, "snapshots", run_id)
        os.makedirs(p, exist_ok=True)
        with gzip.open(os.path.join(p, nom + ".html.gz"), "wt", encoding="utf-8") as f:
            f.write(texte)

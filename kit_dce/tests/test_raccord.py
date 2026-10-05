"""Raccord manifest -> ZIP binaire et reprise du stockage seul : hors réseau, archive FICTIVE, aucune donnée réelle."""
import base64
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(ICI)
sys.path.insert(0, KIT)
sys.path.insert(0, ICI)

import portail_fictif  # noqa: E402
from dce_kit import cycle  # noqa: E402
from dce_kit.raccord import RaccordInvalide, decoder_strict, zip_binaire  # noqa: E402
from dce_kit.tache import PHRASE, preparer  # noqa: E402


def cli(*args, cwd=None):
    p = subprocess.run([sys.executable, os.path.join(KIT, "dce_tache.py"), *args], capture_output=True, text=True, cwd=cwd, timeout=120)
    return p.returncode, p.stdout, p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.w = tempfile.mkdtemp()
        self.octets = portail_fictif.zip_fictif()
        self.sha = hashlib.sha256(self.octets).hexdigest()

    def tearDown(self):
        shutil.rmtree(self.w, ignore_errors=True)

    def manifest_relatif(self, relatif_a="manifest"):
        """Reproduit le manifest du passage r20261005171636 : fichier_local RELATIF (base64/<nom>.b64.txt)."""
        s = os.path.join(self.w, "sortie")
        m = preparer(self.octets, "38 MAT.INF 2026.zip", s)
        base = s if relatif_a == "manifest" else self.w
        for f in m["fichiers"] + [m["zip"]]:
            f["fichier_local"] = os.path.relpath(f["fichier_local"], base)
        json.dump(m, open(os.path.join(s, "manifest.json"), "w"), ensure_ascii=False)
        return os.path.join(s, "manifest.json"), m


class TestRaccord(Base):
    def test_incident_reproduit_puis_corrige(self):
        man, m = self.manifest_relatif()
        self.assertEqual(m["zip"]["fichier_local"], "base64/38 MAT.INF 2026.zip.b64.txt")
        b64 = os.path.join(self.w, "sortie", m["zip"]["fichier_local"])
        self.assertNotEqual(open(b64, "rb").read()[:4], b"PK\x03\x04", "le texte base64 n'est pas un ZIP : cause de l'ErreurIntegrite")
        out = os.path.join(self.w, "stockage", "38 MAT.INF 2026.zip")
        r = zip_binaire(man, self.w, out)
        self.assertEqual((r["etat"], r["sha256"], r["taille"]), ("ok", self.sha, len(self.octets)))
        self.assertEqual(open(out, "rb").read(), self.octets, "octets identiques à l'archive téléchargée")
        self.assertEqual(r["source"], os.path.join("sortie", "base64", "38 MAT.INF 2026.zip.b64.txt"))

    def test_relatif_a_la_racine_et_absolu(self):
        man, _ = self.manifest_relatif(relatif_a="racine")
        self.assertEqual(zip_binaire(man, self.w, os.path.join(self.w, "z1.zip"))["sha256"], self.sha)
        s2 = os.path.join(self.w, "abs")
        preparer(self.octets, "DCE.zip", s2)
        m2 = json.load(open(os.path.join(s2, "manifest.json")))
        self.assertTrue(os.path.isabs(m2["zip"]["fichier_local"]), "preparer écrit désormais des chemins absolus")
        self.assertEqual(zip_binaire(os.path.join(s2, "manifest.json"), self.w, os.path.join(self.w, "z2.zip"))["sha256"], self.sha)

    def test_preparer_sortie_relative_devient_absolue(self):
        code, out, err = cli("preparer", "--zip", self._zip(), "--sortie", "rel", cwd=self.w)
        self.assertEqual(code, 0, err)
        m = json.load(open(os.path.join(self.w, "rel", "manifest.json")))
        self.assertTrue(all(os.path.isabs(f["fichier_local"]) for f in m["fichiers"] + [m["zip"]]))

    def _zip(self):
        p = os.path.join(self.w, "x.zip")
        open(p, "wb").write(self.octets)
        return p

    def test_ambigu_refuse(self):
        man, m = self.manifest_relatif()
        doublon = os.path.join(self.w, m["zip"]["fichier_local"])
        os.makedirs(os.path.dirname(doublon))
        shutil.copy(os.path.join(self.w, "sortie", m["zip"]["fichier_local"]), doublon)
        with self.assertRaisesRegex(RaccordInvalide, "ambigu"):
            zip_binaire(man, self.w, os.path.join(self.w, "z.zip"))

    def test_hors_racine_refuse(self):
        man, m = self.manifest_relatif()
        ailleurs = tempfile.mkdtemp()
        try:
            cible = os.path.join(ailleurs, "a.b64.txt")
            shutil.copy(os.path.join(self.w, "sortie", m["zip"]["fichier_local"]), cible)
            for fl in (cible, os.path.relpath(cible, os.path.join(self.w, "sortie"))):
                m["zip"]["fichier_local"] = fl
                json.dump(m, open(man, "w"))
                with self.assertRaisesRegex(RaccordInvalide, "hors de la racine"):
                    zip_binaire(man, self.w, os.path.join(self.w, "z.zip"))
            lien = os.path.join(self.w, "sortie", "lien.b64.txt")
            os.symlink(cible, lien)
            m["zip"]["fichier_local"] = "lien.b64.txt"
            json.dump(m, open(man, "w"))
            with self.assertRaisesRegex(RaccordInvalide, "hors de la racine"):
                zip_binaire(man, self.w, os.path.join(self.w, "z.zip"))
            man2, _ = self.manifest_relatif()
            with self.assertRaisesRegex(RaccordInvalide, "sortie hors"):
                zip_binaire(man2, self.w, os.path.join(ailleurs, "z.zip"))
            self.assertFalse(os.path.exists(os.path.join(ailleurs, "z.zip")))
        finally:
            shutil.rmtree(ailleurs)

    def test_sortie_hors_racine_aucun_repertoire_cree(self):
        man, _ = self.manifest_relatif()
        ailleurs = tempfile.mkdtemp()
        try:
            cas = [os.path.join(ailleurs, "neuf", "sous", "z.zip"),                      # parent inexistant hors racine
                   os.path.join(self.w, "..", os.path.basename(ailleurs), "n2", "z.zip"),  # « .. » depuis la racine
                   os.path.join(self.w, "lien", "n3", "z.zip")]                          # lien sous la racine vers l'extérieur
            os.symlink(ailleurs, os.path.join(self.w, "lien"))
            for out in cas:
                with self.subTest(out=out), self.assertRaisesRegex(RaccordInvalide, "sortie hors"):
                    zip_binaire(man, self.w, out)
            self.assertEqual(os.listdir(ailleurs), [], "aucun répertoire créé hors de la racine")
            code, o, _ = cli("zip-binaire", "--manifest", man, "--racine", self.w, "--sortie", cas[0])
            self.assertEqual((code, json.loads(o)["code"]), (2, "raccord"))
            self.assertEqual(os.listdir(ailleurs), [])
            r = zip_binaire(man, self.w, os.path.join(self.w, "a", "b", "z.zip"))   # parent inexistant SOUS la racine : créé
            self.assertEqual(r["sha256"], self.sha)
        finally:
            shutil.rmtree(ailleurs)

    def test_decodage_strict(self):
        bon = base64.b64encode(self.octets)
        self.assertEqual(decoder_strict(bon + b"\n", 10**9), self.octets)
        for mauvais in (bon[:40] + b"\n" + bon[40:], bon[:-4] + b"!!!!", bon[:-1], "é".encode() + bon, bon.replace(b"+", b"-")):
            if mauvais == bon:
                continue
            with self.assertRaises(RaccordInvalide):
                decoder_strict(mauvais, 10**9)
        with self.assertRaisesRegex(RaccordInvalide, "non canonique"):
            decoder_strict(b"QR==", 10)   # « A » encodé avec des bits de remplissage non nuls
        with self.assertRaisesRegex(RaccordInvalide, "taille"):
            decoder_strict(bon, 100)

    def test_sha_taille_archive_verifies_avant_ecriture(self):
        man, m = self.manifest_relatif()
        out = os.path.join(self.w, "z.zip")
        for champ, val, motif in (("sha256", "0" * 64, "SHA-256"), ("taille", len(self.octets) + 1, "taille"), ("depot", "pdf", "dépôt")):
            m2 = json.loads(json.dumps(m))
            m2["zip"][champ] = val
            json.dump(m2, open(man, "w"))
            with self.assertRaisesRegex(RaccordInvalide, motif):
                zip_binaire(man, self.w, out)
            self.assertFalse(os.path.exists(out), "rien n'est écrit avant vérification")
        faux = b"PK\x03\x04 pas une archive"
        open(os.path.join(self.w, "sortie", m["zip"]["fichier_local"]), "wb").write(base64.b64encode(faux))
        m["zip"].update(sha256=hashlib.sha256(faux).hexdigest(), taille=len(faux))
        json.dump(m, open(man, "w"))
        with self.assertRaisesRegex(RaccordInvalide, "archive invalide"):
            zip_binaire(man, self.w, out)
        self.assertFalse(os.path.exists(out))

    def test_jamais_d_ecrasement(self):
        man, _ = self.manifest_relatif()
        out = os.path.join(self.w, "z.zip")
        zip_binaire(man, self.w, out)
        self.assertEqual(zip_binaire(man, self.w, out)["etat"], "ok", "idempotent sur le même contenu")
        open(out, "wb").write(b"autre")
        with self.assertRaisesRegex(RaccordInvalide, "rien n'est écrasé"):
            zip_binaire(man, self.w, out)
        self.assertEqual(open(out, "rb").read(), b"autre")

    def test_cli(self):
        man, _ = self.manifest_relatif()
        code, out, err = cli("zip-binaire", "--manifest", man, "--racine", self.w, "--sortie", os.path.join(self.w, "s", "a.zip"))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["sha256"], self.sha)
        code, out, _ = cli("zip-binaire", "--manifest", man, "--racine", os.path.join(self.w, "sortie", "base64"), "--sortie", os.path.join(self.w, "b.zip"))
        self.assertEqual((code, json.loads(out)["code"]), (2, "raccord"))


T0 = datetime.datetime(2026, 10, 5, 17, 40, tzinfo=datetime.timezone.utc)


class TestReprise(Base):
    def setUp(self):
        super().setUp()
        self.man = preparer(self.octets, "38 MAT.INF 2026.zip", os.path.join(self.w, "sortie"))
        self.err = {"code": "stockage", "motif": "ErreurIntegrite: archive ZIP illisible", "le": "2026-10-05T17:30:00Z"}
        self.val = {"phrase": PHRASE, "empreinte": "e" * 64, "par": "humain", "le": "2026-10-05T17:16:00Z"}
        self.dem = {"ao_id": "fx-1", "ref": "1", "org": "O", "etat": "echec", "tache": None, "erreur": self.err, "validation": self.val,
                    "cg": {"empreinte": "e" * 64, "algo": "cg-v3"}, "__version": 21}
        f = self.man["fichiers"] + [self.man["zip"]]
        self.drive = {"ref": "fx-1", "statut": "verifie", "maj": "2026-10-05T17:39:00Z", "archive": {"sha256": self.sha},
                      "fichiers": [{"sha256": x["sha256"], "taille": x["taille"]} for x in f]}

    def rep(self, **k):
        a = dict(did="fx-1", demande=self.dem, manifest=self.man, drive=self.drive, zip_sha256_attendu=self.sha, run="rrep", dossiers_autorises={"fx-1"}, maintenant=T0)
        a.update(k)
        return cycle.reprise_stockage(**a)

    def test_resultat_exige_le_bail_courant(self):
        with self.assertRaisesRegex(ValueError, "pas tenue par ce passage"):
            cycle.resultat("fx-1", self.dem, {"etat": "pret"}, "r20261005171636", manifest=self.man, drive=self.drive, maintenant=T0)

    def test_reprise_pret_epinglee_sans_toucher_consentement(self):
        w = self.rep()
        self.assertEqual((w["op"], w["collection"], w["if_version"], w["data"]["etat"]), ("update", "dce_demande", 21, "pret"))
        self.assertNotIn("validation", w["data"])
        self.assertNotIn("cg", w["data"])
        r = w["data"]["resultat"]
        self.assertEqual((r["stockage"], r["zip_sha256"], r["reprise"]["echec_precedent"]), ("drive", self.sha, self.err))
        self.assertEqual(r["reprise"]["zip_sha256"], self.sha)

    def test_refus(self):
        cas = [(dict(demande={**self.dem, "etat": "pret"}), "pas en échec de stockage"),
               (dict(demande={**self.dem, "erreur": {**self.err, "code": "cg_modifiees"}}), "pas en échec de stockage"),
               (dict(demande={**self.dem, "tache": {"run": "x", "jusqu": "2026-10-05T18:00:00Z"}}), "tenue par"),
               (dict(demande={k: v for k, v in self.dem.items() if k != "__version"}), "version"),
               (dict(dossiers_autorises=set()), "non autorisé"),
               (dict(zip_sha256_attendu="0" * 64), "archive du téléchargement"),
               (dict(zip_sha256_attendu=None), "archive du téléchargement"),
               (dict(drive={**self.drive, "ref": "autre"}), "autre consultation"),
               (dict(drive={**self.drive, "archive": {"sha256": "1" * 64}}), "rangée dans Drive")]
        for k, motif in cas:
            with self.subTest(motif=motif), self.assertRaisesRegex(ValueError, motif):
                self.rep(**k)

    def test_cli(self):
        d = {n: os.path.join(self.w, n + ".json") for n in ("dem", "man", "drv")}
        for n, v in (("dem", {k: x for k, x in self.dem.items() if k != "__version"}), ("man", self.man), ("drv", self.drive)):
            json.dump(v, open(d[n], "w"))
        out = os.path.join(self.w, "ecr.json")
        code, o, err = cli("reprise-stockage", "--id", "fx-1", "--demande", d["dem"], "--version-demande", "21", "--manifest", d["man"], "--drive", d["drv"],
                           "--zip-sha256", self.sha, "--run", "rrep", "--dossiers-autorises", "fx-1", "--sortie", out)
        self.assertEqual(code, 0, err)
        w = json.load(open(out))
        self.assertEqual((len(w), w[0]["if_version"], w[0]["data"]["etat"]), (1, 21, "pret"))

    def test_drive_incomplet_reste_echec(self):
        w = self.rep(drive={**self.drive, "fichiers": self.drive["fichiers"][:-1]})
        self.assertEqual((w["data"]["etat"], w["data"]["erreur"]["code"], w["if_version"]), ("echec", "stockage", 21))


if __name__ == "__main__":
    unittest.main()

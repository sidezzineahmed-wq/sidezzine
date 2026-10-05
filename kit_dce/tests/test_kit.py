"""Tests hors réseau du kit DCE : portail FICTIF local, identité FICTIVE, Chromium réel. Aucun accès au portail réel."""
import base64
import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(ICI)
sys.path.insert(0, KIT)
sys.path.insert(0, ICI)

import portail_fictif  # noqa: E402
from dce_kit.config import Config, ConfigInvalide  # noqa: E402
from dce_kit.tache import PHRASE  # noqa: E402

ENV_FICTIF = {"DCE_NOM": "Fictif", "DCE_PRENOM": "Testeur", "DCE_EMAIL": "test@exemple.invalid"}


def cli(*args, env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("DCE_")}
    e.update(env or {})
    p = subprocess.run([sys.executable, os.path.join(KIT, "dce_tache.py"), *args], capture_output=True, text=True, env=e, timeout=300)
    return p.returncode, p.stdout, p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()


class TestConfig(Base):
    def test_defaut_sans_identite_pour_ouvrir(self):
        c = Config.charger(None, env={}, identite_requise=False)
        self.assertEqual((c.delai_debut_telechargement_s, c.delai_fin_transfert_s), (300, 900))
        with self.assertRaises(ConfigInvalide):
            Config.charger(None, env={})

    def test_cles(self):
        p = os.path.join(self.d, "c.json")
        json.dump({"_note": "commentaire", "delai_page_s": 60}, open(p, "w"))
        self.assertEqual(Config.charger(p, env=ENV_FICTIF).delai_page_s, 60)
        json.dump({"identite": {"nom": "x"}}, open(p, "w"))
        with self.assertRaisesRegex(ConfigInvalide, "inconnues : identite"):
            Config.charger(p, env=ENV_FICTIF)
        json.dump({"delai_debut_telechargement_s": 30}, open(p, "w"))
        with self.assertRaisesRegex(ConfigInvalide, "trop courts"):
            Config.charger(p, env=ENV_FICTIF)


class TestPreparer(Base):
    def test_archive_fictive(self):
        z = os.path.join(self.d, "DCE_fictif.zip")
        octets = portail_fictif.zip_fictif()
        open(z, "wb").write(octets)
        code, out, err = cli("preparer", "--zip", z, "--sortie", os.path.join(self.d, "o"))
        self.assertEqual(code, 0, err)
        m = json.load(open(os.path.join(self.d, "o", "manifest.json")))
        self.assertEqual(m["zip"]["sha256"], hashlib.sha256(octets).hexdigest(), "SHA des octets préparés, pas d'une archive régénérée")
        self.assertEqual(sorted((f["nom"], f["depot"]) for f in m["fichiers"]),
                         [("AVIS EN FR.pdf", "pdf"), ("BPDE.docx", "texte_base64"), ("CPS.pdf", "pdf"), ("RC.pdf", "pdf")])
        for f in m["fichiers"] + [m["zip"]]:
            d = open(f["fichier_local"], "rb").read()
            if f["depot"] == "texte_base64":
                d = base64.b64decode(d)
            self.assertEqual(hashlib.sha256(d).hexdigest(), f["sha256"])

    def test_archive_corrompue(self):
        z = os.path.join(self.d, "x.zip")
        open(z, "wb").write(b"PK\x03\x04 pas une archive")
        code, out, _ = cli("preparer", "--zip", z, "--sortie", os.path.join(self.d, "o"))
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["code"], "ZipInvalide")


class TestEnvironnement(unittest.TestCase):
    def test_chromium_lancable(self):
        code, out, err = cli("verifier-env")
        self.assertEqual(code, 0, err[-800:])
        self.assertEqual(json.loads(out)["etat"], "ok")


class TestPortailFictif(Base):
    def setUp(self):
        super().setUp()
        self.srv, self.etat = portail_fictif.demarrer()
        self.cfg = os.path.join(self.d, "config.json")
        json.dump({"_note": "portail FICTIF local", "base_url": f"http://127.0.0.1:{self.srv.server_address[1]}/index.php",
                   "hote_autorise": "127.0.0.1"}, open(self.cfg, "w"))

    def tearDown(self):
        self.srv.shutdown()

    def ouvrir(self, ref, **kw):
        e = os.path.join(self.d, f"etat_{ref}.json")
        code, out, err = cli("ouvrir", "--ref", ref, "--org", "orgfictif", "--config", self.cfg, "--etat", e, **kw)
        return code, json.load(open(e)), err

    def validation(self, empreinte, ref="R-FICTIF-1", phrase=PHRASE, age_h=0):
        p = os.path.join(self.d, "validation.json")
        le = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=age_h)).strftime("%Y-%m-%dT%H:%M:%SZ")
        json.dump({"ref": ref, "org": "orgfictif", "empreinte": empreinte, "phrase": phrase, "par": "testeur", "le": le}, open(p, "w"))
        return p

    def telecharger(self, val, ref="R-FICTIF-1"):
        e = os.path.join(self.d, "etat_dl.json")
        code, out, err = cli("telecharger", "--ref", ref, "--org", "orgfictif", "--config", self.cfg, "--etat", e, "--validation", val,
                             "--sortie", os.path.join(self.d, "sortie"), env=ENV_FICTIF)
        return code, json.load(open(e)), err

    def test_ouvrir_ne_soumet_rien(self):
        code, e, err = self.ouvrir("R-FICTIF-1")
        self.assertEqual((code, e["etat"]), (0, "attente_validation_CG"), err[-800:])
        self.assertIn("contenu binaire complet du document lié", e["cg"]["portee"])
        self.assertEqual((self.etat.soumis, self.etat.telechargements), ([], []))

    def test_403_arret(self):
        code, e, _ = self.ouvrir("R403")
        self.assertEqual((code, e["etat"], e["code"]), (2, "echec", "http_403"))
        self.assertEqual(len([v for v in self.etat.vues if "R403" in v]), 1, "une seule requête, aucune nouvelle tentative")

    def test_captcha_arret(self):
        code, e, _ = self.ouvrir("RCAP")
        self.assertEqual((code, e["code"]), (2, "controle"))

    def test_sans_validation_humaine_rien_ne_part(self):
        _, e, _ = self.ouvrir("R-FICTIF-1")
        n = len(self.etat.vues)
        for val in (self.validation(e["cg"]["empreinte"], phrase="ok"), self.validation(e["cg"]["empreinte"], age_h=30),
                    self.validation(e["cg"]["empreinte"], ref="AUTRE")):
            code, r, _ = self.telecharger(val)
            self.assertEqual((code, r["code"]), (2, "validation"))
        self.assertEqual(len(self.etat.vues), n, "aucune requête au portail sans validation humaine valable")
        self.assertEqual(self.etat.soumis, [])

    def test_zip_regenere_meme_contenu_autres_octets(self):
        """Cause de l'échec intermittent corrigé : l'archive porte l'heure de sa création (2 s). Deux générations à cheval sur
        une frontière de 2 s diffèrent en octets, pas en contenu."""
        a, b = portail_fictif.zip_fictif((2026, 1, 1, 0, 0, 0)), portail_fictif.zip_fictif((2026, 1, 1, 0, 0, 2))
        self.assertNotEqual(hashlib.sha256(a).hexdigest(), hashlib.sha256(b).hexdigest())
        self.assertEqual(portail_fictif.zip_fictif((2026, 1, 1, 0, 0, 0)), a, "date fixe : octets reproductibles")
        import io
        import zipfile
        contenu = lambda x: {i.filename: zipfile.ZipFile(io.BytesIO(x)).read(i) for i in zipfile.ZipFile(io.BytesIO(x)).infolist()}
        self.assertEqual(contenu(a), contenu(b))

    def test_chaine_complete_apres_validation(self):
        self.etat.zip_date = (2020, 1, 1, 0, 0, 0)  # déterministe : une archive régénérée maintenant aurait d'autres octets
        _, e, _ = self.ouvrir("R-FICTIF-1")
        code, r, err = self.telecharger(self.validation(e["cg"]["empreinte"]))
        self.assertEqual((code, r["etat"]), (0, "pret"), err[-800:])
        self.assertEqual(self.etat.soumis, [{"ref": "R-FICTIF-1", "nom": "Fictif", "prenom": "Testeur", "mail": "test@exemple.invalid", "cgu": "on"}])
        self.assertEqual(len(self.etat.zips_servis), 1, "une seule archive servie")
        self.assertEqual(r["zip_sha256"], hashlib.sha256(self.etat.zips_servis[0]).hexdigest(), "SHA de l'archive réellement servie")
        self.assertNotEqual(r["zip_sha256"], hashlib.sha256(portail_fictif.zip_fictif()).hexdigest(), "une archive régénérée diffère : ne jamais comparer à elle")
        self.assertEqual(len(json.load(open(r["manifest"]))["fichiers"]), 4)

    def test_cg_modifiees_nouvelle_validation(self):
        _, e, _ = self.ouvrir("R-FICTIF-1")
        self.etat.cg_doc = b"%PDF-1.4 Conditions generales fictives v2 %%EOF"
        code, r, _ = self.telecharger(self.validation(e["cg"]["empreinte"]))
        self.assertEqual((code, r["code"]), (2, "cg_modifiees"))
        self.assertEqual(self.etat.soumis, [])


if __name__ == "__main__":
    unittest.main()

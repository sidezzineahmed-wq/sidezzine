"""Confiance TLS du navigateur (mode proxy_ccr) — HORS RÉSEAU, aucun magasin NSS réel : certutil et Playwright sont simulés."""
import asyncio
import hashlib
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dce_kit import confiance  # noqa: E402
from dce_kit.config import Config, ConfigInvalide, Identite  # noqa: E402
from dce_kit.navigateur import NavigateurPlaywright, Refus  # noqa: E402

ICI = os.path.dirname(os.path.abspath(__file__))
PEM = b"-----BEGIN CERTIFICATE-----\nFICTIF\n-----END CERTIFICATE-----\n"
README = "TLS is re-terminated there ... /root/.ccr/agent-proxy-ca.crt (the proxy CA)"


def ok_run(appels):
    def run(args, **kw):
        appels.append(args)
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")
    return run


class Base(unittest.TestCase):
    def setUp(self):
        self.racine = tempfile.mkdtemp(prefix="racine_", dir=ICI)
        p = mock.patch.object(confiance, "INTERDITS", ("/racine-interdite-de-test",))  # le dépôt de test peut être sous /tmp
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(shutil.rmtree, self.racine, True)
        d = os.path.join(self.racine, "ccr")
        os.makedirs(d)
        self.ca, self.sys_, self.readme = (os.path.join(d, n) for n in ("agent-proxy-ca.crt", "system-trust.ca.pem", "README.md"))
        open(self.ca, "wb").write(PEM)
        open(self.sys_, "wb").write(PEM)
        open(self.readme, "w").write(README)
        self.sha = hashlib.sha256(PEM).hexdigest()

    def verifier(self, **kw):
        return confiance.verifier_ca(self.ca, self.sys_, self.readme, kw.get("sha", self.sha))

    def magasins(self):
        return [n for n in os.listdir(self.racine) if n.startswith("nss_")]


class TestVerification(Base):
    def test_ca_officielle_acceptee(self):
        self.assertEqual(self.verifier(), self.ca)

    def test_valeur_revue_reelle_figee(self):
        self.assertEqual(confiance.SHA_REVUE, "70f9315129c67bf82e0a0dadc984adee41331f6b67096f653bb34479e0c0080b")
        self.assertEqual((confiance.CA_OFFICIELLE, confiance.CA_SYSTEME), ("/root/.ccr/agent-proxy-ca.crt", "/root/.ccr/system-trust.ca.pem"))

    def test_pem_inattendu_refuse(self):
        open(self.ca, "wb").write(PEM.replace(b"FICTIF", b"AUTRE"))
        with self.assertRaisesRegex(confiance.ErreurConfiance, "diffère de la confiance système"):
            self.verifier()

    def test_rotation_empreinte_differente_arret(self):
        with self.assertRaisesRegex(confiance.ErreurConfiance, "nouvelle revue requise"):
            self.verifier(sha="0" * 64)

    def test_readme_sans_preuve_refuse(self):
        open(self.readme, "w").write("rien")
        with self.assertRaisesRegex(confiance.ErreurConfiance, "README"):
            self.verifier()

    def test_config_refuse_mode_ou_pem_arbitraire(self):
        with self.assertRaises(ConfigInvalide):
            Config.charger(None, env={"DCE_CONFIANCE_NAVIGATEUR": "/chemin/autre.pem"}, identite_requise=False)
        c = Config.charger(None, env={"DCE_CONFIANCE_NAVIGATEUR": "proxy_ccr", "DCE_RACINE_TRAVAIL": self.racine}, identite_requise=False)
        self.assertEqual((c.confiance_navigateur, c.racine_travail), ("proxy_ccr", self.racine))


class TestMagasin(Base):
    def test_magasin_sous_racine_seule_autorite(self):
        appels = []
        home = confiance.preparer_magasin(self.racine, self.ca, ok_run(appels), certutil="certutil")
        self.assertTrue(os.path.realpath(home).startswith(os.path.realpath(self.racine) + os.sep))
        self.assertEqual([a[1] for a in appels], ["-N", "-A"])
        self.assertIn(["-t", "C,,"], [a[i:i + 2] for a in appels for i in range(len(a))])
        self.assertEqual(sum(1 for a in appels if "-i" in a), 1, "une seule autorité importée")
        confiance.nettoyer(home)
        self.assertEqual(self.magasins(), [])

    def test_tmp_refuse(self):
        with mock.patch.object(confiance, "INTERDITS", ("/tmp",)):
            for r in ("/tmp", tempfile.mkdtemp(dir="/tmp")):
                with self.assertRaisesRegex(confiance.ErreurConfiance, "/tmp"):
                    confiance.preparer_magasin(r, self.ca, ok_run([]), certutil="certutil")

    def test_racine_vide_ou_absente_refusee(self):
        for r in ("", None, os.path.join(self.racine, "absente")):
            with self.assertRaisesRegex(confiance.ErreurConfiance, "racine de travail absente"):
                confiance.preparer_magasin(r, self.ca, ok_run([]), certutil="certutil")

    def test_certutil_absent(self):
        with mock.patch("shutil.which", return_value=None), self.assertRaisesRegex(confiance.ErreurConfiance, "certutil"):
            confiance.preparer_magasin(self.racine, self.ca, ok_run([]))
        self.assertEqual(self.magasins(), [])

    def test_echec_certutil_nettoie_sans_exposer_stderr(self):
        def ko(args, **kw):
            return types.SimpleNamespace(returncode=255, stdout="", stderr="SECRET-INTERNE chemin /root/x")
        with self.assertRaises(confiance.ErreurConfiance) as e:
            confiance.preparer_magasin(self.racine, self.ca, ko, certutil="certutil")
        self.assertNotIn("SECRET-INTERNE", str(e.exception))
        self.assertIn("code 255", str(e.exception))
        self.assertEqual(self.magasins(), [], "magasin supprimé après échec")


class FauxPW:
    def __init__(self, echec_launch=False, echec_close=False):
        self.kw, self.stoppe, P = None, False, self

        class B:
            async def close(self):
                if echec_close:
                    raise RuntimeError("fermeture impossible")

        class Ch:
            async def launch(self, **kw):
                P.kw = kw
                if echec_launch:
                    raise RuntimeError("lancement impossible")
                return B()
        self.chromium = Ch()

    async def stop(self):
        self.stoppe = True


class TestNavigateur(Base):
    def lancer(self, pw):
        c = Config(identite=Identite("", "", ""), confiance_navigateur="proxy_ccr", racine_travail=self.racine)
        n = NavigateurPlaywright(c)
        fabrique = types.SimpleNamespace(start=mock.AsyncMock(return_value=pw))
        with mock.patch("playwright.async_api.async_playwright", return_value=fabrique), \
                mock.patch.object(confiance, "verifier_ca", return_value=self.ca), \
                mock.patch.object(confiance, "preparer_magasin", side_effect=lambda r, ca: confiance.__dict__["_vrai_preparer"](r, ca, ok_run([]), certutil="certutil")):
            asyncio.run(n._demarrer())
        return n

    @classmethod
    def setUpClass(cls):
        confiance._vrai_preparer = confiance.preparer_magasin

    def test_tls_reste_active_et_home_isole(self):
        pw = FauxPW()
        n = self.lancer(pw)
        self.assertEqual(set(pw.kw) - {"env"}, {"headless"}, "aucune option d'ignorance d'erreur TLS")
        self.assertNotIn("ignore_https_errors", pw.kw)
        self.assertFalse(any("ignore-certificate" in str(a) for a in pw.kw.get("args", [])))
        self.assertTrue(pw.kw["env"]["HOME"].startswith(os.path.realpath(self.racine)))
        self.assertEqual(len(self.magasins()), 1)
        asyncio.run(n.fermer())
        self.assertEqual(self.magasins(), [], "magasin supprimé à la fermeture")

    def test_echec_lancement_nettoie(self):
        with self.assertRaisesRegex(RuntimeError, "lancement"):
            self.lancer(FauxPW(echec_launch=True))
        self.assertEqual(self.magasins(), [])

    def test_echec_fermeture_nettoie(self):
        pw = FauxPW(echec_close=True)
        n = self.lancer(pw)
        with self.assertRaisesRegex(RuntimeError, "fermeture"):
            asyncio.run(n.fermer())
        self.assertTrue(pw.stoppe)
        self.assertEqual(self.magasins(), [])

    def test_ca_refusee_aucun_lancement(self):
        c = Config(identite=Identite("", "", ""), confiance_navigateur="proxy_ccr", racine_travail=self.racine)
        n = NavigateurPlaywright(c)
        with mock.patch.object(confiance, "verifier_ca", side_effect=confiance.ErreurConfiance("rotation")), \
                mock.patch("playwright.async_api.async_playwright") as ap:
            with self.assertRaises(Refus):
                asyncio.run(n._demarrer())
            ap.assert_not_called()
        self.assertEqual(self.magasins(), [])

    def test_mode_par_defaut_inchange(self):
        pw = FauxPW()
        n = NavigateurPlaywright(Config(identite=Identite("", "", "")))
        fabrique = types.SimpleNamespace(start=mock.AsyncMock(return_value=pw))
        with mock.patch("playwright.async_api.async_playwright", return_value=fabrique):
            asyncio.run(n._demarrer())
        self.assertEqual(pw.kw, {"headless": True})
        asyncio.run(n.fermer())


if __name__ == "__main__":
    unittest.main()

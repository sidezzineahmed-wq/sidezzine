"""Tests ciblés de l'adaptateur Drive : HTTP SIMULÉ local (faux_google), identifiants FICTIFS, aucun accès réseau réel."""
import hashlib
import io
import json
import logging
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
sys.path.insert(0, ICI)

import faux_google  # noqa: E402
from drive_adapter import Drive, ErreurAuth, ErreurConfig, ErreurIntegrite, sha256_fichier  # noqa: E402

ENV = {"DCE_GDRIVE_CLIENT_ID": "client-fictif.apps.example", "DCE_GDRIVE_CLIENT_SECRET": "SECRET-FICTIF-123", "DCE_GDRIVE_REFRESH_TOKEN": "refresh-fictif-456"}
MO = 1024 * 1024
INTERDITS = ("tok-", "SESSIONSECRET", "SECRET-FICTIF-123", "refresh-fictif-456", "refresh-invalide")


class Arret(Exception):
    """Simule l'arrêt brutal du processus au milieu d'un envoi."""


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.srv, self.et, self.urls = faux_google.demarrer()
        self.f = os.path.join(self.d, "DCE_fictif.bin")
        with open(self.f, "wb") as x:
            x.write(os.urandom(6 * MO + 123))  # > 5 Mo, taille non multiple de 256 Kio
        self.sha = sha256_fichier(self.f)
        self.flux = io.StringIO()
        self.h = logging.StreamHandler(self.flux)
        logging.getLogger("drive_adapter").addHandler(self.h)
        logging.getLogger("drive_adapter").setLevel(logging.DEBUG)
        self.messages = []

    def tearDown(self):
        logging.getLogger("drive_adapter").removeHandler(self.h)
        self.srv.shutdown()
        self.srv.server_close()
        texte = self.flux.getvalue() + "\n".join(self.messages)
        for x in INTERDITS:
            self.assertNotIn(x, texte, f"fuite dans les journaux ou messages : {x}")

    def octets(self):
        with open(self.f, "rb") as x:
            return x.read()

    def drive(self, env=ENV, **k):
        return Drive(env=env, urls=self.urls, morceau=MO, pause_s=0, tests_locaux=True, **k)

    def attendre_erreur(self, typ, fn):
        with self.assertRaises(typ) as e:
            fn()
        self.messages.append(str(e.exception))
        return str(e.exception)


class TestEnvoiRecuperation(Base):
    def test_aller_retour_6_mo(self):
        r = self.drive().envoyer(self.f, "DCE_fictif.bin")
        self.assertEqual((r["taille"], r["sha256"]), (6 * MO + 123, self.sha))
        self.assertGreaterEqual(self.et.puts, 7, "envoi par morceaux de 1 Mio")
        self.assertEqual(self.et.fichiers[r["id"]], self.octets())
        sortie = os.path.join(self.d, "relu.bin")
        g = self.drive().recuperer(r["id"], sortie, self.sha, 6 * MO + 123)
        self.assertEqual((g["sha256"], sha256_fichier(sortie)), (self.sha, self.sha))
        self.assertEqual({h for _, h in self.et.requetes} - {"/token", "/upload"} - {f"/files/{r['id']}"}, set(), "aucune autre requête")

    def test_coupure_reseau_reprise_sans_tout_renvoyer(self):
        self.et.couper_morceaux = {2, 4}
        r = self.drive().envoyer(self.f, "DCE_fictif.bin")
        self.assertEqual(self.et.fichiers[r["id"]], self.octets())
        self.assertLessEqual(self.et.octets_recus, os.path.getsize(self.f), "seuls les octets manquants sont renvoyés")

    def test_reprise_apres_arret_du_processus(self):
        etat = os.path.join(self.d, "envoi.etat")

        def arret(offset):
            if offset >= 3 * MO:
                raise Arret()
        with self.assertRaises(Arret):
            self.drive().envoyer(self.f, "DCE_fictif.bin", etat=etat, apres_morceau=arret)
        self.assertEqual(stat.S_IMODE(os.stat(etat).st_mode), 0o600, "fichier d'état lisible par son seul propriétaire")
        avant = self.et.octets_recus
        r = self.drive().envoyer(self.f, "DCE_fictif.bin", etat=etat)  # nouveau processus, même fichier d'état
        self.assertEqual(self.et.fichiers[r["id"]], self.octets())
        self.assertEqual(len(self.et.sessions), 1, "même session reprise, pas de nouvel envoi")
        self.assertLessEqual(self.et.octets_recus - avant, os.path.getsize(self.f) - 3 * MO)
        self.assertFalse(os.path.exists(etat), "état effacé après succès")

    def test_etat_d_un_autre_fichier_refuse(self):
        etat = os.path.join(self.d, "envoi.etat")
        with open(etat, "w") as x:
            json.dump({"session": "x", "chemin": "/autre", "taille": 1, "sha256": "0"}, x)
        self.attendre_erreur(Exception, lambda: self.drive().envoyer(self.f, "x", etat=etat))


class TestAuthentification(Base):
    def test_refresh_invalide_erreur_explicite_rien_envoye(self):
        msg = self.attendre_erreur(ErreurAuth, lambda: self.drive(env={**ENV, "DCE_GDRIVE_REFRESH_TOKEN": "refresh-invalide"}).envoyer(self.f, "x"))
        self.assertIn("DCE_GDRIVE_REFRESH_TOKEN", msg)
        self.assertEqual((self.et.sessions, self.et.puts), ({}, 0))

    def test_jeton_expire_renouvele_une_fois(self):
        self.et.expirer_premier = True
        r = self.drive().envoyer(self.f, "DCE_fictif.bin")
        self.assertEqual(self.et.fichiers[r["id"]], self.octets())
        self.assertEqual(self.et.emis, 2)

    def test_acces_interdit(self):
        self.attendre_erreur(ErreurAuth, lambda: self.drive().recuperer("1FxINTERDIT0000", os.path.join(self.d, "x"), "0" * 64))

    def test_configuration_absente_ou_non_https(self):
        msg = self.attendre_erreur(ErreurConfig, lambda: Drive(env={}))
        self.assertTrue(all(v in msg for v in ENV))
        self.attendre_erreur(ErreurConfig, lambda: Drive(env=ENV, urls=self.urls))  # http refusé hors mode test local
        self.attendre_erreur(ErreurConfig, lambda: Drive(env=ENV, urls={"jeton": "http://exemple.invalid/token"}, tests_locaux=True))


class TestModeProxy(Base):
    def test_aucun_identifiant_envoye_et_401_explicite(self):
        d = Drive(env={}, urls=self.urls, morceau=MO, pause_s=0, tests_locaux=True, auth="proxy")
        msg = self.attendre_erreur(ErreurAuth, lambda: d.envoyer(self.f, "x"))
        self.assertIn("proxy", msg)
        self.assertEqual((self.et.emis, self.et.sessions), (0, {}), "aucun appel au point de jeton, aucune session")


class TestIntegrite(Base):
    def test_fichier_corrompu_refuse_et_supprime(self):
        r = self.drive().envoyer(self.f, "DCE_fictif.bin")
        self.et.corrompre = True
        sortie = os.path.join(self.d, "relu.bin")
        self.attendre_erreur(ErreurIntegrite, lambda: self.drive().recuperer(r["id"], sortie, self.sha))
        self.assertFalse(os.path.exists(sortie) or os.path.exists(sortie + ".partiel"))

    def test_empreinte_attendue_fausse(self):
        r = self.drive().envoyer(self.f, "DCE_fictif.bin")
        self.attendre_erreur(ErreurIntegrite, lambda: self.drive().recuperer(r["id"], os.path.join(self.d, "y"), "0" * 64))


class TestJournaux(Base):
    def test_masquage(self):
        logging.getLogger("drive_adapter").warning("Authorization: Bearer tok-99 upload_id=SESSIONSECRETabc refresh_token=refresh-fictif-456")
        self.assertIn("[masqué]", self.flux.getvalue())

    def test_cli_verifier_config_sans_valeurs(self):
        out = subprocess.run([sys.executable, "-m", "drive_adapter", "verifier-config"], cwd=os.path.dirname(ICI), env={**{k: v for k, v in os.environ.items() if k != "DCE_GDRIVE_AUTH"}, **ENV}, capture_output=True, text=True)
        self.messages.append(out.stdout + out.stderr)
        self.assertEqual(json.loads(out.stdout)["etat"], "ok")
        out = subprocess.run([sys.executable, "-m", "drive_adapter", "verifier-config"], cwd=os.path.dirname(ICI), env={k: v for k, v in os.environ.items() if not k.startswith("DCE_")}, capture_output=True, text=True)
        self.assertEqual((out.returncode, json.loads(out.stdout)["etat"]), (2, "incomplet"))


if __name__ == "__main__":
    unittest.main()

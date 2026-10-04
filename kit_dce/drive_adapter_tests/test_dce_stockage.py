"""Stockage DCE (dossier, ZIP + documents, manifeste horodaté, vérification, reprise) : faux serveur Google LOCAL, proxy
« Body parameter » SIMULÉ, archive FICTIVE construite ici. Aucun réseau réel, aucune donnée réelle."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
sys.path.insert(0, ICI)

import faux_google  # noqa: E402
from test_proxy_oauth import COFFRE, Horloge, ProxySimule  # noqa: E402
from drive_adapter import Drive, ErreurDrive, ErreurIntegrite  # noqa: E402
from drive_adapter.dce_stockage import StockageDCE, slug  # noqa: E402

ENTREES = {"DCE/RC.pdf": b"%PDF-1.4 fictif RC\n" * 300, "DCE/CPS.pdf": os.urandom(700_000),
           "DCE/BPDE.docx": b"PK fictif docx" * 50, "DCE/annexes/إعلان عربي طويل جدا لاختبار الاقتطاع.pdf": b"%PDF fictif ar" * 40}


def faire_zip(chemin, entrees=ENTREES):
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("DCE/", b"")
        for n, b in entrees.items():
            z.writestr(n, b)


class Coupure(Exception):
    pass


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.srv, self.et, self.urls = faux_google.demarrer()
        self.zip = os.path.join(self.d, "DCE-fictif-0001.zip")
        faire_zip(self.zip)
        self.h = Horloge()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.d, ignore_errors=True)

    def drive(self):
        self.proxy = ProxySimule(self.urls["jeton"])
        return Drive(env={}, urls=self.urls, morceau=256 * 1024, pause_s=0, tests_locaux=True, ouvrir=self.proxy, auth="proxy_oauth", horloge=self.h)

    def sto(self):
        return StockageDCE(self.drive(), horloge=self.h)

    def manifeste_drive(self, m):
        return json.loads(self.et.fichiers[m["_id"]])


class TestStockage(Base):
    def test_parcours_complet_statuts_horodates_et_relecture(self):
        m = self.sto().stocker("AO 0001/2026", self.zip, demande_le="2026-10-04T08:00:00Z", source={"portail": "fictif"})
        self.assertEqual([e["etat"] for e in m["historique"]], ["demande", "acquis", "stockage", "stocke", "verifie"])
        self.assertEqual(m["historique"][0]["le"], "2026-10-04T08:00:00Z")
        self.assertTrue(all(len(e["le"]) == 20 and e["le"].endswith("Z") for e in m["historique"]))
        self.assertEqual(m["statut"], "verifie")
        roles = sorted(f["role"] for f in m["fichiers"])
        self.assertEqual(roles, ["archive"] + ["document"] * len(ENTREES))
        self.assertEqual({f["chemin"] for f in m["fichiers"] if f["role"] == "document"}, set(ENTREES))
        D = self.manifeste_drive(m)
        self.assertEqual(D["statut"], "verifie")
        self.assertEqual(D["fichiers"], m["fichiers"], "le manifeste rangé dans Drive est celui renvoyé")
        r = self.sto().relire(m, os.path.join(self.d, "relu"))
        self.assertTrue(all(x["sha256_identique"] for x in r) and len(r) == len(ENTREES) + 1)
        # tous les fichiers sont dans le dossier de la consultation, lui-même dans la racine privée
        dos = self.et.metas[m["dossier_id"]]
        self.assertEqual((dos["name"], dos["appProperties"]["eaios_ref"]), ("DCE_AO_0001_2026", "AO_0001_2026"))
        racine = self.et.metas[dos["parents"][0]]
        self.assertEqual(racine["name"], "EAIOS_DCE_PRIVE")
        for f in m["fichiers"]:
            self.assertEqual(self.et.metas[f["drive_id"]]["parents"], [m["dossier_id"]])

    def test_manifeste_sans_secret_ni_adresse(self):
        m = self.sto().stocker("AO-2", self.zip)
        brut = self.et.fichiers[m["_id"]].decode()
        for x in list(COFFRE.values()) + ["tok-", "SESSIONSECRET", "http://", "https://", "upload_id"]:
            self.assertNotIn(x, brut)
        self.assertNotIn("_id", json.loads(brut))

    def test_session_neuve_reprend_depuis_drive_sans_renvoi(self):
        m1 = self.sto().stocker("AO-3", self.zip)
        sessions = len(self.et.sessions)
        neuf = self.sto()  # nouvelle session : aucun état local
        lu = neuf.lire_manifeste("AO-3")
        self.assertEqual((lu["statut"], lu["fichiers"]), ("verifie", m1["fichiers"]))
        self.assertEqual([x["ref"] for x in neuf.lister_manifestes()], ["AO-3"])
        m2 = neuf.stocker("AO-3", self.zip)
        self.assertEqual(len(self.et.sessions), sessions, "aucun fichier renvoyé")
        self.assertEqual([f["drive_id"] for f in m2["fichiers"]], [f["drive_id"] for f in m1["fichiers"]])
        self.assertEqual(len([x for x in self.et.metas.values() if x["name"] == "EAIOS_DCE_PRIVE"]), 1, "une seule racine")

    def test_interruption_statut_echec_puis_reprise_sans_doublon(self):
        s = self.sto()
        vrai, n = s.d.envoyer, {"k": 0}

        def coupe(*a, **k):
            n["k"] += 1
            if n["k"] == 4:  # manifeste, archive, 1er document, puis coupure
                raise ErreurDrive("coupure simulée")
            return vrai(*a, **k)
        s.d.envoyer = coupe
        with self.assertRaises(ErreurDrive):
            s.stocker("AO-4", self.zip)
        m = self.sto().lire_manifeste("AO-4")
        self.assertEqual(m["statut"], "echec")
        self.assertIn("coupure simulée", m["historique"][-1]["detail"])
        avant = len(self.et.sessions)
        m = self.sto().stocker("AO-4", self.zip)
        self.assertEqual(m["statut"], "verifie")
        self.assertEqual(len(self.et.sessions) - avant, len(ENTREES) - 1, "seuls les fichiers manquants sont envoyés")
        self.assertEqual([e["etat"] for e in m["historique"]][-5:], ["echec", "acquis", "stockage", "stocke", "verifie"])
        docs = [x for x in self.et.metas.values() if (x.get("appProperties") or {}).get("eaios_role") == "document"]
        self.assertEqual(len(docs), len(ENTREES), "aucun doublon dans Drive")

    def test_lecture_seule_ne_cree_rien(self):
        s = self.sto()
        self.assertIsNone(s.lire_manifeste("AO-RIEN"))
        self.assertEqual(s.lister_manifestes(), [])
        self.assertEqual((self.et.metas, self.et.sessions), ({}, {}), "aucun dossier ni fichier créé par une lecture")
        self.assertFalse([r for r in self.et.requetes if r[0] in ("POST", "PUT", "PATCH") and r[1] != "/token"])

    def test_archive_piegee_refusee(self):
        z = os.path.join(self.d, "piege.zip")
        faire_zip(z, {"../../hors.txt": b"x"})
        with self.assertRaisesRegex(ErreurIntegrite, "chemin"):
            self.sto().stocker("AO-5", z)
        m = self.sto().lire_manifeste("AO-5")
        self.assertEqual(m["statut"], "echec")
        self.assertEqual(m["fichiers"], [])
        z2 = os.path.join(self.d, "bombe.zip")
        faire_zip(z2, {"DCE/zero.txt": b"\0" * (5 * 1024 * 1024)})
        with self.assertRaisesRegex(ErreurIntegrite, "compress"):
            self.sto().stocker("AO-5b", z2)

    def test_fichier_altere_dans_drive_detecte(self):
        s = self.sto()
        m = s.stocker("AO-6", self.zip)
        f = next(x for x in m["fichiers"] if x["chemin"] == "DCE/CPS.pdf")
        b = bytearray(self.et.fichiers[f["drive_id"]])
        b[10] ^= 1
        self.et.fichiers[f["drive_id"]] = bytes(b)
        with self.assertRaisesRegex(ErreurIntegrite, "CPS.pdf"):
            s.verifier(m)
        with self.assertRaises(ErreurIntegrite):
            s.relire(m, os.path.join(self.d, "r"))

    def test_seul_grant_type_part_et_references(self):
        self.sto().stocker("AO-7", self.zip)
        J = [v for v in self.proxy.vues if v["url"].endswith("/token")]
        self.assertTrue(J and all(v["corps"] == b"grant_type=refresh_token" for v in J))
        self.assertFalse(any("tok-" in v["url"] for v in self.proxy.vues))
        for bad in ("", "x" * 81, "...", "/"):
            with self.assertRaises(ErreurDrive):
                slug(bad)
        self.assertEqual(slug("AO 12/2026 - lot 1"), "AO_12_2026_-_lot_1")


if __name__ == "__main__":
    unittest.main()

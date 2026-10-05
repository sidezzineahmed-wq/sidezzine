"""Bout à bout hors réseau : manifest du kit (archive en base64, chemin relatif) -> zip-binaire -> stocker-dce sur le FAUX
Google local -> reprise_stockage. Reproduit l'incident du 05/10/2026 (ErreurIntegrite sur le texte base64) puis le corrige."""
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
sys.path.insert(0, os.path.join(os.path.dirname(ICI), "tests"))

import portail_fictif  # noqa: E402
from test_dce_stockage import Base  # noqa: E402
from drive_adapter import ErreurIntegrite  # noqa: E402
from drive_adapter.__main__ import _resume  # noqa: E402
from dce_kit import cycle  # noqa: E402
from dce_kit.raccord import zip_binaire  # noqa: E402
from dce_kit.tache import PHRASE, preparer  # noqa: E402


class TestRaccordStockage(Base):
    def test_incident_puis_raccord_et_reprise(self):
        octets = portail_fictif.zip_fictif()
        s = os.path.join(self.d, "run_r", "sortie")
        m = preparer(octets, "38 MAT.INF 2026.zip", s)
        m["zip"]["fichier_local"] = os.path.relpath(m["zip"]["fichier_local"], s)       # manifest relatif, comme le passage réel
        man = os.path.join(s, "manifest.json")
        json.dump(m, open(man, "w"), ensure_ascii=False)
        with self.assertRaisesRegex(ErreurIntegrite, "illisible"):                     # l'incident : base64 passé à stocker-dce
            self.sto().stocker("fx-1", os.path.join(s, m["zip"]["fichier_local"]))
        r = zip_binaire(man, os.path.join(self.d, "run_r"), os.path.join(self.d, "run_r", "stockage", m["zip"]["nom"]))
        drv = _resume(self.sto().stocker("fx-1", r["zip"]))
        self.assertEqual((drv["statut"], drv["archive"]["sha256"], drv["archive"]["nom"]), ("verifie", m["zip"]["sha256"], "38 MAT.INF 2026.zip"))
        dem = {"ao_id": "fx-1", "ref": "1", "org": "O", "etat": "echec", "tache": None, "__version": 9,
               "erreur": {"code": "stockage", "motif": "ErreurIntegrite: archive ZIP illisible", "le": "2026-10-05T17:30:00Z"},
               "validation": {"phrase": PHRASE, "empreinte": "e" * 64, "par": "h", "le": "2026-10-05T17:16:00Z"}}
        w = cycle.reprise_stockage("fx-1", dem, m, drv, m["zip"]["sha256"], "rrep", {"fx-1"})
        self.assertEqual((w["data"]["etat"], w["if_version"], w["data"]["resultat"]["fichiers"]), ("pret", 9, len(m["fichiers"]) + 1))
        self.assertTrue(all(x["sha256_identique"] for x in self.sto().relire(self.sto().lire_manifeste("fx-1"), os.path.join(self.d, "relu"))))

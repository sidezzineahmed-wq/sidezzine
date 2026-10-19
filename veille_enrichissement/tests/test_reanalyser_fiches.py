"""Ré-analyse hors ligne du HTML de fiche déjà lu : date réelle de lecture gardée, ré-analyse datée à part, contact et pièces
« non lus » sur une page coupée par l'ancien lecteur, SHA exigé. Fixture du kit (contact fictif), aucun réseau."""
import gzip
import hashlib
import json
import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
import reanalyser_fiches as RF  # noqa: E402

KIT = os.environ.get("KIT_VEILLE", "")


@unittest.skipUnless(KIT, "KIT_VEILLE (kit à jour) requis")
class Reanalyse(unittest.TestCase):
    def test_lu_le_garde_reanalyse_datee_contact_non_lu(self):
        sys.path.insert(0, os.path.join(KIT, "ingestion"))
        from enrichi_pmmp import statuts_blocs  # noqa: E402  (ingestion du kit)
        h = open(os.path.join(KIT, "tests", "fixtures", "fiche_1041719_e5w_v3_contact_fictif.html"), encoding="utf-8").read()
        h = h[:h.index('<div id="ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_panelContcatAdministratif"')]  # coupe v2
        sha = hashlib.sha256(h.encode()).hexdigest()
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "brut"))
        with gzip.open(os.path.join(d, "brut", "e5w_1041719_fiche.html.gz"), "wt", encoding="utf-8", newline="") as f:
            f.write(h)
        lots = {"lu_le": "2026-10-18T09:00:00+00:00", "statut": "lu", "lots": []}
        F = {"pmmp:e5w:1041719": {"id": "pmmp:e5w:1041719", "lu_le": "2026-10-18T09:00:00+00:00", "run": "R0",
                                  "sha256_html_tronque": sha, "lots": lots,
                                  "champs": {"ref": "10/2026/ARR/MERINIDES", "version_lecture": 2, "q": []}},
             "pmmp:e5w:2": {"id": "pmmp:e5w:2", "lu_le": "2026-10-18T09:00:00+00:00", "run": "R0", "sha256_html_tronque": "x" * 64,
                            "champs": {"ref": "Z", "version_lecture": 2}}}
        with gzip.open(os.path.join(d, "brut", "e5w_2_fiche.html.gz"), "wt", encoding="utf-8") as f:
            f.write("autre lecture")
        json.dump(F, open(os.path.join(d, "f.json"), "w"))
        RF.main(["--fiches", os.path.join(d, "f.json"), "--brut", os.path.join(d, "brut"), "--kit", KIT,
                 "--sortie", os.path.join(d, "o.json"), "--rapport", os.path.join(d, "r.json"), "--maintenant", "2026-10-19T21:00:00+00:00"])
        o, r = json.load(open(os.path.join(d, "o.json"))), json.load(open(os.path.join(d, "r.json")))
        x = o["pmmp:e5w:1041719"]
        self.assertEqual((x["lu_le"], x["run"], x["sha256_html_tronque"], x["lots"]), ("2026-10-18T09:00:00+00:00", "R0", sha, lots))
        self.assertEqual((x["reanalyse_le"], x["version_parseur"], x["version_lecture_initiale"]), ("2026-10-19T21:00:00+00:00", 3, 2))
        self.assertEqual(x["champs"]["ret"], "Avenue Abi Imran Fassi ain kadous – Fés")
        self.assertEqual(x["champs"]["ech_date"], "2026-10-19T10:00")
        st = statuts_blocs(x["champs"])
        self.assertEqual((st["contact"], st["docs"], st["retrait"], st["prix_plans"]), ("non_lu", "non_lu", "lu", "lu"))
        self.assertNotIn("reanalyse_le", o["pmmp:e5w:2"], "SHA différent : lecture non touchée")
        self.assertEqual((r["reanalysees"], r["sha_different"]), (1, 1))
        # relancer : déjà à jour, rien ne bouge
        RF.main(["--fiches", os.path.join(d, "o.json"), "--brut", os.path.join(d, "brut"), "--kit", KIT,
                 "--sortie", os.path.join(d, "o2.json"), "--maintenant", "2026-10-20T00:00:00+00:00"])
        self.assertEqual(json.load(open(os.path.join(d, "o2.json")))["pmmp:e5w:1041719"]["reanalyse_le"], "2026-10-19T21:00:00+00:00")


if __name__ == "__main__":
    unittest.main()

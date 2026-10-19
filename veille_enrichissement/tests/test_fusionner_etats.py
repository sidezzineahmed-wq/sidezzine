"""fusionner_etats.py : aucune donnée plus récente perdue entre un passage manuel et un passage horaire publié."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
import fusionner_etats as fe  # noqa: E402


def ecrire(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f)


class TestFusion(unittest.TestCase):
    def test_plus_recent_gagne_rien_perdu(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        A, B, S = (os.path.join(d, x) for x in "abs")
        L = lambda vu, lim, run, **k: {"id": "x", "listing": {"lim": lim}, "dernier_vu_listing": vu, "dernier_run": run,
                                         "premier_vu": k.get("pv", vu), "absences_listing_complet": k.get("abs", 0),
                                         **({"dernier_run_absent": k["dra"]} if "dra" in k else {})}
        ecrire(os.path.join(A, "listing.json"), {"version": 1, "items": {
            "pmmp:o:1": L("2026-10-19T14:40:00+00:00", "2026-11-10", "m", pv="2026-10-01T00:00:00+00:00"),
            "pmmp:o:2": L("2026-10-19T14:10:00+00:00", "2026-10-30", "m0", abs=1, dra="2026-10-19T144000Z"),
            "pmmp:o:4": L("2026-10-19T14:41:00+00:00", "2026-12-01", "m"),
            "pmmp:o:5": L("2026-10-08T23:14:10+00:00", "2026-10-10", "r8", abs=168, dra="2026-10-19T144503Z")}})
        ecrire(os.path.join(B, "listing.json"), {"version": 1, "items": {
            "pmmp:o:1": L("2026-10-19T14:20:00+00:00", "2026-10-22", "h"),
            "pmmp:o:2": L("2026-10-19T14:20:00+00:00", "2026-10-30", "2026-10-19T141938Z"),
            "pmmp:o:3": L("2026-10-19T14:21:00+00:00", "2026-11-01", "h"),
            "pmmp:o:5": L("2026-10-08T23:14:10+00:00", "2026-10-10", "r8", abs=167, dra="2026-10-18T201351Z")}})
        ecrire(os.path.join(A, "fiches", "o_1.json"), {"id": "pmmp:o:1", "lu_le": "2026-10-18T10:00:00+00:00", "champs": {"v": "a"},
                                                      "lots": {"lu_le": "2026-10-19T09:00:00+00:00", "n": 3}})
        ecrire(os.path.join(B, "fiches", "o_1.json"), {"id": "pmmp:o:1", "lu_le": "2026-10-19T14:25:00+00:00", "champs": {"v": "b"}})
        ecrire(os.path.join(B, "fiches", "o_3.json"), {"id": "pmmp:o:3", "lu_le": "2026-10-19T14:25:00+00:00", "champs": {}})
        ecrire(os.path.join(A, "couverture", "m.json"), {"run_id": "m"})
        ecrire(os.path.join(B, "couverture", "h.json"), {"run_id": "h"})
        ecrire(os.path.join(A, "selection.json"), {"items": {"pmmp:o:1": {"dernier_choix": "2026-10-18T10:00:00+00:00"}}})
        ecrire(os.path.join(B, "selection.json"), {"items": {"pmmp:o:1": {"dernier_choix": "2026-10-19T14:25:00+00:00"}}})
        fe.main(["--a", A, "--b", B, "--sortie", S])
        it = json.load(open(os.path.join(S, "listing.json")))["items"]
        self.assertEqual(set(it), {"pmmp:o:1", "pmmp:o:2", "pmmp:o:3", "pmmp:o:4", "pmmp:o:5"})
        # absent des deux côtés : l'absence la plus récente (listing complet manuel) n'est pas écrasée par l'ancienne
        self.assertEqual((it["pmmp:o:5"]["absences_listing_complet"], it["pmmp:o:5"]["dernier_run_absent"]), (168, "2026-10-19T144503Z"))
        self.assertEqual(it["pmmp:o:1"]["listing"]["lim"], "2026-11-10")  # observation manuelle plus récente
        self.assertEqual(it["pmmp:o:1"]["premier_vu"], "2026-10-01T00:00:00+00:00")
        self.assertEqual(it["pmmp:o:2"]["absences_listing_complet"], 1)  # absence constatée après l'observation horaire
        f1 = json.load(open(os.path.join(S, "fiches", "o_1.json")))
        self.assertEqual(f1["champs"]["v"], "b")  # fiche horaire plus récente
        self.assertEqual(f1["lots"]["n"], 3)  # popup des lots le plus récent conservé
        self.assertTrue(os.path.exists(os.path.join(S, "fiches", "o_3.json")))
        self.assertEqual(sorted(os.listdir(os.path.join(S, "couverture"))), ["h.json", "m.json"])
        self.assertEqual(json.load(open(os.path.join(S, "selection.json")))["items"]["pmmp:o:1"]["dernier_choix"], "2026-10-19T14:25:00+00:00")


if __name__ == "__main__":
    unittest.main()

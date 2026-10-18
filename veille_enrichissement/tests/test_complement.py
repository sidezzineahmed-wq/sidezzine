"""Complément complet : reprise, statuts lu / champ absent / inaccessible, arrêt 403, export. Portail FICTIF local (aucun réseau)."""
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
import complement_complet as CC  # noqa: E402
import exporter_complement as EX  # noqa: E402

KIT = os.environ.get("KIT_VEILLE", "")
FICHE = open(os.path.join(ICI, "fixtures", "fiche_1041301_o8p_sans_contact.html"), encoding="utf-8").read()
VUS = []


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse
        q = parse_qs(urlparse(self.path).query)
        r, o = q["refConsultation"][0], q["orgAcronyme"][0]
        VUS.append(r)
        if r == "403":
            self.send_response(403); self.end_headers(); return
        if r == "500":
            self.send_response(500); self.end_headers(); return
        h = FICHE.replace("SK04/2026/CFR", f"REF-{r}")
        if r == "2":
            h = h.replace("> | Sur offre de prix<", "><")
        if r == "9":
            h = "<html><body>maintenance</body></html>"
        b = h.encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(b)


@unittest.skipUnless(KIT and os.path.isdir(KIT), "kit collecteur absent (KIT_VEILLE)")
class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        sys.path.insert(0, KIT)
        import veille.client as C
        cls.C, cls.base = C, C.BASE
        C.BASE = f"http://127.0.0.1:{cls.srv.server_address[1]}/index.php"

    @classmethod
    def tearDownClass(cls):
        cls.C.BASE = cls.base
        cls.srv.shutdown()

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        VUS.clear()

    def run_cc(self, cibles, essais=1):
        p = os.path.join(self.d, "cibles.json")
        json.dump(cibles, open(p, "w"))
        import veille.client as C
        C.ClientPMMP.__init__.__defaults__  # noqa
        orig = C.ClientPMMP.__init__

        def rapide(s, delai_min=3.0, **kw):
            orig(s, delai_min=2.0, gigue=0.0, reprises=0, **{k: v for k, v in kw.items() if k not in ("gigue", "reprises")})
            s.delai_min = 0.0
        C.ClientPMMP.__init__ = rapide
        try:
            return CC.main(["--kit", KIT, "--cibles", p, "--dossier", self.d, "--delai", "2", "--essais", str(essais), "--pause-debut", "99", "--pause-fin", "99"])
        finally:
            C.ClientPMMP.__init__ = orig

    def test_statuts_reprise_et_export(self):
        cib = {"pmmp:o8p:1": {"ref": "REF-1"}, "pmmp:o8p:2": {"ref": "REF-2"}, "pmmp:o8p:9": {"ref": "REF-9"}}
        self.assertEqual(self.run_cc(cib, essais=1), 0)
        r1 = json.load(open(os.path.join(self.d, "cache", "o8p_1.json")))
        r2 = json.load(open(os.path.join(self.d, "cache", "o8p_2.json")))
        self.assertEqual((r1["statut"], r1["mode_passation"], r1["ref"], r1["proc"]), ("lu", "Sur offre de prix", "REF-1", "Appel d'offres ouvert"))
        self.assertIn("refConsultation=1&orgAcronyme=o8p", r1["url"])
        self.assertTrue(r1["lu_le"] and r1["contact_coupe"] is False or r1["lu_le"])
        self.assertEqual((r2["statut"], r2["mode_passation"]), ("champ_absent", None), "élément vide : aucune valeur inventée")
        e9 = json.load(open(os.path.join(self.d, "echecs", "o8p_9.json")))
        self.assertTrue(e9["inaccessible"])
        self.assertFalse(any(f.endswith(".tmp") for f in os.listdir(os.path.join(self.d, "cache"))), "écriture atomique")
        # reprise : rien de déjà lu n'est relu
        VUS.clear()
        self.assertEqual(self.run_cc(cib, essais=1), 0)
        self.assertEqual(VUS, [])
        out = os.path.join(self.d, "c.json")
        EX.main(["--dossier", self.d, "--essais", "1", "--sortie", out])
        c = json.load(open(out))
        self.assertEqual(c["comptes"], {"champ_absent": 1, "inaccessible": 1, "lu": 1})
        self.assertEqual(c["par_id"]["pmmp:o8p:9"]["v"], None)
        # fusion : une lecture antérieure n'est pas remplacée par un « inaccessible »
        prec = {"par_id": {"pmmp:o8p:9": {"statut": "lu", "v": "Au rabais / majoration", "lu_le": "2026-10-01T00:00:00+00:00"}}}
        json.dump(prec, open(os.path.join(self.d, "p.json"), "w"))
        EX.main(["--dossier", self.d, "--essais", "1", "--precedent", os.path.join(self.d, "p.json"), "--sortie", out])
        self.assertEqual(json.load(open(out))["par_id"]["pmmp:o8p:9"]["v"], "Au rabais / majoration")

    def test_echec_reessayable_non_exporte_et_arret_403(self):
        self.assertEqual(self.run_cc({"pmmp:o8p:500": {"ref": "x"}}, essais=1), 0, "5xx : échec compté, pas d'arrêt")
        self.assertEqual(json.load(open(os.path.join(self.d, "echecs", "o8p_500.json")))["tentatives"], 1)
        out = os.path.join(self.d, "c.json")
        EX.main(["--dossier", self.d, "--essais", "3", "--sortie", out])
        self.assertEqual(json.load(open(out))["par_id"], {}, "1 échec sur 3 essais : rien exporté")
        self.assertEqual(self.run_cc({"pmmp:o8p:403": {"ref": "x"}}, essais=3), 3)
        self.assertIn("403", json.load(open(os.path.join(self.d, "etat.json")))["arret"])


if __name__ == "__main__":
    unittest.main()

"""Complément des fiches + lots : une lecture alimente tous les champs, popup lu dans le même passage, identité, reprise
sans relecture, conservation d'une lecture si la suite échoue, arrêt 403. Portail FICTIF local (aucun réseau)."""
import gzip
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
import complement_fiches as CF  # noqa: E402
import integrer_fiches as IF  # noqa: E402
import integrer_fiches as IF  # noqa: E402

KIT = os.environ.get("KIT_VEILLE", "")
FX = os.path.join(KIT, "tests", "fixtures") if KIT else ""
VUS = []


def fx(n):
    return open(os.path.join(FX, n), encoding="utf-8").read()


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse
        q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        r = q["refConsultation"]
        page = q["page"]
        VUS.append((page.split(".")[1], r))
        if r == "403":
            self.send_response(403); self.end_headers(); return
        if page == "commun.PopUpDetailLots":
            if r == "500lots":
                self.send_response(500); self.end_headers(); return
            h = fx("popup_lots_1046170_o4d.html")
            h = h.replace("refConsultation=1046170", "refConsultation=" + ("AUTRE" if r == "faux" else r)).replace("orgAccronyme=o4d", "orgAccronyme=" + q["orgAccronyme"])
        elif r.startswith("al") or r in ("faux", "500lots"):
            h = fx("fiche_1046170_o4d_allotie_sans_contact.html")
        else:
            h = fx("fiche_1041301_o8p_sans_contact.html")
        b = h.encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(b)


@unittest.skipUnless(KIT and os.path.isfile(os.path.join(KIT, "veille", "pmmp_lots.py")), "kit avec pmmp_lots absent (KIT_VEILLE)")
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

    def run_cf(self, cibles, essais=1, paralleles=1):
        p = os.path.join(self.d, "cibles.json")
        json.dump(cibles, open(p, "w"))
        import veille.client as C
        orig = C.ClientPMMP.__init__

        def rapide(s, delai_min=3.0, **kw):
            orig(s, delai_min=2.0, gigue=0.0, reprises=0)
            s.delai_min = 0.0
        C.ClientPMMP.__init__ = rapide
        try:
            return CF.main(["--kit", KIT, "--cibles", p, "--dossier", self.d, "--delai", "0.2", "--essais", str(essais),
                            "--attente-echec-min", "0", "--pause-debut", "99", "--pause-fin", "99", "--paralleles", str(paralleles)])
        finally:
            C.ClientPMMP.__init__ = orig

    def rec(self, o, r):
        return json.load(open(os.path.join(self.d, "cache", f"{o}_{r}.json")))

    def test_un_passage_tous_champs_et_lots(self):
        cib = {"pmmp:o8p:1": {"ref": "SK04/2026/CFR", "besoin": "fiche"}, "pmmp:o4d:al1": {"ref": "14/2026/81800", "besoin": "fiche"},
               "pmmp:o4d:al2": {"ref": "14/2026/81800", "besoin": "lots", "allot": "2 Lots"}}
        self.assertEqual(self.run_cf(cib), 0)
        self.assertEqual(sorted(VUS), sorted([("EntrepriseDetailConsultation", "1"), ("EntrepriseDetailConsultation", "al1"),
                                              ("PopUpDetailLots", "al1"), ("PopUpDetailLots", "al2")]), "un GET par page, pas un par champ")
        r1 = self.rec("o8p", "1")
        F = r1["fiche"]["champs"]
        self.assertEqual((F["est"], F["cau"], F["tp"], F["mode_passation"]), (21446884.14, 428000.0, False, "Sur offre de prix"))
        self.assertEqual(len(F["q"]), 3)
        self.assertFalse(r1["allotie"])
        self.assertNotIn("lots", r1)
        a1 = self.rec("o4d", "al1")
        self.assertTrue(a1["allotie"])
        self.assertIsNone(a1["fiche"]["champs"]["reu"], "libellé « Date et heure : » seul = rien de publié")
        L = a1["lots"]
        self.assertEqual((L["statut"], L["n"], L["n_annonce"]), ("lu", 2, 2))
        self.assertEqual([(x["num"], x["est"], x["cau"], x["tp"]) for x in L["lots"]], [("1", 202447.87, 4000.0, True), ("2", 151835.9, 3000.0, True)])
        self.assertIn("q", L["lots"][0]["ni"], "« - » publié = non indiqué, pas « non exigé » inventé")
        self.assertNotIn("fiche", self.rec("o4d", "al2"), "besoin « lots » : la fiche n'est pas relue")
        self.assertTrue(os.path.exists(os.path.join(self.d, "brut", "o4d_al1_lots.html.gz")))
        self.assertNotIn("Contact Administratif", gzip.open(os.path.join(self.d, "brut", "o8p_1_fiche.html.gz"), "rt").read())
        VUS.clear()
        self.assertEqual(self.run_cf(cib), 0)
        self.assertEqual(VUS, [], "reprise : rien relu")

    def test_integration_fusion_reparse_sans_requete(self):
        cib = {"pmmp:o8p:1": {"ref": "SK04/2026/CFR", "besoin": "fiche"}, "pmmp:o4d:al2": {"ref": "14/2026/81800", "besoin": "lots", "allot": "2 Lots"},
               "pmmp:o4d:al3": {"ref": "14/2026/81800", "besoin": "fiche"}}
        self.assertEqual(self.run_cf(cib), 0)
        VUS.clear()
        coffre = {"pmmp:o4d:al2": {"id": "pmmp:o4d:al2", "lu_le": "2026-10-17T00:00:00+00:00", "run": "r", "sha256_html_tronque": "x", "champs": {"ref": "14/2026/81800", "allot": "2 Lots"}},
                  "pmmp:o4d:al3": {"id": "pmmp:o4d:al3", "lu_le": "2099-01-01T00:00:00+00:00", "run": "futur", "sha256_html_tronque": "y", "champs": {"ref": "14/2026/81800"}}}
        pf, out, comp = (os.path.join(self.d, n) for n in ("f.json", "o.json", "c.json"))
        json.dump(coffre, open(pf, "w"))
        self.assertEqual(IF.main(["--fiches", pf, "--dossier", self.d, "--kit", KIT, "--sortie", out, "--complement", comp]), 0)
        F = json.load(open(out))
        self.assertEqual(VUS, [], "intégration et re-analyse : aucune requête")
        self.assertEqual(F["pmmp:o8p:1"]["champs"]["est"], 21446884.14)
        self.assertEqual(F["pmmp:o4d:al2"]["lu_le"], "2026-10-17T00:00:00+00:00", "popup seul : la fiche du coffre est gardée")
        self.assertEqual(F["pmmp:o4d:al2"]["lots"]["n"], 2)
        self.assertEqual(F["pmmp:o4d:al3"]["run"], "futur", "une lecture du coffre plus récente n'est jamais remplacée")
        self.assertEqual(F["pmmp:o4d:al3"]["lots"]["statut"], "lu", "mais le popup lu plus récemment y est rattaché")
        self.assertEqual(json.load(open(comp))["fiches_inaccessibles"], {})

    def test_integration_fusion_reparse_sans_perte(self):
        cib = {"pmmp:o8p:1": {"ref": "SK04/2026/CFR", "besoin": "fiche"}, "pmmp:o4d:al2": {"ref": "14/2026/81800", "besoin": "lots", "allot": "2 Lots"},
               "pmmp:o4d:al3": {"ref": "14/2026/81800", "besoin": "fiche"}}
        self.assertEqual(self.run_cf(cib), 0)
        VUS.clear()
        coffre = {"pmmp:o4d:al2": {"id": "pmmp:o4d:al2", "lu_le": "2026-10-17T00:00:00+00:00", "run": "r", "sha256_html_tronque": "x", "champs": {"ref": "14/2026/81800", "allot": "2 Lots"}},
                  "pmmp:o4d:al3": {"id": "pmmp:o4d:al3", "lu_le": "2099-01-01T00:00:00+00:00", "run": "futur", "sha256_html_tronque": "y", "champs": {"ref": "14/2026/81800"}}}
        pf, out, comp = (os.path.join(self.d, n) for n in ("f.json", "o.json", "c.json"))
        json.dump(coffre, open(pf, "w"))
        # cache : ancienne analyse (parser précédent) d'une qualification que la re-analyse doit retrouver sans perte
        pc = os.path.join(self.d, "cache", "o8p_1.json")
        rc = json.load(open(pc))
        rc["fiche"]["champs"]["q"] = [{"m": "Equipement", "s": "B.3", "sl": None, "q": None, "ql": None, "c": "2"}]
        json.dump(rc, open(pc, "w"))
        self.assertEqual(IF.main(["--fiches", pf, "--dossier", self.d, "--kit", KIT, "--sortie", out, "--complement", comp]), 0)
        F = json.load(open(out))
        self.assertEqual(VUS, [], "intégration et re-analyse : aucune requête")
        self.assertEqual(len(F["pmmp:o8p:1"]["champs"]["q"]), 3)
        self.assertEqual(len(F["pmmp:o8p:1"]["champs"]["q_txt"]), 3, "lignes publiées gardées")
        self.assertEqual(F["pmmp:o4d:al2"]["lu_le"], "2026-10-17T00:00:00+00:00", "popup seul : la fiche du coffre est gardée")
        self.assertEqual(F["pmmp:o4d:al2"]["lots"]["n"], 2)
        self.assertEqual(F["pmmp:o4d:al3"]["run"], "futur", "une lecture du coffre plus récente n'est jamais remplacée")
        self.assertEqual(F["pmmp:o4d:al3"]["lots"]["statut"], "lu", "mais le popup lu plus récemment y est rattaché")
        self.assertTrue(IF.q_conserve([{"m": "Equipement", "s": "Y1", "c": "3"}], [{"m": "Equipement", "s": "Y", "q": "Y1", "c": "3"}]))
        self.assertFalse(IF.q_conserve([{"m": "Laboratoires", "c": "4", "sl": "CONTROLE"}], [{"m": "Laboratoires", "c": "4"}]), "perte détectée")

    def test_identite_popup_et_conservation_fiche(self):
        cib = {"pmmp:o4d:faux": {"ref": "x", "besoin": "fiche"}, "pmmp:o4d:500lots": {"ref": "x", "besoin": "fiche"}}
        self.assertEqual(self.run_cf(cib, essais=2), 0)
        f = self.rec("o4d", "faux")
        self.assertTrue(f["fiche"]["champs"]["obj"])
        self.assertNotIn("lots", f, "popup d'une autre consultation : rejeté")
        self.assertTrue(json.load(open(os.path.join(self.d, "echecs", "o4d_faux.json")))["inaccessible"])
        n = [v for v in VUS if v == ("EntrepriseDetailConsultation", "500lots")]
        self.assertEqual(len(n), 1, "fiche lue une fois ; seul le popup est retenté")
        self.assertEqual(json.load(open(os.path.join(self.d, "echecs", "o4d_500lots.json")))["tentatives"], 2)

    def test_arret_403(self):
        self.assertEqual(self.run_cf({"pmmp:o8p:403": {"ref": "x", "besoin": "fiche"}}, essais=3), 3)
        self.assertIn("403", json.load(open(os.path.join(self.d, "etat.json")))["arret"])

    def test_deux_connexions(self):
        cib = {f"pmmp:o4d:al{i}": {"ref": "x", "besoin": "fiche"} for i in range(4)}
        self.assertEqual(self.run_cf(cib, paralleles=2), 0)
        self.assertEqual(len(VUS), 8)
        self.assertEqual(len(os.listdir(os.path.join(self.d, "cache"))), 4)


if __name__ == "__main__":
    unittest.main()

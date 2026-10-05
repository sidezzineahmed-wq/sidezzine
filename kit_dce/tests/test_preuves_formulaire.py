"""Preuves d'un formulaire non reconnu à l'ouverture — HORS RÉSEAU (portail FICTIF local, Chromium réel).
Variantes réalistes : libellés en cellules de tableau sans <label for>, état « Téléchargement complet » sans formulaire, formulaire
dans un cadre. Les preuves ne contiennent ni valeur de champ, ni état caché, ni paramètre d'URL autre que page/ref/org."""
import json
import os
import shutil
import tempfile
import unittest

from test_kit import cli
import portail_fictif

SECRETS = ("JETON-SECRET-FICTIF", "VALEUR-FICTIVE", "SESS-FICTIF", "SESS-CADRE", "PRADO_PAGESTATE")


class TestPreuves(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.racine = os.path.join(self.d, "racine")
        os.makedirs(self.racine)
        self.srv, self.etat = portail_fictif.demarrer()
        self.addCleanup(self.srv.shutdown)
        self.cfg = os.path.join(self.d, "config.json")
        json.dump({"base_url": f"http://127.0.0.1:{self.srv.server_address[1]}/index.php", "hote_autorise": "127.0.0.1"}, open(self.cfg, "w"))

    def ouvrir(self, ref, racine=True):
        e = os.path.join(self.d, f"etat_{ref}.json")
        code, _, err = cli("ouvrir", "--ref", ref, "--org", "orgfictif", "--config", self.cfg, "--etat", e,
                           env={"DCE_RACINE_TRAVAIL": self.racine} if racine else None)
        return code, json.load(open(e)), err

    def preuves(self, etat):
        self.assertTrue(etat["preuves"].startswith(self.racine + os.sep), etat)
        brut = open(etat["preuves"], encoding="utf-8").read()
        for s in SECRETS:
            self.assertNotIn(s, brut, "aucune valeur, aucun état caché, aucun paramètre de session")
        return json.loads(brut)

    def test_tableau_sans_label_associe(self):
        code, e, err = self.ouvrir("RTABLE")
        self.assertEqual((code, e["code"], e["motif"]), (2, "formulaire", "champ « Nom » introuvable"), err[-600:])
        p = self.preuves(e)
        self.assertEqual((p["http"], p["titre"], p["page"], p["refConsultation"], p["orgAcronyme"]),
                         (200, "PMMP - Demande de téléchargement", "entreprise.EntrepriseDemandeTelechargementDce", "RTABLE", "orgfictif"))
        self.assertNotIn("jeton", p)
        c = p["cadres"][0]
        self.assertTrue(c["principal"])
        self.assertEqual([(x["type"], x["id"], x["name"], x["libelles"]) for x in c["champs"]],
                         [("text", "ctl0_CONTENU_nom", "ctl0$CONTENU$nom", []), ("text", "ctl0_CONTENU_prenom", "ctl0$CONTENU$prenom", [])])
        self.assertEqual((c["libelles"], c["champs_caches"], c["formulaires"], c["boutons"]), ([], 1, 1, ["Valider"]))
        self.assertEqual(self.etat.soumis, [], "ouvrir ne soumet rien")

    def test_etat_telechargement_complet_sans_formulaire(self):
        code, e, _ = self.ouvrir("RCOMPLET")
        self.assertEqual((code, e["code"]), (2, "formulaire"))
        c = self.preuves(e)["cadres"][0]
        self.assertEqual((c["champs"], c["formulaires"]), ([], 0))
        self.assertIn("Nouveau téléchargement", c["liens"])
        self.assertEqual(self.etat.telechargements, [], "aucun lien suivi")

    def test_formulaire_dans_un_cadre(self):
        code, e, _ = self.ouvrir("RIFRAME")
        self.assertEqual((code, e["code"]), (2, "formulaire"))
        p = self.preuves(e)
        self.assertEqual(p["cadres"][0]["cadres_internes"], 1)
        interne = [c for c in p["cadres"] if not c["principal"]]
        self.assertEqual(len(interne), 1)
        self.assertEqual((interne[0]["chemin"], interne[0]["page"]), ("/cadre", "formulaire"))
        self.assertIn("Nom", [x["title"] for x in interne[0]["champs"]])

    def test_formulaire_reconnu_aucune_preuve(self):
        code, e, err = self.ouvrir("R-FICTIF-1")
        self.assertEqual((code, e["etat"]), (0, "attente_validation_CG"), err[-600:])
        self.assertNotIn("preuves", e)
        self.assertEqual(os.listdir(self.racine), [])

    def test_champ_ambigu_refuse(self):
        code, e, _ = self.ouvrir("RAMBIGU")
        self.assertEqual((code, e["code"], e["motif"]), (2, "formulaire", "champ « Nom » ambigu (2 champs)"))
        self.assertEqual(self.etat.soumis, [])

    def test_fixture_fidele_au_releve_pmmp(self):
        """Relevé PMMP du 05/10/2026 : <label for="nom"> ne vise pas l'id préfixé → aucun libellé associé ; nom accessible = title."""
        import asyncio
        import re
        from playwright.async_api import async_playwright

        async def mesurer():
            async with async_playwright() as pw:
                b = await pw.chromium.launch()
                pg = await b.new_page()
                await pg.goto(f"http://127.0.0.1:{self.srv.server_address[1]}/index.php?page=x&refConsultation=R-FICTIF-1&orgAcronyme=o")
                r = {"labels": await pg.evaluate("document.getElementById('ctl0_CONTENU_PAGE_EntrepriseFormulaireDemande_nom').labels.length"),
                     "ancien": await pg.get_by_label(re.compile(r"^\s*Nom\b", re.I)).count(),
                     "nouveau": [await pg.get_by_role("textbox", name=n, exact=True).count() for n in ("Nom", "Prénom", "Adresse électronique")],
                     "cg": await pg.get_by_role("checkbox", name=re.compile("condition", re.I)).count()}
                await b.close()
                return r
        self.assertEqual(asyncio.run(mesurer()), {"labels": 0, "ancien": 0, "nouveau": [1, 1, 1], "cg": 1})

    def test_sans_racine_pas_de_preuve_meme_refus(self):
        code, e, _ = self.ouvrir("RTABLE", racine=False)
        self.assertEqual((code, e["code"]), (2, "formulaire"))
        self.assertNotIn("preuves", e)


if __name__ == "__main__":
    unittest.main()

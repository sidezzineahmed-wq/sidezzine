"""Copie canonique des CG servies en HTML (section unique div#main-part.main-part, algorithme cg_texte.ALGO) — HORS RÉSEAU.
Démontre : variations TECHNIQUES ignorées (bandeau date/heure hors section, état PRADO, attributs et paramètres de session,
scripts, styles, commentaires, titre) ; changements RÉELS du contenu détectés (mot, clause repliée, lien, image, rubrique)
et rapportés ligne à ligne ; structure inconnue refusée ; PDF toujours haché en binaire ; validation d'un algorithme
antérieur refusée sans migration."""
import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dce_kit import cg_texte, cycle  # noqa: E402
from dce_kit.tache import PHRASE  # noqa: E402
from test_kit import ENV_FICTIF, cli  # noqa: E402
import portail_fictif  # noqa: E402

PAGE = """<!doctype html><html><head><title>T {n}</title><script>var x="{n}";</script></head><body>
<div id="bandeau">Nous sommes le {n}</div><!-- {n} --><form><input type="hidden" name="PRADO_PAGESTATE" value="{n}">
<div id="main-part" class="main-part" data-x="{n}"><style>p{{margin:{n}px}}</style><h1>Conditions d'utilisation</h1>
<div id="rubrique_1"><h2>Conditions</h2><p style="x:{n}">Article 1 : texte&nbsp;contractuel.</p>
<div style="display:none"><p>Article 2 : clause repliée.</p></div>
<p>Voir <a href="/index.php?page=commun.Aide&amp;sid={n}&amp;PRADO_SESSION={n}#aide">l'aide</a>.</p></div>
<div id="rubrique_2"><h2>Pré-requis</h2><ul><li>Point A</li><li>Point&#160;B</li></ul><img src="/i/n.png?v={n}" alt="Navigateurs"></div>
</div></form></body></html>"""


def canon(page):
    return cg_texte.canonique(page)


class TestCanonique(unittest.TestCase):
    def test_contenu_integral_et_variations_techniques_ignorees(self):
        a, b = canon(PAGE.format(n="05/10/2026 13:24:01")), canon(PAGE.format(n="999"))
        self.assertEqual(a, b, "bandeau date/heure hors section, état PRADO, attributs, scripts, commentaires : ignorés")
        self.assertEqual(a.split("\n"), ["Conditions d'utilisation", "§ rubrique_1", "Conditions", "Article 1 : texte contractuel.",
                                         "Article 2 : clause repliée.", "Voir l'aide [→ /index.php?page=commun.Aide#aide].",
                                         "§ rubrique_2", "Pré-requis", "Point A", "Point B", "[image : Navigateurs (/i/n.png)]"])
        for jeton in ("sid", "PRADO", "999", "v="):
            self.assertNotIn(jeton, a, "aucun jeton ni paramètre de session dans la copie canonique")

    def test_changements_reels_detectes(self):
        base = canon(PAGE.format(n=1))
        for avant, apres in (("texte&nbsp;contractuel", "texte contractuel modifié"),         # mot
                             ("clause repliée", "clause repliée étendue"),                     # clause masquée
                             ("page=commun.Aide", "page=commun.AutreAide"),                    # cible de lien
                             ('alt="Navigateurs"', 'alt="Navigateurs et versions"'),           # image
                             ('id="rubrique_2"', 'id="rubrique_3"'),                           # rubrique
                             ("<li>Point A</li>", "")):                                        # suppression
            self.assertNotEqual(cg_texte.empreinte(base), cg_texte.empreinte(canon(PAGE.format(n=1).replace(avant, apres))), apres or avant)

    def test_differences_lisibles(self):
        a = canon(PAGE.format(n=1))
        b = canon(PAGE.format(n=1).replace("clause repliée", "clause repliée étendue"))
        d = cg_texte.differences(a, b)
        self.assertIn("-Article 2 : clause repliée.", d)
        self.assertIn("+Article 2 : clause repliée étendue.", d)

    def test_structure_inconnue_refusee(self):
        cas = {"absente": PAGE.replace('id="main-part"', 'id="contenu"'),
               "ambiguë (2)": PAGE.replace("<h1>", '<div id="main-part" class="main-part"></div><h1>'),
               "forme inattendue": PAGE.replace('class="main-part"', 'class="autre"'),
               "sans texte": '<div id="main-part" class="main-part"><script>x</script></div>'}
        for motif, page in cas.items():
            with self.assertRaisesRegex(cg_texte.ExtractionRefusee, motif.split(" ")[0]):
                canon(page.format(n=1) if "{n}" in page else page)

    def test_balise_non_fermee_ne_masque_pas_la_suite(self):
        p = '<div id="main-part" class="main-part"><select><option>x<option>y</select><p>Clause visible</p></div>'
        self.assertEqual(canon(p), "x\ny\nClause visible")


class TestAlgorithme(unittest.TestCase):
    def test_validation_algorithme_anterieur_refusee_sans_migration(self):
        maint = datetime.datetime.now(datetime.timezone.utc)
        le = maint.strftime("%Y-%m-%dT%H:%M:%SZ")
        d = {"ao_id": "x", "ref": "1", "org": "o", "etat": "cg_validees", "demande_le": le, "__version": 5,
             "cg": {"texte": "t", "lien": "l", "empreinte": "e"}, "validation": {"phrase": PHRASE, "empreinte": "e", "par": "p", "le": le}}
        p = cycle.planifier({"x": d}, {"x"}, "r1", maint)
        self.assertEqual(p["actions"], [], "aucun téléchargement")
        w = p["ecritures"][0]
        self.assertEqual((w["data"]["etat"], w["data"]["erreur"]["code"], w["if_version"]), ("echec", "cg_algo", 5))
        self.assertIn("équivalence du consentement n'est pas prouvée", w["data"]["erreur"]["motif"])
        self.assertNotIn("validation", w["data"], "la validation humaine n'est ni effacée ni réécrite")


class TestParcoursFictif(unittest.TestCase):
    """Chromium réel contre le portail FICTIF ; la validation est écrite par le TEST, comme le ferait un humain dans EAIOS."""
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.racine = os.path.join(self.d, "racine")
        os.makedirs(self.racine)
        self.srv, self.etat = portail_fictif.demarrer()
        self.addCleanup(self.srv.shutdown)
        self.etat.lien_cg, self.etat.zip_date = "/cgu.html", (2020, 1, 1, 0, 0, 0)
        self.cfg = os.path.join(self.d, "config.json")
        json.dump({"base_url": f"http://127.0.0.1:{self.srv.server_address[1]}/index.php", "hote_autorise": "127.0.0.1"}, open(self.cfg, "w"))

    def ouvrir(self):
        e = os.path.join(self.d, "etat_o.json")
        code, _, err = cli("ouvrir", "--ref", "R-FICTIF-1", "--org", "orgfictif", "--config", self.cfg, "--etat", e, env={"DCE_RACINE_TRAVAIL": self.racine})
        return code, json.load(open(e)), err

    def telecharger(self, cg):
        v = os.path.join(self.d, "validation.json")
        le = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        json.dump({"ref": "R-FICTIF-1", "org": "orgfictif", "phrase": PHRASE, "empreinte": cg["empreinte"], "par": "testeur", "le": le,
                   "cg": {k: cg[k] for k in ("texte", "lien", "algo", "canonique") if k in cg}}, open(v, "w"))
        e = os.path.join(self.d, "etat_t.json")
        code, _, err = cli("telecharger", "--ref", "R-FICTIF-1", "--org", "orgfictif", "--config", self.cfg, "--etat", e, "--validation", v,
                           "--sortie", os.path.join(self.d, "sortie"), env={**ENV_FICTIF, "DCE_RACINE_TRAVAIL": self.racine})
        return code, json.load(open(e)), err

    def test_variations_techniques_acceptees(self):
        self.etat.cg_bandeau = "05/10/2026 13:24:00"
        code, e, err = self.ouvrir()
        self.assertEqual(code, 0, err[-800:])
        cg = e["cg"]
        self.assertEqual(cg["algo"], cg_texte.ALGO)
        self.assertIn("section des conditions #main-part", cg["portee"])
        self.assertIn("Article 3 - Clause repliée", cg["canonique"])
        self.assertNotIn("13:24", cg["canonique"])
        self.etat.cg_bandeau = "05/10/2026 13:26:42"
        code, r, err = self.telecharger(cg)
        self.assertEqual((code, r["etat"]), (0, "pret"), err[-800:])
        self.assertGreaterEqual(self.etat.cg_html_vues, 2, "document relu, avec d'autres octets")

    def test_clause_reelle_modifiee_detectee_et_rapportee(self):
        _, e, _ = self.ouvrir()
        self.etat.cg_clause_repliee = "Article 3 - Clause repliée : les données de connexion sont conservées dix ans."
        code, r, _ = self.telecharger(e["cg"])
        self.assertEqual((code, r["code"]), (2, "cg_modifiees"))
        p = json.load(open(r["preuves"]))
        self.assertEqual((p["doc_identique"], p["libelle_identique"], p["lien_identique"]), (False, True, True))
        self.assertIn("+Article 3 - Clause repliée : les données de connexion sont conservées dix ans.", p["differences"])
        self.assertIn("-Article 3 - Clause repliée : les données de connexion sont conservées un an.", p["differences"])
        self.assertEqual((self.etat.soumis, self.etat.telechargements), ([], []), "rien n'est coché, soumis ni téléchargé")

    def test_section_absente_refus_a_l_ouverture(self):
        self.etat.cg_main_part_html = "<div id='contenu'><p>Conditions</p></div>"
        code, e, _ = self.ouvrir()
        self.assertEqual((code, e["etat"], e["code"]), (2, "echec", "cg_extraction"))
        self.assertNotIn("cg", e, "aucune CG validable sans extraction sûre")

    def test_pdf_toujours_binaire(self):
        self.etat.lien_cg = "/cgu.pdf"
        _, e, _ = self.ouvrir()
        self.assertIn("contenu binaire complet", e["cg"]["portee"])
        self.assertNotIn("canonique", e["cg"])
        self.etat.cg_doc = self.etat.cg_doc.replace(b"v1", b"v2")
        code, r, _ = self.telecharger(e["cg"])
        self.assertEqual((code, r["code"]), (2, "cg_modifiees"))


if __name__ == "__main__":
    unittest.main()

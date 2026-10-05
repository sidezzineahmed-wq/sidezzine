"""Copie canonique des CG servies en HTML (section unique div#main-part.main-part, algorithme cg_texte.ALGO) — HORS RÉSEAU.
Démontre : variations TECHNIQUES ignorées (bandeau date/heure hors section, état PRADO, PHPSESSID, scripts, styles,
commentaires, titre de page) ; changements RÉELS détectés (texte, clause repliée, et dans les URL : document, revision,
lang, schéma, hôte, port, chemin, ancre, version d'image) et rapportés ligne à ligne ; aucune valeur de paramètre secret ;
structure attendue exigée (rubrique_1, rubrique_2, titres observés) ; décodage strict ; PDF toujours haché en binaire ;
validation d'un algorithme antérieur refusée sans migration."""
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

LIEN = "https://www.exemple.ma/index.php?page=commun.Document&amp;document=cgu&amp;revision=2&amp;lang=fr&amp;PHPSESSID={n}#art3"
PAGE = """<!doctype html><html><head><title>T {n}</title><script>var x="{n}";</script></head><body>
<div id="bandeau">Nous sommes le {n}</div><!-- {n} --><form><input type="hidden" name="PRADO_PAGESTATE" value="{n}">
<div id="main-part" class="main-part" data-x="{n}"><style>p{{margin:{n}px}}</style><h1>Conditions d’utilisation</h1>
<div id="rubrique_1"><h2>Conditions d'utilisation</h2><p style="x:{n}">Article 1 : texte&nbsp;contractuel.</p>
<div style="display:none"><p>Article 2 : clause repliée.</p></div>
<p>Voir <a href="LIEN">le document</a>.</p></div>
<div id="rubrique_2"><h2>Pré-requis techniques</h2><ul><li>Point A</li><li>Point&#160;B</li></ul><img src="/i/n.png?v=7" alt="Navigateurs"></div>
</div></form></body></html>""".replace("LIEN", LIEN)


def canon(page):
    return cg_texte.canonique(page)


def p(n=1, **remplacements):
    x = PAGE.format(n=n)
    for a, b in remplacements.items():
        x = x.replace(a, b)
    return x


class TestCanonique(unittest.TestCase):
    def test_contenu_integral_et_variations_techniques_ignorees(self):
        a, b = canon(p("05/10/2026 13:24:01")), canon(p("999"))
        self.assertEqual(a, b, "bandeau hors section, état PRADO, PHPSESSID, attributs, scripts, commentaires : ignorés")
        self.assertEqual(a.split("\n"), [
            "Conditions d’utilisation", "§ rubrique_1", "Conditions d'utilisation", "Article 1 : texte contractuel.",
            "Article 2 : clause repliée.",
            "Voir le document [→ https://www.exemple.ma/index.php?page=commun.Document&document=cgu&revision=2&lang=fr#art3].",
            "§ rubrique_2", "Pré-requis techniques", "Point A", "Point B", "[image : Navigateurs (/i/n.png?v=7)]"])
        self.assertNotIn("PHPSESSID", a)
        self.assertNotIn("999", a)

    def test_changements_reels_detectes(self):
        base = cg_texte.empreinte(canon(p()))
        cas = {"mot": ("texte&nbsp;contractuel", "texte contractuel modifié"), "clause repliée": ("clause repliée", "clause repliée étendue"),
               "document": ("document=cgu", "document=cgu2"), "revision": ("revision=2", "revision=3"), "lang": ("lang=fr", "lang=ar"),
               "schéma": ("https://", "http://"), "port": ("www.exemple.ma/", "www.exemple.ma:8443/"), "hôte": ("www.exemple.ma", "autre.exemple.ma"),
               "chemin": ("/index.php", "/v2/index.php"), "ancre": ("#art3", "#art4"), "image v": ("?v=7", "?v=8"),
               "image alt": ('alt="Navigateurs"', 'alt="Navigateurs et versions"'), "paramètre ajouté": ("lang=fr", "lang=fr&amp;annexe=1"),
               "suppression": ("<li>Point A</li>", "")}
        for nom, (a, b) in cas.items():
            self.assertNotEqual(base, cg_texte.empreinte(canon(p(**{a: b}))), nom)

    def test_differences_lisibles(self):
        d = cg_texte.differences(canon(p()), canon(p(**{"revision=2": "revision=3"})))
        self.assertIn("+Voir le document [→ https://www.exemple.ma/index.php?page=commun.Document&document=cgu&revision=3&lang=fr#art3].", d)

    def test_balise_non_fermee_ne_masque_pas_la_suite(self):
        x = p(**{"<ul>": "<select><option>x<option>y</select><ul>"})
        self.assertIn("x\ny\nPoint A", canon(x))


class TestCible(unittest.TestCase):
    def test_techniques_retires_seulement(self):
        self.assertEqual(cg_texte.cible("/a;jsessionid=XYZ/b.php?PHPSESSID=1&PRADO_PAGESTATE=2&v=3&lang=fr#x"), "/a/b.php?v=3&lang=fr#x")

    def test_parametre_secret_empreinte_sans_valeur(self):
        a = cg_texte.cible("/doc?document=cgu&token=ABCDEF123&csrf_key=QWERTY")
        self.assertNotIn("ABCDEF123", a)
        self.assertNotIn("QWERTY", a)
        self.assertIn("document=cgu&token=#empreinte:", a)
        self.assertNotEqual(a, cg_texte.cible("/doc?document=cgu&token=AUTRE&csrf_key=QWERTY"), "valeur changée : détectée")

    def test_identifiants_dans_l_url_empreinte_sans_valeur(self):
        a = cg_texte.cible("https://agent:MotDePasse@h.ma/doc")
        self.assertNotIn("MotDePasse", a)
        self.assertTrue(a.startswith("https://#empreinte:") and a.endswith("@h.ma/doc"), a)
        self.assertNotEqual(a, cg_texte.cible("https://agent:Autre@h.ma/doc"))

    def test_javascript_et_mailto(self):
        self.assertTrue(cg_texte.cible("javascript:ouvrir('s3cr3t')").startswith("javascript:#empreinte:"))
        self.assertNotIn("s3cr3t", cg_texte.cible("javascript:ouvrir('s3cr3t')"))
        self.assertEqual(cg_texte.cible("mailto:support@exemple.ma"), "mailto:support@exemple.ma")


class TestStructure(unittest.TestCase):
    def refus(self, page, motif):
        with self.assertRaisesRegex(cg_texte.ExtractionRefusee, motif):
            canon(page)

    def test_section_absente_ambigue_ou_autre_forme(self):
        self.refus(p(**{'id="main-part"': 'id="contenu"'}), "absente")
        self.refus(p(**{"<h1>": '<div id="main-part" class="main-part"></div><h1>'}), "ambiguë")
        self.refus(p(**{'class="main-part"': 'class="autre"'}), "forme inattendue")

    def test_page_d_erreur_dans_main_part(self):
        self.refus('<html><body><div id="main-part" class="main-part"><p>Erreur : session expirée.</p></div></body></html>', "rubrique_1 absente")

    def test_rubriques_manquantes_doublees_ou_desordonnees(self):
        self.refus(p(**{'id="rubrique_2"': 'id="autre"'}), "rubrique_2 absente")
        self.refus(p(**{"<ul>": '<div id="rubrique_1">x</div><ul>'}), "rubrique_1 en double")
        x = p().replace('id="rubrique_1"', 'id="TMP"').replace('id="rubrique_2"', 'id="rubrique_1"').replace('id="TMP"', 'id="rubrique_2"')
        self.refus(x, "rubrique_2 avant rubrique_1")

    def test_titres_attendus(self):
        self.refus(p(**{"<h2>Pré-requis techniques</h2>": "<h2>Prérequis</h2>"}), "Pré-requis techniques")
        self.refus(p(**{"<h1>Conditions d’utilisation</h1>": "", "<h2>Conditions d'utilisation</h2>": "<h2>Conditions</h2>"}), "Conditions d'utilisation")

    def test_rubrique_sans_contenu(self):
        self.refus(p(**{"<ul><li>Point A</li><li>Point&#160;B</li></ul><img src=\"/i/n.png?v=7\" alt=\"Navigateurs\">": ""}), "rubrique_2 sans contenu")

    def test_section_non_fermee(self):
        self.refus(p().replace("</div>\n</div></form>", "</div></form>"), "non fermée")


class TestDecodage(unittest.TestCase):
    def test_utf8_declare_ok(self):
        self.assertIn("Pré-requis", cg_texte.decoder(p().encode(), "text/html; charset=UTF-8"))

    def test_meta_seule_ok_et_latin1_correct(self):
        x = p(**{"<head>": '<head><meta charset="iso-8859-1">', "’": "'"}).encode("latin-1")
        self.assertIn("Pré-requis", cg_texte.decoder(x, "text/html"))

    def test_octets_invalides_refuses(self):
        with self.assertRaisesRegex(cg_texte.ExtractionRefusee, "octets invalides"):
            cg_texte.decoder(p(**{"’": "'"}).encode("latin-1"), "text/html; charset=utf-8")

    def test_encodage_inconnu_absent_ou_contradictoire_refuse(self):
        with self.assertRaisesRegex(cg_texte.ExtractionRefusee, "inconnu"):
            cg_texte.decoder(p().encode(), "text/html; charset=x-inconnu")
        with self.assertRaisesRegex(cg_texte.ExtractionRefusee, "non déclaré"):
            cg_texte.decoder(p().encode(), "text/html")
        with self.assertRaisesRegex(cg_texte.ExtractionRefusee, "contradictoires"):
            cg_texte.decoder(p(**{"<head>": '<head><meta charset="iso-8859-1">'}).encode(), "text/html; charset=utf-8")

    def test_document_tronque_refuse(self):
        with self.assertRaisesRegex(cg_texte.ExtractionRefusee, "tronqué"):
            cg_texte.decoder(p().encode()[:-200], "text/html; charset=utf-8")


class TestAlgorithme(unittest.TestCase):
    def test_validation_algorithme_anterieur_refusee_sans_migration(self):
        maint = datetime.datetime.now(datetime.timezone.utc)
        le = maint.strftime("%Y-%m-%dT%H:%M:%SZ")
        for algo in (None, "cg-v2"):
            cg = {"texte": "t", "lien": "l", "empreinte": "e", **({"algo": algo} if algo else {})}
            d = {"ao_id": "x", "ref": "1", "org": "o", "etat": "cg_validees", "demande_le": le, "__version": 5, "cg": cg,
                 "validation": {"phrase": PHRASE, "empreinte": "e", "par": "p", "le": le}}
            pl = cycle.planifier({"x": d}, {"x"}, "r1", maint)
            self.assertEqual(pl["actions"], [], "aucun téléchargement")
            w = pl["ecritures"][0]
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
        with open(self.cfg, "w") as f:
            json.dump({"base_url": f"http://127.0.0.1:{self.srv.server_address[1]}/index.php", "hote_autorise": "127.0.0.1"}, f)

    def ouvrir(self):
        e = os.path.join(self.d, "etat_o.json")
        code, _, err = cli("ouvrir", "--ref", "R-FICTIF-1", "--org", "orgfictif", "--config", self.cfg, "--etat", e, env={"DCE_RACINE_TRAVAIL": self.racine})
        with open(e) as f:
            return code, json.load(f), err

    def telecharger(self, cg):
        v = os.path.join(self.d, "validation.json")
        le = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(v, "w") as f:
            json.dump({"ref": "R-FICTIF-1", "org": "orgfictif", "phrase": PHRASE, "empreinte": cg["empreinte"], "par": "testeur", "le": le,
                       "cg": {k: cg[k] for k in ("texte", "lien", "algo", "canonique") if k in cg}}, f)
        e = os.path.join(self.d, "etat_t.json")
        code, _, err = cli("telecharger", "--ref", "R-FICTIF-1", "--org", "orgfictif", "--config", self.cfg, "--etat", e, "--validation", v,
                           "--sortie", os.path.join(self.d, "sortie"), env={**ENV_FICTIF, "DCE_RACINE_TRAVAIL": self.racine})
        with open(e) as f:
            return code, json.load(f), err

    def test_variations_techniques_acceptees(self):
        self.etat.cg_bandeau = "05/10/2026 13:24:00"
        code, e, err = self.ouvrir()
        self.assertEqual(code, 0, err[-800:])
        cg = e["cg"]
        self.assertEqual(cg["algo"], cg_texte.ALGO)
        self.assertIn("section des conditions #main-part", cg["portee"])
        self.assertIn("Article 3 - Clause repliée", cg["canonique"])
        self.assertIn("revision=2&lang=fr#art3", cg["canonique"])
        self.assertNotIn("13:24", cg["canonique"])
        self.assertNotIn("PHPSESSID", cg["canonique"])
        self.etat.cg_bandeau = "05/10/2026 13:26:42"
        code, r, err = self.telecharger(cg)
        self.assertEqual((code, r["etat"]), (0, "pret"), err[-800:])
        self.assertGreaterEqual(self.etat.cg_html_vues, 2, "document relu, avec d'autres octets")

    def test_clause_reelle_modifiee_detectee_et_rapportee(self):
        _, e, _ = self.ouvrir()
        self.etat.cg_clause_repliee = "Article 3 - Clause repliée : les données de connexion sont conservées dix ans."
        code, r, _ = self.telecharger(e["cg"])
        self.assertEqual((code, r["code"]), (2, "cg_modifiees"))
        with open(r["preuves"]) as f:
            pr = json.load(f)
        self.assertEqual((pr["doc_identique"], pr["libelle_identique"], pr["lien_identique"]), (False, True, True))
        self.assertIn("+Article 3 - Clause repliée : les données de connexion sont conservées dix ans.", pr["differences"])
        self.assertIn("-Article 3 - Clause repliée : les données de connexion sont conservées un an.", pr["differences"])
        self.assertEqual((self.etat.soumis, self.etat.telechargements), ([], []), "rien n'est coché, soumis ni téléchargé")

    def test_revision_du_document_lie_detectee(self):
        _, e, _ = self.ouvrir()
        self.etat.cg_lien_doc = self.etat.cg_lien_doc.replace("revision=2", "revision=3")
        code, r, _ = self.telecharger(e["cg"])
        self.assertEqual((code, r["code"]), (2, "cg_modifiees"))
        self.assertEqual((self.etat.soumis, self.etat.telechargements), ([], []))

    def test_section_absente_ou_page_erreur_refus_a_l_ouverture(self):
        for html in ("<div id='contenu'><p>Conditions</p></div>", "<div id='main-part' class='main-part'><p>Erreur technique.</p></div>"):
            self.etat.cg_main_part_html = html
            code, e, _ = self.ouvrir()
            self.assertEqual((code, e["etat"], e["code"]), (2, "echec", "cg_extraction"), html)
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

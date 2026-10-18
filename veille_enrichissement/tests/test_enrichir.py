"""Tests hors ligne de enrichir_pmmp.py sur des extraits RÉELS du portail PMMP (rappels PRADO, formulaire, fiche)."""
import copy
import json
import os
import re
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
import enrichir_pmmp as E  # noqa: E402

FX = os.path.join(ICI, "fixtures")
lire = lambda n: open(os.path.join(FX, n), encoding="utf-8").read()
RAPPELS = {c: lire(f"rappel_classification_{c}.html") for c in "0123"}


def releve(par_entite=None, controle=None):
    pe, ctl = E.entites_par_classification(RAPPELS)
    return {"debut": "2026-10-17T23:55:00+00:00", "fin": "2026-10-17T23:58:00+00:00", "url": E.URL_RECHERCHE, "methode": "test",
            "par_entite": pe if par_entite is None else par_entite, "controle_listes": ctl if controle is None else controle,
            "controle_recherche": {"totaux": {"toutes": {"total": 4419}, "1": {"total": 3443}, "2": {"total": 964}, "3": {"total": 12}},
                                   "somme_classes": 4419, "partition_totaux": True},
            "procedures_formulaire": {"champ": "ctl0$CONTENU_PAGE$AdvancedSearch$procedureType",
                                      "codes": E.procedures_formulaire(lire("formulaire_procedureType.html"))}}


def item(o, r, ref, proc="Appel d'offres ouvert"):
    return {"r": r, "o": o, "ref": ref, "proc": proc, "lim": "2026-11-20", "mo": "X"}


def fiche(o, r, ref, mode, lu_le, proc="Appel d'offres ouvert"):
    return {"id": f"pmmp:{o}:{r}", "lu_le": lu_le, "run": "run-" + lu_le[:10], "sha256_html_tronque": "ab" * 32,
            "champs": {"ref": ref, "proc": proc, "mode_passation": mode}}


class Classification(unittest.TestCase):
    def test_partition_officielle_reelle(self):
        pe, ctl = E.entites_par_classification(RAPPELS)
        self.assertTrue(ctl["partition_exacte"])
        self.assertEqual(ctl["par_classification"], {"1": 57, "2": 16, "3": 4})
        self.assertEqual(ctl["entites_toutes"], 77)
        self.assertEqual(pe["g3h"]["libelle"], "Etat")             # Ministère de l'intérieur : Etat (classification PMMP de l'entité)
        self.assertEqual(pe["j0w"]["libelle"], "Collectivité locale")  # Région Marrakech-Safi
        self.assertEqual(pe["w6x"]["libelle"], "Etablissement public")  # CDG
        self.assertEqual(pe["y6u"]["code"], "3")                    # Chambre des représentants : EEP selon PMMP (pas de déduction par le nom)

    def test_entite_dans_deux_listes_ambigue_donc_inconnue(self):
        r = dict(RAPPELS)
        r["2"] = re.sub(r'(<select[^>]*\$organismesNames"[^>]*>)', r'\1<option value="g3h">Ministère</option>', r["2"])
        pe, ctl = E.entites_par_classification(r)
        self.assertNotIn("g3h", pe)
        self.assertIn("g3h", ctl["ambigues"])
        self.assertFalse(ctl["partition_exacte"])

    def test_entite_absente_des_classes_inconnue(self):
        r = dict(RAPPELS)
        r["3"] = re.sub(r'<option value="w6x">[^<]*</option>', "", r["3"])
        pe, ctl = E.entites_par_classification(r)
        self.assertNotIn("w6x", pe)
        self.assertEqual(ctl["sans_classification"], ["w6x"])

    def test_rappel_incoherent_refuse(self):
        r = dict(RAPPELS)
        r["2"] = RAPPELS["1"]
        with self.assertRaises(ValueError):
            E.entites_par_classification(r)

    def test_heritage_par_entite_et_inconnue(self):
        cat = {"maj": "m", "items": [item("g3h", "1", "A"), item("j0w", "2", "B"), item("zzz", "3", "C")]}
        out = E.construire(cat, releve(), {}, [], None, "sha")
        cv = out["classification"]["couverture"]
        self.assertEqual(cv["par_code"], {"1": 1, "2": 1, "inconnu": 1})
        self.assertEqual(cv["entites_inconnues"], ["zzz"])


class ModePassation(unittest.TestCase):
    def test_fiche_reelle_mode_distinct_de_la_procedure(self):
        sys.path.insert(0, os.environ.get("KIT_VEILLE", ""))
        try:
            from veille.pmmp_fiche import lire_fiche  # kit du collecteur, si disponible
        except Exception:
            self.skipTest("kit collecteur absent (KIT_VEILLE)")
        f = lire_fiche(lire("fiche_1041301_o8p_sans_contact.html"))
        self.assertEqual(f["proc"], "Appel d'offres ouvert")
        self.assertEqual(f["mode_passation"], "Sur offre de prix")

    def test_element_modePassation_present_dans_la_fiche_reelle(self):
        h = lire("fiche_1041301_o8p_sans_contact.html")
        self.assertIn('id="ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_modePassation"> | Sur offre de prix', h)
        self.assertIn(">Appel d'offres ouvert</span>", h)

    def test_codes_procedure_formulaire_reels(self):
        c = E.procedures_formulaire(lire("formulaire_procedureType.html"))
        self.assertEqual(c["Appel d'offres ouvert"], "1")
        self.assertEqual(c["Appel d'offres ouvert simplifié"], "50")
        self.assertEqual(len(c), 28)
        self.assertNotIn("Sur offre de prix", c)  # les modes ne sont pas des procédures

    def test_inconnu_jamais_par_defaut(self):
        cat = {"maj": "m", "items": [item("g3h", "1", "A"), item("g3h", "2", "B")]}
        out = E.construire(cat, releve(), {"pmmp:g3h:1": fiche("g3h", "1", "A", "Au rabais / majoration", "2026-10-10T10:00:00+00:00")}, [], None, "s")
        m = out["mode_passation"]
        self.assertEqual(m["couverture"]["connues"], 1)
        self.assertEqual(m["couverture"]["inconnues"], 1)
        self.assertNotIn("pmmp:g3h:2", m["par_id"])
        self.assertEqual(m["par_id"]["pmmp:g3h:1"]["v"], "Au rabais / majoration")
        self.assertEqual(m["par_id"]["pmmp:g3h:1"]["source"], "collecteur")
        self.assertEqual(m["par_id"]["pmmp:g3h:1"]["lu_le"], "2026-10-10T10:00:00+00:00")

    def test_valeur_vide_ignoree(self):
        cat = {"maj": "m", "items": [item("g3h", "1", "A")]}
        out = E.construire(cat, releve(), {"pmmp:g3h:1": fiche("g3h", "1", "A", None, "2026-10-10T10:00:00+00:00")}, [], None, "s")
        self.assertEqual(out["mode_passation"]["par_id"], {})

    def test_reference_discordante_non_jointe(self):
        cat = {"maj": "m", "items": [item("g3h", "1", "A-2")]}
        out = E.construire(cat, releve(), {"pmmp:g3h:1": fiche("g3h", "1", "A", "Sur offre de prix", "2026-10-10T10:00:00+00:00")}, [], None, "s")
        self.assertEqual(out["mode_passation"]["couverture"]["connues"], 0)
        self.assertEqual(out["mode_passation"]["couverture"]["reference_discordante"], ["pmmp:g3h:1"])
        self.assertIn("pmmp:g3h:1", out["mode_passation"]["par_id"])  # conservée, mais non utilisée

    def test_plus_recente_gagne_et_sources_conservees(self):
        cat = {"maj": "m", "items": [item("g3h", "1", "A")]}
        comp = [{"id": "pmmp:g3h:1", "lu_le": "2026-10-18T00:00:00+00:00", "mode_passation": "Sur offre de prix", "proc": "Appel d'offres ouvert",
                 "ref": "A", "url": "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1&orgAcronyme=g3h",
                 "sha256_html_tronque": "cd" * 32}]
        out = E.construire(cat, releve(), {"pmmp:g3h:1": fiche("g3h", "1", "A", "Au rabais / majoration", "2026-10-10T10:00:00+00:00")}, comp, None, "s")
        r = out["mode_passation"]["par_id"]["pmmp:g3h:1"]
        self.assertEqual((r["v"], r["source"], r["lu_le"]), ("Sur offre de prix", "complement_eaios", "2026-10-18T00:00:00+00:00"))
        self.assertTrue(r["url"].startswith("https://www.marchespublics.gov.ma/"))
        self.assertEqual(r["sha256_html_tronque"], "cd" * 32)


class Reprise(unittest.TestCase):
    def test_idempotent_et_sans_perte(self):
        cat = {"maj": "m", "items": [item("g3h", "1", "A"), item("j0w", "2", "B")]}
        F = {"pmmp:g3h:1": fiche("g3h", "1", "A", "Sur offre de prix", "2026-10-10T10:00:00+00:00"),
             "pmmp:j0w:2": fiche("j0w", "2", "B", "Au rabais / majoration", "2026-10-11T10:00:00+00:00")}
        a = E.construire(cat, releve(), F, [], None, "s")
        b = E.construire(cat, releve(), F, [], copy.deepcopy(a), "s")
        self.assertEqual(E.octets_json(a), E.octets_json(b))
        # passage suivant : le collecteur n'a plus la fiche j0w:2 (rotation) et l'annonce n'est plus au catalogue
        cat2 = {"maj": "m2", "items": [item("g3h", "1", "A")]}
        c = E.construire(cat2, releve(), {"pmmp:g3h:1": F["pmmp:g3h:1"]}, [], copy.deepcopy(b), "s2")
        self.assertIn("pmmp:j0w:2", c["mode_passation"]["par_id"])  # rien n'est perdu
        self.assertEqual(c["mode_passation"]["couverture"]["lues_hors_catalogue_conservees"], 1)
        # une lecture plus ANCIENNE ne remplace pas
        vieux = fiche("g3h", "1", "A", "Au rabais / majoration", "2026-10-01T10:00:00+00:00")
        d = E.construire(cat2, releve(), {"pmmp:g3h:1": vieux}, [], copy.deepcopy(c), "s2")
        self.assertEqual(d["mode_passation"]["par_id"]["pmmp:g3h:1"]["v"], "Sur offre de prix")

    def test_cli_refuse_releve_non_verifie_et_ecrit_seulement_la_sortie(self):
        with tempfile.TemporaryDirectory() as t:
            cat = {"maj": "m", "items": [item("g3h", "1", "A")]}
            pc = os.path.join(t, "catalogue.json")
            json.dump(cat, open(pc, "w"))
            r = releve()
            r["controle_recherche"]["partition_totaux"] = False
            pr = os.path.join(t, "releve.json")
            json.dump(r, open(pr, "w"))
            avant = sorted(os.listdir(t))
            self.assertEqual(E.main(["construire", "--catalogue", pc, "--releve", pr, "--sortie", os.path.join(t, "o.json")]), 2)
            self.assertEqual(sorted(os.listdir(t)), avant)
            r["controle_recherche"]["partition_totaux"] = True
            json.dump(r, open(pr, "w"))
            octets = open(pc, "rb").read()
            self.assertEqual(E.main(["construire", "--catalogue", pc, "--releve", pr, "--sortie", os.path.join(t, "o.json")]), 0)
            self.assertEqual(open(pc, "rb").read(), octets)  # catalogue jamais modifié
            o = json.load(open(os.path.join(t, "o.json")))
            self.assertEqual(o["classification"]["couverture"]["par_code"], {"1": 1})


if __name__ == "__main__":
    unittest.main()

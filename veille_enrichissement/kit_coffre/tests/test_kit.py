"""Tests isolés : aucun accès réseau (le client HTTP est remplacé par un faux qui lève une erreur)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)

import construire_catalogue as cc  # noqa: E402
import maj_quotidienne as mq  # noqa: E402
from veille import client as client_mod  # noqa: E402
from veille.etat import Etat  # noqa: E402
from veille.html_outils import masquer_coordonnees, montant  # noqa: E402
from veille.pmmp_fiche import fiche_valide, lire_fiche, lire_qualification, tronquer_contact  # noqa: E402
from veille.pmmp_listing import lignes, lire_ligne, total_et_pages  # noqa: E402
from veille.schema import CHAMPS, make_id, split_id, valider_catalogue, valider_item  # noqa: E402


def lire(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def fx(nom):
    return lire(os.path.join(ICI, "fixtures", nom))


REG, PROV, ALIAS = mq.charger_ref()


class PasDeReseau(unittest.TestCase):
    def test_requests_interdit_pendant_les_tests(self):
        self.assertTrue(client_mod.requests.Session.request.__name__ == "_interdit")


def _interdit(*a, **k):
    raise AssertionError("accès réseau interdit dans les tests")


client_mod.requests.Session.request = _interdit


class TestIds(unittest.TestCase):
    def test_format(self):
        self.assertEqual(make_id("o8p", "1041301"), "pmmp:o8p:1041301")
        self.assertEqual(split_id("pmmp:o8p:1041301"), ("o8p", "1041301"))
        for o, r in [("O8P", "1"), ("o8p", "12a"), ("", "1041301"), ("o8p", "")]:
            with self.assertRaises(ValueError):
                make_id(o, r)

    def test_debit_minimum(self):
        with self.assertRaises(ValueError):
            client_mod.ClientPMMP(delai_min=1.0)


class TestListing(unittest.TestCase):
    def setUp(self):
        self.h = fx("listing_extrait.html")
        self.L = {x["r"]: x for x in (lire_ligne(rw, PROV, ALIAS) for rw in lignes(self.h))}

    def test_compteurs(self):
        self.assertEqual(total_et_pages(self.h), {"total": 3796, "pages": 8, "page": 1, "taille_page": 500})
        self.assertEqual(len(self.L), 5)

    def test_ligne_simple(self):
        x = self.L["1040952"]
        self.assertEqual((x["o"], x["ref"], x["cat"], x["proc"], x["pub"], x["lim"], x["h"]),
                         ("d4q", "81/2026/DR9", "Travaux", "Appel d'offres ouvert", "2026-09-18", "2026-11-25", "10:00"))
        self.assertEqual(x["mo"], "OFFICE NATIONAL DE L'ELECTRICITE ET DE L'EAU POTABLE - BRANCHE EAU")
        self.assertEqual((x["lx"], x["etr"], x["nat"], x["lots"], x["env"]), (["TANGER-ASSILAH"], [], False, False, True))

    def test_nat_lots_alias(self):
        self.assertTrue(self.L["1039331"]["nat"])
        self.assertEqual(self.L["1039331"]["lx"], ["TETOUAN", "FAHS-ANJRA"])
        self.assertTrue(self.L["1038578"]["lots"])
        self.assertFalse(self.L["1038578"]["env"])
        self.assertEqual(self.L["1039794"]["lx"], ["ES-SEMARA"])  # alias constaté
        self.assertEqual(self.L["1039794"]["etr"], [])


class TestFiche(unittest.TestCase):
    def test_fiche_reelle(self):
        h, coupe = tronquer_contact(fx("fiche_1041301_o8p_sans_contact.html"))
        f = lire_fiche(h)
        self.assertTrue(fiche_valide(f))
        self.assertEqual((f["ref"], f["lim"], f["h"], f["est"], f["tp"], f["cau"], f["var"], f["allot"]),
                         ("SK04/2026/CFR", "2026-11-20", "13:00", 21446884.14, False, 428000.0, False, None))
        self.assertEqual(len(f["q"]), 3)
        self.assertEqual(f["q"][0], {"m": "Equipement", "s": "B", "sl": "Travaux routiers et voirie urbaine", "q": "B.3",
                                     "ql": "Ouvrages d'assainissement routiers et traitement de l'environnement", "c": "2"})
        self.assertIsNone(f["ag"]); self.assertIsNone(f["vis"]); self.assertIsNone(f["reu"]); self.assertIsNone(f["proto"])
        self.assertEqual(f["dep"], "la Caisse pour le Financement Routier")

    def test_contact_jamais_conserve(self):
        faux = ('<div id="ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_panelContcatAdministratif" class="line">'
                '<div>Contact Administratif : </div><span>Agent Fictif</span> fictif@example.org 0600000000</div>')
        h = fx("fiche_1041301_o8p_sans_contact.html").replace("</body>", faux + "</body>")
        t, coupe = tronquer_contact(h)
        self.assertTrue(coupe)
        self.assertNotIn("fictif@example.org", t)
        self.assertNotIn("Agent Fictif", json.dumps(lire_fiche(t), ensure_ascii=False))

    def test_absent_reste_null(self):
        f = lire_fiche("<html><body>rien</body></html>")
        self.assertFalse(fiche_valide(f))
        self.assertIsNone(f["est"]); self.assertIsNone(f["cau"]); self.assertIsNone(f["tp"]); self.assertEqual(f["q"], [])

    def test_qualif_partielle_sans_invention(self):
        self.assertEqual(lire_qualification("Equipement / Classe 3"),
                         {"m": "Equipement", "s": None, "sl": None, "q": None, "ql": None, "c": "3"})

    def test_outils(self):
        self.assertEqual(montant("21 446 884,14"), 21446884.14)
        self.assertEqual(montant("428 000,00 MAD "), 428000.0)
        self.assertIsNone(montant("-"))
        self.assertNotIn("661", masquer_coordonnees("Visite 20/10/2026 10:00, contact M. X : +212 661 264 193"))
        self.assertIn("20/10/2026 10:00", masquer_coordonnees("Visite 20/10/2026 10:00, contact M. X : +212 661 264 193"))


class TestEtatEtCatalogue(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.etat = Etat(self.d)
        self.rows = [lire_ligne(rw, PROV, ALIAS) for rw in lignes(fx("listing_extrait.html"))]

    def tearDown(self):
        shutil.rmtree(self.d)

    def _couv(self, run, complet, total):
        self.etat.enregistrer_couverture(run, {"run_id": run, "fin": run, "statut": "X" if complet else "PARTIEL",
                                               "listing": {"total_annonce": total, "complete": complet}})

    def test_catalogue_31_champs_et_det(self):
        for x in self.rows:
            self.etat.enregistrer_ligne(x, "2026-10-02T10:00:00+00:00", "r1")
        h, _ = tronquer_contact(fx("fiche_1041301_o8p_sans_contact.html"))
        # fiche d'une consultation présente dans l'état
        x = dict(self.rows[0]); x.update({"r": "1041301", "o": "o8p", "lim": "2026-11-20", "h": "13:00"})
        self.etat.enregistrer_ligne(x, "2026-10-02T10:00:00+00:00", "r1")
        self.etat.enregistrer_fiche("pmmp:o8p:1041301", lire_fiche(h), "2026-10-02T10:05:00+00:00", "r1", "x")
        self._couv("r1", False, 3796)
        cat, rap = cc.construire(self.etat, REG, "2026-10-02")
        self.assertEqual(valider_catalogue(cat, REG), [])
        for it in cat["items"]:
            self.assertEqual(list(it.keys()), CHAMPS)
        det = [i for i in cat["items"] if i["det"]]
        self.assertEqual(len(det), 1)
        self.assertEqual(cat["n_details"], 1)
        nd = [i for i in cat["items"] if not i["det"]][0]
        self.assertTrue(all(nd[k] is None for k in ("est", "tp", "cau", "var", "allot", "ouv", "dep", "proto")))
        self.assertIsNone(nd["cls"])  # aucune passe classification -> null, pas devinée
        self.assertEqual(cat["total_portail"], 3796)

    def test_listing_ne_redate_pas_la_fiche(self):
        x = self.rows[0]
        i = self.etat.enregistrer_ligne(x, "2026-10-01T10:00:00+00:00", "r1")
        f = {"ref": x["ref"], "obj": x["obj"], "lim": "2026-11-11", "h": "10:00"}
        self.etat.enregistrer_fiche(i, f, "2026-10-01T10:01:00+00:00", "r1", "x")
        avant = lire(self.etat.chemin_fiche(i))
        self.etat.enregistrer_ligne(x, "2026-10-02T10:00:00+00:00", "r2")  # listing plus récent : lim 2026-11-25
        self.etat.sauver_listing()
        self.assertEqual(lire(self.etat.chemin_fiche(i)), avant)
        self._couv("r2", False, 3796)
        cat, rap = cc.construire(self.etat, REG, "2026-10-02")
        it = [c for c in cat["items"] if c["r"] == x["r"]][0]
        self.assertEqual(it["lim"], "2026-11-25")  # observation la plus récente
        self.assertTrue(any(a["id"] == i and a["champ"] == "lim" for a in rap["a_relire"]))
        # écart listing/fiche sans changement du listing APRÈS la lecture : pas « changée » (sinon relue à chaque passage)
        choix, stats = mq.choisir_fiches(self.etat, {i}, 5, relire_anciennes=False, aujourd_hui="2026-10-02",
                                         maintenant_iso="2026-10-02T10:30:00+00:00")
        self.assertEqual((choix, stats["file_changees"]), ([], 0))
        # elle reste relisable par l'âge (24 h)
        choix, stats = mq.choisir_fiches(self.etat, {i}, 5, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:30:00+00:00")
        self.assertEqual(stats["categorie"][i], "anciennes")

    def test_pas_de_suppression_sur_collecte_partielle(self):
        for x in self.rows:
            self.etat.enregistrer_ligne(x, "2026-10-01T10:00:00+00:00", "r1")
        self.etat.sauver_listing()
        # 2e passage partiel : une seule ligne revue ; on N'appelle PAS marquer_absents (couverture partielle)
        self.etat.enregistrer_ligne(self.rows[0], "2026-10-02T10:00:00+00:00", "r2")
        self._couv("r2", False, 3796)
        cat, _ = cc.construire(self.etat, REG, "2026-10-02")
        self.assertEqual(cat["n"], 5)
        self.assertTrue(all(e["absences_listing_complet"] == 0 for e in self.etat.listing["items"].values()))

    def test_absence_sur_listing_complet_signalee_non_supprimee(self):
        for x in self.rows:
            self.etat.enregistrer_ligne(x, "2026-10-01T10:00:00+00:00", "r1")
        ids = {make_id(self.rows[0]["o"], self.rows[0]["r"])}
        self.assertEqual(self.etat.marquer_absents_listing_complet(ids, "r2"), 4)
        self._couv("r2", True, 1)
        cat, rap = cc.construire(self.etat, REG, "2026-10-02")
        self.assertEqual(cat["n"], 5)
        self.assertEqual(len(rap["absents_listing_complet_conserves"]), 4)

    def test_date_passee_exclue(self):
        for x in self.rows:
            self.etat.enregistrer_ligne(x, "2026-10-01T10:00:00+00:00", "r1")
        self._couv("r1", False, 3796)
        cat, rap = cc.construire(self.etat, REG, "2030-01-01")
        self.assertEqual(cat["n"], 0)
        self.assertEqual(rap["exclus_date_passee"], 5)
        self.assertEqual(len(self.etat.listing["items"]), 5)  # l'état garde tout

    def test_cls_herite_par_id_null_pour_nouveau(self):
        for x in self.rows:
            self.etat.enregistrer_ligne(x, "2026-10-01T10:00:00+00:00", "r1")
        self._couv("r1", False, 3796)
        connu = make_id(self.rows[0]["o"], self.rows[0]["r"])
        cat, rap = cc.construire(self.etat, REG, "2026-10-02", cls_heritee={connu: "Etat"})
        cls = {f"pmmp:{i['o']}:{i['r']}": i["cls"] for i in cat["items"]}
        self.assertEqual(cls[connu], "Etat")
        self.assertEqual(sum(v is None for v in cls.values()), 4)
        self.assertEqual(rap["sans_cls"], 4)
        self.assertNotIn(connu, rap["ids_cls_inconnu"])

    def test_validateur_refuse(self):
        x = {k: None for k in CHAMPS}
        x.update({"r": "1", "o": "o8p", "lx": [], "etr": [], "nat": False, "lots": False, "det": False, "env": False,
                  "q": [], "dom": [], "est": 12.0})
        self.assertTrue(any("sans fiche" in e for e in valider_item(x)))
        x2 = dict(x); x2["est"] = None; x2["cls"] = "Inconnu"
        self.assertTrue(any("cls" in e for e in valider_item(x2)))


class TestCoffre(unittest.TestCase):
    def test_aller_retour_et_catalogue_valide(self):
        import coffre
        d = tempfile.mkdtemp()
        try:
            etat = Etat(os.path.join(d, "e"))
            rows = [lire_ligne(rw, PROV, ALIAS) for rw in lignes(fx("listing_extrait.html"))]
            for x in rows:
                etat.enregistrer_ligne(x, "2026-10-02T10:00:00+00:00", "r1")
            etat.sauver_listing()
            i = make_id(rows[0]["o"], rows[0]["r"])
            etat.enregistrer_fiche(i, {"ref": "x"}, "2026-10-02T10:01:00+00:00", "r1", "h")
            etat.enregistrer_couverture("r1", {"run_id": "r1", "statut": "PARTIEL", "listing": {"total_annonce": 9, "ids_distincts": 5, "pages_lues": [{"page": 1}]}})
            cat = os.path.join(d, "cat.json")
            with open(cat, "w") as f:
                f.write("{}")
            coffre.pack(etat.d, os.path.join(d, "c1"), cat)
            self.assertFalse(os.path.exists(os.path.join(d, "c1", "stock", "catalogue_valide.json")))  # partiel
            self.assertTrue(coffre.verifier(os.path.join(d, "c1"))["ok"])
            coffre.unpack(os.path.join(d, "c1"), os.path.join(d, "e2"))
            e2 = Etat(os.path.join(d, "e2"))
            self.assertEqual(e2.listing["items"].keys(), etat.listing["items"].keys())
            self.assertEqual(e2.fiche(i)["lu_le"], "2026-10-02T10:01:00+00:00")  # date de lecture conservée
            etat.enregistrer_couverture("r2", {"run_id": "r2", "statut": "LISTING_COMPLET_ANNONCES_DE_CONSULTATION_FENETRE_PAR_DEFAUT",
                                               "listing": {"total_annonce": 5, "ids_distincts": 5, "pages_lues": [{"page": 1}], "complete": True},
                                               "fin": "2026-10-02T10:10:00+00:00",
                                               "fiches": {"lues": [{"id": i, "lu_le": "2026-10-02T10:09:00+00:00"}], "echecs": []}})
            coffre.pack(etat.d, os.path.join(d, "c2"), cat, None, os.path.join(d, "c1"))
            self.assertTrue(os.path.exists(os.path.join(d, "c2", "stock", "catalogue_valide.json")))
            st = json.loads(lire(os.path.join(d, "c2", "stock", "statut.json")))
            self.assertEqual(st["dernier_listing_complet"]["run_id"], "r2")
            self.assertEqual(len(st["historique"]), 2)
            self.assertIn("ne signifie PAS", st["perimetre"])
            self.assertEqual(st["derniere_maj_fiches"]["run_id"], "r2")
            self.assertEqual(st["dernier_succes_listing"]["run_id"], "r2")
            ctl = coffre.controle(os.path.join(d, "c2"), "2026-10-02T10:30:00+00:00")
            self.assertFalse(ctl["alerte"], ctl)
            ctl = coffre.controle(os.path.join(d, "c2"), "2026-10-02T13:00:00+00:00")
            self.assertTrue(ctl["alerte"])
            # statut annoncé complet mais couverture non confirmée -> catalogue_valide inchangé
            os.remove(os.path.join(d, "c2", "stock", "catalogue_valide.json"))
            etat.enregistrer_couverture("r3", {"run_id": "r3", "statut": "LISTING_COMPLET_ANNONCES_DE_CONSULTATION_FENETRE_PAR_DEFAUT",
                                               "listing": {"total_annonce": 6, "ids_distincts": 5, "pages_lues": [{"page": 1}], "complete": False}})
            coffre.pack(etat.d, os.path.join(d, "c3"), cat, None, os.path.join(d, "c2"))
            self.assertFalse(os.path.exists(os.path.join(d, "c3", "stock", "catalogue_valide.json")))
        finally:
            shutil.rmtree(d)


class FauxListing:
    """Simule le portail : chaque appel renvoie une page (total, pages, n° de page, lignes)."""
    def __init__(self, pages):
        self.pages = pages  # liste de (total, nb_pages, ids)
        self.k = 0

    def _h(self, k):
        total, nbp, ids = self.pages[k]
        rows = "".join(f'<tr class=""><input name="x$refCons" value="{r}" /><input name="x$orgCons" value="o8p" />'
                       f'<td headers="cons_dateEnd"><div class="cloture-line"> 01/01/2099<br>10:00 </div></td></tr>' for r in ids)
        return (f'<span id="ctl0_CONTENU_PAGE_resultSearch_nombreElement">{total}</span>'
                f'<span id="ctl0_CONTENU_PAGE_resultSearch_nombrePageTop">{nbp}</span>'
                f'<input name="ctl0$CONTENU_PAGE$resultSearch$numPageTop" type="text" value="{k + 1}" />'
                f'<select name="ctl0$CONTENU_PAGE$resultSearch$listePageSizeTop"><option selected="selected" value="500">500</option></select>'
                + rows)

    def rechercher(self, classification=None):
        return self._h(0), {}

    def taille_500(self, h):
        return self._h(0)

    def page(self, h, n):
        return self._h(n - 1)


class TestPagination(unittest.TestCase):
    def _passe(self, pages):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        etat = Etat(d)
        couv = {}
        mq.passe_listing(FauxListing(pages), etat, "r", PROV, ALIAS, 0, None, False, couv)
        return couv

    def test_nombre_de_pages_dynamique_complet(self):
        c = self._passe([(5, 3, ["101", "102"]), (5, 3, ["103", "104"]), (5, 3, ["105"])])
        self.assertTrue(c["complete"]); self.assertEqual(c["pages_annoncees"], 3); self.assertEqual(len(c["pages_lues"]), 3)

    def test_changement_pendant_le_parcours_partiel(self):
        c = self._passe([(5, 3, ["101", "102"]), (6, 3, ["103", "104"]), (6, 3, ["105", "106"])])
        self.assertFalse(c["complete"]); self.assertFalse(c["stable"])
        self.assertTrue(any("modifié" in r for r in c["raisons_incomplet"]))

    def test_page_supplementaire_annoncee_lue_mais_partiel(self):
        c = self._passe([(5, 2, ["101", "102", "103"]), (7, 3, ["104", "105"]), (7, 3, ["106", "107"])])
        self.assertEqual(len(c["pages_lues"]), 3)
        self.assertFalse(c["complete"])

    def test_couverture_insuffisante_partiel(self):
        c = self._passe([(5, 2, ["101", "102"]), (5, 2, ["103", "104"])])
        self.assertFalse(c["complete"])


BASE_FICHE = {"ref": "R", "obj": "O", "mo": None, "cat": "Travaux", "proc": "AOO", "pub": "2026-10-01", "lim": "2026-12-01",
              "h": "10:00", "lx": [], "nat": False, "etr": [], "lots": False, "env": False, "lieux_portail": []}


class TestRotationFiches(unittest.TestCase):
    def _etat(self, n=30):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        etat = Etat(d)
        ids = [etat.enregistrer_ligne(dict(BASE_FICHE, r=str(1000 + k), o="o8p"), f"2026-10-01T{k % 24:02d}:00:00+00:00", "r1")
               for k in range(n)]
        return etat, ids

    def _lire(self, etat, choix, quand, run, ok=True):
        for i in choix:
            if ok:
                etat.enregistrer_fiche(i, dict(BASE_FICHE, **{k: etat.listing["items"][i]["listing"][k] for k in ("lim", "obj")}), quand, run, "x")
            etat.noter_tentative(i, quand, run, ok, None if ok else "boom")

    def test_priorite_stricte_changees_puis_nouvelles_puis_anciennes(self):
        etat, ids = self._etat()
        for i in ids[:6]:  # 6 fiches lues il y a 3 jours
            self._lire(etat, [i], "2026-09-29T10:00:00+00:00", "r0")
        for i in ids[:2]:  # 2 contredites ensuite par un listing réel (report de date)
            x = dict(BASE_FICHE, r=etat.listing["items"][i]["r"], o="o8p", lim="2026-12-15")
            etat.enregistrer_ligne(x, "2026-10-02T09:00:00+00:00", "r2")
        c1, s1 = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:00:00+00:00")
        self.assertEqual(s1["choisies"], {"changees": 2, "nouvelles": 8, "anciennes": 0})  # nouvelles avant anciennes
        self.assertEqual(set(c1[:2]), set(ids[:2]))
        # sans nouvelles en file, les anciennes complètent
        c, s = mq.choisir_fiches(etat, set(ids[:8]), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:00:00+00:00")
        self.assertEqual(s["choisies"], {"changees": 2, "nouvelles": 2, "anciennes": 4})

    def test_rotation_sans_repetition_sur_plusieurs_passages(self):
        etat, ids = self._etat(30)
        vus, t = [], 10
        for k in range(3):  # 3 passages horaires de 10 : 30 fiches toutes différentes
            now = f"2026-10-02T{t + k:02d}:00:00+00:00"
            c, _ = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso=now)
            self.assertEqual(len(c), 10)
            self.assertFalse(set(c) & set(vus))
            vus += c
            self._lire(etat, c, now, f"r{k}")
            etat.sauver_selection()
        c, _ = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T13:00:00+00:00")
        self.assertEqual(c, [])  # tout lu il y a moins de 24 h : rien à relire
        c, s = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-03T10:30:00+00:00")
        self.assertEqual(set(c), set(vus[:10]))  # 24 h plus tard : les plus anciennes lectures d'abord
        self.assertEqual(s["choisies"]["anciennes"], 10)

    def test_ecart_permanent_listing_fiche_ne_boucle_pas(self):
        etat, ids = self._etat(3)
        i = ids[0]
        etat.enregistrer_ligne(dict(BASE_FICHE, r="1000", o="o8p", lim="2026-12-15"), "2026-10-02T09:00:00+00:00", "r2")
        c, s = mq.choisir_fiches(etat, {i}, 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T09:30:00+00:00")
        # lecture : le portail affiche encore l'ancienne date dans la fiche (écart persistant)
        etat.enregistrer_fiche(i, dict(BASE_FICHE), "2026-10-02T09:40:00+00:00", "r2", "x")
        etat.noter_tentative(i, "2026-10-02T09:40:00+00:00", "r2", True)
        etat.enregistrer_ligne(dict(BASE_FICHE, r="1000", o="o8p", lim="2026-12-15"), "2026-10-02T10:00:00+00:00", "r3")
        c, s = mq.choisir_fiches(etat, {i}, 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:30:00+00:00")
        self.assertEqual(c, [])  # listing inchangé depuis la lecture : pas relue à chaque passage
        etat.enregistrer_ligne(dict(BASE_FICHE, r="1000", o="o8p", lim="2026-12-20"), "2026-10-02T11:00:00+00:00", "r4")
        c, s = mq.choisir_fiches(etat, {i}, 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T11:30:00+00:00")
        self.assertEqual(s["categorie"].get(i), "changees")  # nouveau changement réel : relue

    def test_echec_mis_en_pause_et_ne_bloque_pas_la_file(self):
        etat, ids = self._etat(15)
        c1, _ = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:00:00+00:00")
        self._lire(etat, c1[:3], "2026-10-02T10:05:00+00:00", "r1", ok=False)
        self._lire(etat, c1[3:], "2026-10-02T10:05:00+00:00", "r1")
        c2, s2 = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T11:00:00+00:00")
        self.assertFalse(set(c1) & set(c2))
        self.assertEqual(s2["en_pause_apres_echec"], 3)
        self.assertEqual(len(c2), 5)
        c3, _ = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T16:10:00+00:00")
        self.assertEqual(set(c3) & set(c1), set(c1[:3]))  # après 6 h, les échecs reviennent (après les jamais tentées)

    def test_selection_persiste_dans_le_coffre(self):
        import coffre
        etat, ids = self._etat(12)
        c1, _ = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:00:00+00:00")
        self._lire(etat, c1[:8], "2026-10-02T10:05:00+00:00", "r1")
        self._lire(etat, c1[8:], "2026-10-02T10:05:00+00:00", "r1", ok=False)
        etat.sauver_listing(); etat.sauver_selection()
        etat.enregistrer_couverture("r1", {"run_id": "r1", "statut": "PARTIEL", "listing": {}})
        d = os.path.dirname(etat.d.rstrip("/")) if False else tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        coffre.pack(etat.d, os.path.join(d, "c"))
        self.assertIn("stock/etat/selection.json", json.loads(lire(os.path.join(d, "c", "manifest.json")))["fichiers"])
        self.assertTrue(coffre.verifier(os.path.join(d, "c"))["ok"])
        coffre.unpack(os.path.join(d, "c"), os.path.join(d, "e2"))
        e2 = Etat(os.path.join(d, "e2"))
        self.assertEqual(e2.selection, etat.selection)
        c2, s2 = mq.choisir_fiches(e2, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T11:00:00+00:00")
        self.assertEqual(set(c2), set(ids) - set(c1))  # restitué : ni les lues, ni les échecs en pause
        self.assertEqual(s2["en_pause_apres_echec"], 2)

    def test_consultation_expiree_ignoree(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        etat = Etat(d)
        x = {"r": "1001", "o": "o8p", "ref": "R", "obj": "O", "mo": None, "cat": "T", "proc": "P", "pub": None, "lim": "2026-09-01",
             "h": "10:00", "lx": [], "nat": False, "etr": [], "lots": False, "env": False, "lieux_portail": []}
        i = etat.enregistrer_ligne(x, "2026-10-01T10:00:00+00:00", "r1")
        c, _ = mq.choisir_fiches(etat, {i}, 10, aujourd_hui="2026-10-02")
        self.assertEqual(c, [])


# ---------------- détail par lot (popup officiel « Détail des lots ») ----------------
from veille.pmmp_lots import identite_popup, lire_lots, lire_popup  # noqa: E402
from veille.pmmp_fiche import libelle_seul  # noqa: E402


class FauxRep:
    def __init__(self, h, url):
        self.content, self.url = h.encode(), url


class FauxClient:
    """Sert la fiche allotie et son popup officiels (o4d/1046170) ; « echec » simule un popup en erreur réseau."""
    def __init__(self, popup_echec=False, popup_403=False):
        self.vus, self.popup_echec, self.popup_403 = [], popup_echec, popup_403

    def get(self, params):
        self.vus.append(params["page"])
        if params["page"] == "commun.PopUpDetailLots":
            if self.popup_403:
                raise client_mod.ArretCollecte("HTTP 403 sur popup : arrêt")
            if self.popup_echec:
                raise client_mod.ArretCollecte("échec GET popup : HTTP 502")
            return FauxRep(fx("popup_lots_1046170_o4d.html"), "https://x/index.php?page=commun.PopUpDetailLots")
        return FauxRep(fx("fiche_1046170_o4d_allotie_sans_contact.html"), "https://x/index.php?page=entreprise.EntrepriseDetailConsultation")


class TestLots(unittest.TestCase):
    def test_popup_officiel_par_lot_sans_somme(self):
        r = lire_popup(fx("popup_lots_1046170_o4d.html"), "o4d", "1046170", "2 Lots ")
        self.assertEqual((r["statut"], r["n"]), ("lu", 2))
        a, b = r["lots"]
        self.assertEqual((a["num"], a["intitule"], a["cat"], a["est"], a["est_libelle"], a["cau"], a["tp"], a["var"]),
                         ("1", "Surveillance ET gardiennage", "Services", 202447.87, "Estimation (en Dhs TTC)", 4000.0, True, False))
        self.assertEqual((b["num"], b["est"], b["cau"]), ("2", 151835.9, 3000.0))
        for k in ("q", "ag", "vis", "reu", "proto"):
            self.assertIn(k, a["ni"], "« - » publié = non indiqué")
            self.assertNotIn(k, a)
        self.assertNotIn("est", r, "aucune estimation globale sommée")

    def test_identite_et_lots_incomplets(self):
        h = fx("popup_lots_1046170_o4d.html")
        self.assertTrue(identite_popup(h, "o4d", "1046170"))
        self.assertFalse(identite_popup(h, "o4d", "104617"))
        self.assertEqual(lire_popup(h, "o8p", "1046170")["statut"], "inaccessible")
        p = lire_popup(h, "o4d", "1046170", "3 Lots")
        self.assertEqual((p["statut"], p["n"], p["n_annonce"]), ("partiel", 2, 3), "moins de lots que « N Lots » : partiel")

    def test_bloc_masque_et_valeurs_publiees(self):
        h = fx("popup_lots_1046170_o4d.html").replace('repeaterLots_ctl1_panelCautionProvisoire" style="display:;"',
                                                       'repeaterLots_ctl1_panelCautionProvisoire" style="display:none;"', 1)
        h = h.replace('<span id="ctl0_CONTENU_PAGE_repeaterLots_ctl0_qualification">-</span>',
                      '<span id="ctl0_CONTENU_PAGE_repeaterLots_ctl0_qualification"><li>Equipement / B- Travaux routiers / B.3- Ouvrages / Classe 2</li></span>', 1)
        h = h.replace('<span id="ctl0_CONTENU_PAGE_repeaterLots_ctl0_agrements">-</span>',
                      '<span id="ctl0_CONTENU_PAGE_repeaterLots_ctl0_agrements"><li>D13. Etudes générales</li></span>', 1)
        a, b = lire_lots(h)
        self.assertEqual(a["q"], [{"m": "Equipement", "s": "B", "sl": "Travaux routiers", "q": "B.3", "ql": "Ouvrages", "c": "2"}])
        self.assertEqual(a["ag"], ["D13. Etudes générales"])
        self.assertIn("cau", b["na"], "bloc masqué : non affiché, distinct de non indiqué")
        self.assertNotIn("cau", b)
        self.assertIn("q", b["ni"])

    def test_qualification_lignes_officielles(self):
        # lignes publiées relevées sur PMMP le 18/10/2026 (fiches et popups de lots) : aucun segment perdu
        L = lire_qualification
        self.assertEqual(L("Equipement / Y- Amenagement des cours d'eau et protection contre les innondations / "
                           "Y1- Travaux de recalibrage et d'endiguement des cours et épis / Classe 3"),
                         {"m": "Equipement", "s": "Y", "sl": "Amenagement des cours d'eau et protection contre les innondations",
                          "q": "Y1", "ql": "Travaux de recalibrage et d'endiguement des cours et épis", "c": "3"})
        self.assertEqual(L("Equipement / B- Travaux routiers et voirie urbaine / B.1- Travaux de terrassements routiers courants / Classe 2"),
                         {"m": "Equipement", "s": "B", "sl": "Travaux routiers et voirie urbaine", "q": "B.1",
                          "ql": "Travaux de terrassements routiers courants", "c": "2"})
        self.assertEqual(L("Habitat / 2 Travaux De Voirie / 2.2 Sans objet. / Classe 4"),
                         {"m": "Habitat", "s": "2", "sl": "Travaux De Voirie", "q": "2.2", "ql": "Sans objet.", "c": "4"})
        self.assertEqual(L("Agriculture / Travaux de plantation et de réhabilitation des arbres fruitiers et arbustes / "
                           "10.1.Travaux de plantation et de réhabilitation des arbres fruitiers et arbustes / Classe 5")["q"], "10.1")
        self.assertEqual(L("Laboratoires / ETUDES GEOTECHNIQUES / ETUDES GEOTECHNIQUES DES BATIMENTS COURANTS / Classe 3"),
                         {"m": "Laboratoires", "s": None, "sl": "ETUDES GEOTECHNIQUES", "q": None,
                          "ql": "ETUDES GEOTECHNIQUES DES BATIMENTS COURANTS", "c": "3"}, "secteur et qualification sans code : texte gardé")
        self.assertEqual(L("Laboratoires / Classe 1"), {"m": "Laboratoires", "s": None, "sl": None, "q": None, "ql": None, "c": "1"})
        f = lire_fiche(fx("fiche_1041301_o8p_sans_contact.html"))
        self.assertEqual(len(f["q_txt"]), len(f["q"]), "lignes publiées conservées pour un nouveau calcul sans requête")

    def test_libelle_seul_rien_de_publie(self):
        f = lire_fiche(fx("fiche_1046170_o4d_allotie_sans_contact.html"))
        self.assertEqual((f["allot"], f["reu"], f["proto"], f["est"], f["tp"], f["cau"]), ("2 Lots", None, None, None, None, None))
        self.assertTrue(libelle_seul("Date et heure limite :") and libelle_seul("Date et heure"))
        self.assertFalse(libelle_seul("Date et heure : 02/11/2026 15:00 salle"))


class TestLotsPassageHoraire(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.etat = Etat(self.d)
        self.i = "pmmp:o4d:1046170"

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_fiche_allotie_et_popup_meme_passage(self):
        c = FauxClient()
        res = mq.lire_fiches(c, self.etat, "r1", [self.i], False, True)
        self.assertEqual(c.vus, ["entreprise.EntrepriseDetailConsultation", "commun.PopUpDetailLots"])
        doc = self.etat.fiche(self.i)
        self.assertEqual((doc["lots"]["statut"], doc["lots"]["n"]), ("lu", 2))
        self.assertTrue(doc["lots"]["lu_le"])
        self.assertEqual(res["lots_lus"], 1)

    def test_echec_popup_garde_la_lecture_precedente_et_403_arrete(self):
        mq.lire_fiches(FauxClient(), self.etat, "r1", [self.i], False, True)
        avant = self.etat.fiche(self.i)["lots"]
        res = mq.lire_fiches(FauxClient(popup_echec=True), self.etat, "r2", [self.i], False, True)
        doc = self.etat.fiche(self.i)
        self.assertEqual(doc["run"], "r2", "la fiche est bien relue")
        self.assertEqual(doc["lots"], avant, "popup en échec : ancienne lecture conservée avec sa date")
        self.assertEqual(len(res["lots_echecs"]), 1)
        with self.assertRaises(client_mod.ArretCollecte):
            mq.lire_fiches(FauxClient(popup_403=True), self.etat, "r3", [self.i], False, True)

    def test_coffre_conserve_les_lots_et_catalogue_sans_libelle(self):
        import coffre
        mq.lire_fiches(FauxClient(), self.etat, "r1", [self.i], False, True)
        out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, out)
        coffre.pack(self.d, out)
        e2 = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, e2)
        coffre.unpack(out, e2)
        self.assertEqual(Etat(e2).fiche(self.i)["lots"]["n"], 2)
        f = self.etat.fiche(self.i)
        f["champs"]["reu"] = "Date et heure :"  # ancienne lecture (parser précédent)
        self.etat.enregistrer_fiche(self.i, f["champs"], f["lu_le"], "r1", "x", f["lots"])
        x = {"r": "1046170", "o": "o4d", "ref": "14/2026/81800", "obj": "o", "mo": "m", "cat": "Services", "proc": "p", "pub": "2026-10-01",
             "lim": "2026-10-19", "h": "13:00", "lx": [], "nat": True, "etr": [], "lots": True, "env": False, "lieux_portail": None}
        self.etat.enregistrer_ligne(x, "2026-10-01T00:00:00+00:00", "r1")
        cat, _ = cc.construire(self.etat, REG, "2026-10-02")
        it = cat["items"][0]
        self.assertTrue(it["det"])
        self.assertIsNone(it["reu"])
        self.assertEqual((it["est"], it["cau"], it["tp"]), (None, None, None), "alloti : rien d'aplati au niveau annonce")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Tests isolés : aucun accès réseau (le client HTTP est remplacé par un faux qui lève une erreur)."""
import json
import os
import shutil
import sys
import tempfile
import re
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

    def test_zone_entreprise_jamais_conservee_contact_publie_lu_tel_quel(self):
        # v3 : le contact administratif PUBLIÉ est lu (demande utilisateur) ; la zone entreprise (pièces téléchargées,
        # questions, cautions, dépôts) est coupée dès la réception
        faux = ('<!--Debut Bloc Pieces telechargees--><div id="ctl0_CONTENU_PAGE_panelOnglet2">question privée Q-123</div>')
        h = fx("fiche_1041719_e5w_v3_contact_fictif.html") + faux
        t, coupe = tronquer_contact(h)
        self.assertTrue(coupe)
        self.assertNotIn("Q-123", t)
        f = lire_fiche(t)
        self.assertEqual(f["contact"], {"nom": "Agent Fictif", "email": "contact.fictif@example.org", "tel": "0500000000",
                                        "fax": "0500000001"})

    def test_fiche_v3_meme_id_e5w_1041719(self):
        # fiche officielle e5w/1041719 (contact remplacé par des valeurs fictives) : valeurs confirmées par l'utilisateur
        f = lire_fiche(fx("fiche_1041719_e5w_v3_contact_fictif.html"))
        self.assertEqual((f["ref"], f["lim"], f["h"], f["est"], f["cau"], f["tp"], f["var"]),
                         ("10/2026/ARR/MERINIDES", "2026-10-20", "09:00", 1276320.0, 25000.0, False, False))
        self.assertIn("Réservé", f["obj"])  # l'objet garde sa mention ; TPME reste le champ officiel « Non »
        self.assertEqual(f["ret"], "Avenue Abi Imran Fassi ain kadous – Fés")
        self.assertEqual(f["prix_plans"], 0.0)  # « 0,00 MAD » publié : vrai zéro, pas « inconnu »
        self.assertEqual(f["ech_date"], "2026-10-19T10:00")  # prospectus : distincts de la remise des plis (20/10 09:00)
        self.assertTrue(f["ech_txt"].startswith("LES CONCURRENTS DOIVENT DEPOSER LES PROSPECTUS"))
        self.assertNotIn("0612345678", f["ech_txt"])  # texte libre : téléphones toujours masqués
        self.assertEqual(len(f["dom"]), 3)
        self.assertEqual(f["dep"], "www.marchespublics.gov.ma")
        self.assertTrue(f["ouv"].startswith("bureau de Monsieur le Président"))
        self.assertIsNone(f["reu"]); self.assertIsNone(f["vis"]); self.assertEqual(f["q"], []); self.assertIsNone(f["ag"])
        self.assertEqual(f["docs"], [{"type": "dce", "libelle": "Dossier de consultation", "taille": "648 Ko",
                                      "url": "index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=1041719&orgAcronyme=e5w"}])
        self.assertEqual(f["blocs_lus"], ["contact", "docs", "echantillons", "prix_plans", "retrait"])
        self.assertEqual(f["version_lecture"], 3)

    def test_pieces_vide_confirme_avec_preuve_jamais_sur_section_illisible(self):
        h = fx("fiche_1041719_e5w_v3_contact_fictif.html")
        # structure officielle complète, 3 liens explicitement masqués, aucun avis visible : zéro pièce confirmé
        masque = re.sub(r'<li\s+style="display:\s*block"', '<li style="display:none"', h)
        self.assertNotEqual(masque, h)
        f = lire_fiche(masque)
        self.assertEqual((f["docs"], f["docs_preuve"]), (None, "gabarit_masque_non_vide"), "lien rempli mais masqué : ambigu, non lu")
        vide = re.sub(r'<a id="ctl0_CONTENU_PAGE_linkDownloadDce"[^>]*>.*?</a>', '<a id="ctl0_CONTENU_PAGE_linkDownloadDce"></a>', masque, flags=re.S)
        f = lire_fiche(vide)
        self.assertEqual((f["docs"], f["docs_preuve"], f["page_id"]), ([], "liens_officiels_tous_masques", "e5w:1041719"))
        self.assertIn("docs", f["blocs_lus"])
        panneau_masque = vide.replace('<div id="ctl0_CONTENU_PAGE_panelPieces">', '<div id="ctl0_CONTENU_PAGE_panelPieces" style="display:none">')
        self.assertNotEqual(panneau_masque, vide)
        self.assertIsNone(lire_fiche(panneau_masque)["docs"], "panneau des pièces masqué : non lu")
        # bloc officiel « aucune pièce » visible, sans bloc des liens
        seul = re.sub(r'<div id="ctl0_CONTENU_PAGE_divPiecesConsultation".*?<!--Fin Bloc Pieces Consultation-->',
                      '<div id="ctl0_CONTENU_PAGE_divNoPiecesConsultation">Aucune pièce</div>', h, flags=re.S)
        self.assertEqual((lire_fiche(seul)["docs"], lire_fiche(seul)["docs_preuve"]), ([], "bloc_aucune_piece"))
        masque_aussi = seul.replace('divNoPiecesConsultation">', 'divNoPiecesConsultation" style="display:none">')
        self.assertIsNone(lire_fiche(masque_aussi)["docs"], "aucun bloc visible : non lu")
        # sections illisibles : jamais « aucun document »
        casse = h.replace('id="ctl0_CONTENU_PAGE_pictoComplement"', 'id="ctl0_CONTENU_PAGE_pictoAutre"')
        self.assertEqual((lire_fiche(casse)["docs"], lire_fiche(casse)["docs_preuve"]), (None, "structure_inattendue"))
        sans_lib = re.sub(r'(id="ctl0_CONTENU_PAGE_linkDownloadDce"[^>]*>)[^<]*(</a>)', r'\1\2', h)
        self.assertEqual((lire_fiche(sans_lib)["docs"], lire_fiche(sans_lib)["docs_preuve"]), (None, "lien_visible_sans_libelle"))
        self.assertNotIn("docs", lire_fiche(sans_lib)["blocs_lus"])
        coupe = h[:h.index('<div id="ctl0_CONTENU_PAGE_divPiecesConsultation"')]
        self.assertEqual((lire_fiche(coupe)["docs"], lire_fiche(coupe)["docs_preuve"]), (None, "bloc_absent"))

    def test_avis_seulement_visibles(self):
        h = fx("fiche_1041719_e5w_v3_contact_fictif.html")
        self.assertEqual([d["type"] for d in lire_fiche(h)["docs"]], ["dce"], "gabarits d'avis masqués non retenus")
        gab = h.replace('<div class="blue bold">Avis de publicité</div>',
                        '<div class="blue bold">Avis de publicité</div><ul><li style="display:none"><a href="index.php?page=entreprise.ExtraitPV&refConsultation=1041719&orgAcronyme=e5w">Lien masqué</a></li></ul>', 1)
        self.assertEqual([d["type"] for d in lire_fiche(gab)["docs"]], ["dce"])
        vis = h.replace('<div class="blue bold">Avis de publicité</div>',
                        '<div class="blue bold">Avis de publicité</div><ul><li class="picto-link"><a href="index.php?page=entreprise.ExtraitPV&refConsultation=1041719&orgAcronyme=e5w">Extrait de PV</a></li></ul>', 1)
        self.assertIn({"type": "avis", "libelle": "Extrait de PV", "taille": None,
                       "url": "index.php?page=entreprise.ExtraitPV&refConsultation=1041719&orgAcronyme=e5w"}, lire_fiche(vis)["docs"])

    def test_ancienne_page_tronquee_contact_et_documents_non_lus(self):
        # page coupée avant le contact (lectures v2 en cache) : contact / documents NON LUS (None, absents de blocs_lus)
        h = fx("fiche_1041719_e5w_v3_contact_fictif.html")
        h = h[:h.index('<div id="ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_panelContcatAdministratif"')]
        f = lire_fiche(h)
        self.assertIsNone(f["contact"]); self.assertIsNone(f["docs"])
        self.assertNotIn("contact", f["blocs_lus"]); self.assertNotIn("docs", f["blocs_lus"])
        self.assertEqual(f["ret"], "Avenue Abi Imran Fassi ain kadous – Fés")  # bloc présent avant le contact : lu

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


class FauxPortail:
    """Portail simulé fidèle au protocole réel : filtre date limite inclusif par jour (+ catégorie, + type de procédure),
    10 lignes en page 1, 500 après taille_500, ordre instable d'une requête à l'autre (tri sans clé unique).
    items : r -> (date limite iso, code catégorie[, code procédure]) ; evenements = {n° de requête: f(portail)} (appliqué
    AVANT la réponse) ; apres = {début jj/mm/aaaa: f(portail)} (appliqué juste APRÈS la 1re lecture de cette partition)."""
    CAT = {"1": "Travaux", "2": "Fournitures", "3": "Services", "9": "Autre"}

    def __init__(self, items, du="19/10/2026", au="19/04/2027", evenements=None, doublon_partition=None, apres=None,
                 procedures=("1", "2", "50")):
        import random
        self.items = {r: (v + ("1",))[:3] for r, v in items.items()}
        self.fenetre = {"dateMiseEnLigneStart": du, "dateMiseEnLigneEnd": au,
                        "dateMiseEnLigneCalculeStart": "19/04/2026", "dateMiseEnLigneCalculeEnd": du}
        self.procedures = list(procedures)
        self.evenements = evenements or {}
        self.apres = dict(apres or {})
        self.doublon_partition = doublon_partition  # (début jj/mm/aaaa, nb de réponses) : le portail répète une ligne
        self.c = type("C", (), {"nb_requetes": 0})()
        self.rnd = random.Random(7)
        self.q = None
        self.globaux = []  # n° des requêtes de total global (fenêtre entière, sans filtre)
        self.pages_demandees = 0

    def _tick(self):
        self.c.nb_requetes += 1
        ev = self.evenements.pop(self.c.nb_requetes, None)
        if ev:
            ev(self)

    def _sel(self):
        import datetime as dt
        d = lambda s: dt.date(int(s[6:]), int(s[3:5]), int(s[:2])).isoformat()
        f = self.q
        return sorted(r for r, (lim, cat, proc) in self.items.items()
                      if d(f["dateMiseEnLigneStart"]) <= lim <= d(f["dateMiseEnLigneEnd"])
                      and f.get("categorie") in (None, cat) and f.get("procedureType") in (None, proc))

    def _jma(self, r):
        lim = self.items[r][0] if r in self.items else "2026-10-19"
        return f"{lim[8:]}/{lim[5:7]}/{lim[:4]}"

    def _h(self, ids, total, taille, page):
        rows = "".join(f'<tr class=""><input name="x$refCons" value="{r}" /><input name="x$orgCons" value="o8p" />'
                       f'<span id="a_panelBlocCategorie">{self.CAT[self.items.get(r, ("", "1", "1"))[1]]}</span>'
                       f'<td headers="cons_dateEnd"><div class="cloture-line"> {self._jma(r)}<br>10:00 </div></td></tr>'
                       for r in ids)
        return (f'<span id="ctl0_CONTENU_PAGE_resultSearch_nombreElement">{total}</span>'
                f'<span id="ctl0_CONTENU_PAGE_resultSearch_nombrePageTop">{max(1, -(-total // taille))}</span>'
                f'<input name="ctl0$CONTENU_PAGE$resultSearch$numPageTop" type="text" value="{page}" />'
                f'<select name="ctl0$CONTENU_PAGE$resultSearch$listePageSizeTop"><option selected="selected" value="{taille}">{taille}</option></select>'
                + rows)

    def rechercher(self, classification=None, fenetre=None):
        self._tick()
        self.q = {**self.fenetre, **(fenetre or {})}
        if self.q["dateMiseEnLigneStart"] == self.fenetre["dateMiseEnLigneStart"] and self.q["dateMiseEnLigneEnd"] == \
                self.fenetre["dateMiseEnLigneEnd"] and not self.q.get("categorie") and not self.q.get("procedureType"):
            self.globaux.append(self.c.nb_requetes)
        s = self._sel()
        return self._h(s[:10], len(s), 10, 1), {}

    def partition(self, du, au, categorie=None, procedure=None):
        f = {"dateMiseEnLigneStart": du.strftime("%d/%m/%Y"), "dateMiseEnLigneEnd": au.strftime("%d/%m/%Y")}
        if categorie:
            f["categorie"] = categorie
        if procedure:
            f["procedureType"] = procedure
        h, _ = self.rechercher(fenetre=f)
        return h, total_et_pages(h)

    def taille_500(self, h):
        self._tick()
        s = self._sel()
        self.rnd.shuffle(s)
        page = s[:500]
        dp = self.doublon_partition
        if dp and dp[1] > 0 and self.q["dateMiseEnLigneStart"] == dp[0] and page:
            page = page + page[:1]
            self.doublon_partition = (dp[0], dp[1] - 1)
        h = self._h(page, len(s), 500, 1)
        ev = self.apres.pop(self.q["dateMiseEnLigneStart"], None)
        if ev:
            ev(self)
        return h

    def page(self, h, n):
        self.pages_demandees += 1
        raise AssertionError("pagination interdite : une partition doit tenir en une réponse")


def _items(n_par_jour, cat=lambda k: "1", proc=lambda k: "1"):
    import datetime as dt
    out, k = {}, 0
    for j, n in enumerate(n_par_jour):
        lim = (dt.date(2026, 10, 19) + dt.timedelta(days=j)).isoformat()
        for _ in range(n):
            out[str(1000000 + k)] = (lim, cat(k), proc(k))
            k += 1
    return out


GROS = [300, 300, 300] + [3] * 50


class TestPartitions(unittest.TestCase):
    def _passe(self, portail, etat=None):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        etat = etat or Etat(d)
        couv = {}
        ids = mq.passe_partitionnee(portail, etat, "r", PROV, ALIAS, couv)
        return ids, couv, etat

    def _ok(self, portail, couv, ids):
        attendu = {f"pmmp:o8p:{r}" for r in portail.items}
        self.assertTrue(couv["complete"], couv["raisons_incomplet"])
        self.assertEqual(ids, attendu)
        self.assertEqual(couv["ids_distincts"], len(attendu))
        self.assertEqual(couv["total_annonce"], len(attendu))
        self.assertEqual(len(couv["pages_lues"]), couv["pages_annoncees"])
        self.assertTrue(all(p["lignes"] <= 500 for p in couv["pages_lues"]))
        self.assertEqual(portail.pages_demandees, 0)

    def test_partitions_disjointes_couverture_exacte_et_tour_de_verification(self):
        p = FauxPortail(_items([182, 356, 250, 0, 90, 410, 30] + [5] * 170))
        ids, couv, etat = self._passe(p)
        self._ok(p, couv, ids)
        self.assertEqual(len(couv["controles"]), 1)  # portail immobile : un seul contrôle suffit
        self.assertTrue(all(x["lectures"] == 2 and x["confirmee"] for x in couv["pages_lues"]))  # deux lectures identiques
        self.assertEqual(len(etat.listing["items"]), len(p.items))

    def test_fenetre_fixee_envoyee_a_chaque_requete(self):
        # méthode RÉELLE CollecteListing.partition, client qui enregistre chaque POST (aucun réseau)
        import datetime as dt
        from veille.pmmp_listing import CollecteListing, P_RECH
        envois = []

        class Rep:
            url, content = "u", b'<span id="ctl0_CONTENU_PAGE_resultSearch_nombreElement">0</span>'

        class Client:
            nb_requetes = 0

            def post(self, url, data):
                envois.append(dict(data))
                return Rep()
        cl = CollecteListing(Client())
        cl.url = "u"
        champs = {"dateMiseEnLigneStart": "19/10/2026", "dateMiseEnLigneEnd": "19/04/2027",
                  "dateMiseEnLigneCalculeStart": "19/04/2026", "dateMiseEnLigneCalculeEnd": "19/10/2026", "annonceType": "3"}
        cl.h = "".join(f'<input type="text" name="{P_RECH}{k}" value="{v}" />' for k, v in champs.items())
        cl.fenetre = dict(champs)
        cl.fenetre["dateMiseEnLigneCalculeEnd"] = "19/10/2026"
        cl.h = cl.h.replace('value="19/10/2026" />', 'value="20/10/2026" />', 1)  # formulaire « recalculé » après minuit
        cl.partition(dt.date(2026, 10, 19), dt.date(2027, 4, 19))
        cl.partition(dt.date(2026, 10, 20), dt.date(2026, 10, 20), "1", "50")
        self.assertEqual([e[P_RECH + "dateMiseEnLigneStart"] for e in envois], ["19/10/2026", "20/10/2026"])
        self.assertEqual([e[P_RECH + "dateMiseEnLigneEnd"] for e in envois], ["19/04/2027", "20/10/2026"])
        self.assertTrue(all(e[P_RECH + "dateMiseEnLigneCalculeEnd"] == "19/10/2026" for e in envois))  # fixée à l'ouverture
        self.assertEqual((envois[1][P_RECH + "categorie"], envois[1][P_RECH + "procedureType"]), ("1", "50"))
        p = FauxPortail(_items([100, 100]))
        _, couv, _ = self._passe(p)
        self.assertEqual(couv["fenetre_date_limite"], ["2026-10-19", "2027-04-19"])

    def test_jour_au_dela_de_500_sous_partition_par_categorie(self):
        p = FauxPortail(_items([30, 1200, 30], cat=lambda k: "123"[k % 3]))
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)
        self.assertEqual(couv["subdivisions"][0]["par"], "categorie")

    def test_categorie_inconnue_d_un_jour_subdivise_jamais_complet(self):
        p = FauxPortail(_items([30, 600, 30], cat=lambda k: "9" if k == 40 else "123"[k % 3]))
        ids, couv, _ = self._passe(p)
        self.assertFalse(couv["complete"])
        self.assertTrue(any("sous-partitions" in r and "inconnue" in r for r in couv["raisons_incomplet"]))

    def test_jour_et_categorie_au_dela_de_500_sous_partition_par_procedure(self):
        p = FauxPortail(_items([20, 700, 20], proc=lambda k: ("1", "2", "50")[k % 3]))
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)
        self.assertEqual([s["par"] for s in couv["subdivisions"]], ["categorie", "procedure"])

    def test_partition_indivisible_au_dela_de_500_partiel_sans_pagination(self):
        p = FauxPortail(_items([20, 700, 20]))  # même jour, même catégorie, même procédure
        ids, couv, _ = self._passe(p)
        self.assertFalse(couv["complete"])
        self.assertTrue(any("indivisible" in r for r in couv["raisons_incomplet"]))
        self.assertEqual(p.pages_demandees, 0)

    def test_insertion_apres_lecture_detectee_puis_confirmee(self):
        p = FauxPortail(_items(GROS), apres={"19/10/2026": lambda q: q.items.__setitem__("2000001", ("2026-10-19", "1", "1"))})
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)
        self.assertIn("pmmp:o8p:2000001", ids)
        p19 = [x for x in couv["pages_lues"] if x["partition"].startswith("2026-10-19")][0]
        self.assertEqual((p19["changements_vus"], p19["lectures"]), (1, 3))  # changée, relue jusqu'à deux lectures identiques

    def test_suppression_apres_lecture_sans_effacer_l_etat(self):
        p = FauxPortail(_items(GROS), apres={"19/10/2026": lambda q: q.items.pop("1000000")})
        ids, couv, etat = self._passe(p)
        self._ok(p, couv, ids)
        self.assertNotIn("pmmp:o8p:1000000", ids)
        self.assertIn("pmmp:o8p:1000000", etat.listing["items"])  # vue avant sa disparition : jamais supprimée

    def test_report_de_date_limite_entre_partitions(self):
        p = FauxPortail(_items(GROS), apres={"19/10/2026": lambda q: q.items.__setitem__("1000000", ("2026-11-30", "1", "1"))})
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)
        self.assertTrue(any(x["changements_vus"] for x in couv["pages_lues"]))

    def test_echange_a_total_constant_dans_une_meme_partition(self):
        def echange(q):
            q.items.pop("1000000")
            q.items["2000002"] = ("2026-10-19", "1", "1")
        p = FauxPortail(_items(GROS), apres={"19/10/2026": echange})
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)
        self.assertIn("pmmp:o8p:2000002", ids)
        self.assertNotIn("pmmp:o8p:1000000", ids)
        self.assertTrue([x for x in couv["pages_lues"] if x["partition"].startswith("2026-10-19")][0]["changements_vus"])

    def test_echange_a_total_constant_entre_deux_partitions_deja_lues(self):
        # toutes les partitions lues, total global inchangé : seul le tour de relecture peut le voir
        sec = FauxPortail(_items(GROS))
        self._passe(sec)
        debut_tour = sec.globaux[-2]  # avant-dernier total global = début du contrôle final (portail immobile)

        def echange(q):
            q.items.pop("1000000")  # 19/10
            q.items["2000003"] = ("2027-03-01", "1", "1")  # partition lointaine, déjà lue
        p = FauxPortail(_items(GROS), evenements={debut_tour: echange})
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)
        c0 = couv["controles"][0]
        self.assertEqual(c0["total_avant"], c0["total_apres"])  # total global constant : seul le recomptage le voit
        self.assertEqual(len(c0["comptes_differents"]), 2)
        self.assertEqual(len(couv["controles"]), 2)
        self.assertIn("pmmp:o8p:2000003", ids)
        self.assertNotIn("pmmp:o8p:1000000", ids)

    def test_publication_pendant_le_controle_dans_une_partition_deja_recomptee(self):
        sec = FauxPortail(_items(GROS))
        self._passe(sec)
        k = sec.globaux[-2]  # total global avant contrôle ; k+1 = recomptage de la 1re partition (19/10)
        p = FauxPortail(_items(GROS), evenements={k + 2: lambda q: q.items.__setitem__("2000010", ("2026-10-19", "1", "1"))})
        ids, couv, _ = self._passe(p)
        self.assertTrue(couv["complete"], couv["raisons_incomplet"])
        self.assertEqual(couv["instant_reference"], "debut_controle")
        self.assertEqual(couv["total_annonce"], len(p.items) - 1)  # instantané exact au début du contrôle
        self.assertEqual(couv["publications_apres_reference"], 1)  # enregistrée à part, jamais incluse
        self.assertEqual(couv["total_global_apres_controle"], len(p.items))  # l'annonce publiée après : passage suivant
        self.assertNotIn("pmmp:o8p:2000010", ids)

    def test_publication_pendant_le_controle_dans_une_partition_pas_encore_recomptee(self):
        sec = FauxPortail(_items(GROS))
        self._passe(sec)
        k = sec.globaux[-2]
        p = FauxPortail(_items(GROS), evenements={k + 1: lambda q: q.items.__setitem__("2000011", ("2027-03-01", "1", "1"))})
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)  # écart de compte (+1) : jamais toléré, partition relue, nouveau contrôle, annonce incluse
        self.assertIn("pmmp:o8p:2000011", ids)
        self.assertEqual(len(couv["controles"]), 2)
        self.assertEqual(list(couv["controles"][0]["ecarts_de_compte"].values()), [1])

    def test_contre_exemple_hausse_globale_ne_date_pas_un_ajout(self):
        # x publié dans P (19/10) AVANT le début du contrôle, y retiré de Q (lointaine) avant, z publié dans Q après le début :
        # somme = total du début, écart P = +1, écart Q = 0, hausse globale = 1. Une règle « ajouts tolérés si hausse globale »
        # déclarerait COMPLET sans x (présent au début) : ici le contrôle est refusé et P relue.
        sec = FauxPortail(_items(GROS))
        self._passe(sec)
        k = sec.globaux[-2]

        def avant(q):
            q.items["2000020"] = ("2026-10-19", "1", "1")  # x
            q.items.pop("1000999")  # y (partition lointaine)
        p = FauxPortail(_items(GROS), evenements={k: avant, k + 1: lambda q: q.items.__setitem__("2000021", (q.items["1000998"][0], "1", "1"))})
        ids, couv, _ = self._passe(p)
        c0 = couv["controles"][0]
        self.assertTrue(c0["raisons"])  # refusé
        self.assertIsNone(c0["instant_reference"])
        self.assertTrue(couv["complete"], couv["raisons_incomplet"])
        self.assertIn("pmmp:o8p:2000020", ids)  # x retrouvé par la relecture de P
        # limite assumée et visible : y retiré et z publié dans la MÊME partition après sa dernière lecture (compte inchangé)
        # ne sont vus qu'au passage suivant
        self.assertIn("pmmp:o8p:1000999", ids)
        self.assertNotIn("pmmp:o8p:2000021", ids)

    def test_retrait_pendant_le_controle_jamais_tolere(self):
        sec = FauxPortail(_items(GROS))
        self._passe(sec)
        k = sec.globaux[-2]
        p = FauxPortail(_items(GROS), evenements={k + 1: lambda q: q.items.pop("1000999")})  # partition pas encore recomptée
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)  # écart négatif : partition relue, nouveau contrôle, retrait constaté
        self.assertEqual(len(couv["controles"]), 2)
        self.assertNotIn("pmmp:o8p:1000999", ids)

    def test_passage_interrompu_amorce_le_suivant(self):
        p = FauxPortail(_items(GROS), evenements={14: lambda q: (_ for _ in ()).throw(client_mod.ArretCollecte("budget de temps du passage atteint avant POST"))})
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        etat, c1 = Etat(d), {}
        with self.assertRaises(client_mod.ArretCollecte):
            mq.passe_partitionnee(p, etat, "r1", PROV, ALIAS, c1)
        lues = [x["partition"] for x in c1["pages_lues"]]
        self.assertTrue(lues)  # lectures faites avant l'arrêt, gardées (jamais une preuve de complétude)
        self.assertIs(c1["complete"], False)
        etat.enregistrer_couverture("r1", {"run_id": "r1", "listing": c1})  # comme main()
        c2 = {}
        ids = mq.passe_partitionnee(p, etat, "r2", PROV, ALIAS, c2)
        self._ok(p, c2, ids)
        rel = {x["partition"]: x["lectures"] for x in c2["pages_lues"]}
        self.assertTrue(all(rel[c] == 1 for c in lues if c in rel))  # confirmées par la lecture du passage interrompu

    def test_doublon_du_portail_trace_puis_relu(self):
        p = FauxPortail(_items(GROS), doublon_partition=("19/10/2026", 1))
        ids, couv, _ = self._passe(p)
        self._ok(p, couv, ids)
        self.assertTrue(any("doublon" in a for x in couv["anomalies_vues"] for a in x["anomalies"]))

    def test_doublon_persistant_partiel(self):
        p = FauxPortail(_items(GROS), doublon_partition=("19/10/2026", 99))
        ids, couv, _ = self._passe(p)
        self.assertFalse(couv["complete"])
        self.assertTrue(any("doublon" in r for r in couv["raisons_incomplet"]))

    def test_portail_qui_bouge_sans_cesse_reste_partiel_explique(self):
        p = FauxPortail(_items(GROS))
        for k in range(3, 600):
            p.evenements[k] = (lambda k: lambda q: q.items.__setitem__(str(3000000 + k), ("2026-10-20", "1", "1")))(k)
        ids, couv, etat = self._passe(p)
        self.assertFalse(couv["complete"])
        self.assertLessEqual(len(couv["controles"]), 6)  # itérations bornées
        self.assertLess(couv["requetes_listing"], 400)
        self.assertTrue(couv["raisons_incomplet"])
        self.assertTrue(all(e["absences_listing_complet"] == 0 for e in etat.listing["items"].values()))

    def test_ligne_hors_bornes_jamais_acceptee(self):
        p = FauxPortail(_items([10, 10]))
        p._jma = lambda r: "01/01/2030" if r == "1000000" else FauxPortail._jma(p, r)  # 2030 : hors fenêtre 19/10/2026–19/04/2027
        ids, couv, _ = self._passe(p)
        self.assertFalse(couv["complete"])
        self.assertTrue(any("hors bornes" in r for r in couv["raisons_incomplet"]))

    def test_403_et_coupure_reseau_arretent_sans_conclure(self):
        def refus(q):
            raise client_mod.ArretCollecte("HTTP 403 sur partition : arrêt (pas de contournement)")

        def coupure(q):
            raise client_mod.ArretCollecte("échec POST : Connection reset by peer")
        for ev in (refus, coupure):
            for k in (1, 4, 40):  # au début, pendant le découpage, pendant le tour de vérification
                p = FauxPortail(_items(GROS), evenements={k: ev})
                couv = {}
                d = tempfile.mkdtemp()
                self.addCleanup(shutil.rmtree, d)
                with self.assertRaises(client_mod.ArretCollecte):
                    mq.passe_partitionnee(p, Etat(d), "r", PROV, ALIAS, couv)
                self.assertIs(couv["complete"], False)  # décrit, jamais conclu
                self.assertIn("interrompu", couv)
                pr = json.loads(lire(os.path.join(d, "progression_listing.json")))
                self.assertEqual(pr["phase"], "interrompu")

    def test_budget_de_temps_arret_propre_client_reel(self):
        import time
        c = client_mod.ClientPMMP(delai_min=2.0)
        c.echeance = time.monotonic() + 1  # déjà presque atteint : aucune requête envoyée (le réseau est interdit ici)
        with self.assertRaises(client_mod.ArretCollecte) as e:
            c.get({"page": "x"})
        self.assertIn("budget", str(e.exception))
        self.assertEqual(c.nb_requetes, 0)

    def test_progression_ecrite_a_chaque_partition(self):
        p = FauxPortail(_items(GROS))
        _, couv, etat = self._passe(p)
        pr = json.loads(lire(os.path.join(etat.d, "progression_listing.json")))
        self.assertEqual(pr["phase"], "fini")
        self.assertEqual(pr["partitions"], couv["pages_annoncees"])
        self.assertEqual(pr["requetes"], couv["requetes_listing"])

    def test_confirmation_par_la_lecture_du_passage_precedent(self):
        p = FauxPortail(_items(GROS))
        _, c1, etat = self._passe(p)
        etat.enregistrer_couverture("r", {"run_id": "r", "listing": c1})  # comme main()
        p.items["2000009"] = ("2026-10-19", "1", "1")  # une seule partition change entre les deux passages
        couv = {}
        ids = mq.passe_partitionnee(p, etat, "r2", PROV, ALIAS, couv)
        self._ok(p, couv, ids)
        rel = {x["partition"]: x["lectures"] for x in couv["pages_lues"]}
        self.assertEqual(rel.pop([k for k in rel if k.startswith("2026-10-19")][0]), 2)  # changée : relue dans le passage
        self.assertTrue(all(v == 1 for v in rel.values()))  # inchangées : confirmées par la lecture précédente
        self.assertTrue(all(x["lecture_precedente"] == "r" for x in couv["pages_lues"]))
        self.assertLess(couv["requetes_listing"], c1["requetes_listing"])

    def test_lecture_precedente_trop_ancienne_ignoree(self):
        p = FauxPortail(_items(GROS))
        _, c1, etat = self._passe(p)
        etat.enregistrer_couverture("r", {"run_id": "r", "listing": c1})  # comme main()
        self.assertTrue(mq.lectures_precedentes(etat))
        self.assertEqual(mq.lectures_precedentes(etat, "2099-01-01T00:00:00+00:00"), {})

    def test_plan_couvre_exactement_la_fenetre(self):
        import datetime as dt
        p = FauxPortail(_items([300, 300, 300]))
        _, _, etat = self._passe(p)
        du, au = dt.date(2026, 10, 19), dt.date(2027, 4, 19)
        plan = mq.planifier_partitions(etat, du, au, 400)
        self.assertEqual(plan[0][0], du)
        self.assertEqual(plan[-1][1], au)
        self.assertTrue(all(b + dt.timedelta(days=1) == a for (_, b), (a, _) in zip(plan, plan[1:])))


class TestStatutEtCatalogueGarde(unittest.TestCase):
    def test_partiel_ne_remplace_pas_dernier_succes_et_fiches_suivent(self):
        import coffre
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        etat = Etat(os.path.join(d, "e"))
        x = {"r": "1041301", "o": "o8p", "ref": "R", "obj": "O", "mo": "M", "cat": "Travaux", "proc": "AOO", "pub": "2026-10-01",
             "lim": "2026-12-01", "h": "10:00", "lx": [], "nat": False, "etr": [], "lots": False, "env": False, "lieux_portail": []}
        etat.enregistrer_ligne(x, "2026-10-02T10:00:00+00:00", "r1")
        etat.sauver_listing()
        etat.enregistrer_couverture("r1", {"run_id": "r1", "statut": "LISTING_COMPLET_ANNONCES_DE_CONSULTATION_FENETRE_PAR_DEFAUT",
                                           "fin": "2026-10-02T10:10:00+00:00",
                                           "listing": {"total_annonce": 1, "ids_distincts": 1, "pages_lues": [{"page": 1}], "complete": True}})
        cat, _ = cc.construire(etat, REG, "2026-10-02")
        pc = os.path.join(d, "cat.json")
        with open(pc, "w") as f:
            json.dump(cat, f)
        coffre.pack(etat.d, os.path.join(d, "c1"), pc)
        # passage suivant PARTIEL + fiche lue entre-temps (visite publiée)
        etat.enregistrer_fiche("pmmp:o8p:1041301", {"ref": "R", "obj": "O", "vis": "le 20/10/2026", "q": [], "dom": []},
                               "2026-10-02T11:00:00+00:00", "r2", "h")
        etat.enregistrer_couverture("r2", {"run_id": "r2", "statut": "PARTIEL", "fin": "2026-10-02T11:10:00+00:00",
                                           "listing": {"total_annonce": 2, "ids_distincts": 1, "pages_lues": [{"page": 1}], "complete": False}})
        cat2, _ = cc.construire(etat, REG, "2026-10-02")
        with open(pc, "w") as f:
            json.dump(cat2, f)
        coffre.pack(etat.d, os.path.join(d, "c2"), pc, None, os.path.join(d, "c1"))
        st = json.loads(lire(os.path.join(d, "c2", "stock", "statut.json")))
        self.assertEqual(st["dernier_succes"]["run_id"], "r1")  # jamais le partiel
        self.assertEqual(st["derniere_tentative"]["run_id"], "r2")
        cv = json.loads(lire(os.path.join(d, "c2", "stock", "catalogue_valide.json")))
        self.assertEqual(cv["maj"], "2026-10-02T10:10:00+00:00")  # même listing de référence
        self.assertEqual([i["r"] for i in cv["items"]], ["1041301"])  # aucun identifiant ajouté
        self.assertEqual(cv["items"][0]["vis"], "le 20/10/2026")  # fiche lue depuis : reprise
        self.assertTrue(cv["items"][0]["det"])


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

    def test_nouvelles_avant_relectures_saturation_du_budget_et_reprise(self):
        # 12 anciennes déjà lues dont le listing a changé + 8 nouvelles sans fiche ; budget épuisé après 5 lectures
        etat, ids = self._etat(20)
        h = fx("fiche_1041301_o8p_sans_contact.html")
        for i in ids[:12]:
            etat.enregistrer_fiche(i, {"ref": "R", "obj": "O", "lim": "2026-12-01", "h": "10:00"}, "2026-10-01T08:00:00+00:00", "r0", "x")
            e = etat.listing["items"][i]
            e["listing"]["lim"] = "2026-12-15"
            e.setdefault("changements", []).append({"vu_le": "2026-10-02T09:00:00+00:00", "run": "r1", "diff": {"lim": ["2026-12-01", "2026-12-15"]}})
        nouvelles, changees = set(ids[12:]), set(ids[:12])
        choix, st = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:00:00+00:00",
                                      nouvelles_max=150)
        self.assertEqual(set(choix[:8]), nouvelles)  # nouvelles d'abord
        self.assertTrue(set(choix[8:]) <= changees and len(choix) == 18)  # puis 10 relectures au plus
        n = [0]

        class C:
            def get(self, params):
                n[0] += 1
                if n[0] > 5:
                    raise client_mod.ArretCollecte("budget de temps du passage atteint avant GET")
                return FauxRep(h, "u")
        res = mq.lire_fiches(C(), etat, "r2", choix, False, True)
        self.assertEqual({x["id"] for x in res["lues"]}, set(choix[:5]))  # les 5 lues sont des nouvelles
        self.assertTrue(set(choix[:5]) <= nouvelles)
        # passage suivant : les 3 nouvelles restantes reviennent en tête, avant toute relecture (aucune marquée tentée)
        choix2, st2 = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T11:00:00+00:00",
                                        nouvelles_max=150)
        self.assertEqual(set(choix2[:3]), nouvelles - set(choix[:5]))
        self.assertEqual(st2["file_nouvelles"], 3)
        # plafond honnête : reliquat mesuré
        choix3, st3 = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T11:00:00+00:00",
                                        nouvelles_max=2)
        self.assertEqual(st3["reliquat_nouvelles_plafond"], 1)
        self.assertEqual(set(choix3[:2]) <= nouvelles, True)

    def test_reliquat_pieces_non_lues_parmi_les_relectures_sans_priver_les_nouvelles(self):
        # 15 anciennes (5 avec pièces lues v3, 10 sans) + 4 nouvelles ; 10 places de relecture
        etat, ids = self._etat(19)
        for j, i in enumerate(ids[:15]):
            ch = {"ref": "R", "obj": "O", "lim": "2026-12-01", "h": "10:00"}
            if j < 5:
                ch["blocs_lus"] = ["contact", "docs"]
            etat.enregistrer_fiche(i, ch, "2026-09-01T08:00:00+00:00" if j < 5 else "2026-09-20T08:00:00+00:00", "r0", "x")
        choix, st = mq.choisir_fiches(etat, set(ids), 10, aujourd_hui="2026-10-02", maintenant_iso="2026-10-02T10:00:00+00:00",
                                      nouvelles_max=150)
        self.assertEqual(set(choix[:4]), set(ids[15:]))  # nouvelles d'abord
        self.assertEqual(set(choix[4:]), set(ids[5:15]))  # puis les 10 sans pièces lues, malgré une lecture plus récente
        self.assertEqual(st["reliquat_pieces_non_lues_eligibles"], 10)

    def test_inventaire_des_pieces_garde_si_relecture_illisible(self):
        etat, ids = self._etat(1)
        i = ids[0]
        etat.enregistrer_fiche(i, {"ref": "R", "obj": "O", "docs": [{"type": "dce"}], "docs_preuve": "liens_visibles",
                                   "blocs_lus": ["contact", "docs"]}, "2026-10-19T21:00:00+00:00", "r1", "x")
        etat.enregistrer_fiche(i, {"ref": "R", "obj": "O2", "docs": None, "docs_preuve": "structure_inattendue",
                                   "blocs_lus": ["contact"]}, "2026-10-20T08:00:00+00:00", "r2", "y")
        f = etat.fiche(i)
        self.assertEqual((f["lu_le"], f["champs"]["obj"]), ("2026-10-20T08:00:00+00:00", "O2"), "lecture récente : fait foi")
        self.assertEqual((f["champs"]["docs"], f["champs"]["docs_lu_le"]), ([{"type": "dce"}], "2026-10-19T21:00:00+00:00"))
        self.assertIn("docs", f["champs"]["blocs_lus"])
        etat.enregistrer_fiche(i, {"ref": "R", "obj": "O3", "docs": [], "docs_preuve": "bloc_aucune_piece",
                                   "blocs_lus": ["contact", "docs"]}, "2026-10-21T08:00:00+00:00", "r3", "z")
        self.assertEqual((etat.fiche(i)["champs"]["docs"], etat.fiche(i)["champs"].get("docs_lu_le")), ([], None), "nouvelle lecture des pièces : fait foi")

    def test_commande_exacte_de_la_routine_nouvelles_d_abord_et_reliquat(self):
        # main() avec la commande EXACTE de la tâche horaire : --etat W --fiches 10 --sans-snapshots --delai 3
        # (aucune option nouvelle) ; portail simulé : listing = 20 annonces, 12 déjà lues et changées, 8 nouvelles ;
        # budget épuisé après 6 lectures de fiches
        etat, ids = self._etat(20)
        for i in ids[:12]:
            etat.enregistrer_fiche(i, {"ref": "R", "obj": "O", "lim": "2026-12-01", "h": "10:00"}, "2026-10-01T08:00:00+00:00", "r0", "x")
            e = etat.listing["items"][i]
            e["listing"]["lim"] = "2026-12-15"
            e.setdefault("changements", []).append({"vu_le": "2099-01-01T00:00:00+00:00", "run": "r1", "diff": {"lim": ["2026-12-01", "2026-12-15"]}})
        etat.sauver_listing()
        nouvelles = set(ids[12:])
        h = fx("fiche_1041301_o8p_sans_contact.html")
        lus = []

        class Client:
            nb_requetes, octets_recus, echeance = 0, 0, None

            def __init__(self, *a, **k):
                pass

            def get(self, params):
                if len(lus) >= 6:
                    raise client_mod.ArretCollecte("budget de temps du passage atteint avant GET")
                lus.append(params)
                return FauxRep(h, "u")

        class Listing:
            def __init__(self, c):
                self.c, self.organismes, self.fenetre, self.types_annonce = c, {}, {}, []

            def ouvrir(self):
                pass

        def passe(cl, et, run_id, *a, **k):
            a[2].update({"complete": True, "total_annonce": 20, "ids_distincts": 20, "pages_lues": [{"page": 1}]})
            for i in ids:
                et.listing["items"][i]["dernier_run"] = run_id
            return set(ids)
        anciens = (mq.ClientPMMP, mq.CollecteListing, mq.passe_partitionnee, sys.argv)
        mq.ClientPMMP, mq.CollecteListing, mq.passe_partitionnee = Client, Listing, passe
        sys.argv = ["maj_quotidienne.py", "--etat", etat.d, "--fiches", "10", "--sans-snapshots", "--delai", "3"]
        try:
            with self.assertRaises(SystemExit):  # code 1 : arrêt des fiches sur budget (rien n'est conclu)
                mq.main()
        finally:
            mq.ClientPMMP, mq.CollecteListing, mq.passe_partitionnee, sys.argv = anciens
        c = json.loads(lire(os.path.join(etat.d, "couverture", sorted(os.listdir(os.path.join(etat.d, "couverture")))[-1])))
        F = c["fiches"]
        self.assertEqual(F["selection"]["regle"], "nouvelles (max 150) > changees > anciennes (n=10)")  # actif par défaut
        self.assertEqual((F["selection"]["file_nouvelles"], F["selection"]["file_changees"]), (8, 12))  # file avant
        self.assertEqual(F["selection"]["choisies"], {"changees": 10, "nouvelles": 8, "anciennes": 0})
        self.assertEqual(len(F["lues"]), 6)
        self.assertTrue({x["id"] for x in F["lues"]} <= nouvelles)  # ordre : nouvelles d'abord
        self.assertEqual(F["reliquat"], {"nouvelles_non_lues_budget": 2, "relectures_non_faites_budget": 10,
                                         "nouvelles_au_dela_du_plafond": 0})  # reliquat après, mesuré

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
        self.assertEqual(L("Laboratoires / RECHERCHE-DEVELOPPEMENT / RECHERCHE-DEVELOPPEMENT EN HYDRAULIQUE ET MARITIME / Classe 1")["sl"],
                         "RECHERCHE-DEVELOPPEMENT", "un mot avec tiret n'est pas un code")
        self.assertEqual(L("Laboratoires / Classe 1"), {"m": "Laboratoires", "s": None, "sl": None, "q": None, "ql": None, "c": "1"})
        f = lire_fiche(fx("fiche_1041301_o8p_sans_contact.html"))
        self.assertEqual(len(f["q_txt"]), len(f["q"]), "lignes publiées conservées pour un nouveau calcul sans requête")

    def test_visite_officielle_lue(self):
        # bloc officiel (fiche l5b/1049723, 18/10/2026) : la visite est dans le sous-bloc panelRepeaterVisitesLieux
        P = "ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_"
        h = (f'<span id="{P}reference">R/1</span><span id="{P}objet">O</span><div id="{P}panelVisitesLieux" class="line" style="display:;">'
             f'<div class="intitule-240 bold">Visites des lieux : </div><div id="{P}panelRepeaterVisitesLieux" class="content-bloc bloc-500">'
             f'<ul class="default-list"><li><span id="{P}repeaterVisitesLieux_ctl1_dateVisites">28/10/2026 11:00</span>,&nbsp;'
             f'<span id="{P}repeaterVisitesLieux_ctl1_adresseVisites">- Siège de la Fondation, Casablanca – Anfa </span></li></ul></div></div>'
             f'<div id="{P}panelVariante" class="line"><span id="{P}varianteValeur">Non</span></div>')
        self.assertEqual(lire_fiche(h)["vis"], "28/10/2026 11:00, - Siège de la Fondation, Casablanca – Anfa")
        vide = fx("fiche_1046170_o4d_allotie_sans_contact.html")
        self.assertIsNone(lire_fiche(vide)["vis"], "sous-bloc vide : rien de publié")

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

    def test_arret_pendant_les_fiches_garde_le_compte_des_fiches_lues(self):
        n = [0]
        h = fx("fiche_1041301_o8p_sans_contact.html")

        class C:
            def get(self, params):
                n[0] += 1
                if n[0] > 2:
                    raise client_mod.ArretCollecte("budget de temps du passage atteint avant GET")
                return FauxRep(h, "u")
        ids = ["pmmp:o8p:1041301", "pmmp:o8p:1041302", "pmmp:o8p:1041303"]
        res = mq.lire_fiches(C(), self.etat, "r", ids, False, True)
        self.assertEqual(len(res["lues"]), 2)  # lues avant l'arrêt : comptées et enregistrées
        self.assertIn("budget", res["arret"])
        self.assertIsNotNone(self.etat.fiche("pmmp:o8p:1041302"))
        self.assertIsNone(self.etat.fiche("pmmp:o8p:1041303"))

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

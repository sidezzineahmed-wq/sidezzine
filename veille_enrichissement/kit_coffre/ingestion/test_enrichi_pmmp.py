"""Enrichissement PMMP joint (mode de passation + classification Etat/CL/EEP) dans l'ingestion. Données fictives pour les
annonces ; référentiel de classification = relevé OFFICIEL réel du kit (referentiel/classification_entites.json)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingestion_catalogue as I  # noqa: E402
from enrichi_pmmp import enrichir  # noqa: E402
from test_ingestion import AUJ, cat, item, statut  # noqa: E402

REF = json.load(open(I.REFERENTIEL_CLASSIFICATION, encoding="utf-8"))


def it(r, o, ref=None, **kw):
    x = item(r, **kw)
    x["o"], x["ref"] = o, ref or f"{r}/2026"
    return x


def fiche(ref, mode, lu_le, proc="Appel d'offres ouvert"):
    return {"lu_le": lu_le, "run": "R-" + lu_le[:13], "champs": {"ref": ref, "proc": proc, "mode_passation": mode}}


class Referentiel(unittest.TestCase):
    def test_releve_officiel_verifie(self):
        c = REF["controle_listes"]
        self.assertTrue(c["partition_exacte"])
        self.assertEqual(c["par_classification"], {"1": 57, "2": 16, "3": 4})
        t = REF["controle_recherche"]
        self.assertTrue(t["partition_totaux"])
        self.assertEqual([t["totaux"][k].get("incoherents") for k in ("2", "3")], [[], []])
        self.assertEqual((REF["par_entite"]["g3h"]["libelle"], REF["par_entite"]["j0w"]["libelle"], REF["par_entite"]["w6x"]["libelle"]),
                         ("Etat", "Collectivité locale", "Etablissement public"))
        self.assertEqual(REF["procedures_formulaire"]["codes"]["Appel d'offres ouvert simplifié"], "50")


class Enrichir(unittest.TestCase):
    def test_mode_distinct_procedure_inconnu_et_classification_heritee(self):
        items = [it(1, "g3h"), it(2, "j0w"), it(3, "zzz")]
        e = enrichir(items, {"pmmp:g3h:1": fiche("1/2026", "Au rabais / majoration", "2026-10-10T10:00:00+00:00")}, REF)
        m = e["mode_passation"]
        self.assertEqual(m["par_id"]["pmmp:g3h:1"], {"v": "Au rabais / majoration", "ref": "1/2026", "lu_le": "2026-10-10T10:00:00+00:00",
                                                      "run": "R-2026-10-10T10", "source": "collecteur"})
        self.assertEqual((m["couverture"]["connues"], m["couverture"]["inconnues"]), (1, 2), "sans lecture = inconnu, jamais une valeur par défaut")
        self.assertNotIn("Appel d'offres ouvert", m["couverture"]["valeurs"], "la procédure n'est pas un mode")
        c = e["classification"]["couverture"]
        self.assertEqual((c["par_code"], c["entites_inconnues"]), ({"1": 1, "2": 1, "inconnu": 1}, ["zzz"]))
        self.assertEqual(e["procedures"]["codes"]["Appel d'offres ouvert"], "1")

    def test_plus_recente_gagne_sans_perte_et_reference_discordante(self):
        items = [it(1, "g3h"), it(2, "g3h", ref="2/2026-MODIF")]
        F = {"pmmp:g3h:1": fiche("1/2026", "Sur offre de prix", "2026-10-10T10:00:00+00:00"),
             "pmmp:g3h:2": fiche("2/2026", "Sur offre de prix", "2026-10-10T10:00:00+00:00")}
        e1 = enrichir(items, F, REF)
        self.assertEqual(e1["mode_passation"]["couverture"]["reference_discordante"], ["pmmp:g3h:2"])
        # passage suivant : fiche 1 sortie de fiches.json (rotation) ; complément plus récent pour 2 ; lecture plus ANCIENNE pour 1
        prec = json.loads(json.dumps(e1))
        prec["mode_passation"]["par_id"]["pmmp:g3h:2"] = {"v": "Au rabais / majoration", "ref": "2/2026-MODIF", "lu_le": "2026-10-18T00:10:00+00:00",
                                                          "source": "complement_eaios", "url": "https://www.marchespublics.gov.ma/x"}
        e2 = enrichir(items, {"pmmp:g3h:1": fiche("1/2026", "Au rabais / majoration", "2026-10-01T00:00:00+00:00")}, REF, prec)
        p = e2["mode_passation"]["par_id"]
        self.assertEqual(p["pmmp:g3h:1"]["v"], "Sur offre de prix", "lecture plus ancienne : ne remplace pas")
        self.assertEqual((p["pmmp:g3h:2"]["v"], p["pmmp:g3h:2"]["source"]), ("Au rabais / majoration", "complement_eaios"))
        self.assertEqual(e2["mode_passation"]["couverture"]["connues"], 2)
        e3 = enrichir([items[0]], {}, REF, e2)
        self.assertIn("pmmp:g3h:2", e3["mode_passation"]["par_id"], "annonce sortie du catalogue : lecture conservée")
        self.assertEqual(e3["mode_passation"]["couverture"]["lues_hors_catalogue_conservees"], 1)

    def test_referentiel_absent_classification_precedente_conservee(self):
        items = [it(1, "w6x")]
        e1 = enrichir(items, {}, REF)
        e2 = enrichir(items, {}, None, e1)
        self.assertEqual(e2["classification"]["par_entite"], e1["classification"]["par_entite"])
        self.assertEqual(e2["classification"]["couverture"]["par_code"], {"3": 1})
        self.assertNotIn("classification", enrichir(items, {}, None, None), "rien inventé sans source")


class Pipeline(unittest.TestCase):
    """Branche exécutée par le passage horaire : ingestion_catalogue.py main() avec --fiches et --details-precedents."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)

    def j(self, n, v):
        p = os.path.join(self.d, n)
        json.dump(v, open(p, "w"))
        return p

    def test_cli_details_porte_l_enrichissement_et_le_conserve(self):
        prec = cat([it(100 + i, "g3h", det=True) for i in range(20)], maj="2026-09-26T12:57:48+00:00")
        its = [it(100 + i, "g3h") for i in range(20)] + [it(1, "j0w"), it(2, "w6x")]
        nouv = cat(its, total=len(its))
        F = {"pmmp:j0w:1": fiche("1/2026", "Au rabais / majoration", "2026-10-17T22:00:00+00:00")}
        base = ["--catalogue-valide", self.j("v.json", nouv), "--statut", self.j("s.json", statut(len(its))), "--aujourdhui", AUJ]
        self.assertEqual(I.main(base + ["--precedent", self.j("p.json", prec), "--fiches", self.j("f.json", F), "--sortie", os.path.join(self.d, "o1")]), 0)
        L = lambda o, n: json.load(open(os.path.join(self.d, o, n)))
        e = L("o1", "catalogue_details.json")["pmmp_enrichi"]
        self.assertEqual(e["mode_passation"]["par_id"]["pmmp:j0w:1"]["v"], "Au rabais / majoration")
        self.assertEqual(e["classification"]["couverture"]["par_code"], {"1": 20, "2": 1, "3": 1})
        self.assertEqual(L("o1", "catalogue.json")["items"][0].keys(), {k: 0 for k in I.CHAMPS}.keys(), "schéma à 31 champs inchangé")
        # passage suivant : la fiche n'est plus dans fiches.json -> valeur conservée ; rien d'autre ne change -> « inchangé »
        P = os.path.join(self.d, "o1")
        a = base + ["--precedent", os.path.join(P, "catalogue.json"), "--details-precedents", os.path.join(P, "catalogue_details.json"),
                    "--hors-precedents", os.path.join(P, "catalogue_hors_listing.json"), "--etat-precedent", os.path.join(P, "catalogue_etat.json"),
                    "--fiches", self.j("f2.json", {}), "--sortie", os.path.join(self.d, "o2")]
        self.assertEqual(I.main(a), 0)
        self.assertEqual(L("o2", "catalogue_details.json")["pmmp_enrichi"]["mode_passation"]["par_id"]["pmmp:j0w:1"]["v"], "Au rabais / majoration")
        self.assertEqual(L("o2", "ingestion_rapport.json")["etat"], "inchange", "idempotent : mêmes octets")


class Complement(unittest.TestCase):
    """referentiel/mode_passation_complement.json : lectures du complément EAIOS, conservées par le kit à chaque passage."""

    def comp(self, **recs):
        return {"version": 1, "par_id": recs}

    def test_lu_absent_inaccessible_jamais_de_valeur_inventee(self):
        items = [it(1, "g3h"), it(2, "g3h"), it(3, "g3h"), it(4, "g3h")]
        C = self.comp(**{"pmmp:g3h:1": {"statut": "lu", "v": "Au rabais / majoration", "ref": "1/2026", "lu_le": "2026-10-18T01:00:00+00:00", "url": "u1"},
                         "pmmp:g3h:2": {"statut": "champ_absent", "v": None, "ref": "2/2026", "lu_le": "2026-10-18T01:01:00+00:00", "url": "u2"},
                         "pmmp:g3h:3": {"statut": "inaccessible", "tentatives": 3, "dernier_echec": "2026-10-18T01:02:00+00:00", "raison": "HTTP 500"}})
        e = enrichir(items, {}, REF, None, C)["mode_passation"]
        self.assertEqual(e["par_id"]["pmmp:g3h:1"]["source"], "complement_eaios")
        self.assertNotIn("pmmp:g3h:2", e["par_id"])
        self.assertNotIn("pmmp:g3h:3", e["par_id"])
        cv = e["couverture"]
        self.assertEqual((cv["connues"], cv["champ_absent"], cv["inaccessibles"], cv["non_lues"]), (1, 1, 1, 1))
        self.assertEqual(e["inaccessibles"]["pmmp:g3h:3"]["tentatives"], 3)

    def test_lecture_plus_recente_gagne_sur_absent_et_inaccessible(self):
        items = [it(2, "g3h"), it(3, "g3h")]
        C = self.comp(**{"pmmp:g3h:2": {"statut": "champ_absent", "ref": "2/2026", "lu_le": "2026-10-18T01:01:00+00:00"},
                         "pmmp:g3h:3": {"statut": "inaccessible", "tentatives": 3}})
        e1 = enrichir(items, {}, REF, None, C)
        F = {"pmmp:g3h:2": fiche("2/2026", "Sur offre de prix", "2026-10-18T05:00:00+00:00"),
             "pmmp:g3h:3": fiche("3/2026", "Sur offre de prix", "2026-10-18T05:00:00+00:00")}
        e2 = enrichir(items, F, REF, e1, C)["mode_passation"]
        self.assertEqual((e2["couverture"]["connues"], e2["couverture"]["champ_absent"], e2["couverture"]["inaccessibles"]), (2, 0, 0))

    def test_cli_charge_le_complement_du_kit_par_defaut_et_le_conserve(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        j = lambda n, v: (json.dump(v, open(os.path.join(d, n), "w")), os.path.join(d, n))[1]
        its = [it(100 + i, "g3h") for i in range(20)] + [it(1, "j0w")]
        C = self.comp(**{"pmmp:j0w:1": {"statut": "lu", "v": "Au rabais / majoration", "ref": "1/2026", "lu_le": "2026-10-18T01:00:00+00:00", "url": "u"}})
        base = ["--catalogue-valide", j("v.json", cat(its, total=len(its))), "--statut", j("s.json", statut(len(its))), "--aujourdhui", AUJ,
                "--precedent", j("p.json", cat([it(100 + i, "g3h") for i in range(20)])), "--complement-mode", j("c.json", C)]
        self.assertEqual(I.main(base + ["--sortie", os.path.join(d, "o1")]), 0)
        e = json.load(open(os.path.join(d, "o1", "catalogue_details.json")))["pmmp_enrichi"]["mode_passation"]
        self.assertEqual(e["par_id"]["pmmp:j0w:1"]["v"], "Au rabais / majoration")
        self.assertTrue(os.path.basename(I.COMPLEMENT_MODE) == "mode_passation_complement.json")


class Lots(unittest.TestCase):
    def test_par_lot_identite_conservation_et_inaccessibles(self):
        L = lambda lu, st="lu", n=2: {"lu_le": lu, "statut": st, "n": n, "n_annonce": 2,
                                      "lots": [{"num": str(i + 1), "est": 100.0 * (i + 1), "tp": i == 0, "ni": ["q"], "na": [], "est_brut": "x"}
                                               for i in range(n)]}
        items = [it("1", "o1", "A", lots=True), it("2", "o1", "B", lots=True), it("3", "o1", "C", lots=True), it("4", "o1", "D", lots=False)]
        fiches = {"pmmp:o1:1": {"lu_le": "2026-10-18T10:00:00+00:00", "champs": {"ref": "A"}, "lots": L("2026-10-18T10:00:00+00:00")},
                  "pmmp:o1:2": {"lu_le": "2026-10-18T10:00:00+00:00", "champs": {"ref": "AUTRE"}, "lots": L("2026-10-18T10:00:00+00:00")},
                  "pmmp:o1:3": {"lu_le": "2026-10-18T10:00:00+00:00", "champs": {"ref": "C"}, "lots": L("2026-10-18T10:00:00+00:00", "partiel", 1)}}
        e = enrichir(items, fiches, None, None, None, {"lots_inaccessibles": {"pmmp:o1:9": {"tentatives": 3}}})
        lo = e["lots"]
        self.assertEqual(lo["couverture"], {"alloties": 3, "lues": 1, "partielles": 1, "inaccessibles": 0, "non_lues": 1, "lots": 3})
        self.assertNotIn("est_brut", lo["par_id"]["pmmp:o1:1"]["lots"][0])
        self.assertEqual([x["est"] for x in lo["par_id"]["pmmp:o1:1"]["lots"]], [100.0, 200.0], "valeurs par lot, pas de somme")
        self.assertNotIn("pmmp:o1:9", lo["inaccessibles"], "hors catalogue : non gardé")
        # passage suivant sans la fiche (ex. fichier fiches incomplet) : la lecture publiée est conservée ; une plus ancienne ne gagne pas
        old = {"pmmp:o1:1": {"lu_le": "2026-10-01T00:00:00+00:00", "champs": {"ref": "A"}, "lots": L("2026-10-01T00:00:00+00:00", n=1)}}
        e2 = enrichir(items, old, None, e, None)
        self.assertEqual(e2["lots"]["par_id"]["pmmp:o1:1"]["n"], 2)
        self.assertEqual(enrichir(items[1:], {}, None, e, None)["lots"]["par_id"].get("pmmp:o1:1"), None, "annonce retirée : élaguée")


if __name__ == "__main__":
    unittest.main()

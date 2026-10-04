"""Cycle complet sans serveur, hors réseau : file -> planifier -> kit (Chromium réel, portail FICTIF) -> resultat -> écritures.
La base est SIMULÉE avec les règles documentées d'ArtifactData (versions, if_version obligatoire sur un document existant,
lot tout-ou-rien, update qui fusionne) ; les dépôts d'assets sont simulés par des identifiants."""
import copy
import datetime
import json
import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
sys.path.insert(0, ICI)

import portail_fictif  # noqa: E402
from dce_kit import cycle  # noqa: E402
from dce_kit.tache import PHRASE  # noqa: E402
from test_kit import ENV_FICTIF, cli  # noqa: E402

UTC = datetime.timezone.utc


class BaseSimulee:
    """Règles d'ArtifactData reproduites : version par document, écriture refusée sans if_version sur un document existant,
    refus si la version a changé, lot atomique, update = fusion récursive."""
    def __init__(self):
        self.docs = {}

    def lire(self, coll, did):
        d = self.docs.get((coll, did))
        return None if d is None else {**copy.deepcopy(d["data"]), "__version": d["v"]}

    def collection(self, coll):
        return {did: self.lire(c, did) for (c, did) in self.docs if c == coll}

    @staticmethod
    def _fusion(a, b):
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                BaseSimulee._fusion(a[k], v)
            else:
                a[k] = copy.deepcopy(v)

    def lot(self, ecritures):
        for w in ecritures:
            ex = self.docs.get((w["collection"], w["doc_id"]))
            if ex and w.get("if_version") != ex["v"]:
                raise RuntimeError(f"version changée ou absente : {w['collection']}/{w['doc_id']}")
        for w in ecritures:
            k, ex = (w["collection"], w["doc_id"]), self.docs.get((w["collection"], w["doc_id"]))
            data = {x: y for x, y in w["data"].items() if x != "__version"}
            if w["op"] == "set" or not ex:
                self.docs[k] = {"data": copy.deepcopy(data), "v": (ex["v"] + 1) if ex else 1}
            else:
                self._fusion(ex["data"], data)
                ex["v"] += 1


class TestCycle(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.db = BaseSimulee()
        self.srv, self.portail = portail_fictif.demarrer()
        self.cfg = os.path.join(self.d, "config.json")
        json.dump({"base_url": f"http://127.0.0.1:{self.srv.server_address[1]}/index.php", "hote_autorise": "127.0.0.1"}, open(self.cfg, "w"))
        self.db.lot([{"op": "set", "collection": "dce_demande", "doc_id": "fx-test", "data": {
            "ao_id": "fx-test", "ref": "R-FICTIF-1", "org": "orgfictif", "etat": "demandee", "demande_par": "testeur",
            "demande_le": "2026-01-01T00:00:00Z"}}])

    def tearDown(self):
        self.srv.shutdown()

    def j(self, nom, obj):
        p = os.path.join(self.d, nom)
        json.dump(obj, open(p, "w"), ensure_ascii=False)
        return p

    def passage(self, run):
        """Un passage de tâche : planifier, prendre le bail, exécuter le kit, traduire le résultat, écrire."""
        f = self.j(f"file_{run}.json", self.db.collection("dce_demande"))
        plan_p = os.path.join(self.d, f"plan_{run}.json")
        code, _, err = cli("planifier", "--file", f, "--dossiers-autorises", "fx-test", "--run", run, "--sortie", plan_p)
        self.assertEqual(code, 0, err)
        plan = json.load(open(plan_p))
        if plan["ecritures"]:
            self.db.lot(plan["ecritures"])
        for a in plan["actions"]:
            etat_p = os.path.join(self.d, f"etat_{run}.json")
            args = [a["commande"], "--ref", a["ref"], "--org", a["org"], "--config", self.cfg, "--etat", etat_p]
            man = dep = None
            if a["commande"] == "telecharger":
                sortie = os.path.join(self.d, f"sortie_{run}")
                args += ["--validation", os.path.join(self.d, f"validation_{a['id']}.json"), "--sortie", sortie]
                cli(*args, env=ENV_FICTIF)
                if json.load(open(etat_p))["etat"] == "pret":
                    man = os.path.join(sortie, "manifest.json")
                    m = json.load(open(man))
                    dep = self.j(f"depots_{run}.json", {f["fichier_local"]: "asset-" + f["sha256"][:8] for f in m["fichiers"] + [m["zip"]]})
            else:
                cli(*args)
            dem = self.j(f"dem_{run}.json", self.db.lire("dce_demande", a["id"]))
            reg = self.db.lire("dcef", a["id"])
            opt = ["--registre", self.j(f"reg_{run}.json", reg)] if reg else []
            opt += ["--manifest", man, "--depots", dep] if man else []
            ecr_p = os.path.join(self.d, f"ecr_{run}.json")
            code, _, err = cli("resultat", "--id", a["id"], "--demande", dem, "--etat", etat_p, "--run", run, "--sortie", ecr_p, *opt)
            self.assertEqual(code, 0, err)
            self.db.lot(json.load(open(ecr_p)))
        return plan

    def valider_humain(self, empreinte=None):
        d = self.db.lire("dce_demande", "fx-test")
        le = datetime.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.db.lot([{"op": "update", "collection": "dce_demande", "doc_id": "fx-test", "if_version": d["__version"], "data": {
            "etat": "cg_validees", "validation": {"phrase": PHRASE, "empreinte": empreinte or d["cg"]["empreinte"], "par": "testeur", "le": le}}}])

    def test_cycle_complet(self):
        self.passage("r1")
        d = self.db.lire("dce_demande", "fx-test")
        self.assertEqual(d["etat"], "attente_validation_CG")
        self.assertIsNone(d["tache"])
        self.assertEqual(self.portail.soumis, [], "passage 1 : rien n'est soumis")
        p = self.passage("r2")
        self.assertEqual(p["actions"], [], "sans validation humaine, aucune action")
        self.valider_humain()
        self.portail.zip_date = (2026, 1, 1, 0, 0, 0)
        self.passage("r3")
        d, reg = self.db.lire("dce_demande", "fx-test"), self.db.lire("dcef", "fx-test")
        self.assertEqual(d["etat"], "pret", d.get("erreur"))
        self.assertEqual(len(self.portail.soumis), 1)
        self.assertEqual(sorted(reg["fichiers"]), ["dce_1000", "dce_1001", "dce_1002", "dceo_1000", "dcezip_1000"])
        self.assertEqual(reg["fichiers"]["dceo_1000"]["enc"], "base64")
        self.assertIsNone(self.db.lire("ao", "fx-test"), "le dossier lui-même n'est jamais écrit par la tâche")
        # nouvelle demande du même DCE : téléchargé à nouveau après une NOUVELLE validation, mais aucun doublon rattaché
        self.db.lot([{"op": "update", "collection": "dce_demande", "doc_id": "fx-test", "if_version": d["__version"], "data": {"etat": "demandee"}}])
        self.passage("r4")
        self.valider_humain()
        self.portail.zip_date = (2026, 1, 1, 0, 0, 2)  # même contenu, archive aux octets différents (portail qui régénère)
        self.passage("r5")
        d, reg2 = self.db.lire("dce_demande", "fx-test"), self.db.lire("dcef", "fx-test")
        self.assertNotEqual(d["resultat"]["zip_sha256"], reg["lots"][0]["zip"]["sha256"], "archives différentes en octets")
        self.assertTrue(d["resultat"]["deja_importe"], "doublon reconnu par le contenu")
        self.assertEqual(sorted(reg2["fichiers"]), sorted(reg["fichiers"]))

    def test_validation_non_conforme_rejetee(self):
        self.passage("r1")
        self.valider_humain(empreinte="autre")
        self.passage("r2")
        d = self.db.lire("dce_demande", "fx-test")
        self.assertEqual((d["etat"], d["erreur"]["code"]), ("attente_validation_CG", "validation"))
        self.assertEqual(self.portail.soumis, [])

    def test_403_echec_sans_nouvelle_tentative(self):
        d = self.db.lire("dce_demande", "fx-test")
        self.db.lot([{"op": "update", "collection": "dce_demande", "doc_id": "fx-test", "if_version": d["__version"], "data": {"ref": "R403"}}])
        self.passage("r1")
        self.passage("r2")
        d = self.db.lire("dce_demande", "fx-test")
        self.assertEqual((d["etat"], d["erreur"]["code"]), ("echec", "http_403"))
        self.assertEqual(len([v for v in self.portail.vues if "R403" in v]), 1)

    def test_dossier_non_autorise_ignore(self):
        self.db.lot([{"op": "set", "collection": "dce_demande", "doc_id": "reel-1", "data": {
            "ao_id": "reel-1", "ref": "X", "org": "Y", "etat": "demandee", "demande_le": "2026-01-01T00:00:00Z"}}])
        p = cycle.planifier(self.db.collection("dce_demande"), {"fx-test"}, "r1")
        self.assertEqual([a["id"] for a in p["actions"]], ["fx-test"])
        self.assertIn("reel-1", [i["id"] for i in p["ignorees"]])

    def test_deux_passages_concurrents_un_seul_gagne(self):
        file = self.db.collection("dce_demande")
        p1, p2 = cycle.planifier(file, {"fx-test"}, "rA"), cycle.planifier(file, {"fx-test"}, "rB")
        self.db.lot(p1["ecritures"])
        with self.assertRaises(RuntimeError):
            self.db.lot(p2["ecritures"])
        self.assertEqual(self.db.lire("dce_demande", "fx-test")["tache"]["run"], "rA")

    def test_bail_echu_echec_explicite(self):
        file = self.db.collection("dce_demande")
        self.db.lot(cycle.planifier(file, {"fx-test"}, "rA")["ecritures"])
        plus_tard = datetime.datetime.now(UTC) + datetime.timedelta(minutes=cycle.BAIL_MIN + 1)
        p = cycle.planifier(self.db.collection("dce_demande"), {"fx-test"}, "rB", maintenant=plus_tard)
        self.assertEqual(p["actions"], [])
        self.db.lot(p["ecritures"])
        self.assertEqual(self.db.lire("dce_demande", "fx-test")["erreur"]["code"], "interrompu")

    def test_depot_incomplet_rien_rattache(self):
        d = {"tache": {"run": "r"}, "__version": 3}
        m = {"zip": {"nom": "a.zip", "sha256": "z", "taille": 1, "fichier_local": "/z"},
             "fichiers": [{"nom": "RC.pdf", "chemin": "RC.pdf", "taille": 1, "sha256": "s", "depot": "pdf", "fichier_local": "/a"}]}
        w = cycle.resultat("fx-test", d, {"etat": "pret"}, "r", manifest=m, depots={"/a": "id1"})
        self.assertEqual(len(w), 1)
        self.assertEqual((w[0]["data"]["etat"], w[0]["data"]["erreur"]["code"]), ("echec", "depot"))

    def test_cli_versions_obligatoires(self):
        """Lecture réelle par out_dir : documents SANS version ; la CLI exige --versions et n'écrit jamais sans épinglage."""
        dossier = os.path.join(self.d, "lu", "dce_demande")
        os.makedirs(dossier)
        json.dump({k: v for k, v in self.db.lire("dce_demande", "fx-test").items() if k != "__version"}, open(os.path.join(dossier, "fx-test.json"), "w"))
        sortie = os.path.join(self.d, "plan.json")
        code, _, err = cli("planifier", "--file", dossier, "--dossiers-autorises", "fx-test", "--run", "r", "--sortie", sortie)
        self.assertNotEqual(code, 0)
        self.assertIn("--versions", err)
        code, _, err = cli("planifier", "--file", dossier, "--dossiers-autorises", "fx-test", "--run", "r", "--sortie", sortie, "--versions", self.j("v.json", {"fx-test": 1}))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.load(open(sortie))["ecritures"][0]["if_version"], 1)

    def test_resultat_drive_verifie_sans_asset(self):
        d = {"tache": {"run": "r"}, "validation": {"par": "testeur"}, "__version": 4}
        m = {"zip": {"nom": "a.zip", "sha256": "z" * 64, "taille": 10, "fichier_local": "/z"},
             "fichiers": [{"nom": "RC.pdf", "chemin": "DCE/RC.pdf", "taille": 3, "sha256": "s" * 64, "depot": "pdf", "fichier_local": "/a"}]}
        drv = {"ref": "fx-test", "statut": "verifie", "maj": "2026-10-04T18:45:52Z",
               "fichiers": [{"sha256": "z" * 64, "taille": 10, "drive_id": "1" * 20}, {"sha256": "s" * 64, "taille": 3, "drive_id": "2" * 20}]}
        w = cycle.resultat("fx-test", d, {"etat": "pret"}, "r", manifest=m, drive=drv)
        self.assertEqual([(x["collection"], x["if_version"]) for x in w], [("dce_demande", 4)], "aucune écriture dcef")
        r = w[0]["data"]["resultat"]
        self.assertEqual((w[0]["data"]["etat"], r["stockage"], r["fichiers"], r["verifie_le"]), ("pret", "drive", 2, "2026-10-04T18:45:52Z"))
        self.assertNotIn("1" * 20, json.dumps(w), "aucun identifiant Drive écrit dans EAIOS")
        w = cycle.resultat("fx-test", d, {"etat": "pret"}, "r", manifest=m, drive={**drv, "fichiers": drv["fichiers"][:1]})
        self.assertEqual((w[0]["data"]["etat"], w[0]["data"]["erreur"]["code"]), ("echec", "stockage"))
        self.assertIn("RC.pdf", w[0]["data"]["erreur"]["motif"])
        w = cycle.resultat("fx-test", d, {"etat": "pret"}, "r", manifest=m, drive={**drv, "statut": "stocke"})
        self.assertEqual(w[0]["data"]["erreur"]["motif"], "stockage Drive non vérifié")

    def test_resultat_refuse_sans_bail(self):
        with self.assertRaises(ValueError):
            cycle.resultat("fx-test", {"tache": {"run": "autre"}}, {"etat": "echec"}, "r")


if __name__ == "__main__":
    unittest.main()

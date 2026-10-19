"""Intégration du relevé des pièces (checkpoint du dépôt) avant les relectures réseau : validation stricte, SHA des lots,
jamais une lecture plus récente écrasée, date propre de l'inventaire, idempotence. Données fictives."""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import integrer_releve_pieces as IR  # noqa: E402
from veille.etat import Etat  # noqa: E402

DCE = {"type": "dce", "libelle": "Dossier de consultation", "taille": "1 Ko",
       "url": "index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=1&orgAcronyme=o1"}


def ent(r="1", o="o1", lu="2026-10-19T21:30:00+00:00", docs=None, preuve="liens_visibles", **kw):
    e = {"id": f"pmmp:{o}:{r}", "org": o, "ref_consultation": r, "reference": f"REF-{r}", "page_id": f"{o}:{r}", "lu_le": lu,
         "docs": [dict(DCE, url=DCE["url"].replace("=1&", f"={r}&").replace("=o1", f"={o}"))] if docs is None else docs,
         "docs_preuve": preuve, "version_lecture": 3}
    e.update(kw)
    return e


class Releve(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.etat = Etat(os.path.join(self.d, "etat"))
        for r in ("1", "2", "3", "4", "5"):
            self.etat.enregistrer_fiche(f"pmmp:o1:{r}", {"ref": f"REF-{r}", "obj": "O", "blocs_lus": ["contact"]},
                                        "2026-10-18T10:00:00+00:00", "r0", "x")

    def depot(self, entrees, casser=False):
        base = os.path.join(self.d, "depot", "veille_enrichissement", "releve_pieces")
        os.makedirs(base, exist_ok=True)
        b = json.dumps({"version": 1, "entrees": entrees}).encode()
        open(os.path.join(base, "lot_0001.json"), "wb").write(b)
        sha = hashlib.sha256(b).hexdigest()
        json.dump({"version": 1, "lots": [{"fichier": "lot_0001.json", "sha256": "0" * 64 if casser else sha, "n": len(entrees)}]},
                  open(os.path.join(base, "index.json"), "w"))
        return os.path.join(self.d, "depot")

    def run_(self, entrees, **kw):
        return IR.main(["--etat", os.path.join(self.d, "etat"), "--depot", self.depot(entrees, **kw),
                        "--rapport", os.path.join(self.d, "r.json")]) or json.load(open(os.path.join(self.d, "r.json")))

    def test_application_validation_et_date_propre(self):
        E = [ent("1"), ent("2", docs=[], preuve="liens_officiels_tous_masques"), ent("3", docs=[], preuve="structure_inattendue"),
             ent("4", page_id="o9:4"), ent("5", reference="AUTRE"), ent("6")]
        r = self.run_(E)
        self.assertEqual((r["appliquees"], r["avec_pieces"], r["vides_confirmes"]), (2, 1, 1))
        self.assertEqual(r["ignorees"], {"vide_sans_preuve": 1, "page_id": 1, "reference_differente": 1, "fiche_absente": 1})
        f = self.etat.fiche("pmmp:o1:1")
        self.assertEqual((f["lu_le"], f["champs"]["docs_lu_le"], f["champs"]["docs_source"]),
                         ("2026-10-18T10:00:00+00:00", "2026-10-19T21:30:00+00:00", "releve_pieces"), "date de la fiche inchangée")
        self.assertIn("docs", f["champs"]["blocs_lus"])
        self.assertEqual(self.run_(E)["appliquees"], 0, "idempotent")

    def test_jamais_ecraser_plus_recent_et_lot_corrompu(self):
        self.etat.enregistrer_fiche("pmmp:o1:1", {"ref": "REF-1", "obj": "O", "docs": [], "docs_preuve": "bloc_aucune_piece",
                                                  "blocs_lus": ["contact", "docs"]}, "2026-10-20T08:00:00+00:00", "r9", "y")
        r = self.run_([ent("1")])
        self.assertEqual((r["appliquees"], r["deja_a_jour_ou_plus_recent"]), (0, 1))
        self.assertEqual(self.etat.fiche("pmmp:o1:1")["champs"]["docs"], [])
        r = self.run_([ent("2")], casser=True)
        self.assertEqual((r["lots_lus"], r["lots_refuses_sha"], r["appliquees"]), (0, ["lot_0001.json"], 0))

    def test_liens_d_une_autre_consultation_refuses(self):
        r = self.run_([ent("1", docs=[dict(DCE, url=DCE["url"].replace("refConsultation=1", "refConsultation=9"))])])
        self.assertEqual(r["ignorees"], {"lien_autre_consultation": 1})
        r = self.run_([ent("2", docs=[dict(DCE, url="javascript:alert(1)")])])
        self.assertEqual(r["ignorees"], {"lien": 1})
        reg = {"type": "reglement", "libelle": "Règlement de consultation", "taille": None,
               "url": "index.php?page=entreprise.EntrepriseDownloadReglement&reference=Mw==&orgAcronyme=o1"}  # base64("3")
        self.assertEqual(self.run_([ent("3", docs=[reg])])["appliquees"], 1)
        r = self.run_([ent("4", docs=[dict(reg, url=reg["url"].replace("Mw==", "OQ=="))])])  # base64("9") : autre consultation
        self.assertEqual(r["ignorees"], {"lien_autre_consultation": 1})


if __name__ == "__main__":
    unittest.main()

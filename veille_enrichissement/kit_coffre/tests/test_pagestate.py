"""Lecture passive de l'état de page PRADO : contact publié ancré au résumé, identité, refus (structure, longueurs, zlib,
doublons, visibilité, gabarit). État SYNTHÉTIQUE de même structure que les pages officielles, valeurs fictives."""
import base64
import os
import sys
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from veille import pmmp_pagestate as PS  # noqa: E402


def S(s):
    b = s.encode()
    return b's:%d:"%s";' % (len(b), b)


def A(*paires):
    return b"a:%d:{" % len(paires) + b"".join(k + v for k, v in paires) + b"}"


def I(n):
    return b"i:%d;" % n


def T(t):
    return A((I(0), A((S("Text"), S(t)))))


def O(cls, *paires):
    c = cls.encode()
    return b'O:%d:"%s":%d:{' % (len(c), c, len(paires)) + b"".join(k + v for k, v in paires) + b"}"


def etat(ref="REF/2026", obj="Objet fictif", nom="Agent Fictif", email="contact.fictif@example.org", tel="0500000000",
         fax="0500000001", visible=True, panneau_double=False, resume_double=False):
    props = A((S("Style"), O("TPanelStyle", (S("\x00TPanelStyle\x00_d"), b"N;")))) if visible else A((S("Visible"), b"b:0;"))
    detail = A((S("email"), T(email) if email is not None else A()), (S("telephone"), T(tel)), (S("telecopieur"), T(fax)))
    panneau = A((S("ctl37"), A()), (S("contactAdministratif"), T(nom)), (S("blocDetailContactAdministratif"), detail), (I(0), props))
    enfants = [(S("reference"), T(ref)), (S("ctl3"), A()), (S("objet"), T(obj)), (S("panelContcatAdministratif"), panneau)]
    if panneau_double:
        enfants.append((S("ctl9"), A((S("panelContcatAdministratif"), panneau))))
    resume = A(*enfants)
    racine = [(S("ctl0"), A((S("idEntrepriseConsultationSummary"), resume)))]
    if resume_double:
        racine.append((S("ctl1"), A((S("idEntrepriseConsultationSummary"), resume))))
    racine.append((S("zoneEntreprise"), A((S("jeton"), S("ne-jamais-lire")))))
    return b"0123456789abcdef0123456789abcdef01234567" + A(*racine)  # préfixe d'empreinte fictif (40 hex)


def page(b, ref="1041719", org="e5w", brut=None, double=False):
    v = brut if brut is not None else base64.b64encode(zlib.compress(b)).decode()
    inp = f'<input type="hidden" name="PRADO_PAGESTATE" id="PRADO_PAGESTATE" value="{v}" />'
    return (f'<form id="ctl0_ctl1" method="post" action="/index.php?page=entreprise.EntrepriseDetailsConsultation&amp;'
            f'refConsultation={ref}&amp;orgAcronyme={org}">' + inp + (inp if double else "") + "</form>")


def lire(h, ref_page="REF/2026", obj_page="Objet fictif"):
    return PS.lire_contact(h, "e5w", "1041719", ref_page, obj_page)


class Contact(unittest.TestCase):
    def test_contact_publie_lu_sous_le_resume(self):
        c, m = lire(page(etat()))
        self.assertIsNone(m)
        self.assertEqual(c, {"nom": "Agent Fictif", "email": "contact.fictif@example.org", "tel": "0500000000", "fax": "0500000001"})

    def test_tiret_publie_vaut_non_indique(self):
        c, _ = lire(page(etat(fax="-")))
        self.assertIsNone(c["fax"])

    def test_identite_differente(self):
        self.assertIsNone(lire(page(etat()), ref_page="AUTRE")[0])
        self.assertIsNone(lire(page(etat(obj="Autre objet")))[0])
        self.assertIsNone(lire(page(etat(), org="x9z"))[0], "même référence chez un autre acheteur : contexte refusé")
        self.assertIsNone(lire(page(etat(), ref="1041720"))[0])
        self.assertIsNone(lire(page(etat()).replace("<form", "<div"))[0], "contexte de page absent")

    def test_doublons_refuses(self):
        self.assertIsNone(lire(page(etat(panneau_double=True)))[0])
        self.assertIsNone(lire(page(etat(resume_double=True)))[0])
        self.assertIsNone(lire(page(etat(), double=True))[0], "deux états de page")

    def test_longueurs_tailles_zlib_invalides(self):
        b = etat()
        self.assertIsNone(lire(page(b.replace(b's:12:"Agent Fictif"', b's:13:"Agent Fictif"')))[0])
        self.assertIsNone(lire(page(b[:-1]))[0], "structure tronquée")
        self.assertIsNone(lire(page(b + b"i:1;"))[0], "données après la racine")
        self.assertIsNone(lire(page(b[40:]))[0], "préfixe d'empreinte absent")
        self.assertIsNone(lire(page(b, brut="pas-du-base64!"))[0])
        self.assertIsNone(lire(page(b, brut=base64.b64encode(b"pas du zlib").decode()))[0])
        self.assertIsNone(lire(page(b, brut=base64.b64encode(zlib.compress(b)[:-6]).decode()))[0], "flux zlib incomplet")
        bombe = base64.b64encode(zlib.compress(b"x" * (PS.MAX_ETAT + 10))).decode()
        self.assertIsNone(lire(page(b, brut=bombe))[0], "état décompressé trop grand")
        self.assertIsNone(lire(page(b"").replace('value=""', 'value=""'))[0])

    def test_panneau_invisible_et_gabarit(self):
        self.assertEqual(lire(page(etat(visible=False)))[1], "panneau du contact invisible")
        self.assertIsNone(lire(page(etat(email="@@@@")))[0])
        self.assertIsNone(lire(page(etat(email=None)))[0], "valeur non portée par l'état (gabarit HTML) : non lue")

    def test_rien_hors_du_resume(self):
        c, _ = lire(page(etat()))
        self.assertNotIn("ne-jamais-lire", repr(c))


if __name__ == "__main__":
    unittest.main()

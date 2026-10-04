"""Mode proxy_oauth : le proxy de l'environnement (identifiant d'API « Body parameter ») est SIMULÉ ici. Il intercepte la seule
requête POST /token, retire Authorization et les champs homonymes, ajoute client_id, client_secret et refresh_token depuis un
coffre FICTIF, puis transmet au faux serveur Google local. Aucun réseau réel, aucun identifiant réel."""
import logging
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_drive import MO, Base  # noqa: E402
from drive_adapter import Drive, ErreurAuth, sha256_fichier  # noqa: E402
from drive_adapter.drive_resumable import _SansRedirection  # noqa: E402

COFFRE = {"client_id": "client-fictif.apps.example", "client_secret": "SECRET-FICTIF-123", "refresh_token": "refresh-fictif-456"}


class ProxySimule:
    """Reproduit le comportement décrit pour « Body parameter » : seulement pour l'hôte et le chemin listés."""
    def __init__(self, url_jeton, coffre=COFFRE):
        self.cible, self.coffre, self.vues = urllib.parse.urlparse(url_jeton), coffre, []
        self.ouvrir_reel = urllib.request.build_opener(_SansRedirection).open

    def __call__(self, req, timeout=None):
        u = urllib.parse.urlparse(req.full_url)
        self.vues.append({"url": req.full_url, "methode": req.get_method(), "entetes": dict(req.header_items()), "corps": req.data if u.path == self.cible.path else None})
        if (u.hostname, u.port, u.path) == (self.cible.hostname, self.cible.port, self.cible.path) and req.get_method() == "POST":
            champs = dict(urllib.parse.parse_qsl((req.data or b"").decode()))
            for k in self.coffre:
                champs.pop(k, None)  # clés homonymes retirées avant injection
            champs.update(self.coffre)
            req = urllib.request.Request(req.full_url, data=urllib.parse.urlencode(champs).encode(), method="POST",
                                         headers={k: v for k, v in req.header_items() if k.lower() not in ("authorization", "content-length")})
        return self.ouvrir_reel(req, timeout=timeout)


class Horloge:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t


class TestProxyOAuth(Base):
    def drive_proxy(self, horloge=None):
        self.proxy = ProxySimule(self.urls["jeton"])
        return Drive(env={}, urls=self.urls, morceau=MO, pause_s=0, tests_locaux=True, ouvrir=self.proxy, auth="proxy_oauth", horloge=horloge or Horloge())

    def jetons_avant_proxy(self):
        return [v for v in self.proxy.vues if urllib.parse.urlparse(v["url"]).path == "/token"]

    def test_requete_avant_proxy_sans_secret(self):
        d = self.drive_proxy()
        d.envoyer(self.f, "DCE_fictif.bin")
        J = self.jetons_avant_proxy()
        self.assertEqual(len(J), 1)
        self.assertEqual(J[0]["corps"], b"grant_type=refresh_token", "seul grant_type part de la session")
        self.assertFalse(any(k.lower() == "authorization" for k in J[0]["entetes"]))
        brut = repr(self.proxy.vues)
        for secret in COFFRE.values():
            self.assertNotIn(secret, brut, "aucun secret dans une requête émise par l'adaptateur")
        self.assertEqual(self.et.corps_jeton, [["client_id", "client_secret", "grant_type", "refresh_token"]], "le proxy a injecté les trois champs")
        self.assertFalse(hasattr(d, "_secret") or hasattr(d, "_refresh"), "l'adaptateur ne détient aucun secret")

    def test_aller_retour_sha_et_jeton_jamais_dans_url(self):
        r = self.drive_proxy().envoyer(self.f, "DCE_fictif.bin")
        sortie = os.path.join(self.d, "relu.bin")
        g = self.drive_proxy().recuperer(r["id"], sortie, self.sha, os.path.getsize(self.f))
        self.assertEqual((g["sha256"], sha256_fichier(sortie)), (self.sha, self.sha))
        self.assertFalse(any("tok-" in v["url"] for v in self.proxy.vues), "jeton d'accès jamais dans une URL")

    def test_renouvellement_anticipe_a_expiration(self):
        h = Horloge()
        self.et.duree_jeton = 120  # renouvelé 60 s avant l'expiration
        d = self.drive_proxy(h)
        r = d.envoyer(self.f, "DCE_fictif.bin")
        self.assertEqual(self.et.emis, 1)
        h.t += 61
        d.recuperer(r["id"], os.path.join(self.d, "a.bin"), self.sha)
        self.assertEqual(self.et.emis, 2, "jeton renouvelé avant son expiration, sans attendre un 401")
        self.assertTrue(all(v["corps"] == b"grant_type=refresh_token" for v in self.jetons_avant_proxy()))

    def test_401_un_seul_renouvellement_puis_erreur(self):
        self.et.toujours_401 = True
        msg = self.attendre_erreur(ErreurAuth, lambda: self.drive_proxy().envoyer(self.f, "x"))
        self.assertEqual(self.et.emis, 2, "un seul renouvellement sur 401, pas de boucle")
        self.assertIn("401", msg)

    def test_coffre_incomplet_erreur_explicite(self):
        d = self.drive_proxy()
        self.proxy.coffre = {"client_id": "client-fictif.apps.example"}
        msg = self.attendre_erreur(ErreurAuth, lambda: d.envoyer(self.f, "x"))
        self.assertIn("Body parameter", msg)
        self.assertEqual((self.et.sessions, self.et.puts), ({}, 0))

    def test_jeton_ni_fichier_ni_journal(self):
        etat = os.path.join(self.d, "envoi.etat")

        def arret(offset):
            raise KeyboardInterrupt
        d = self.drive_proxy()
        with self.assertRaises(KeyboardInterrupt):
            d.envoyer(self.f, "DCE_fictif.bin", etat=etat, apres_morceau=arret)
        with open(etat) as x:
            self.assertNotIn("tok-", x.read(), "jeton d'accès jamais écrit dans le fichier d'état")
        logging.getLogger("drive_adapter").info("contrôle")

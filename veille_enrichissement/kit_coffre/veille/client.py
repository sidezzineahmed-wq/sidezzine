"""Client HTTP prudent pour le portail public PMMP (aucun login, aucun secret).

- au moins DELAI_MIN secondes (+ gigue) entre deux requêtes, toutes requêtes confondues ;
- quelques reprises seulement, avec attente croissante, sur erreurs réseau / 5xx / 429 ;
- aucune tentative de contournement : un 403 ou une page de contrôle arrête la collecte ;
- délais réseau bornés (connexion 30 s, lecture `timeout`) et échéance globale facultative (`echeance`, horloge
  monotone) : au-delà, aucune nouvelle requête n'est envoyée (ArretCollecte « budget de temps atteint »).
"""
import os
import random
import time

import requests

BASE = "https://www.marchespublics.gov.ma/index.php"
UA = "Mozilla/5.0 (EAIOS veille catalogue; usage interne gerance)"


class ArretCollecte(RuntimeError):
    """Le portail refuse ou répond de façon inattendue : on s'arrête, on ne contourne pas."""


class ClientPMMP:
    def __init__(self, delai_min=3.0, gigue=1.5, reprises=2, timeout=90, journal=None):
        if delai_min < 2.0:
            raise ValueError("delai_min < 2 s refusé (débit prudent)")
        self.delai_min, self.gigue, self.reprises, self.timeout = delai_min, gigue, reprises, timeout
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.s.headers["Accept-Language"] = "fr"
        ca = os.environ.get("REQUESTS_CA_BUNDLE")
        if ca:
            self.s.verify = ca
        self._dernier = 0.0
        self.nb_requetes = 0
        self.octets_recus = 0
        self.echeance = None  # time.monotonic() au-delà duquel plus aucune requête n'est envoyée
        self.journal = journal  # callable(dict) facultatif

    def _attendre(self):
        reste = self.delai_min + random.uniform(0, self.gigue) - (time.monotonic() - self._dernier)
        if reste > 0:
            time.sleep(reste)

    def _req(self, methode, url, **kw):
        err = None
        for essai in range(self.reprises + 1):
            self._attendre()
            reste = None if self.echeance is None else self.echeance - time.monotonic()
            if reste is not None and reste < 5:
                raise ArretCollecte(f"budget de temps du passage atteint avant {methode} : arrêt propre (rien n'est conclu)")
            t0 = time.monotonic()
            try:
                lecture = self.timeout if reste is None else max(5.0, min(self.timeout, reste))
                r = self.s.request(methode, url, timeout=(min(30.0, lecture), lecture), stream=True, **kw)
                morceaux = []
                for m in r.iter_content(65536):  # le délai de lecture ne borne que le silence : l'échéance borne le total
                    morceaux.append(m)
                    if self.echeance is not None and time.monotonic() > self.echeance:
                        r.close()
                        raise ArretCollecte(f"budget de temps du passage atteint pendant la réception ({methode}) : "
                                            "arrêt propre (rien n'est conclu)")
                r._content, r._content_consumed = b"".join(morceaux), True
            except requests.RequestException as e:
                err = e
                r = None
            finally:
                self._dernier = time.monotonic()
                self.nb_requetes += 1
            if r is not None:
                self.octets_recus += len(r.content)
                if self.journal:
                    self.journal({"m": methode, "url": r.url[:200], "code": r.status_code, "octets": len(r.content),
                                  "encodage": r.headers.get("Content-Encoding"), "duree_s": round(time.monotonic() - t0, 1)})
                if r.status_code in (401, 403):
                    raise ArretCollecte(f"HTTP {r.status_code} sur {url} : arrêt (pas de contournement)")
                if r.status_code == 200:
                    return r
                err = RuntimeError(f"HTTP {r.status_code}")
                if r.status_code not in (429, 500, 502, 503, 504):
                    break
            if self.echeance is not None and self.echeance - time.monotonic() < 10 * (essai + 1) + 5:
                break
            time.sleep(10 * (essai + 1))
        raise ArretCollecte(f"échec {methode} {url} : {err}")

    def get(self, params):
        return self._req("GET", BASE, params=params)

    def post(self, url, data):
        return self._req("POST", url, data=data)


def texte(r):
    """Le portail mélange UTF-8 et quelques octets latin-1 (commentaires) : décodage tolérant."""
    return r.content.decode("utf-8", "replace")

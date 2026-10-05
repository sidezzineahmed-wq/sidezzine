import json
import os
import re
from dataclasses import dataclass, field

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ConfigInvalide(ValueError):
    pass


@dataclass
class Identite:
    """Identité saisie sur le formulaire. Fournie par l'exploitant (variables DCE_NOM, DCE_PRENOM, DCE_EMAIL) :
    jamais inventée, jamais complétée par défaut, jamais écrite dans ce dépôt."""
    nom: str
    prenom: str
    email: str

    def verifier(self):
        if not (self.nom.strip() and self.prenom.strip() and EMAIL.match(self.email.strip())):
            raise ConfigInvalide("identité incomplète : DCE_NOM, DCE_PRENOM et DCE_EMAIL valides sont exigés")


@dataclass
class Config:
    identite: Identite
    base_url: str = "https://www.marchespublics.gov.ma/index.php"
    hote_autorise: str = "www.marchespublics.gov.ma"
    chromium: str = ""                        # chemin d'un Chromium déjà installé (sinon celui de Playwright)
    confiance_navigateur: str = ""            # "" (défaut) ou "proxy_ccr" : autorité OFFICIELLE de l'environnement, revue (confiance.py)
    racine_travail: str = ""                  # dossier de travail (hors /tmp) où créer le magasin NSS temporaire
    zip_max: int = 200 * 2**20
    cg_validite_h: int = 24                   # une validation humaine de CG non utilisée expire
    delai_page_s: int = 90                    # chargement d'une page du portail
    delai_debut_telechargement_s: int = 300   # début du téléchargement après le clic (premier essai réel : ~2 min au total)
    delai_fin_transfert_s: int = 900          # fin du transfert de l'archive

    @staticmethod
    def charger(chemin=None, env=os.environ, identite_requise=True):
        d = {}
        if chemin:
            with open(chemin, encoding="utf-8") as f:
                d = json.load(f)
        if not isinstance(d, dict):
            raise ConfigInvalide("le fichier de configuration doit contenir un objet JSON")
        d = {k: v for k, v in d.items() if not str(k).startswith("_")}  # clés de commentaire (« _note ») ignorées
        inconnus = sorted(set(d) - (set(Config.__dataclass_fields__) - {"identite"}))
        if inconnus:
            raise ConfigInvalide("clés de configuration inconnues : " + ", ".join(inconnus))
        for cle, var in (("confiance_navigateur", "DCE_CONFIANCE_NAVIGATEUR"), ("racine_travail", "DCE_RACINE_TRAVAIL")):
            if not d.get(cle) and env.get(var):
                d[cle] = env[var]
        idt = Identite(env.get("DCE_NOM", ""), env.get("DCE_PRENOM", ""), env.get("DCE_EMAIL", ""))
        c = Config(identite=idt, **d)
        if identite_requise:
            c.identite.verifier()
        if c.confiance_navigateur not in ("", "proxy_ccr"):
            raise ConfigInvalide("confiance_navigateur : seul « proxy_ccr » est accepté (aucun certificat arbitraire)")
        if c.delai_debut_telechargement_s < 120 or c.delai_fin_transfert_s < c.delai_debut_telechargement_s:
            raise ConfigInvalide("délais de téléchargement trop courts (début ≥ 120 s, fin de transfert ≥ début)")
        return c

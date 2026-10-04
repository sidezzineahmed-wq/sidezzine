# Kit DCE générique (tâche cloud finie)

Récupère le dossier de consultation (DCE) d'une consultation publique du portail des marchés publics, en deux temps
séparés par une **validation humaine des conditions générales (CG) pour chaque téléchargement**. Aucun serveur permanent :
chaque commande est une étape courte d'une tâche cloud, et écrit un JSON d'état.

| Commande | Effet | Autorisée d'avance (`.claude/settings.json`) |
|---|---|---|
| `verifier-env` | Playwright importable, Chromium lançable (page vide locale) | oui |
| `ouvrir` | Ouvre la page DCE, vérifie ref/org, lit les CG et l'empreinte. **Ne remplit, ne coche, ne soumet rien.** | oui |
| `telecharger` | Exige la validation humaine (phrase exacte, empreinte, moins de 24 h), refuse si les CG ont changé, saisit l'identité de l'exploitant, soumet, capture l'archive | **non** : approbation à chaque exécution |
| `preparer` | Contrôle le ZIP ; PDF tels quels, autres fichiers et ZIP d'origine en base64 ; `manifest.json` avec SHA-256 | oui |

- 401/403, page de contrôle ou CAPTCHA : état `echec`, code de sortie 2, **aucune nouvelle tentative**, aucun contournement.
- L'identité vient des variables d'environnement `DCE_NOM`, `DCE_PRENOM`, `DCE_EMAIL` de l'exploitant ; elle n'est jamais
  écrite dans ce dépôt.
- Délais : page 90 s, début du téléchargement 300 s, fin du transfert 900 s.

Installation et tests (hors réseau, portail FICTIF local, Chromium réel) :

    pip install -r kit_dce/requirements.txt
    python3 -m unittest discover -s kit_dce/tests -v

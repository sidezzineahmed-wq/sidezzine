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
| `planifier` | Lit la file `dce_demande` (export ArtifactData), choisit au plus une action, rend les écritures qui prennent le bail (épinglées `if_version`) | oui |
| `resultat` | Traduit l'état d'une commande en écritures épinglées : `dce_demande` et registre `dcef` (clés `dce_1000+`), anti-doublon par empreinte du ZIP **et du contenu** | oui |

Cycle d'une tâche cloud finie (aucun serveur) : lecture de la file par ArtifactData → `planifier` → lot ArtifactData du bail →
`ouvrir` ou `telecharger` → `preparer` → dépôt des fichiers par Artifact (asset) → `resultat` → lot ArtifactData. La tâche
n'écrit jamais le document du dossier ; la validation des CG est écrite par un humain depuis la page.

- 401/403, page de contrôle ou CAPTCHA : état `echec`, code de sortie 2, **aucune nouvelle tentative**, aucun contournement.
- L'identité vient des variables d'environnement `DCE_NOM`, `DCE_PRENOM`, `DCE_EMAIL` de l'exploitant ; elle n'est jamais
  écrite dans ce dépôt.
- Délais : page 90 s, début du téléchargement 300 s, fin du transfert 900 s.

Installation et tests (hors réseau, portail FICTIF local, Chromium réel) :

    pip install -r kit_dce/requirements.txt
    python3 -m unittest discover -s kit_dce/tests -v

## Stockage privé dans Google Drive (`drive_adapter/`, optionnel)

Au lieu des dépôts Artifact, une tâche peut ranger le DCE dans le Google Drive du compte exploitant (portée `drive.file`) :

    (cd kit_dce && python3 -m drive_adapter stocker-dce --ref <id du dossier> --zip <archive> [--demande-le <ISO>] [--etat-dir <dossier>])
    (cd kit_dce && python3 -m drive_adapter etat-dce --ref <id>)      # lecture seule : statut et fichiers rangés
    (cd kit_dce && python3 -m drive_adapter lister-dce)               # lecture seule : consultations rangées

- Arborescence `EAIOS_DCE_PRIVE/DCE_<ref>/` : archive d'origine et chaque document, manifeste `eaios_dce_manifeste_<ref>.json`
  avec statuts horodatés (UTC) `demande → acquis → stockage → stocke → verifie` ou `echec`, taille, SHA-256, MD5 et identifiant
  Drive par fichier. Aucun partage, aucun changement de droits. Un identifiant Drive n'est pas une adresse de téléchargement.
- Idempotent : un fichier déjà rangé (même SHA-256, même taille) n'est pas renvoyé ; une session neuve reprend depuis Drive.
  Les lectures (`etat-dce`, `lister-dce`) ne créent rien.
- Authentification `DCE_GDRIVE_AUTH=proxy_oauth` : la tâche n'envoie que `grant_type=refresh_token` à
  `https://oauth2.googleapis.com/token` ; `client_id`, `client_secret` et `refresh_token` sont ajoutés par le proxy de
  l'environnement (identifiant d'API « Body parameter » limité à cet hôte et au chemin `/token`). Aucun secret dans ce dépôt,
  aucun jeton écrit sur disque ni dans les journaux.
- `resultat --drive <sortie de stocker-dce>` (au lieu de `--depots`) : le dossier n'est marqué prêt que si Drive a vérifié
  tous les fichiers du manifest ; aucune entrée n'est écrite dans `dcef`.
- Fichier d'état de reprise : droits `0600` sous Linux (chemin d'exécution prévu). Sous Windows ces droits ne s'appliquent pas.

Tests (hors réseau, faux serveur Google local, proxy simulé) :

    (cd kit_dce/drive_adapter_tests && python3 -m unittest discover -s . -t .)

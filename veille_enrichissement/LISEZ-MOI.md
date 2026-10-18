# Enrichissement PMMP du catalogue EAIOS (B1.1 Veille)

Produit `catalogue_pmmp_enrichi.json`, publié **à côté** de `catalogue.json` dans l'artefact EAIOS. Ce fichier est joint
au catalogue :
- par annonce, avec la clé `pmmp:<org>:<ref>` ;
- par entité publique, avec le code PMMP `<org>`.

Le schéma à 31 champs de `catalogue.json` n'est pas modifié, ni l'ingestion horaire : celle-ci ne republie que les
quatre fichiers `catalogue*.json` et laisse ce fichier intact.

## Sources officielles (vérifiées le 17-18/10/2026)

Formulaire public : <https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons=>

### Etat / CL / EEP

Liste source : `ctl0$CONTENU_PAGE$AdvancedSearch$classification`, avec les valeurs 1 Etat, 2 Collectivité locale,
3 Etablissement public.

Le panneau qui la contient est masqué tant que le mode « Recherche dans une liste » n'est pas choisi
(`type_rechercheEntite=exact`). La liste est un `TActiveDropDownList` PRADO : son rappel renvoie la liste officielle des
entités publiques (`organismesNames`) de la classification choisie.

Relevé du 17/10, 23:55 UTC :
- 77 entités = 57 Etat + 16 Collectivités locales (les Régions) + 4 Etablissements publics ;
- partition exacte : ni chevauchement, ni absence.

Contrôle par la recherche filtrée (mode liste + classification), à 23:58 UTC :
- totaux 3 443 + 964 + 12 = 4 419, égal au total non filtré ;
- les 964 et 12 annonces renvoyées (relevées intégralement) appartiennent toutes à une entité de la même classification.

> L'ancien constat du kit (« filtre ignoré par le portail », 02/10) venait d'une recherche lancée sans
> `type_rechercheEntite=exact` : le filtre n'est appliqué qu'en mode liste.

**Règle d'attribution.** La classification est celle de l'**entité publique** de rattachement, c'est-à-dire
l'`orgAcronyme` de l'annonce. Ce rattachement est unique.

**Cas particuliers.**
- Une entité absente de la liste relevée, ou présente dans plusieurs listes, donne une classification inconnue.
- Aucune déduction par le nom (Commune, SA, Ministère…) ni par l'ancien champ `cls`.
- Exemple : les acheteurs rattachés au « Ministère de l'Intérieur » (y compris les communes et les sociétés régionales)
  sont classés « Etat » par PMMP. C'est ce que filtre le portail.

### Mode de passation

Source : élément `ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_modePassation` de la fiche publique d'une
consultation, affiché après la procédure. Exemple : « Procédure : Appel d'offres ouvert | Sur offre de prix ».

Valeurs observées : « Sur offre de prix » et « Au rabais / majoration ».

Le mode est **distinct de la procédure**. Ne pas confondre avec la liste du formulaire libellée « Mode de passation »
(`procedureType`), qui contient les **procédures** : ses codes sont relevés comme identifiants PMMP des procédures
(1 « Appel d'offres ouvert », 50 « Appel d'offres ouvert simplifié »…).

Le formulaire n'a pas de champ national/international.

Origine des valeurs, toutes avec leur date de lecture réelle :
1. `fiches.json` du collecteur (coffre), champ `mode_passation`, que l'analyseur de fiche lisait déjà sans l'exporter ;
2. le complément borné ci-dessous.

La jointure n'est utilisée que si la référence lue est égale à celle du catalogue. Une annonce sans lecture est
« non renseignée », jamais une valeur par défaut.

## Commandes

```
# relevé officiel borné (≈ 12 requêtes, ≥ 4 s entre elles, client du kit : arrêt sur 401/403)
python3 enrichir_pmmp.py releve --kit <coffre>/stock/kit --sortie <dossier>

# complément borné et repris (cache par fiche ; date limite la plus proche d'abord ; contacts tronqués avant analyse)
python3 enrichir_pmmp.py completer --kit <coffre>/stock/kit --catalogue catalogue.json \
    --fiches <coffre>/stock/etat/fiches.json --cache <dossier_cache> --max 100 --aujourdhui AAAA-MM-JJ

# construction hors ligne, idempotente, sans perte (la lecture la plus récente gagne ; rien n'est supprimé)
python3 enrichir_pmmp.py construire --catalogue catalogue.json --releve releve_classification.json \
    --fiches <coffre>/stock/etat/fiches.json --complement <dossier_cache> \
    --precedent catalogue_pmmp_enrichi.json --sortie catalogue_pmmp_enrichi.json
```

`construire` refuse (code 2) un relevé dont la partition n'est pas vérifiée. Il n'écrit que `--sortie`.

Tests : `KIT_VEILLE=<coffre>/stock/kit python3 -m unittest discover -s tests -v`.

## Intégration au passage horaire (en place depuis le 18/10/2026)

Le passage horaire existant a été conservé tel quel : même tâche, même fréquence, mêmes permissions, mêmes quatre fichiers
publiés.

**Ce qui a changé dans le kit.** Le kit qu'il recharge depuis le coffre (`stock/kit`, version 331 du coffre, publiée le
18/10 à 00:26 UTC) contient désormais :
- `ingestion/enrichi_pmmp.py`, appelé par `ingestion/ingestion_catalogue.py` ;
- le référentiel `referentiel/classification_entites.json` (relevé officiel ci-dessus) ;
- les tests `ingestion/test_enrichi_pmmp.py`, exécutés par l'étape « tests ingestion » de chaque passage.

**Ce que fait chaque passage.** `catalogue_details.json` reçoit la clé `pmmp_enrichi`. Les modes de passation sont lus
dans `fiches.json` (le collecteur lit déjà `modePassation` sur chaque fiche) et repris de la publication précédente :
aucune perte. Le schéma de `catalogue.json` et les trois autres fichiers sont identiques octet pour octet à ceux de
l'ancien kit (essai sur les données réelles du 18/10).

**Ce qui reste manuel.**
- Une nouvelle entité publique inconnue reste « inconnue » jusqu'à un nouveau `releve`, qui met à jour le référentiel du kit.
- Le complément borné (`completer`) n'est pas lancé par le passage horaire : il sert ponctuellement et ses lectures sont
  reprises comme « précédentes ».

Copie de revue du kit modifié : `kit_coffre/`.

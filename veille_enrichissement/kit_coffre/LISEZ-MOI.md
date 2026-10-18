# Kit Veille PMMP — producteur du catalogue (isolé)

Ce kit produit **uniquement** `catalogue.json` au format EAIOS : 31 champs par item, `regions`, `maj`, `total_portail`, `n` et `n_details`.

Ce qu'il ne fait pas :

- il n'écrit pas dans EAIOS et ne publie rien ;
- il ne planifie aucune exécution ;
- il ne se connecte à aucun compte et n'utilise aucun secret.

Source : le portail public www.marchespublics.gov.ma, en lecture anonyme.

## Installation sur PC (Windows)

```
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v        (tests sans réseau)
```

## Utilisation (manuelle)

```
python maj_quotidienne.py --etat donnees --fiches 50
python construire_catalogue.py --etat donnees --sortie sortie\catalogue.json
```

- `maj_quotidienne.py` lit le listing des consultations en cours (500 lignes par page, toutes les pages par défaut). `--max-pages N` limite le nombre de pages. Il lit ensuite au plus N fiches, par priorité stricte : (1) les fiches dont le listing a changé (date/heure limite, objet, référence…) après leur dernière lecture ; (2) les nouvelles, jamais lues (jamais tentées d'abord, puis les plus récemment apparues) ; (3) les lectures les plus anciennes (au moins 24 h, `--age-min-relecture-h`). Le journal `selection.json` garde la date du dernier choix et les échecs de chaque fiche entre les passages : une fiche en échec est mise en pause (6 h, doublée à chaque échec, max 48 h) et une fiche choisie récemment ne revient pas avant 24 h. `--sans-relecture` désactive la relecture des anciennes. Le nombre de pages vient du portail ; si le total ou le nombre de pages change pendant le parcours, le passage est PARTIEL.
- Le débit est d'au moins 3 s par requête, plus une gigue. Une valeur sous 2 s est refusée. La collecte s'arrête net sur un 401/403 ou une page inattendue : rien n'est contourné.
- `construire_catalogue.py` travaille hors ligne. Il valide le schéma et les identifiants, puis écrit `catalogue.json` et `catalogue_rapport.json`. Si la validation échoue, il n'écrit rien (code de sortie 2).

## État persistant (`--etat`)

| Registre | Fichier | Contenu |
|---|---|---|
| Dernier listing | `listing.json` | Par id `pmmp:<org>:<refConsultation>` : champs vus au listing, `premier_vu`, `dernier_vu_listing`, changements constatés (ex. report de date) |
| Couverture | `couverture/<run>.json` | Pour chaque passage : total annoncé, pages et lignes lues, statut, familles couvertes et manquantes, journal HTTP (sans contenu) |
| Journal de sélection | `selection.json` | Par id : `dernier_choix`, `tentatives`, `echecs_consecutifs`, `dernier_echec` |
| Dernière lecture de fiche | `fiches/<org>_<ref>.json` | Champs de la fiche et `lu_le`, la date de la lecture réelle |
| Snapshots | `snapshots/<run>/*.html.gz` | HTML public brut ; les fiches sont tronquées avant le bloc des contacts |

Règles appliquées :

- **Fiches** : une fiche n'est réécrite que par une nouvelle lecture réelle. Un listing ne la re-date jamais. Si un listing plus récent la contredit, elle est marquée « à relire » dans le rapport.
- **Aucune suppression sur absence** : une collecte partielle ne marque rien. Un listing complet incrémente seulement `absences_listing_complet`. L'exclusion n'a lieu que si la date limite connue est passée, ou sur l'option `--exclure-absents-complets N`.
- **Information absente** : elle vaut `null`, ou `[]` pour les listes. Quand `det=false`, tous les champs de fiche sont null.
- **Contact administratif** : il n'est jamais lu ni stocké. Les téléphones et e-mails présents dans `vis`, `reu` et `proto` sont masqués.

## Dérivations (constatées sur le portail le 2026-10-02)

- **`nat`** : la liste des lieux du portail contient « MAROC ».
- **`lx` et `etr`** : `lx` reçoit les lieux du référentiel `referentiel/regions.json`, ainsi que les 3 alias constatés dans `alias_lieux.json`. Les autres lieux vont dans `etr`.
- **`lots`** : le pictogramme « Détail des lots » est visible.
- **`env`** : le bloc « dispositions environnementales » est présent.
- **`ent`** : libellé de l'organisme dans la liste « Entité publique » du portail.
- **`cls`** : **non collectable**, car le filtre « classification » est ignoré par le portail (même total filtré et non filtré). L'ancienne valeur est conservée pour les IDs connus du catalogue EAIOS du 2026-09-26 (`referentiel/cls_heritee_par_id.json`, valeur non re-vérifiée). Les nouveaux IDs reçoivent un `null` explicite et sont listés dans `catalogue_rapport.json` (`ids_cls_inconnu`). `--sans-cls-heritee` désactive cet héritage.

## Familles

**Couverte** : les annonces de consultation, tous types de procédure et toutes catégories, dans la fenêtre de recherche par défaut du portail. Cette fenêtre va de la date du jour à +6 mois pour la date limite, et de -6 mois à la date du jour pour la mise en ligne.

**Manquantes** :

- les autres types d'annonce du portail : information, résultat définitif, extrait de PV, rapport d'achèvement, décision de résiliation, rapport de présentation ;
- les bons de commande et avis d'achat ;
- les annulations (une disparition n'est jamais interprétée) ;
- les rectificatifs en tant que tels ;
- le DCE ;
- les consultations hors de la fenêtre par défaut ;
- `cls` pour les nouveaux IDs.

Un passage n'est jamais qualifié « complet PMMP ». Le meilleur statut possible est `LISTING_COMPLET_ANNONCES_DE_CONSULTATION_FENETRE_PAR_DEFAUT`.

## Raccordement (à faire plus tard avec le modèle d'état)

- **Entrée** : aucune.
- **Sortie** : `sortie/catalogue.json`, au même schéma que le catalogue EAIOS, et `sortie/catalogue_rapport.json`.
- **Clé stable** : `pmmp:<org>:<refConsultation>`, qui se recompose à partir de `o` et `r`.

## Coffre (stockage persistant d'essai, hors EAIOS)

Les artefacts ne servent pas les archives : `coffre.py` stocke l'état en quelques JSON agrégés.

```
python coffre.py verifier --source coffre_in                     # SHA-256 contre manifest.json
python coffre.py unpack   --source coffre_in --etat donnees
python coffre.py kit      --kit . --sortie coffre_out             # copie du kit sans données
python coffre.py pack     --etat donnees --sortie coffre_out --catalogue sortie/catalogue.json --rapport sortie/catalogue_rapport.json --precedent coffre_in
python coffre.py carte    --racine coffre_out --manifeste-precedent coffre_in/manifest.json   # carte `files` de publication
```

`stock/catalogue_valide.json` n'est remplacé que par un passage dont le listing « Annonces de consultation » est
complet et sans erreur ; un passage partiel ne met à jour que `catalogue_dernier_passage.json`.
`stock/statut.json` garde la dernière tentative, le dernier succès, le dernier listing complet, les erreurs et
l'historique de couverture. Un listing complet de ces pages ne signifie pas la collecte de tous les types d'annonces PMMP.

## Enrichissement PMMP joint (depuis le 18/10/2026)

`ingestion/ingestion_catalogue.py` ajoute à `catalogue_details.json` la clé `pmmp_enrichi`, calculée par `ingestion/enrichi_pmmp.py`. Le schéma de `catalogue.json` (31 champs) ne change pas, et aucun nouvel argument n'est requis.

- **Mode de passation** : élément `modePassation` de la fiche PMMP (« Sur offre de prix », « Au rabais / majoration »). Il est distinct de la procédure.
  - Source : `fiches.json` (`mode_passation`, `lu_le`), passé par `--fiches`.
  - Les valeurs déjà publiées sont reprises de `--details-precedents` et la lecture la plus récente gagne : rien n'est perdu à la rotation des fiches.
- **Classification Etat/CL/EEP** : classification PMMP de l'entité publique, d'après `referentiel/classification_entites.json` (relevé officiel du 17/10/2026, 23:55-23:58 UTC).
  - Méthode : rappel PRADO de la liste « Etat/CL/EEP » de la recherche avancée, contrôlé par la recherche filtrée.
  - Résultat : 57 Etat, 16 CL, 4 EEP ; totaux 3 443 + 964 + 12 = 4 419.
  - Une annonce hérite de son entité (orgAcronyme) ; entité inconnue = inconnue.
  - Le filtre n'est appliqué par le portail qu'en mode liste (`type_rechercheEntite=exact`) : c'est ce qui explique le constat « ignoré » du 02/10.
- **Tests** : `ingestion/test_enrichi_pmmp.py`, exécuté avec `unittest discover -s ingestion`.

## Détail par lot et lecture complète des fiches (depuis le 18/10/2026)

- **Popup « Détail des lots »** (`index.php?page=commun.PopUpDetailLots&orgAccronyme=<org>&refConsultation=<ref>&lang=fr`, deux « c » comme sur le portail) : `veille/pmmp_lots.py`.
  - `maj_quotidienne.py` le lit **dans le même passage** que la fiche d'une consultation allotie (une requête de plus, même débit, arrêt sur 401/403).
  - Stocké dans la fiche, clé `lots` datée séparément : `{lu_le, url, sha256_html_tronque, statut, n, n_annonce, lots[]}`. Si le popup échoue, la lecture précédente est gardée telle quelle.
  - Identité : l'action du formulaire du popup doit porter la même organisation et la même consultation. Statut `partiel` si moins de lots lisibles que « N Lots » de la fiche.
  - Par lot : `num`, `intitule`, `cat`, `est` (TTC tel que publié, `est_libelle`), `cau`, `tp`, `q` (lignes système / secteur / qualification / classe), `ag`, `vis`, `reu`, `proto`, `var`, `env`, `autres`. `ni` = non indiqué (« - »), `na` = bloc non affiché. Aucune somme, aucune valeur au niveau de l'annonce.
- **Catalogue** : pour une consultation allotie, `est`, `cau`, `tp`, `q`, `ag` de `catalogue.json` restent null / vides ; les valeurs par lot vont dans `catalogue_details.json` → `pmmp_enrichi.lots` (couverture : lues, partielles, inaccessibles, non lues).
- **Libellé seul** : « Date et heure : » sans date ni lieu (réunion, échantillons des consultations alloties) vaut « rien de publié » ; `construire_catalogue.py` neutralise aussi les anciennes lectures.
- **Complément borné** (lecture publique, 2 connexions au plus, départs espacés d'au moins 4 s, pause aux minutes 10-22) : les fiches lues sont fusionnées dans `stock/etat/fiches.json` (la lecture la plus récente gagne) ; les lectures impossibles après essais sont listées dans `referentiel/fiches_complement.json` (`fiches_inaccessibles`, `lots_inaccessibles`), lues par l'ingestion (`--complement-fiches`, défaut du kit).
- **Tests** : `tests/test_kit.py` (popup officiel, identité, lots partiels, passage horaire, coffre) et `ingestion/test_enrichi_pmmp.py` (section `lots`).

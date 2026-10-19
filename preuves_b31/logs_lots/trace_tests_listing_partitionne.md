# Listing PMMP partitionné : trace des tests (19/10/2026)

## Diagnostic réel (couvertures du coffre, fichiers statut Drive)
- 18/10 12:14, 19/10 10:14, 11:15, 12:24 : PARTIEL avec total stable et lignes = total, mais 1 à 2 identifiants lus deux
  fois (4422/4424, 4464/4466, 4508/4510, 4549/4550) : pagination à ordre instable (tri sans clé unique), autant
  d'annonces jamais vues.
- 18/10 21:14 → 19/10 09:13 : coupure TLS du portail (« Connection reset by peer »), arrêt sans conclure.
- 19/10 13:17 : la tâche horaire n'a rien exécuté (« exécution du kit refusée par le contrôle de permissions de
  l'environnement (code issu de l'artefact) ») : ni collecte, ni publication, ni ingestion. Hors kit.
- Défaut du kit : `coffre.pack` remplaçait `statut.dernier_succes` par un listing PARTIEL, d'où « ingestion refusée »
  aux passages 10:14, 11:15, 12:24.

## Sondes réelles du protocole (19/10, 1 connexion, ≥ 4 s)
- tris proposés : catégorie, publié le, référence, objet, organisme, date limite : aucune clé unique.
- date limite « entre / et » inclusive au jour et additive : 19/10 = 182, 20/10 = 356, 19–20/10 = 538 ;
  partition 20/10 lue en une réponse de 500 lignes/page : 356 lignes, 356 distinctes, toutes au 2026-10-20.
- catégorie (1 Travaux) : 1811 sur 4566.

## Échecs de tests rencontrés et correction (prémisse fausse prouvée, sinon code corrigé)
Première version (pagination de dernier recours, réconciliation par recomptage) :
1. 403/coupure : l'événement à la requête 5 ne pouvait pas survenir (450 lignes = une seule partition, lue à la
   requête 3) → jeu de données agrandi (1050 lignes) et événement à la requête 4.
2. « lignes ≤ 500 » appliqué à une partition paginée → sans objet : la pagination n'est plus jamais acceptée.
3. « hors bornes » : 01/01/2027 est DANS la fenêtre 19/10/2026–19/04/2027 → date 01/01/2030.
4. portail mouvant toutes les 4 requêtes : se stabilisait entre deux tours, complet légitime → événement à chaque
   requête.
Revue (exigences) → CODE corrigé, pas les tests :
- un échange ajout/suppression à total constant entre deux partitions déjà lues donnait un FAUX COMPLET avec le seul
  recomptage → tour de vérification qui relit toutes les partitions et exige les mêmes identifiants ;
- pagination de dernier recours acceptable si réunion = total → supprimée ; sous-partition par type de procédure,
  partition indivisible > 500 = PARTIEL ;
- couverture des catégories implicite → somme des sous-partitions = total du parent recompté au même tour ;
- total global sans bornes explicites → bornes fixées à l'ouverture envoyées à chaque requête.
Deuxième version :
5. fenêtre fixée : le test vérifiait la méthode `partition` du faux portail et non la méthode réelle → test sur
   `CollecteListing.partition` réelle avec un client qui enregistre les POST.
6. échange entre partitions lues : `globaux[1]` était le premier comptage du découpage (plan = fenêtre entière sur un
   état vide), pas le début du tour → `globaux[-2]`.

Résultat : kit 56/56 (dont 17 TestPartitions et 1 TestStatutEtCatalogueGarde).

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

## Production 19/10 après-midi (kit v3 publié au coffre a8f6)
- 14:45–14:59 (passage manuel, kit v3) : LISTING_COMPLET, 16 partitions confirmées, 89 requêtes, 163 Mo, 855 s ;
  contrôle 5 : total début 4602 = total fin 4602 = somme 4602 = distincts 4602, aucun écart de compte.
- 15:17 et 16:14 (tâche horaire, kit v3) : PARTIEL, budget 1200 s atteint (120 et 114 requêtes) ; 16:14 relancé sans amorce
  (le passage interrompu de 15:17 n'avait gardé aucune lecture) → 37 pages de 500 lignes (11,8 s chacune, ~476 Ko/s).
  Ingestion EAIOS du catalogue complet de 14:59 : refusée à 15:46 par le contrôle d'autorisation de l'environnement,
  publiée à 16:37 (EAIOS 2bb6 : 4648 consultations, 4596 avec fiche, 52 sans fiche).

## Revue de la règle « ajouts tolérés pendant le contrôle » (retirée avant publication)
Prédicat écrit : toutes partitions confirmées, somme = total du début, écarts de compte tous > 0, somme des écarts ≤ hausse
du total global pendant le contrôle → complet au début du contrôle.
Contre-exemple : x publié dans P AVANT le début (après la lecture de P), y retiré de Q avant le début, z publié dans Q après
le début : somme = total du début, écart P = +1, écart Q = 0, hausse = 1 → la règle déclarait COMPLET sans x. Une hausse
globale ne date pas un ajout (le portail ne publie que le jour). Règle retirée, ainsi que la référence « fin du
contrôle » (une partition déjà recomptée peut changer avant la fin sans que son compte le montre).
Règle gardée : comptes = totaux confirmés pour TOUTES les partitions (aucun écart) et somme = distincts = total du DÉBUT
du contrôle ; variation ultérieure du total enregistrée à part (publications_apres_reference). Test
`test_contre_exemple_hausse_globale_ne_date_pas_un_ajout`. Le passage complet de 14:59 satisfait la règle stricte.
Autres corrections : lectures d'un passage interrompu gardées comme amorce (jamais comme preuve) ; réserve de budget
pour les fiches (min(240 s, budget/5)) ; arrêt du listing sur budget = PARTIEL mais fiches lues dans la réserve.
Kit : 65/65.

## 19/10 17:14 (tâche horaire, kit v3) et livraison 17:5x
- 17:14 : LISTING_COMPLET 4674 ; contrôle 3 refusé (somme 4672, début 4673, fin 4674, 2 partitions changées) ;
  contrôle 5 : début 4674 = fin 4674 = somme 4674, aucun écart de compte → conforme à la règle stricte.
  Fiches : 5 lues avant l'arrêt sur budget, mais rapportées « 0 » (la liste était perdue sur ArretCollecte) → corrigé :
  arrêt budget/réseau = fiches déjà lues comptées ; 401/403 = arrêt immédiat (inchangé). Test dédié. Kit 66/66.
- Livraison : coffre e534 (base e246 relue, kit strict, 52 + 72 fiches nouvelles, catalogue_valide reconstruit sur le
  listing complet 17:14 : 4720 dont 4720 avec fiche) ; EAIOS 4104 (4720/4720 avec fiche, 389 alloties 389 popups,
  0 visite non lue, 245 consultations nouvelles depuis le catalogue du 18/10, toutes avec fiche).
- Lieu : « MAROC » est un lieu choisi par l'acheteur (375 / 4602 ; 372 avec province) et non une racine ; la page
  remplaçait la province par « Tout le Maroc » → libellé « Tout le Maroc · <provinces> » (part_mpv.js, JS d8827446c319).
  QA mpv4 24/24, mpv3 31/31, mpv2 66/66, mpv 50/50 (contrôle du bandeau rendu dépendant des données : le dernier essai
  17:14 a un listing réussi ET une erreur de fiches enregistrée).

## Famine des fiches nouvelles et vrai passage 19/10 18:13 (kit coffre 1883)
- Constat réel : 14:19 file_nouvelles 30 → 1 lue ; 17:14 file_nouvelles 124 → 1 choisie (10 places, changées d'abord).
- Correctif (actif par défaut, commande exacte de la tâche : --fiches 10) : nouvelles sans fiche d'abord (plafond 150),
  puis 10 relectures (changées puis anciennes) ; reliquat mesuré (budget / plafond), reprise en tête de file au passage
  suivant. Tests : saturation du budget (8 nouvelles + 12 changées, arrêt après 5 lectures) et main() avec la commande
  exacte de la tâche (règle, ordre, reliquat). Kit 68/68. Coffre a0b9 (code) puis 1883 (test) publiés à 18:02/18:05.
- Passage 2026-10-19T181353Z (tâche horaire, coffre 1883) : LISTING_COMPLET 4682, 56 requêtes listing, 109 Mo, 565 s ;
  14/16 partitions confirmées par la lecture précédente, 2 relues ; contrôle 1 : 4682 = 4682 = 4682, aucun écart.
  Fiches : règle « nouvelles (max 150) > changees > anciennes (n=10) », file avant 8 nouvelles / 4 changées / 1781
  anciennes, 18 lues dans l'ordre 8 n → 4 c → 6 a (18:23:29–18:25:53), 0 échec, reliquat 0.
  Coffre 525a, EAIOS 6cf5 publiés par la tâche elle-même : 4728 (4682 + 46), 4728 avec fiche, 8 nouveaux IDs, 0 disparu.
  Les 8 nouveaux : fiche v2 lue par ce passage, mode lu (« Sur offre de prix »), classification de l'entité (relevé
  officiel 17/10) ; aucun alloti parmi eux (popup non exercé sur un nouvel ID ce passage).

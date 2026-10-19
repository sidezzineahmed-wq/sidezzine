# Fiche PMMP complète : audit PMMP → lecteur → stockage → ingestion → B1.1 (19/10/2026)

Référence de comparaison : fiche officielle e5w/1041719 (10/2026/ARR/MERINIDES, luminaires LED, Fès), relue en entier
le 19/10 à 18:53 UTC ; cas alloti g3h/1044229 (433/2026/SRMCS, 3 lots), lu à 18:56 UTC. Aucune autre requête.

## Champs exclus ou non exportés par le collecteur avant v3

| Bloc PMMP | Avant v3 | Cause |
|---|---|---|
| Contact administratif publié | coupé | page tronquée AVANT `panelContcatAdministratif` (règle « contacts tronqués ») |
| Pièces de la consultation, documents d'avis | coupés | même coupure (blocs situés après le contact) |
| Adresse de retrait des dossiers | non extraite | jamais lue par le lecteur |
| Prix d'acquisition des plans | non extrait | jamais lu |
| Prospectus / échantillons | fusionnés dans `proto` (« Date et heure limite : … • texte ») | pas de date séparée ; non affiché dans la fiche B1.1 |
| Type d'annonce | lu, non exporté | absent du schéma à 31 champs |
| Code acheteur, lieux de la fiche, texte brut des qualifications | lus, non exportés | internes (restent hors parcours) |

Depuis v3, la coupure se fait à la zone entreprise (« Pièces téléchargées », questions, cautions, dépôts, messagerie) :
aucune donnée du compte ou de l'espace soumissionnaire n'est lue ni gardée.

## Table champ / couverture / source (données publiées le 19/10 au soir)

COUVERTURE_A_COMPLETER

## Règles appliquées

- Inconnu ≠ non indiqué (« - ») ≠ non publié ≠ par lot. Statut par bloc v3 : `lu`, `non_publie` (page lue au-delà du bloc),
  `non_lu` (lecture antérieure ou page coupée avant le bloc). Contact et pièces des lectures v2 = « pas encore lus ».
- TPE / PME : champ officiel tel que publié (e5w/1041719 : « Non », objet « Réservé… » conservé ; rien n'est déduit).
- Estimation : jamais de somme des lots ; « 0 » publié n'est pas un montant exploitable ; prix des plans « 0,00 » = vrai zéro.
- Pièces : lien vers la page publique PMMP du même identifiant (vérifié refConsultation / orgAcronyme), « non joint dans EAIOS » ;
  aucun formulaire soumis en test.
- Texte libre (prospectus, visites, réunion) : téléphones et e-mails masqués ; contact = seulement le bloc administratif publié.
- Ré-analyse hors ligne : HTML déjà lu au SHA identique ; `lu_le` inchangé, `reanalyse_le` et `version_parseur` à part.
- Compatibilité : seule règle de version = `version_lecture < 2` (visite non lue) ; une fiche v3 compte comme lue.
- Fixtures : `PRADO_PAGESTATE` vidé (l'état encodé contenait le contact d'origine, y compris dans la fixture o4d déjà
  commitée, nettoyée ici ; l'historique git antérieur la contient encore).

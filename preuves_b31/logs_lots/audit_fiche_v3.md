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

Base : coffre e227 (tâche de 20:13, listing complet 4 699 + 46 conservées = 4 745 consultations), publiée en coffre 21f0
puis EAIOS aa2a (19/10, 20:46–20:53 UTC). Couverture des 4 745 consultations du catalogue publié :

| Champ PMMP | Lecteur | Stockage / ingestion | Fiche B1.1 | Couverture | Source |
|---|---|---|---|---|---|
| Référence, objet, acheteur, entité | `ref`, `obj`, `mo` / organismes | catalogue (31 champs) | résumé | 4 745 | listing + fiche |
| Type d'annonce | `type_annonce` | `complements_fiche` | Source | 4 745 | fiche |
| Procédure / mode / catégorie | `proc`, `mode_passation`, `cat` | catalogue + `mode_passation` | résumé / Conditions | 4 745 | fiche |
| Allotissement, lots | `allot` + popup | `pmmp_enrichi.lots` | Détail par lot | 389 alloties, 389 lues | popup |
| Estimation TTC, caution, TPE/PME | `est`, `cau`, `tp` (par lot si alloti) | catalogue / lots | résumé, Conditions | lus (jamais sommés) | fiche / popup |
| Domaines | `dom` | catalogue | Conditions | lus | fiche |
| Retrait du dossier | `ret` | `complements_fiche` | Retrait, dépôt et ouverture | 4 745 lus | fiche (4 529 ré-analysées hors ligne, `lu_le` gardé) |
| Dépôt / ouverture | `dep`, `ouv` | catalogue | Retrait, dépôt et ouverture | lus | fiche |
| Prix des plans | `prix_plans` | `complements_fiche` | Conditions | 4 745 lus | fiche |
| Qualification / agréments | `q`, `ag` | catalogue / lots | résumé, Conditions | lus | fiche / popup |
| Prospectus, échantillons | `ech_date`, `ech_txt` | `complements_fiche` | Conditions (distinct de la remise des plis) | bloc lu 4 745, publié 687 | fiche |
| Réunion, visites | `reu`, `vis` | catalogue | Conditions / résumé | lus (0 visite non lue) | fiche |
| Variante | `var` | catalogue | Conditions | lus | fiche |
| Contact administratif publié | `contact` | `complements_fiche` (`sources_blocs`) | Contact administratif | 4 745 : 216 lecture v3, 4 529 état de page | fiche / état de page de la même lecture |
| Pièces de la consultation | `docs` | `complements_fiche` | Documents publiés sur PMMP | 216 lues ; 4 529 « pas encore lues » + lien fiche PMMP | fiche v3 seulement |
| Provenance | `lu_le`, `run`, `reanalyse_le`, `version_parseur` | `complements_fiche` | Source de la fiche | 4 745 | collecteur |

Nombres exacts du résiduel (catalogue valide live, aucune archive hors catalogue) :
- base 525a (4 728) : 4 647 pages en cache au SHA identique ; contact de l'état de page 4 540 ; résiduel 188
  (81 sans page conforme, 94 contact non porté par l'état, 12 objet de l'état ≠ page, 1 état de type non pris en charge) ;
  188 relues v3 (19:58–20:28, 2 connexions, ≥ 4 s, pause 10–22), 0 échec ;
- base e227 (4 745, après la tâche de 20:13 encore en v2) : résiduel 27 (fiches relues par la tâche sans cache), relues
  20:37–20:40, 0 échec ; résultat 4 745 / 4 745 champs du résumé v3 et contact, 0 `lu_le` reculé, 0 popup perdu.
- Pièces : non relues en masse (visibilité des liens absente de l'état) ; complétées au fil des relectures horaires.
- Texte prospectus e5w/1041719 : la source publiée s'arrête elle-même sur « … 10 HEURES O » (tel quel).

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

## Pièces publiées : relecture du résiduel (19/10, depuis 21:03 UTC) — EN COURS

- Résiduel exact au catalogue valide (4 745 identifiants distincts) : 216 lues + 4 529 à lire (4 362 ouvertes + 167 à date
  limite passée encore au catalogue). Cache v1/v2 inutilisable (bloc des pièces jamais présent) ; aucune page d'inventaire plus
  légère (liens publiés = formulaire DCE ou téléchargements).
- Publication intermédiaire : coffre c760 (kit : lecteur strict, file horaire « pièces non lues » de 60, inventaire gardé) et
  EAIOS 8a5d : pièces relevées 393 / 4 745, 0 vide confirmé, 4 352 pas encore lues (visible dans « Source et couverture »).
- Débit réel : ~4,5–4,9 s par fiche (2 connexions, ≥ 4 s, pause 10–22), ~590 fiches / h avec pauses.
- Checkpoints : `compl_docs/cache/<org>_<ref>.json` (champs lus, lu_le, SHA) + `brut/` (HTML tronqué, local, jamais publié)
  + `etat.json` ; consommés par `outils_pieces/prep_coffre_docs.py` (integrer_fiches, lecture la plus récente gagne, lots et
  inventaire validé gardés) sur le coffre relu en direct, puis ingestion EAIOS.
- Hors session : la tâche horaire (kit c760) reprend d'elle-même jusqu'à 60 fiches sans pièces par passage réussi, après les
  nouvelles ; limite constatée : passages de 19:15 et 21:14 tués à 600 s par la limite d'outil de leur session (rien publié).

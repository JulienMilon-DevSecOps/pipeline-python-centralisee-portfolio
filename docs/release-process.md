# Processus de release

Deux cycles de version distincts : celui de **la pipeline** elle-même, et celui
des **projets consommateurs** qui l'utilisent.

## 1. Versions de la pipeline

### SemVer

Tags `x.y.z`, sans préfixe :

| Changement                                                                 | Version  |
|----------------------------------------------------------------------------|----------|
| Correction sans effet sur le contrat                                       | patch `z` |
| Nouveau job ou nouvel input, avec un défaut qui ne change rien pour l'existant | mineure `y` |
| Input renommé ou supprimé, défaut qui change le comportement (ex : un contrôle qui devient bloquant), job renommé, **droit supplémentaire demandé** | majeure `x` |

Le **contrat** est celui de [inputs.md](inputs.md) : noms des inputs et
secrets, droits requis, noms des workflows, conventions de tags.

Un droit supplémentaire est cassant : un projet dont le bloc `permissions:` ne
le prévoit pas voit son run refusé au démarrage.

### Publier une version

1. Toutes les modifications sont dans `CHANGELOG.md`, section de la version,
   **datée avant le tag**.
2. La CI du dépôt est verte sur la branche principale.
3. Pose du tag `x.y.z` : la CI crée la GitHub Release (notes reprises du
   CHANGELOG).
4. Un tag publié **n'est jamais déplacé** : une erreur se corrige dans la
   version suivante. Un projet épinglé sur `1.2.0` doit obtenir exactement la
   même pipeline aujourd'hui et dans six mois.

### Changements cassants

- Annoncés dans le CHANGELOG sous une section **« Migration »** : ce qui
  change, pour qui, et le diff à appliquer dans le `ci.yml`.
- Quand c'est possible, une version mineure précédente introduit le nouvel
  input à côté de l'ancien, marqué déprécié ; la majeure suivante le retire.
- Un défaut qui se durcit (contrôle rendu bloquant) est une majeure : la valeur
  précédente reste accessible par un input explicite.

## 2. Montée de version dans un projet consommateur

1. Lire le CHANGELOG entre la version actuelle et la cible (sections
   « Migration » en priorité).
2. Ouvrir une PR qui change uniquement `@x.y.z` (plus les adaptations
   demandées).
3. Le run de la PR exécute la nouvelle version sur le vrai code du projet :
   c'est le test d'intégration.
4. Merge, puis release du projet comme d'habitude.

Renovate peut ouvrir ces PR automatiquement à chaque nouveau tag de la
pipeline.

## 3. Tags des projets consommateurs

Le job `rules` reconnaît ces conventions (tout autre tag ne déclenche rien) :

| Tag                    | Exemple              | Effet                                                  |
|------------------------|----------------------|--------------------------------------------------------|
| `V-x.y.z`              | `V-1.4.0`            | contrôles + tests, puis publication (PyPI, ou image `1.4.0` + `latest`) |
| `V-x.y.z-rcN`          | `V-1.4.0-rc1`        | contrôles + tests, puis publication sur TestPyPI       |
| `PPR-x.y.z-AAAAMMJJ`   | `PPR-1.4.0-20261231` | déploiement en pré-production (illustratif)            |
| `PRD-x.y.z-AAAAMMJJ`   | `PRD-1.4.0-20261231` | déploiement en production, après approbation (illustratif) |

Le préfixe `V-` distingue les releases des projets des tags `x.y.z` de la
pipeline elle-même.

Chaque projet consommateur tient son propre CHANGELOG, avec les mêmes règles :
entrée datée avant le tag, tag jamais déplacé.

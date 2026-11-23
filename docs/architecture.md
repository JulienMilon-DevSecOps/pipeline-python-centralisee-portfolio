# Architecture et choix de conception

Ce document explique **pourquoi** la pipeline est construite ainsi, et ce que
chaque choix coûte.

## 1. Centraliser les pipelines

Les jobs vivent dans un dépôt dédié ; les projets consommateurs appellent ses
workflows réutilisables.

| Gain                                                        | Coût                                                    |
|-------------------------------------------------------------|---------------------------------------------------------|
| Une correction ou un nouveau contrôle sert tous les projets | Le dépôt central devient une dépendance critique        |
| Mêmes contrôles de sécurité partout, par défaut             | Il faut le versionner, le tester et documenter ses changements |
| `ci.yml` des projets courts et lisibles en revue            | Les cas particuliers demandent des points d'extension prévus |

La condition pour que le compromis soit bon : traiter le dépôt central **comme
un logiciel** (versions, CHANGELOG, compatibilité, tests), pas comme un dossier
de snippets.

## 2. Épingler une version, jamais `@main`

```yaml
jobs:
  pipeline:
    uses: my-org/pipeline-python-factory/.github/workflows/python-package.example.yml@1.0.0
```

- **Reproductible** : relancer un ancien run donne le même résultat.
- **Pas d'effet de bord** : une modification du dépôt central ne casse aucun
  projet tant qu'il n'a pas choisi de monter de version.
- **Montée de version explicite** : une PR qui change `@1.0.0`, dont le run
  teste la nouvelle version sur le vrai code du projet avant le merge.

Pour aller plus loin, épingler par SHA de commit (`@<sha> # 1.0.0`) : un tag
peut techniquement être déplacé, un SHA non. Un outil de mise à jour des
dépendances (Renovate) maintient le SHA et le commentaire.

## 3. Workflow réutilisable et inputs typés

`on: workflow_call` déclare des **inputs** typés (`string`, `boolean`,
`number`) avec leur valeur par défaut. GitHub refuse au démarrage du run un
input inconnu ou d'un mauvais type.

GitHub ne propose ni liste de valeurs autorisées ni expression régulière pour
un input : le premier job, `rules`, les valide et arrête le run avec un message
explicite.

```yaml
- id: rules
  env:
    DEPLOY_MODE: ${{ inputs.deploy_mode }}
  run: |
    case "$DEPLOY_MODE" in none | compose | helm) ;; *)
      echo "::error title=Input invalide::deploy_mode='$DEPLOY_MODE' (none, compose ou helm)"; exit 1 ;;
    esac
```

Les inputs ne sont **jamais** interpolés dans un script (`run: echo ${{ inputs.x }}`) :
ils passent par `env:`. Une valeur contenant `"; curl …` reste une donnée, pas
une commande.

## 4. Une brique commune : `python-checks.yml`

Les contrôles et tests sont les mêmes pour un package et pour une image. Ils
sont écrits une fois dans `python-checks.yml`, appelé par les deux pipelines :

```yaml
jobs:
  checks:
    uses: ./.github/workflows/python-checks.yml   # même dépôt, même commit
    with:
      project_dir: ${{ inputs.project_dir }}
  build-package:
    needs: checks
    if: needs.checks.outputs.ci == 'true'
```

- `uses: ./…` dans un workflow réutilisable désigne **le même commit du dépôt
  de la pipeline**, pas le dépôt du consommateur : la version épinglée est
  cohérente de bout en bout.
- Les sorties de la brique (`ci`, `kind`, `version`) pilotent les jobs de la
  pipeline appelante.
- **Coût** : chaque input doit être déclaré dans la pipeline et transmis à la
  brique.

Piège évité : une **action locale** (`uses: ./.github/actions/x`) appelée depuis
un workflow réutilisable serait cherchée dans le dépôt **du consommateur** (le
dossier de travail), où elle n'existe pas. Les scripts sont donc écrits dans les
workflows eux-mêmes.

## 5. Un job `rules` pour les déclencheurs

Le `on:` est celui du projet consommateur : la pipeline ne peut pas l'imposer.
Le job `rules` classe la ref une fois pour toutes :

| Ref | `kind` | `ci` (contrôles, tests, build) |
|-----|--------|------|
| branche, pull request | `branch` | `true` |
| `V-1.2.3` | `release` | `true` |
| `V-1.2.3-rc1` | `rc` | `true` |
| `PPR-1.2.3-20261231` / `PRD-1.2.3-20261231` | `preproduction` / `production` | `false` |
| autre tag | `none` | `false` |

Chaque job ne lit que ces sorties (`if: needs.checks.outputs.kind == 'release'`) :
changer un déclencheur se fait en un endroit.

## 6. Ancres YAML pour les étapes partagées

Dans un même fichier, une étape définie une fois sert à plusieurs jobs :

```yaml
pytest:
  steps:
    - &install_deps
      name: Installer les dépendances (.venv)
      run: …
dependency-scan:
  steps:
    - *install_deps
```

GitHub n'accepte pas la fusion de clés (`<<:`) : une variante se fait par
`env:` au niveau du job (ex : `publish-pypi` et `publish-testpypi` partagent la
même étape d'upload, seules l'URL et le secret changent).

## 7. Ordre des jobs et blocage

Pas de stages : un graphe `needs:` explicite.

- Contrôles et tests en **parallèle** (pipeline plus rapide).
- Le build attend la réussite de **toute** la brique `checks`.
- `latest` n'est posé qu'après un scan réussi.
- Un contrôle rendu non bloquant (`*_allow_failure: true` → `continue-on-error`)
  apparaît en échec dans la liste des jobs, mais ne bloque pas la suite.

Simplification de la vitrine : le tag de version de l'image est poussé dès le
build, puis scanné. Une chaîne plus stricte ne pousse qu'un tag technique au
build et pose les tags définitifs après le scan.

## 8. Droits et secrets au plus juste

- `permissions: {}` en tête de chaque workflow, puis chaque job déclare ce dont
  il a besoin (`contents: read`, `packages: write`…).
- Le `ci.yml` du projet fixe le **plafond** : un job qui demande plus est refusé
  au démarrage du run.
- Secrets transmis par `secrets: inherit` ; ceux de publication et de
  déploiement vivent dans des **environments** (`pypi`, `preproduction`,
  `production`), lisibles seulement par les jobs qui les déclarent.
- `persist-credentials: false` au checkout : le token n'est pas laissé dans
  `.git/config` pour les étapes suivantes.

## 9. Épinglage des dépendances de la CI

- Actions tierces par **SHA** + version en commentaire
  (`actions/checkout@3d3c42e… # v7.0.1`).
- Outils (gitleaks, Trivy, crane, actionlint) exécutés par `docker run` sur une
  image épinglée par **digest**.
- Python et outils pip à version figée (`RUFF_VERSION`, `PIP_AUDIT_VERSION`).

Ces outils tournent avec accès au `GITHUB_TOKEN` et aux secrets : un outil
piégé pourrait les voler. L'épinglage fige ce qui a été validé ; un outil de
mise à jour propose les nouvelles versions par PR.

## 10. Déploiement interchangeable (illustratif)

`deploy-compose` et `deploy-helm` montrent deux mises en œuvre d'une même étape :

- même déclencheur : `PPR-x.y.z-AAAAMMJJ` (pré-production) ou
  `PRD-x.y.z-AAAAMMJJ` (production) ;
- même entrée : la version `x.y.z` extraite du tag, image déjà scannée ;
- l'**environment** GitHub porte les secrets (différents par environment) et la
  protection : `production` exige une approbation (*Required reviewers*) ;
- `concurrency` : jamais deux déploiements simultanés sur un environment ;
- deux implémentations choisies par `deploy_mode`.

Ce sont des **exemples génériques**, pas des templates de production.

## 11. Ce que la vitrine simplifie

| Vitrine                                      | Pipeline complète (privée)                 |
|----------------------------------------------|--------------------------------------------|
| Installation des dépendances par pip         | pip ou uv                                  |
| `pytest` sans service                        | PostgreSQL de test jetable                 |
| Publication PyPI par token                   | Token ou Trusted Publishing (sans secret)  |
| Tag de version poussé au build               | Tag technique, tags définitifs après scan, nettoyage du registre |
| Pas de signature                             | Signature cosign (clé ou keyless), SBOM    |
| 1 à 2 jobs simplifiés par étape              | SAST, contrôle du Dockerfile, version du tag, auto-tests |

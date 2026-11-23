# Contrat des inputs

Les inputs et secrets ci-dessous forment l'**interface publique** de la
pipeline : leurs noms et leur rôle ne changent pas sans version majeure (voir
[release-process.md](release-process.md)).

- **Défaut** : valeur déclarée par le workflow, surchargeable dans le `with:`
  du `ci.yml` du projet consommateur.
- **Secret** : à créer dans *Settings → Secrets and variables → Actions* (ou
  dans un environment), **jamais** dans un fichier du dépôt.
- Les exemples sont fictifs.

## Inputs

### Python (les deux pipelines)

| Input                           | Type    | Rôle                                                      | Défaut             | Exemple             |
|---------------------------------|---------|-----------------------------------------------------------|--------------------|---------------------|
| `python_version`                | string  | Version de Python (`actions/setup-python`)                | `3.12`             | `3.13`              |
| `project_dir`                   | string  | Dossier du projet Python depuis la racine du dépôt        | `.`                | `backend`           |
| `requirements_files`            | string  | Fichiers requirements installés s'ils existent            | `requirements.txt` | `requirements.txt requirements-dev.txt` |
| `project_extras`                | string  | Extras installés avec le projet (`pip install -e ".[…]"`) | `test`             | `test,database`     |
| `pytest_enabled`                | boolean | Exécuter les tests                                        | `true`             | `false`             |
| `pytest_args`                   | string  | Arguments de pytest                                       | `-v`               | `-q -m "not slow"`  |
| `pytest_cov_source`             | string  | Code mesuré par la couverture                             | `.`                | `my_package`        |
| `ruff_allow_failure`            | boolean | Lint et formatage non bloquants                           | `false`            | `true`              |
| `dependency_scan_allow_failure` | boolean | Analyse des dépendances non bloquante                     | `false`            | `true`              |

### Image (`python-docker.example.yml`)

| Input                | Type    | Rôle                                               | Défaut               | Exemple                     |
|----------------------|---------|----------------------------------------------------|----------------------|-----------------------------|
| `dockerfile_path`    | string  | Dockerfile, depuis la racine du dépôt              | `Dockerfile`         | `docker/Dockerfile`         |
| `docker_context`     | string  | Contexte de build                                  | `.`                  | `backend`                   |
| `scan_severity`      | string  | Niveaux de CVE qui font échouer le scan            | `CRITICAL`           | `HIGH,CRITICAL`             |
| `scan_allow_failure` | boolean | Scan non bloquant (la publication continue)        | `false`              | `true`                      |

L'image est publiée sous `ghcr.io/<owner>/<repo>` (minuscules).

### Déploiement (illustratif)

| Input          | Type   | Rôle                         | Défaut               | Exemple            |
|----------------|--------|------------------------------|----------------------|--------------------|
| `deploy_mode`  | string | `none`, `compose` ou `helm` (validé par `rules`) | `none` | `helm`  |
| `compose_file` | string | Fichier compose (mode compose) | `deploy/compose.yml` | `compose.prod.yml` |
| `helm_chart`   | string | Chart Helm (mode helm)       | `deploy/chart`       | `oci://ghcr.io/my-org/charts/my-app` |

## Secrets et variables

Transmis par `secrets: inherit`. Les secrets de publication et de déploiement
se créent de préférence dans l'**environment** du job : ils ne sont lisibles
que par lui, et l'environment peut exiger une approbation ou n'accepter que
certains tags (*Deployment branches and tags*).

| Nom                  | Type     | Rôle                                         | Requis                   | Environment       |
|----------------------|----------|----------------------------------------------|--------------------------|-------------------|
| `PYPI_TOKEN`         | secret   | Token d'API PyPI                             | publication PyPI         | `pypi`            |
| `TEST_PYPI_TOKEN`    | secret   | Token d'API TestPyPI                         | publication TestPyPI     | `testpypi`        |
| `DEPLOY_DOCKER_HOST` | secret   | Daemon distant (`ssh://deploy@app.example.com`) | `deploy_mode: compose` | `preproduction`, `production` |
| `DEPLOY_SSH_KEY`     | secret   | Clé privée SSH du compte de déploiement      | `deploy_mode: compose`   | idem              |
| `DEPLOY_KNOWN_HOSTS` | secret   | Empreinte de l'hôte (`ssh-keyscan`)          | `deploy_mode: compose`   | idem              |
| `KUBECONFIG_CONTENT` | secret   | Accès au cluster                             | `deploy_mode: helm`      | idem              |
| `KUBE_NAMESPACE`     | variable | Namespace cible (non secret : `vars`)        | `deploy_mode: helm`      | idem              |

La même clé porte une valeur différente par environment : la production n'est
jamais lisible depuis la pré-production.

Fourni par GitHub, à ne pas créer : `GITHUB_TOKEN` (ghcr.io, Releases), dont
les droits sont plafonnés par le bloc `permissions:` du `ci.yml`.

## Droits requis (`permissions:` du projet)

| Pipeline | Droits |
|----------|--------|
| `python-package.example.yml` | `contents: read` |
| `python-docker.example.yml`  | `contents: read`, `packages: write` |

## Règles d'hygiène

- Un token par projet et par usage, avec la portée minimale (PyPI : limité au
  projet).
- Protéger les tags de release (`V-*`, `PPR-*`, `PRD-*`) par un **ruleset** :
  seules les personnes autorisées déclenchent une publication ou un déploiement.
- Ne jamais activer le mode debug (`ACTIONS_STEP_DEBUG`) sur un run qui manipule
  des secrets sans relire ses logs.
- Aucun secret dans `env:` ou `with:` d'un workflow, ni dans un fichier `.env`
  versionné.

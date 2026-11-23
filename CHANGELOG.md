# Changelog

Toutes les modifications notables de la vitrine sont décrites ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
versions : [SemVer](https://semver.org/lang/fr/) (tags `x.y.z`, sans préfixe).

## [Non publié]

## [0.1.0] - 2026-11-23

### Ajouté

- Workflows réutilisables d'exemple `python-package.example.yml` (check →
  test → build → publish) et `python-docker.example.yml` (check → test →
  build → scan → publish → deploy illustratif).
- Brique commune `python-checks.yml` : job `rules` (déclencheurs et validation
  des inputs), `secret-detection`, `ruff`, `pytest`, `dependency-scan`.
- Exemples de projets consommateurs : `examples/consumer-package/ci.yml` et
  `examples/consumer-api/ci.yml`.
- Application d'exemple `examples/sample-app/` (FastAPI, pytest, Dockerfile),
  testée par la CI du dépôt.
- CI du dépôt : yamllint, actionlint (+ shellcheck), pipeline Docker d'exemple
  appliquée à `sample-app` (build de l'image sans push), GitHub Release sur les
  tags `x.y.z`.
- Documentation : `docs/architecture.md`, `docs/inputs.md`,
  `docs/release-process.md`.
- Licence MIT.

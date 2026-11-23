"""Point d'entrée de l'API d'exemple."""

from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI

app = FastAPI(title="sample-app")


def _app_version() -> str:
    """Lit la version installée du package.

    Returns:
        La version du package, ou "inconnue" s'il n'est pas installé.
    """
    try:
        return version("sample-app")
    except PackageNotFoundError:
        return "inconnue"


@app.get("/health")
def health() -> dict[str, str]:
    """Indique que l'API répond (utilisé par le HEALTHCHECK de l'image).

    Returns:
        Le statut de l'API.
    """
    return {"status": "ok"}


@app.get("/version")
def get_version() -> dict[str, str]:
    """Donne la version déployée de l'API.

    Returns:
        La version du package.
    """
    return {"version": _app_version()}

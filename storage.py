from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Callable

import requests
import streamlit as st

LOCAL_DATA_PATH = Path(__file__).parent / "data" / "asignaciones.json"
DEFAULT_DATA: dict[str, Any] = {"people": {}, "days": {}}


def _get_github_config() -> tuple[str, str, str, str] | None:
    """Obtiene configuración de GitHub desde st.secrets o variables de entorno."""
    token = ""
    repo = ""
    branch = "main"
    file_path = "data/asignaciones.json"

    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
        repo = st.secrets.get("GITHUB_REPO", "")
        branch = st.secrets.get("GITHUB_BRANCH", "main")
        file_path = st.secrets.get("GITHUB_DATA_PATH", "data/asignaciones.json")
    except Exception:
        pass

    token = token or os.environ.get("GITHUB_TOKEN", "")
    repo = repo or os.environ.get("GITHUB_REPO", "")
    branch = os.environ.get("GITHUB_BRANCH", branch)
    file_path = os.environ.get("GITHUB_DATA_PATH", file_path)

    if token and repo:
        return token, repo, branch, file_path
    return None


def is_github_persistence_enabled() -> bool:
    return _get_github_config() is not None


def _normalize_data(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"people": {}, "days": {}}
    people = raw.get("people")
    days = raw.get("days")
    return {
        "people": people if isinstance(people, dict) else {},
        "days": days if isinstance(days, dict) else {},
    }


def _load_local() -> dict[str, Any]:
    if not LOCAL_DATA_PATH.exists():
        LOCAL_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_DATA_PATH.write_text(json.dumps(DEFAULT_DATA, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"people": {}, "days": {}}
    try:
        content = LOCAL_DATA_PATH.read_text(encoding="utf-8")
        return _normalize_data(json.loads(content))
    except Exception:
        return {"people": {}, "days": {}}


def _save_local(data: dict[str, Any]) -> None:
    LOCAL_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_DATA_PATH.write_text(
        json.dumps(_normalize_data(data), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _github_get(cfg: tuple[str, str, str, str]) -> tuple[dict[str, Any], str | None]:
    token, repo, branch, file_path = cfg
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.get(url, headers=headers, params={"ref": branch}, timeout=10)
    if resp.status_code == 404:
        return {"people": {}, "days": {}}, None
    resp.raise_for_status()
    payload = resp.json()
    sha = payload.get("sha")
    decoded = base64.b64decode(payload["content"]).decode("utf-8")
    return _normalize_data(json.loads(decoded)), sha


def _github_put(
    cfg: tuple[str, str, str, str],
    data: dict[str, Any],
    sha: str | None,
    message: str,
) -> bool:
    token, repo, branch, file_path = cfg
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    content_str = json.dumps(_normalize_data(data), indent=2, ensure_ascii=False)
    body: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    resp = requests.put(url, headers=headers, json=body, timeout=10)
    if resp.status_code == 409:
        return False
    resp.raise_for_status()
    return True


def load_data() -> dict[str, Any]:
    """Carga el estado actual del calendario desde GitHub o desde disco local."""
    cfg = _get_github_config()
    if cfg is None:
        return _load_local()
    data, _ = _github_get(cfg)
    return data


def update_data(mutator: Callable[[dict[str, Any]], None], commit_message: str = "Actualizar calendario 2027") -> dict[str, Any]:
    """Aplica una modificación de forma segura (con reintento si hay conflicto en GitHub)."""
    cfg = _get_github_config()
    if cfg is None:
        data = _load_local()
        mutator(data)
        _save_local(data)
        return data

    for _ in range(3):
        data, sha = _github_get(cfg)
        mutator(data)
        if _github_put(cfg, data, sha, commit_message):
            return data

    raise RuntimeError("No se pudo guardar por conflicto simultáneo. Intenta nuevamente.")

"""Safe JSON reads and atomic writes for compatibility data files."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import tempfile
from threading import RLock
from typing import Any, TypeVar

T = TypeVar("T")
_WRITE_LOCK = RLock()
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_KNOWLEDGE_ROOT = _PROJECT_ROOT / "knowledge"
LOGGER = logging.getLogger(__name__)


class CloudPersistenceError(RuntimeError):
    """Raised when configured cloud persistence rejects a JSON write."""


def _document_name(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(_KNOWLEDGE_ROOT.resolve()).as_posix()
    except ValueError:
        return None


def _cloud_client() -> Any | None:
    """Return the configured client without making local tests require secrets."""

    try:
        from core.database import DatabaseUnavailableError, get_supabase_client

        return get_supabase_client()
    except (DatabaseUnavailableError, KeyError, RuntimeError):
        return None
    except Exception as exc:
        LOGGER.warning("Cloud knowledge client is unavailable: %s", exc)
        return None


def knowledge_store_is_ready(client: Any) -> bool:
    """Return whether the launch persistence table is installed."""

    try:
        client.table("knowledge_documents").select("name").limit(1).execute()
        return True
    except Exception:
        return False


def _load_cloud_value(path: Path) -> Any | None:
    name = _document_name(path)
    client = _cloud_client() if name else None
    if client is None:
        return None

    try:
        response = (
            client.table("knowledge_documents")
            .select("payload")
            .eq("name", name)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        LOGGER.warning("Unable to read cloud knowledge document %s: %s", name, exc)
        return None

    if not response.data:
        return None
    return response.data[0].get("payload")


def load_json(path: Path, default: T) -> T:
    """Load JSON and return a copy-safe default for missing/invalid files."""

    cloud_value = _load_cloud_value(path)
    if cloud_value is not None:
        return cloud_value

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
        return default


def save_json(path: Path, value: Any) -> bool:
    """Atomically save JSON and mirror knowledge documents to Supabase.

    Local files remain useful for development and seed data. When Supabase is
    configured, a failed cloud write is raised so the UI never claims durable
    success for data that exists only on an ephemeral app filesystem.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    with _WRITE_LOCK:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            text=True,
        )

        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=4, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

    name = _document_name(path)
    client = _cloud_client() if name else None
    if client is None:
        return False

    try:
        (
            client.table("knowledge_documents")
            .upsert({"name": name, "payload": value}, on_conflict="name")
            .execute()
        )
        return True
    except Exception as exc:
        raise CloudPersistenceError(
            f"The local file was updated, but cloud persistence failed for {name}."
        ) from exc

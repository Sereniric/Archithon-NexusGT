import json
from pathlib import Path
from typing import Iterable, Optional, Union


KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parents[1] / "knowledge_base" / "permissions.json"


class KnowledgeBaseError(ValueError):
    """Raised when the permission knowledge base cannot be used."""


def load_permission_knowledge_base(path: Optional[Union[str, Path]] = None) -> list[dict]:
    """Load and validate the permission knowledge-base list."""
    knowledge_base_path = Path(path) if path is not None else KNOWLEDGE_BASE_PATH

    try:
        with knowledge_base_path.open("r", encoding="utf-8") as file:
            entries = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        raise KnowledgeBaseError("The permission knowledge base could not be loaded.") from exc

    if not isinstance(entries, list):
        raise KnowledgeBaseError("The permission knowledge base must contain a JSON list.")

    return entries


def analyze_permissions(
    permissions: Optional[Iterable[str]],
    knowledge_base_path: Optional[Union[str, Path]] = None,
) -> dict:
    """Match permission identifiers to the deterministic knowledge base."""
    identifiers = list(permissions or [])
    entries = load_permission_knowledge_base(knowledge_base_path)

    entries_by_permission = {
        entry.get("permission"): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("permission"), str)
    }

    recognized = []
    unknown = []

    for identifier in identifiers:
        if not isinstance(identifier, str) or not identifier.strip():
            continue

        exact_identifier = identifier.strip()
        entry = entries_by_permission.get(exact_identifier)

        if entry is None:
            unknown.append({
                "permission": exact_identifier,
                "status": "Unknown / Unsupported",
            })
            continue

        recognized.append({
            "permission": exact_identifier,
            "description": entry.get("description", "Not available"),
            "capability": entry.get("capability", "Not available"),
            "privacy_implications": entry.get("privacy_implications", "Not available"),
            "protection_level": entry.get("protection_level", "Not available"),
            "official_documentation_url": entry.get("official_documentation_url", "Not available"),
            "category": entry.get("category", "Not available"),
        })

    return {
        "total": len(recognized) + len(unknown),
        "recognized": recognized,
        "unknown": unknown,
    }


match_permissions = analyze_permissions

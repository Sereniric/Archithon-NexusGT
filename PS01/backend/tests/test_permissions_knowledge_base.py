import json
from pathlib import Path


KNOWLEDGE_BASE = Path(__file__).resolve().parents[1] / "knowledge_base" / "permissions.json"
REQUIRED_FIELDS = {
    "permission",
    "description",
    "capability",
    "privacy_implications",
    "protection_level",
    "official_documentation_url",
    "category",
}


def load_permissions():
    with KNOWLEDGE_BASE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    assert isinstance(data, list)
    return data


def test_permission_knowledge_base_is_valid_json():
    load_permissions()


def test_permission_entries_have_required_fields():
    for entry in load_permissions():
        assert REQUIRED_FIELDS.issubset(entry), entry


def test_permission_identifiers_are_unique():
    identifiers = [entry["permission"] for entry in load_permissions()]
    assert len(identifiers) == len(set(identifiers))


def test_required_values_are_nonempty():
    for entry in load_permissions():
        for field in REQUIRED_FIELDS:
            value = entry[field]
            assert isinstance(value, str) and value.strip(), (entry["permission"], field)

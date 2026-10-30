import json
import sys
from pathlib import Path

import pytest


PS01_ROOT = Path(__file__).resolve().parents[2]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.analyzer.permission_analyzer import (
    KnowledgeBaseError,
    analyze_permissions,
)


def test_known_permission_match():
    result = analyze_permissions(["android.permission.CAMERA"])
    assert result["total"] == 1
    assert len(result["recognized"]) == 1
    assert result["unknown"] == []


def test_correct_explanation_fields():
    result = analyze_permissions(["android.permission.RECORD_AUDIO"])
    record = result["recognized"][0]
    assert record["permission"] == "android.permission.RECORD_AUDIO"
    assert record["description"]
    assert record["capability"]
    assert record["privacy_implications"]
    assert record["protection_level"]
    assert record["official_documentation_url"]


def test_unknown_permission_detection():
    result = analyze_permissions(["com.example.permission.NOT_IN_KNOWLEDGE_BASE"])
    assert len(result["recognized"]) == 0
    assert result["unknown"] == [{
        "permission": "com.example.permission.NOT_IN_KNOWLEDGE_BASE",
        "status": "Unknown / Unsupported",
    }]


def test_exact_permission_identifier_is_preserved():
    identifier = "android.permission.ACCESS_FINE_LOCATION.custom"
    result = analyze_permissions([identifier])
    assert result["unknown"][0]["permission"] == identifier


def test_empty_permission_list():
    assert analyze_permissions([]) == {
        "total": 0,
        "recognized": [],
        "unknown": [],
    }


def test_mixed_known_and_unknown_permissions():
    result = analyze_permissions([
        "android.permission.CAMERA",
        "com.example.permission.CUSTOM",
    ])
    assert result["total"] == 2
    assert len(result["recognized"]) == 1
    assert len(result["unknown"]) == 1


def test_missing_optional_knowledge_base_fields(tmp_path):
    knowledge_base = tmp_path / "permissions.json"
    knowledge_base.write_text(json.dumps([{
        "permission": "com.example.permission.MINIMAL",
        "description": "Description is available",
    }]), encoding="utf-8")

    result = analyze_permissions(
        ["com.example.permission.MINIMAL"],
        knowledge_base_path=knowledge_base,
    )
    record = result["recognized"][0]
    assert record["description"] == "Description is available"
    assert record["capability"] == "Not available"
    assert record["privacy_implications"] == "Not available"


def test_duplicate_permissions_are_not_invented_or_recounted(tmp_path):
    knowledge_base = tmp_path / "permissions.json"
    knowledge_base.write_text(json.dumps([{
        "permission": "com.example.permission.ONE",
        "description": "One",
    }]), encoding="utf-8")

    result = analyze_permissions(["com.example.permission.ONE", "com.example.permission.ONE"], knowledge_base)
    assert result["total"] == 2

import json
import sys
from pathlib import Path


PS01_ROOT = Path(__file__).resolve().parents[2]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.reporting.report_generator import generate_report_markdown, generate_report_json


def complete_results():
    permission_analysis = {
        "recognized": [{
            "permission": "android.permission.CAMERA",
            "description": "Allows camera access.",
            "capability": "Can capture photos and video.",
            "privacy_implications": "May expose visual information.",
            "protection_level": "dangerous",
            "official_documentation_url": "https://developer.android.com/reference/android/Manifest.permission#CAMERA",
            "category": "Hardware",
        }],
        "unknown": [{"permission": "com.example.CUSTOM", "status": "Unknown / Unsupported"}],
        "total": 2,
    }
    policy_analysis = {
        "topics": [{
            "topic": "Camera, microphone, and contacts",
            "summary": "We use the camera for video calls.",
            "excerpts": ["We use the camera for video calls."],
        }],
        "mentioned_topics": 1,
        "missing_topics": ["Location data"],
    }
    comparison = {
        "comparisons": [{
            "permission": "android.permission.CAMERA",
            "status": "Policy Coverage Found",
            "relevant_policy_topic": "Camera, microphone, and contacts",
            "reason": "The policy topic describes camera access.",
            "supporting_excerpts": ["We use the camera for video calls."],
        }],
        "unknown_permissions": permission_analysis["unknown"],
        "coverage_count": 1,
        "gap_count": 0,
        "unknown_count": 1,
    }
    purpose = {
        "performed": True,
        "application_name": "Camera App",
        "message": "Purpose analysis based on stated purpose.",
        "assessments": [{
            "permission": "android.permission.CAMERA",
            "capability": "Can capture photos and video.",
            "assessment": "Potentially relevant",
            "explanation": "The purpose mentions video and does not establish actual behavior.",
        }],
        "unknown_permissions": permission_analysis["unknown"],
    }
    return permission_analysis, policy_analysis, comparison, purpose


def test_complete_report_contains_all_sections():
    permission, policy, comparison, purpose = complete_results()
    report = generate_report_markdown(permission, policy, comparison, purpose, "Camera App", "A video calling app")
    assert "Application name: Camera App" in report
    assert "Total permission count: 2" in report
    assert "android.permission.CAMERA" in report
    assert "com.example.CUSTOM" in report
    assert "We use the camera for video calls." in report
    assert "Location data" in report
    assert "Policy Coverage Found" in report
    assert "Potentially relevant" in report
    assert "Declared permissions do not prove actual runtime" in report


def test_missing_optional_inputs_are_handled():
    report = generate_report_markdown()
    assert "Application name: Not provided" in report
    assert "Stated purpose: Not provided" in report
    assert "Privacy policy analysis was not provided" in report
    assert "Purpose analysis was not performed" in report


def test_report_keeps_exact_permission_identifier():
    permission, policy, comparison, purpose = complete_results()
    exact = "com.example.permission.UNIQUE-CASE"
    permission["unknown"] = [{"permission": exact, "status": "Unknown / Unsupported"}]
    report = generate_report_markdown(permission, policy, comparison, purpose)
    assert exact in report


def test_json_report_is_valid_and_structured():
    permission, policy, comparison, purpose = complete_results()
    structured = generate_report_json(
        permission_analysis=permission,
        policy_analysis=policy,
        comparison=comparison,
        purpose=purpose,
    )
    parsed = json.loads(structured)
    assert parsed["permission_analysis"]["total"] == 2
    assert parsed["comparison"]["coverage_count"] == 1


def test_report_does_not_claim_malicious_or_safe_status():
    permission, policy, comparison, purpose = complete_results()
    report = generate_report_markdown(permission, policy, comparison, purpose)
    assert "malicious or safe" in report

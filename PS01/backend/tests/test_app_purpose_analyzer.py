import sys
from pathlib import Path


PS01_ROOT = Path(__file__).resolve().parents[2]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.analyzer.app_purpose_analyzer import (
    POTENTIALLY_RELEVANT,
    NEEDS_REVIEW,
    NO_RELATIONSHIP,
    UNKNOWN,
    analyze_application_purpose,
)


def permission_analysis(recognized=None, unknown=None):
    return {
        "recognized": recognized or [],
        "unknown": unknown or [],
        "total": len(recognized or []) + len(unknown or []),
    }


def test_relevant_permission_and_purpose():
    result = analyze_application_purpose("Camera App", "A camera app that takes photographs and records video", permission_analysis([{
        "permission": "android.permission.CAMERA",
        "capability": "Can capture photographs and videos.",
    }]))
    assessment = result["assessments"][0]
    assert assessment["permission"] == "android.permission.CAMERA"
    assert assessment["assessment"] == POTENTIALLY_RELEVANT
    assert "does not establish actual app behavior" in assessment["explanation"]


def test_potentially_unrelated_permission():
    result = analyze_application_purpose("Calculator", "A calculator for basic arithmetic and equations", permission_analysis([{
        "permission": "android.permission.CAMERA",
        "capability": "Can capture photographs and videos.",
    }]))
    assert result["assessments"][0]["assessment"] == NO_RELATIONSHIP


def test_unclear_short_purpose():
    result = analyze_application_purpose("Utility", "Utility app", permission_analysis([{
        "permission": "android.permission.CAMERA",
        "capability": "Can capture photographs and videos.",
    }]))
    assert result["assessments"][0]["assessment"] == NEEDS_REVIEW


def test_missing_purpose_skips_analysis():
    result = analyze_application_purpose("Example App", "", permission_analysis([{
        "permission": "android.permission.CAMERA",
        "capability": "Can capture photographs.",
    }]))
    assert result["performed"] is False
    assert result["assessments"] == []


def test_unknown_permission_remains_unknown():
    result = analyze_application_purpose("Custom App", "A custom application for communication", permission_analysis(
        unknown=[{"permission": "com.example.permission.CUSTOM", "status": "Unknown / Unsupported"}],
    ))
    assert result["unknown_permissions"] == [{
        "permission": "com.example.permission.CUSTOM",
        "assessment": UNKNOWN,
        "capability": "Unknown capability — unsupported by the knowledge base",
        "explanation": "The exact permission is unknown, so no capability or purpose relationship was invented.",
    }]


def test_empty_permission_analysis():
    result = analyze_application_purpose("App", "A useful application", permission_analysis())
    assert result["performed"] is True
    assert result["assessments"] == []


def test_unmapped_recognized_permission_needs_review():
    result = analyze_application_purpose("App", "A general productivity application", permission_analysis([{
        "permission": "android.permission.POST_NOTIFICATIONS",
        "capability": "Can post notifications.",
    }]))
    assert result["assessments"][0]["assessment"] == NEEDS_REVIEW


def test_assessment_does_not_claim_actual_behavior():
    result = analyze_application_purpose("Navigation App", "Provides maps and navigation", permission_analysis([{
        "permission": "android.permission.ACCESS_FINE_LOCATION",
        "capability": "Can obtain precise location.",
    }]))
    explanation = result["assessments"][0]["explanation"]
    assert "does not establish actual app behavior" in explanation

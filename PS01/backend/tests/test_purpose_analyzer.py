import sys
from pathlib import Path


PS01_ROOT = Path(__file__).resolve().parents[2]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.analyzer.purpose_analyzer import (
    COVERAGE_FOUND,
    NO_POLICY_STATEMENT,
    UNKNOWN,
    compare_permissions_with_policy,
)


def permission_analysis(permissions):
    return {
        "total": len(permissions),
        "recognized": [{"permission": item} for item in permissions],
        "unknown": [],
    }


def policy_analysis(topics):
    return {
        "topics": topics,
        "mentioned_topics": len(topics),
        "missing_topics": [],
    }


def test_permission_with_relevant_policy_coverage():
    policy = policy_analysis([{
        "topic": "Location data",
        "excerpts": ["We collect your precise location."],
    }])
    result = compare_permissions_with_policy(
        permission_analysis(["android.permission.ACCESS_FINE_LOCATION"]), policy
    )
    record = result["comparisons"][0]
    assert record["status"] == COVERAGE_FOUND
    assert record["supporting_excerpts"] == ["We collect your precise location."]


def test_permission_without_relevant_policy_coverage():
    policy = policy_analysis([{
        "topic": "Personal data collection",
        "excerpts": ["We collect your email address."],
    }])
    result = compare_permissions_with_policy(
        permission_analysis(["android.permission.CAMERA"]), policy
    )
    assert result["comparisons"][0]["status"] == NO_POLICY_STATEMENT
    assert result["gap_count"] == 1


def test_multiple_permissions_use_different_topics():
    policy = policy_analysis([
        {"topic": "Location data", "excerpts": ["We use location."]},
        {"topic": "Camera, microphone, and contacts", "excerpts": ["We use the camera."]},
    ])
    result = compare_permissions_with_policy(permission_analysis([
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.CAMERA",
    ]), policy)
    assert all(record["status"] == COVERAGE_FOUND for record in result["comparisons"])


def test_unknown_permissions_remain_separate():
    result = compare_permissions_with_policy({
        "recognized": [],
        "unknown": [{"permission": "com.example.CUSTOM", "status": "Unknown / Unsupported"}],
    }, policy_analysis([]))
    assert result["unknown_count"] == 1
    assert result["unknown_permissions"][0]["permission"] == "com.example.CUSTOM"
    assert result["comparisons"] == []


def test_missing_policy_topic_is_a_gap_not_false_match():
    result = compare_permissions_with_policy(
        permission_analysis(["android.permission.RECORD_AUDIO"]),
        policy_analysis([{"topic": "Location data", "excerpts": ["We use location."]}]),
    )
    assert result["comparisons"][0]["status"] == NO_POLICY_STATEMENT


def test_empty_permission_input():
    result = compare_permissions_with_policy(permission_analysis([]), policy_analysis([]))
    assert result["comparisons"] == []
    assert result["coverage_count"] == 0


def test_empty_policy_input_is_unknown():
    result = compare_permissions_with_policy(
        permission_analysis(["android.permission.CAMERA"]),
        {"topics": [], "mentioned_topics": 0, "missing_topics": []},
    )
    assert result["comparisons"][0]["status"] == UNKNOWN


def test_supporting_excerpt_is_preserved():
    excerpt = "We access the camera only when you start a video call."
    result = compare_permissions_with_policy(
        permission_analysis(["android.permission.CAMERA"]),
        policy_analysis([{"topic": "Camera, microphone, and contacts", "excerpts": [excerpt]}]),
    )
    assert result["comparisons"][0]["supporting_excerpts"] == [excerpt]


def test_no_false_match_between_location_and_camera():
    result = compare_permissions_with_policy(
        permission_analysis(["android.permission.CAMERA"]),
        policy_analysis([{"topic": "Location data", "excerpts": ["We collect location."]}]),
    )
    assert result["comparisons"][0]["status"] == NO_POLICY_STATEMENT

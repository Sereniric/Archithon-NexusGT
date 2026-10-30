import sys
from pathlib import Path

import pytest


PS01_ROOT = Path(__file__).resolve().parents[2]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.analyzer.policy_analyzer import PolicyAnalysisError, analyze_policy_text


def test_relevant_policy_text():
    policy = "We collect your email address and precise location when you use the app."
    result = analyze_policy_text(policy)
    assert result["mentioned_topics"] >= 2


def test_multiple_topics_are_identified():
    policy = (
        "We collect your name and email address. "
        "We may share data with third-party vendors. "
        "We use cookies for advertising and analytics."
    )
    result = analyze_policy_text(policy)
    names = {item["topic"] for item in result["topics"]}
    assert "Personal data collection" in names
    assert "Data sharing with third parties" in names
    assert "Advertising and tracking" in names


def test_supporting_excerpts_are_exact_source_sentences():
    policy = "We retain account data for two years. We store it in encrypted databases."
    result = analyze_policy_text(policy)
    storage = next(item for item in result["topics"] if item["topic"] == "Data storage and retention")
    assert storage["excerpts"][0] in policy
    assert storage["summary"] in policy


def test_empty_policy_input():
    result = analyze_policy_text("")
    assert result["mentioned_topics"] == 0
    assert result["topics"] == []
    assert len(result["missing_topics"]) == 8


def test_irrelevant_policy_text():
    result = analyze_policy_text("The weather today is sunny and mild.")
    assert result["mentioned_topics"] == 0
    assert len(result["missing_topics"]) == 8


def test_missing_topics_are_listed():
    result = analyze_policy_text("We use cookies for advertising.")
    assert "Personal data collection" in result["missing_topics"]


def test_summary_is_grounded_in_original_text():
    policy = "We use your location to provide local search results."
    result = analyze_policy_text(policy)
    location = next(item for item in result["topics"] if item["topic"] == "Location data")
    for excerpt in location["excerpts"]:
        assert excerpt in policy
    assert location["summary"] in policy


@pytest.mark.parametrize("bad_input", [b"\xff\xfe\xfa", 123, object()])
def test_malformed_or_unreadable_input(bad_input):
    with pytest.raises(PolicyAnalysisError):
        analyze_policy_text(bad_input)


def test_utf8_bytes_are_supported():
    result = analyze_policy_text("We collect the user's email address.".encode("utf-8"))
    assert result["mentioned_topics"] >= 1

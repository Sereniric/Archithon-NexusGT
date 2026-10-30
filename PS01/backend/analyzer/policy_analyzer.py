import re
from typing import Optional, Union


TOPIC_KEYWORDS = {
    "Personal data collection": (
        "personal information", "personal data", "collect", "collected", "collection",
        "name", "email address", "phone number", "identifier",
    ),
    "Device information": (
        "device information", "device id", "device identifier", "ip address",
        "operating system", "hardware", "browser", "mobile device",
    ),
    "Location data": (
        "location", "gps", "geolocation", "coordinates", "precise location",
        "approximate location",
    ),
    "Camera, microphone, and contacts": (
        "camera", "photo", "microphone", "audio recording", "contacts", "address book",
    ),
    "Data storage and retention": (
        "store", "stored", "storage", "retain", "retained", "retention", "delete",
        "deletion", "database", "server",
    ),
    "Data sharing with third parties": (
        "share", "shared", "sharing", "third party", "third-party", "vendor",
        "partner", "service provider", "disclosure",
    ),
    "Advertising and tracking": (
        "advertising", "advertisement", "ad provider", "tracking", "track",
        "cookie", "analytics", "pixel", "personalized ads",
    ),
    "Data security and deletion": (
        "secure", "security", "encrypt", "encryption", "safeguard", "protect",
        "deletion", "delete", "destroy", "access request",
    ),
}


class PolicyAnalysisError(ValueError):
    """Raised when privacy-policy text cannot be processed."""


def _sentences(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    parts = re.split(r"(?<=[.!?])\s+|\n+", normalized)
    return [part.strip() for part in parts if part.strip()]


def analyze_policy_text(policy_text: Optional[Union[str, bytes, bytearray]]) -> dict:
    """Extract evidence-grounded privacy-policy statements by topic."""
    if policy_text is None:
        return {"topics": [], "mentioned_topics": 0, "missing_topics": list(TOPIC_KEYWORDS)}

    if isinstance(policy_text, bytearray):
        policy_text = bytes(policy_text)

    if isinstance(policy_text, bytes):
        try:
            policy_text = policy_text.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PolicyAnalysisError("The privacy-policy file is unreadable. Please upload a UTF-8 text file.") from exc
    elif not isinstance(policy_text, str):
        raise PolicyAnalysisError("Privacy-policy input must be text.")

    if not policy_text.strip():
        return {"topics": [], "mentioned_topics": 0, "missing_topics": list(TOPIC_KEYWORDS)}

    sentences = _sentences(policy_text)
    topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        excerpts = []
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                if sentence not in excerpts:
                    excerpts.append(sentence)

        if excerpts:
            summary = excerpts[0]
            topics.append({
                "topic": topic,
                "status": "Mentioned",
                "summary": summary,
                "excerpts": excerpts,
            })

    mentioned_topics = len(topics)
    mentioned_names = {record["topic"] for record in topics}
    missing_topics = [topic for topic in TOPIC_KEYWORDS if topic not in mentioned_names]

    return {
        "topics": topics,
        "mentioned_topics": mentioned_topics,
        "missing_topics": missing_topics,
    }

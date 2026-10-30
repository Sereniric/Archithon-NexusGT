import re
from typing import Optional


POTENTIALLY_RELEVANT = "Potentially relevant"
NEEDS_REVIEW = "Needs review / unclear"
NO_RELATIONSHIP = "No clear relationship identified"
UNKNOWN = "Unknown / Cannot Determine"


PURPOSE_KEYWORDS = {
    "camera": ("camera", "photo", "video", "picture", "scan", "qr"),
    "microphone": ("microphone", "audio", "voice", "recording", "call"),
    "location": ("location", "map", "navigation", "weather", "travel", "delivery", "nearby"),
    "contacts": ("contacts", "address book", "people", "friends", "social"),
    "calendar": ("calendar", "schedule", "event", "appointment"),
    "sms": ("sms", "text message", "messaging", "verification code", "otp"),
    "calls": ("phone", "call", "telephone", "dial"),
    "files": ("file", "document", "download", "storage", "gallery", "photo", "video", "media"),
    "device": ("device", "system", "network", "bluetooth", "sensor", "notification", "account"),
    "health": ("health", "fitness", "heart", "activity", "step", "sensor"),
}

PERMISSION_PURPOSE_GROUP = {
    "android.permission.CAMERA": "camera",
    "android.permission.RECORD_AUDIO": "microphone",
    "android.permission.ACCESS_FINE_LOCATION": "location",
    "android.permission.ACCESS_COARSE_LOCATION": "location",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "location",
    "android.permission.READ_CONTACTS": "contacts",
    "android.permission.WRITE_CONTACTS": "contacts",
    "android.permission.READ_CALENDAR": "calendar",
    "android.permission.WRITE_CALENDAR": "calendar",
    "android.permission.READ_SMS": "sms",
    "android.permission.RECEIVE_SMS": "sms",
    "android.permission.SEND_SMS": "sms",
    "android.permission.CALL_PHONE": "calls",
    "android.permission.READ_CALL_LOG": "calls",
    "android.permission.WRITE_CALL_LOG": "calls",
    "android.permission.READ_PHONE_STATE": "device",
    "android.permission.READ_EXTERNAL_STORAGE": "files",
    "android.permission.WRITE_EXTERNAL_STORAGE": "files",
    "android.permission.READ_MEDIA_IMAGES": "files",
    "android.permission.READ_MEDIA_VIDEO": "files",
    "android.permission.READ_MEDIA_AUDIO": "files",
    "android.permission.BODY_SENSORS": "health",
    "android.permission.ACTIVITY_RECOGNITION": "health",
    "android.permission.BLUETOOTH_SCAN": "device",
    "android.permission.BLUETOOTH_CONNECT": "device",
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def analyze_application_purpose(
    application_name: Optional[str],
    application_purpose: Optional[str],
    permission_analysis: Optional[dict],
) -> dict:
    """Assess whether recognized permission capabilities relate to a stated purpose."""
    name = (application_name or "").strip()
    purpose = (application_purpose or "").strip()

    if not purpose:
        return {
            "performed": False,
            "application_name": name or "Not provided",
            "message": "Purpose analysis was not performed because no application purpose was provided.",
            "assessments": [],
            "unknown_permissions": [],
        }

    if not isinstance(permission_analysis, dict):
        permission_analysis = {"recognized": [], "unknown": []}

    purpose_text = purpose.lower()
    purpose_tokens = _tokens(purpose_text)
    assessments = []

    for record in permission_analysis.get("recognized", []):
        identifier = record.get("permission", "")
        capability = record.get("capability", "Not available")
        group = PERMISSION_PURPOSE_GROUP.get(identifier)

        if group is None:
            category = NEEDS_REVIEW
            explanation = "The permission has no deterministic purpose mapping; its relationship cannot be established from the available purpose text."
        else:
            keywords = PURPOSE_KEYWORDS[group]
            keyword_match = any(keyword in purpose_text for keyword in keywords)

            if keyword_match:
                category = POTENTIALLY_RELEVANT
                explanation = f"The stated purpose contains language related to {group}; the permission's known capability may support that stated functionality. This does not establish actual app behavior."
            elif len(purpose_tokens) < 3:
                category = NEEDS_REVIEW
                explanation = "The purpose description is too short to establish a clear relationship. Further review would be needed."
            else:
                category = NO_RELATIONSHIP
                explanation = f"No clear relationship was identified between the stated purpose and the permission's known {group}-related capability."

        assessments.append({
            "permission": identifier,
            "capability": capability,
            "assessment": category,
            "explanation": explanation,
        })

    unknown_permissions = []
    for record in permission_analysis.get("unknown", []):
        unknown_permissions.append({
            "permission": record.get("permission", ""),
            "assessment": UNKNOWN,
            "capability": "Unknown capability — unsupported by the knowledge base",
            "explanation": "The exact permission is unknown, so no capability or purpose relationship was invented.",
        })

    return {
        "performed": True,
        "application_name": name or "Not provided",
        "message": "Purpose analysis based only on the user-stated description and known permission capabilities.",
        "assessments": assessments,
        "unknown_permissions": unknown_permissions,
    }

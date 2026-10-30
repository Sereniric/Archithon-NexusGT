from typing import Optional


COVERAGE_FOUND = "Policy Coverage Found"
NO_POLICY_STATEMENT = "No Relevant Policy Statement Found"
UNKNOWN = "Unknown / Cannot Determine"


PERMISSION_TOPIC_MAP = {
    "android.permission.CAMERA": ("Camera, microphone, and contacts", "camera access"),
    "android.permission.RECORD_AUDIO": ("Camera, microphone, and contacts", "microphone access"),
    "android.permission.READ_CONTACTS": ("Camera, microphone, and contacts", "contact access"),
    "android.permission.WRITE_CONTACTS": ("Camera, microphone, and contacts", "contact access"),
    "android.permission.ACCESS_FINE_LOCATION": ("Location data", "precise location access"),
    "android.permission.ACCESS_COARSE_LOCATION": ("Location data", "approximate location access"),
    "android.permission.ACCESS_BACKGROUND_LOCATION": ("Location data", "background location access"),
    "android.permission.READ_CALENDAR": ("Personal data collection", "personal calendar data access"),
    "android.permission.WRITE_CALENDAR": ("Personal data collection", "personal calendar data access"),
    "android.permission.READ_SMS": ("Personal data collection", "SMS data access"),
    "android.permission.RECEIVE_SMS": ("Personal data collection", "SMS data access"),
    "android.permission.SEND_SMS": ("Personal data collection", "SMS data access"),
    "android.permission.READ_CALL_LOG": ("Personal data collection", "call history data access"),
    "android.permission.WRITE_CALL_LOG": ("Personal data collection", "call history data access"),
    "android.permission.CALL_PHONE": ("Personal data collection", "phone access"),
    "android.permission.READ_PHONE_STATE": ("Device information", "device and phone state information"),
    "android.permission.READ_EXTERNAL_STORAGE": ("Data storage and retention", "stored file access"),
    "android.permission.WRITE_EXTERNAL_STORAGE": ("Data storage and retention", "stored file access"),
    "android.permission.READ_MEDIA_IMAGES": ("Data storage and retention", "stored image access"),
    "android.permission.READ_MEDIA_VIDEO": ("Data storage and retention", "stored video access"),
    "android.permission.READ_MEDIA_AUDIO": ("Data storage and retention", "stored audio access"),
    "android.permission.ACTIVITY_RECOGNITION": ("Device information", "activity and device sensor data"),
    "android.permission.BODY_SENSORS": ("Personal data collection", "body sensor data"),
    "android.permission.BLUETOOTH_SCAN": ("Device information", "nearby Bluetooth device information"),
    "android.permission.BLUETOOTH_CONNECT": ("Device information", "paired Bluetooth device information"),
}


def compare_permissions_with_policy(
    permission_analysis: Optional[dict],
    policy_analysis: Optional[dict],
) -> dict:
    """Compare recognized permissions with policy topics without making risk judgments."""
    if not isinstance(permission_analysis, dict) or not permission_analysis.get("recognized"):
        permission_results = []
        unknown_permissions = [] if not isinstance(permission_analysis, dict) else permission_analysis.get("unknown", [])
        if isinstance(permission_analysis, dict):
            permission_results = []
        return {
            "comparisons": permission_results,
            "unknown_permissions": unknown_permissions,
            "coverage_count": 0,
            "gap_count": 0,
            "unknown_count": len(unknown_permissions),
        }

    policy_is_empty = (
        not isinstance(policy_analysis, dict)
        or policy_analysis.get("mentioned_topics", 0) == 0
        or not policy_analysis.get("topics")
    )
    policy_topics = [] if not isinstance(policy_analysis, dict) else policy_analysis.get("topics", [])
    topics_by_name = {
        record.get("topic"): record
        for record in policy_topics
        if isinstance(record, dict) and record.get("topic")
    }

    comparisons = []
    coverage_count = 0
    gap_count = 0

    for permission in permission_analysis.get("recognized", []):
        identifier = permission.get("permission", "")
        mapping = PERMISSION_TOPIC_MAP.get(identifier)

        if mapping is None or policy_is_empty:
            status = UNKNOWN
            relevant_topic = mapping[0] if mapping is not None else None
            reason = (
                "The supplied policy text is empty, so policy coverage cannot be determined."
                if policy_is_empty
                else "No deterministic policy-topic mapping is defined for this permission."
            )
            excerpts = []
        else:
            relevant_topic, access_label = mapping
            reason = f"The policy topic is relevant because it describes {access_label}."
            topic_record = topics_by_name.get(relevant_topic)

            if topic_record is not None and topic_record.get("excerpts"):
                status = COVERAGE_FOUND
                excerpts = list(topic_record["excerpts"])
                coverage_count += 1
            else:
                status = NO_POLICY_STATEMENT
                excerpts = []
                gap_count += 1

        comparisons.append({
            "permission": identifier,
            "status": status,
            "relevant_policy_topic": relevant_topic,
            "reason": reason,
            "supporting_excerpts": excerpts,
        })

    unknown_permissions = permission_analysis.get("unknown", [])
    return {
        "comparisons": comparisons,
        "unknown_permissions": unknown_permissions,
        "coverage_count": coverage_count,
        "gap_count": gap_count,
        "unknown_count": len(unknown_permissions),
    }

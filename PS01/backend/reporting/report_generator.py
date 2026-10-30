import json
from datetime import datetime, timezone
from typing import Optional


def generate_report_markdown(
    permission_analysis: Optional[dict] = None,
    policy_analysis: Optional[dict] = None,
    policy_comparison: Optional[dict] = None,
    purpose_result: Optional[dict] = None,
    application_name: Optional[str] = None,
    application_purpose: Optional[str] = None,
) -> str:
    """Generate a readable evidence-linked report from existing analyzer outputs."""
    permission_analysis = permission_analysis if isinstance(permission_analysis, dict) else {}
    policy_analysis = policy_analysis if isinstance(policy_analysis, dict) else {}
    policy_comparison = policy_comparison if isinstance(policy_comparison, dict) else {}
    purpose_result = purpose_result if isinstance(purpose_result, dict) else {}

    name = (application_name or "").strip() or "Not provided"
    stated_purpose = (application_purpose or "").strip() or "Not provided"
    extracted_permissions = [
        record.get("permission", "")
        for record in permission_analysis.get("recognized", [])
    ] + [
        record.get("permission", "")
        for record in permission_analysis.get("unknown", [])
    ]

    lines = [
        "# Explainable Application Privacy and Permission Analysis Report",
        "",
        "## Application Information",
        f"- Application name: {name}",
        f"- Stated purpose: {stated_purpose}",
        "",
        "## Extracted Android Permissions",
        f"- Total permission count: {len(extracted_permissions)}",
    ]

    if extracted_permissions:
        for permission in extracted_permissions:
            lines.append(f"- `{permission}`")
    else:
        lines.append("- No permissions were provided or extracted.")

    lines.extend(["", "## Recognized Permission Explanations"])
    recognized = permission_analysis.get("recognized", [])
    if recognized:
        for record in recognized:
            lines.extend([
                f"### `{record.get('permission', '')}`",
                f"- Description: {record.get('description', 'Not available')}",
                f"- Capability: {record.get('capability', 'Not available')}",
                f"- Potential privacy implications: {record.get('privacy_implications', 'Not available')}",
                f"- Protection level: {record.get('protection_level', 'Not available')}",
                f"- Official documentation: {record.get('official_documentation_url', 'Not available')}",
                f"- Category: {record.get('category', 'Not available')}",
            ])
            lines.append("")
    else:
        lines.append("No recognized permissions were found.")

    lines.extend(["", "## Unknown / Unsupported Permissions"])
    unknown_permissions = permission_analysis.get("unknown", [])
    if unknown_permissions:
        for record in unknown_permissions:
            lines.append(f"- `{record.get('permission', '')}` — Unknown / Unsupported")
    else:
        lines.append("No unknown permissions were found.")

    lines.extend(["", "## Privacy Policy Analysis"])
    policy_topics = policy_analysis.get("topics", [])
    if policy_topics:
        for record in policy_topics:
            lines.append(f"### {record.get('topic', 'Unidentified topic')}")
            lines.append(f"Summary grounded in supplied text: {record.get('summary', 'Not available')}")
            lines.append("Supporting excerpts:")
            for excerpt in record.get("excerpts", []):
                lines.append(f"> {excerpt}")
            lines.append("")
    elif policy_analysis:
        lines.append("No privacy-policy topics were identified from the supplied text.")
    else:
        lines.append("Privacy policy analysis was not provided.")

    missing_topics = policy_analysis.get("missing_topics", [])
    lines.append("### Missing or undetermined topics")
    if missing_topics:
        for topic in missing_topics:
            lines.append(f"- {topic}")
    else:
        lines.append("No missing topics were reported, or a policy was not supplied.")

    lines.extend(["", "## Permission–Policy Comparison"])
    if policy_comparison:
        comparisons = policy_comparison.get("comparisons", [])
        lines.append(f"- Policy coverage found: {policy_comparison.get('coverage_count', 0)}")
        lines.append(f"- Potential transparency gaps: {policy_comparison.get('gap_count', 0)}")
        lines.append(f"- Unknown permissions: {policy_comparison.get('unknown_count', 0)}")
        for record in comparisons:
            lines.append(f"### `{record.get('permission', '')}`")
            lines.append(f"- Status: {record.get('status', 'Unknown / Cannot Determine')}")
            lines.append(f"- Relevant policy topic: {record.get('relevant_policy_topic') or 'Not available'}")
            lines.append(f"- Reason: {record.get('reason', 'Not available')}")
            excerpts = record.get("supporting_excerpts", [])
            if excerpts:
                lines.append("- Supporting policy excerpts:")
                for excerpt in excerpts:
                    lines.append(f"  > {excerpt}")
        if not comparisons and not policy_comparison.get("unknown_permissions"):
            lines.append("No recognized permissions were available for comparison.")
    else:
        lines.append("Permission–policy comparison was not provided or inputs were missing.")

    lines.extend(["", "## Application Purpose Assessment"])
    if purpose_result and purpose_result.get("performed"):
        lines.append(f"- Application purpose used: {stated_purpose}")
        for record in purpose_result.get("assessments", []):
            lines.extend([
                f"### `{record.get('permission', '')}`",
                f"- Known capability: {record.get('capability', 'Not available')}",
                f"- Assessment: {record.get('assessment', 'Needs review / unclear')}",
                f"- Explanation: {record.get('explanation', 'Not available')}",
            ])
        for record in purpose_result.get("unknown_permissions", []):
            lines.extend([
                f"### `{record.get('permission', '')}`",
                "- Assessment: Unknown / Cannot Determine",
                "- Capability: Unknown capability — unsupported by the knowledge base",
                f"- Explanation: {record.get('explanation', 'No explanation available')}",
            ])
    elif purpose_result:
        lines.append(purpose_result.get("message", "Purpose analysis was not performed."))
    else:
        lines.append("Purpose analysis was not performed or no purpose was provided.")

    lines.extend([
        "",
        "## Potential Transparency Gaps and Items Requiring Review",
        "- Missing policy statements are potential transparency gaps, not proof of wrongdoing.",
        "- Unknown or unmapped permissions require further review rather than speculative explanation.",
        "- Purpose assessments are based only on the user-stated description and known permission capabilities.",
        "",
        "## Limitations",
        "- Declared permissions do not prove actual runtime application behavior or data access.",
        "- Policy summaries are deterministic extracts from supplied policy text and do not verify compliance.",
        "- This report makes no claim that the application is malicious or safe.",
        "- The comparison may be incomplete where permissions, policy topics, or purpose mappings are unavailable.",
    ])

    return "\n".join(lines).rstrip() + "\n"


def generate_report_json(**results) -> str:
    """Generate structured JSON for optional machine-readable inspection."""
    return json.dumps(results, indent=2, ensure_ascii=False)

from typing import Union

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException


ANDROID_NAMESPACE = "http://schemas.android.com/apk/res/android"
PERMISSION_TAGS = {
    "uses-permission",
    "uses-permission-sdk-23",
    "uses-permission-sdk-m",
}


class ManifestParseError(ValueError):
    """Raised when a manifest cannot be safely parsed as XML."""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag.rsplit(":", 1)[-1]


def extract_permissions(content: Union[str, bytes, bytearray]) -> list[str]:
    """Safely extract unique Android permission names in declaration order."""
    if content is None:
        return []

    if isinstance(content, bytearray):
        content = bytes(content)

    if isinstance(content, bytes):
        if not content.strip():
            return []
    elif isinstance(content, str):
        if not content.strip():
            return []
    else:
        raise TypeError("Manifest content must be text, bytes, or bytearray")

    try:
        root = ElementTree.fromstring(content)
    except (ElementTree.ParseError, DefusedXmlException, ValueError) as exc:
        raise ManifestParseError("The uploaded file is not valid AndroidManifest.xml content.") from exc

    permissions = []
    seen = set()

    for element in root.iter():
        if _local_name(element.tag) not in PERMISSION_TAGS:
            continue

        name = element.attrib.get("{" + ANDROID_NAMESPACE + "}name")
        if name is None:
            name = element.attrib.get("name")

        if name and name.strip():
            permission = name.strip()
            if permission not in seen:
                seen.add(permission)
                permissions.append(permission)

    return permissions


parse_manifest = extract_permissions

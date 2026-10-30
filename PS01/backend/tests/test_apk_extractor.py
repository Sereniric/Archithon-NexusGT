import io
import sys
import zipfile
from pathlib import Path

import pytest


PS01_ROOT = Path(__file__).resolve().parents[2]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.analyzer.apk_extractor import (
    APKExtractionError,
    MAX_APK_SIZE,
    extract_manifest_from_apk,
)
from backend.analyzer.manifest_parser import extract_permissions
from backend.analyzer.permission_analyzer import analyze_permissions

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
REAL_APK = FIXTURE_DIR / "real-app-profile.apk"


def make_apk(manifest: bytes) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("AndroidManifest.xml", manifest)
    return output.getvalue()


def test_real_profile_apk_decodes_manifest_and_permissions():
    manifest = extract_manifest_from_apk(REAL_APK.read_bytes())
    permissions = extract_permissions(manifest)

    assert "android.permission.INTERNET" in permissions
    analysis = analyze_permissions(permissions)
    assert analysis["total"] == len(permissions)
    assert any(record["permission"].endswith("DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION") for record in analysis["unknown"])


def test_plain_xml_manifest_inside_apk_is_supported():
    xml = b'<manifest xmlns:android="http://schemas.android.com/apk/res/android"><uses-permission android:name="android.permission.CAMERA" /></manifest>'
    decoded = extract_manifest_from_apk(make_apk(xml))
    assert extract_permissions(decoded) == ["android.permission.CAMERA"]


def test_empty_apk_rejected():
    with pytest.raises(APKExtractionError, match="empty"):
        extract_manifest_from_apk(b"")


def test_non_zip_rejected():
    with pytest.raises(APKExtractionError, match="not a valid APK/ZIP"):
        extract_manifest_from_apk(b"not a zip file")


def test_missing_manifest_rejected():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("classes.dex", b"dummy")
    with pytest.raises(APKExtractionError, match="does not contain"):
        extract_manifest_from_apk(output.getvalue())


def test_apk_over_size_limit_rejected():
    with pytest.raises(APKExtractionError, match="50 MB"):
        extract_manifest_from_apk(b"x" * (MAX_APK_SIZE + 1))


def test_manifest_over_decompressed_limit_rejected():
    apk = make_apk(b"x" * (10 * 1024 * 1024 + 1))
    with pytest.raises(APKExtractionError, match="10 MB"):
        extract_manifest_from_apk(apk)


def test_password_protected_entry_rejected():
    apk = bytearray(make_apk(b"<manifest />"))
    local_name_position = apk.find(b"AndroidManifest.xml")
    assert local_name_position >= 0
    # Directly mark both the central and local headers with encrypted-entry flags.
    for header in (b"PK\x03\x04", b"PK\x01\x02"):
        start = 0
        while True:
            start = apk.find(header, start)
            if start < 0:
                break
            if header == b"PK\x03\x04":
                apk[start + 6] |= 0x01
            else:
                apk[start + 8] |= 0x01
            start += 4
    with pytest.raises(APKExtractionError, match="Password-protected"):
        extract_manifest_from_apk(apk)


def test_wrong_content_type_rejected():
    with pytest.raises(TypeError, match="bytes or bytearray"):
        extract_manifest_from_apk("<manifest />")

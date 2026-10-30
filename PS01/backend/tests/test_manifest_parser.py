import sys
from pathlib import Path

import pytest


PS01_ROOT = Path(__file__).resolve().parents[2]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.analyzer.manifest_parser import ManifestParseError, extract_permissions


def test_successful_permission_extraction():
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android">
      <uses-permission android:name="android.permission.CAMERA" />
    </manifest>
    """
    assert extract_permissions(manifest) == ["android.permission.CAMERA"]


def test_multiple_permission_declarations():
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android">
      <uses-permission android:name="android.permission.CAMERA" />
      <uses-permission-sdk-23 android:name="android.permission.ACCESS_FINE_LOCATION" />
      <uses-permission-sdk-m android:name="android.permission.RECORD_AUDIO" />
    </manifest>
    """
    assert extract_permissions(manifest) == [
        "android.permission.CAMERA",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.RECORD_AUDIO",
    ]


def test_duplicate_permissions_preserve_first_order():
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android">
      <uses-permission android:name="android.permission.CAMERA" />
      <uses-permission android:name="android.permission.CAMERA" />
      <uses-permission android:name="android.permission.RECORD_AUDIO" />
    </manifest>
    """
    assert extract_permissions(manifest) == [
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
    ]


def test_manifest_with_no_permissions():
    manifest = '<manifest xmlns:android="http://schemas.android.com/apk/res/android" />'
    assert extract_permissions(manifest) == []


def test_malformed_xml_raises_clear_error():
    with pytest.raises(ManifestParseError, match="not valid AndroidManifest.xml"):
        extract_permissions("<manifest><uses-permission></manifest>")


@pytest.mark.parametrize("content", ["", "   ", b"", b"  "])
def test_empty_input_returns_no_permissions(content):
    assert extract_permissions(content) == []


def test_android_namespace_handling():
    manifest = b"""
    <manifest xmlns:android="http://schemas.android.com/apk/res/android">
      <application>
        <uses-permission android:name="android.permission.READ_CONTACTS" />
      </application>
    </manifest>
    """
    assert extract_permissions(manifest) == ["android.permission.READ_CONTACTS"]

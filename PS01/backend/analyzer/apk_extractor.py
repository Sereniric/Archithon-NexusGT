import io
import zipfile
from typing import Union

from androguard.core.axml import AXMLPrinter


MAX_APK_SIZE = 50 * 1024 * 1024
MAX_MANIFEST_SIZE = 10 * 1024 * 1024
MANIFEST_ENTRY = "AndroidManifest.xml"


class APKExtractionError(ValueError):
    """Raised when an APK cannot be safely validated or decoded."""


def extract_manifest_from_apk(content: Union[bytes, bytearray]) -> bytes:
    """Validate an APK, read its manifest entry, and decode binary manifest XML."""
    if isinstance(content, bytearray):
        content = bytes(content)
    if not isinstance(content, bytes):
        raise TypeError("APK content must be bytes or bytearray")
    if len(content) > MAX_APK_SIZE:
        raise APKExtractionError("The APK exceeds the maximum upload size of 50 MB.")
    if not content:
        raise APKExtractionError("The uploaded APK is empty.")

    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
            try:
                manifest_info = archive.getinfo(MANIFEST_ENTRY)
            except KeyError as exc:
                raise APKExtractionError("The APK does not contain AndroidManifest.xml.") from exc

            if manifest_info.flag_bits & 0x1:
                raise APKExtractionError("Password-protected APK entries are not supported.")
            if manifest_info.file_size > MAX_MANIFEST_SIZE:
                raise APKExtractionError("The decompressed AndroidManifest.xml exceeds the 10 MB safety limit.")

            try:
                with archive.open(manifest_info, "r") as manifest_file:
                    binary_manifest = manifest_file.read(MAX_MANIFEST_SIZE + 1)
            except (zipfile.BadZipFile, RuntimeError, EOFError) as exc:
                raise APKExtractionError("The uploaded APK contains a corrupt AndroidManifest.xml entry.") from exc
    except APKExtractionError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, EOFError, OSError) as exc:
        raise APKExtractionError("The uploaded file is not a valid APK/ZIP package.") from exc

    if len(binary_manifest) > MAX_MANIFEST_SIZE:
        raise APKExtractionError("The decompressed AndroidManifest.xml exceeds the 10 MB safety limit.")

    if binary_manifest.lstrip().startswith(b"<"):
        return binary_manifest

    try:
        decoded_xml = AXMLPrinter(binary_manifest).get_xml()
    except Exception as exc:
        raise APKExtractionError("The APK manifest is malformed or uses an unsupported Android binary XML format.") from exc

    if isinstance(decoded_xml, str):
        return decoded_xml.encode("utf-8")
    if isinstance(decoded_xml, bytes):
        return decoded_xml

    raise APKExtractionError("The APK decoder could not serialize the Android manifest.")

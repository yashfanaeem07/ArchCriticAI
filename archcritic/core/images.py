"""
core/images.py
--------------
Small helpers for turning an uploaded image into the format the AI expects.
"""

import base64

# Image formats we accept from the uploader (lower-case, no leading dot).
SUPPORTED_IMAGE_TYPES = ("png", "jpg", "jpeg", "webp", "gif")


def encode_image_block(image_bytes: bytes, media_type: str) -> dict:
    """
    Convert raw image bytes into an API "image" content block.

    media_type is the MIME type, e.g. "image/png" or "image/jpeg" - Streamlit's
    uploader gives this to us directly via `uploaded_file.type`.
    """
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.b64encode(image_bytes).decode("utf-8"),
        },
    }

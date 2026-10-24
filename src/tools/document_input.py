"""Image payloads for the injected model client; no network calls here."""
import base64

def image_block(data: bytes, media_type: str) -> dict:
    if media_type not in {"image/png", "image/jpeg", "image/gif", "image/webp"}:
        raise ValueError("Upload a PNG, JPEG, GIF, or WebP image. Convert PDF pages to images first.")
    return {"type": "image", "source": {"type": "base64", "media_type": media_type,
            "data": base64.standard_b64encode(data).decode("ascii")}}

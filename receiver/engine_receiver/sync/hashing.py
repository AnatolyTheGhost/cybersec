from __future__ import annotations

import hashlib

try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False


def compute_hash(content: str | bytes) -> str:
    """Compute hash for file content, preferring BLAKE3."""
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content

    if HAS_BLAKE3:
        return blake3.blake3(content_bytes).hexdigest()
    
    return hashlib.sha256(content_bytes).hexdigest()

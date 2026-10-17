"""
Audit & Tamper-Evident SHA-256 Stamp Generator.
Generates cryptographic proof of state for business approvals and quality decisions.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict


def generate_audit_stamp(entity_id: str, action: str, user_id: str, payload: Dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    raw = f"{entity_id}:{action}:{user_id}:{serialized}:{datetime.now(timezone.utc).date().isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

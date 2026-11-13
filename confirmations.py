"""
Confirmations module - server-issued single-use confirmation tokens.
New module for API-06.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import secrets


# Pending confirmations store (in-memory for demo)
# Key: confirmation_id -> {kind, draft_hash, session_id, expires_at, used}
PENDING_CONFIRMATIONS: Dict[str, Dict[str, Any]] = {}


CONFIRMATION_TTL_SECONDS = 120  # 2 minutes


def generate_confirmation_id() -> str:
    """Generate a unique confirmation ID."""
    return secrets.token_hex(16)


def generate_draft_hash(draft: Dict[str, Any]) -> str:
    """Generate hash for draft verification."""
    import json
    draft_str = json.dumps(draft, sort_keys=True)
    return hashlib.sha256(draft_str.encode()).hexdigest()


def create_confirmation(kind: str, draft: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    Create a pending confirmation for a consequential action.
    Returns confirmation object with masked summary.
    """
    conf_id = generate_confirmation_id()
    draft_hash = generate_draft_hash(draft)
    expires_at = datetime.utcnow() + timedelta(seconds=CONFIRMATION_TTL_SECONDS)

    # Create masked summary
    if kind == "tanker":
        masked_summary = f"Tanker request at {draft.get('address', 'unknown')} near {draft.get('landmark', 'unknown')}, contact ending {draft.get('contact_number', '')[-4:] if draft.get('contact_number') else '****'}, capacity {draft.get('capacity', 'unknown')}L"
    elif kind == "grievance":
        masked_summary = f"Grievance: {draft.get('category', 'unknown')} at {draft.get('location', 'unknown')}"
    else:
        masked_summary = f"{kind} request"

    PENDING_CONFIRMATIONS[conf_id] = {
        "kind": kind,
        "draft_hash": draft_hash,
        "session_id": session_id,
        "expires_at": expires_at,
        "used": False,
        "draft": draft  # Store draft for submission
    }

    return {
        "id": conf_id,
        "kind": kind,
        "summary_masked": masked_summary,
        "expires_in": CONFIRMATION_TTL_SECONDS
    }


def verify_and_use_confirmation(
    conf_id: str,
    decision: str,
    session_id: str,
    current_draft: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Verify and use a confirmation token.
    If decision is "confirm", submit the action through tools.
    """
    if conf_id not in PENDING_CONFIRMATIONS:
        return {
            "status": "error",
            "message": "Invalid confirmation ID"
        }

    conf = PENDING_CONFIRMATIONS[conf_id]

    # Check if already used
    if conf["used"]:
        return {
            "status": "error",
            "message": "Confirmation already used"
        }

    # Check if expired
    if datetime.utcnow() > conf["expires_at"]:
        del PENDING_CONFIRMATIONS[conf_id]
        return {
            "status": "error",
            "message": "Confirmation expired"
        }

    # Check session match
    if conf["session_id"] != session_id:
        return {
            "status": "error",
            "message": "Confirmation does not belong to this session"
        }

    # Check draft hash if current draft provided
    if current_draft is not None:
        current_hash = generate_draft_hash(current_draft)
        if current_hash != conf["draft_hash"]:
            return {
                "status": "error",
                "message": "Draft has changed since confirmation was issued"
            }

    # If decision is cancel, just mark as used
    if decision == "cancel":
        conf["used"] = True
        return {
            "status": "cancelled",
            "message": "Action cancelled by user"
        }

    # Decision is confirm - mark as used and submit
    conf["used"] = True

    # Submit through tools
    from .tools import call_tool

    if conf["kind"] == "tanker":
        result = call_tool("submit_tanker_booking", session_id, conf["draft"], session_id)
        return {
            "status": "completed",
            "booked": result.get("booked", False),
            "message": result.get("message", ""),
            "official_url": result.get("official_url")
        }
    elif conf["kind"] == "grievance":
        result = call_tool("submit_grievance", session_id, conf["draft"], session_id)
        return {
            "status": "completed",
            "filed": result.get("filed", False),
            "message": result.get("message", ""),
            "official_url": result.get("official_url")
        }
    else:
        return {
            "status": "error",
            "message": f"Unknown confirmation kind: {conf['kind']}"
        }


def cleanup_expired_confirmations():
    """Remove expired confirmations (call periodically)."""
    now = datetime.utcnow()
    expired_ids = [
        cid for cid, conf in PENDING_CONFIRMATIONS.items()
        if now > conf["expires_at"]
    ]
    for cid in expired_ids:
        del PENDING_CONFIRMATIONS[cid]

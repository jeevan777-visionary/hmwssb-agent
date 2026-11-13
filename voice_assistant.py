"""
Voice assistant module - wake word, standby, flows, memory.
Verbatim from BUILD_SPEC with fixes for D-02, D-10, D-11, D-08.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re


# Voice memory keyed by session ID (fix for D-11)
VOICE_MEMORY: Dict[str, Dict[str, Any]] = {}


# Session TTL (default 30 minutes)
SESSION_TTL_SECONDS = 1800


ACTIVE_TIMEOUT_MS = 45000  # 45 seconds of no speech returns to standby


def generate_session_id() -> str:
    """Generate a unique session ID."""
    import secrets
    return secrets.token_hex(16)


def get_session_memory(session_id: str) -> Dict[str, Any]:
    """Get or create session memory."""
    if session_id not in VOICE_MEMORY:
        VOICE_MEMORY[session_id] = {
            "mode": "standby",
            "last_activity": datetime.utcnow(),
            "flow": None,
            "flow_state": {},
            "last_reply": None
        }
    return VOICE_MEMORY[session_id]


def update_session_activity(session_id: str):
    """Update last activity timestamp."""
    if session_id in VOICE_MEMORY:
        VOICE_MEMORY[session_id]["last_activity"] = datetime.utcnow()


def check_session_expiry(session_id: str) -> bool:
    """Check if session has expired."""
    if session_id not in VOICE_MEMORY:
        return True

    memory = VOICE_MEMORY[session_id]
    age = datetime.utcnow() - memory["last_activity"]
    return age.total_seconds() > SESSION_TTL_SECONDS


def purge_session(session_id: str):
    """Delete session memory."""
    if session_id in VOICE_MEMORY:
        del VOICE_MEMORY[session_id]


def is_wake_word(text: str) -> bool:
    """Check if text contains wake word 'Jal' or variants."""
    text_lower = text.lower().strip()
    wake_patterns = [
        r"^jal\b",
        r"\bjal\b",
        r"^jall\b",
        r"\bjall\b"
    ]
    for pattern in wake_patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def is_cancel_command(text: str) -> bool:
    """
    Check if text is a cancel command.
    Fix for D-10: only match whole utterance, not partial matches like "no landmark".
    """
    text_lower = text.lower().strip()
    cancel_patterns = [
        r"^(cancel|stop|never mind|forget it|forget)\b$",
        r"^(that's all|that is all|thats all)\b$"
    ]
    for pattern in cancel_patterns:
        if re.match(pattern, text_lower):
            return True
    return False


def contains_digit_run(text: str) -> bool:
    """
    Check if text contains a 4-8 digit run (for OTP/password rejection).
    Fix for D-08: reject digit runs outside flows too.
    """
    # Match 4-8 consecutive digits
    pattern = r"\d{4,8}"
    return bool(re.search(pattern, text))


def redact_digits(text: str) -> str:
    """Redact digit runs from text for logging."""
    return re.sub(r"\d{4,8}", "[REDACTED]", text)


def start_voice_session(user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Start a voice session."""
    if session_id is None:
        session_id = generate_session_id()

    memory = get_session_memory(session_id)
    memory["mode"] = "standby"
    memory["last_activity"] = datetime.utcnow()
    memory["flow"] = None
    memory["flow_state"] = {}

    return {
        "reply": "Voice assistant started. Say 'Jal' to wake me up, or just start talking.",
        "spoken": "Voice assistant started. Say Jal to wake me up.",
        "mode": "standby",
        "session_id": session_id
    }


def handle_voice_input(
    text: str,
    user_id: str,
    session_id: str,
    lang: str = "en",
    require_wake: bool = False
) -> Dict[str, Any]:
    """
    Handle voice input with wake word, flows, and confirmation.
    Fix for D-02: removed screen_confirmed field.
    """
    # Check session expiry
    if check_session_expiry(session_id):
        purge_session(session_id)
        return {
            "reply": "Session expired. Please start a new voice session.",
            "mode": "standby",
            "session_id": session_id
        }

    memory = get_session_memory(session_id)
    update_session_activity(session_id)

    # Check for OTP/password (fix for D-08)
    if contains_digit_run(text):
        redacted = redact_digits(text)
        return {
            "reply": "For security, please never say your OTP or password aloud. Use the sign-in screen instead.",
            "spoken": "Please never say your OTP or password aloud. Use the sign-in screen instead.",
            "mode": memory["mode"],
            "transcript": redacted,
            "ignored": True
        }

    # Standby mode: require wake word
    if memory["mode"] == "standby" and require_wake:
        if not is_wake_word(text):
            return {
                "reply": "",
                "spoken": "",
                "mode": "standby",
                "ignored": True
            }
        else:
            # Wake word detected, switch to active
            memory["mode"] = "active"
            if text.lower().strip() == "jal":
                return {
                    "reply": "I'm listening. How can I help you?",
                    "spoken": "I'm listening. How can I help you?",
                    "mode": "active",
                    "transcript": text
                }
            # Continue with the rest of the utterance

    # Check for cancel command (fix for D-10: whole utterance only)
    if is_cancel_command(text):
        if memory["flow"]:
            memory["flow"] = None
            memory["flow_state"] = {}
            return {
                "reply": "Cancelled. Nothing was submitted.",
                "spoken": "Cancelled. Nothing was submitted.",
                "mode": "standby",
                "transcript": text
            }
        else:
            return {
                "reply": "Okay. Say 'Jal' when you're ready to continue.",
                "spoken": "Okay. Say Jal when you're ready to continue.",
                "mode": "standby",
                "transcript": text
            }

    # Handle active flows
    if memory["flow"]:
        flow_result = handle_flow_step(text, memory["flow"], memory["flow_state"], user_id)
        if flow_result.get("complete"):
            # Flow complete, return to standby
            memory["flow"] = None
            memory["flow_state"] = {}
            memory["mode"] = "standby"

            # If confirmation needed, create confirmation object (API-06)
            if flow_result.get("needs_confirmation"):
                # Import confirmation module
                from .confirmations import create_confirmation
                draft = flow_result.get("draft")
                kind = flow_result.get("kind")
                conf = create_confirmation(kind, draft, session_id)
                flow_result["confirmation"] = conf
                flow_result["reply"] = "Please confirm on the screen."
                flow_result["spoken"] = "Please confirm on the screen."

            return flow_result
        else:
            # Flow continues
            memory["flow_state"] = flow_result.get("flow_state", memory["flow_state"])
            return flow_result

    # No active flow - use orchestrator
    from .orchestrator import handle

    result = handle(text, user_id, lang)
    reply = result.get("reply", "")

    # Check if this starts a flow
    if result.get("intent") == "tanker_booking":
        memory["flow"] = "tanker"
        memory["flow_state"] = {"step": "address"}
        return {
            "reply": "I'll help you book a tanker. What's your address?",
            "spoken": "I'll help you book a tanker. What's your address?",
            "mode": "active",
            "flow": "tanker",
            "transcript": text
        }

    if result.get("intent") == "grievance":
        memory["flow"] = "grievance"
        memory["flow_state"] = {"step": "category"}
        return {
            "reply": "I'll help you file a grievance. What type of issue is it? (water supply, billing, sewerage, quality, connection, or other)",
            "spoken": "I'll help you file a grievance. What type of issue is it?",
            "mode": "active",
            "flow": "grievance",
            "transcript": text
        }

    # Update last reply for "say that again"
    memory["last_reply"] = reply

    return {
        "reply": reply,
        "spoken": reply,  # Simple TTS text - in production, process differently
        "mode": memory["mode"],
        "transcript": text,
        "tool": result.get("tool"),
        "intent": result.get("intent")
    }


def handle_flow_step(text: str, flow: str, flow_state: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handle a step in an active flow."""
    if flow == "tanker":
        return handle_tanker_flow(text, flow_state, user_id)
    elif flow == "grievance":
        return handle_grievance_flow(text, flow_state, user_id)
    else:
        return {"error": "unknown_flow"}


def handle_tanker_flow(text: str, flow_state: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handle tanker booking flow."""
    step = flow_state.get("step", "address")

    if step == "address":
        flow_state["address"] = text
        flow_state["step"] = "landmark"
        return {
            "reply": "What's a nearby landmark?",
            "spoken": "What's a nearby landmark?",
            "mode": "active",
            "flow": "tanker",
            "flow_state": flow_state
        }

    elif step == "landmark":
        flow_state["landmark"] = text
        flow_state["step"] = "contact"
        return {
            "reply": "What's your contact number?",
            "spoken": "What's your contact number?",
            "mode": "active",
            "flow": "tanker",
            "flow_state": flow_state
        }

    elif step == "contact":
        # Validate 10-digit number
        if not re.match(r"^\d{10}$", text.strip()):
            return {
                "reply": "Please provide a valid 10-digit mobile number.",
                "spoken": "Please provide a valid 10-digit mobile number.",
                "mode": "active",
                "flow": "tanker",
                "flow_state": flow_state
            }
        flow_state["contact_number"] = text
        flow_state["step"] = "capacity"
        return {
            "reply": "What capacity do you need? 5000 liters, 10000 liters, or 15000 liters?",
            "spoken": "What capacity do you need? 5000, 10000, or 15000 liters?",
            "mode": "active",
            "flow": "tanker",
            "flow_state": flow_state
        }

    elif step == "capacity":
        valid_capacities = ["5000", "10000", "15000", "5000l", "10000l", "15000l", "5000 liters", "10000 liters", "15000 liters"]
        text_clean = text.lower().strip()
        if text_clean not in valid_capacities:
            return {
                "reply": "Please choose: 5000, 10000, or 15000 liters.",
                "spoken": "Please choose: 5000, 10000, or 15000 liters.",
                "mode": "active",
                "flow": "tanker",
                "flow_state": flow_state
            }
        flow_state["capacity"] = text_clean.replace(" liters", "").replace("l", "")
        flow_state["step"] = "confirm"

        # Prepare draft
        draft = {
            "address": flow_state["address"],
            "landmark": flow_state["landmark"],
            "contact_number": flow_state["contact_number"],
            "capacity": flow_state["capacity"]
        }

        return {
            "reply": f"Tanker request: {draft['address']} near {draft['landmark']}, contact ending {draft['contact_number'][-4:]}, capacity {draft['capacity']} liters. Say 'confirm' to proceed.",
            "spoken": f"Tanker request: address near landmark, contact ending {draft['contact_number'][-4:]}, capacity {draft['capacity']} liters. Say confirm to proceed.",
            "mode": "active",
            "flow": "tanker",
            "flow_state": flow_state,
            "draft": draft,
            "needs_confirmation": True,
            "kind": "tanker"
        }

    elif step == "confirm":
        if text.lower().strip() == "confirm":
            draft = {
                "address": flow_state["address"],
                "landmark": flow_state["landmark"],
                "contact_number": flow_state["contact_number"],
                "capacity": flow_state["capacity"]
            }
            return {
                "reply": "Please confirm on the screen.",
                "spoken": "Please confirm on the screen.",
                "mode": "active",
                "flow": "tanker",
                "draft": draft,
                "needs_confirmation": True,
                "kind": "tanker",
                "complete": True
            }
        else:
            return {
                "reply": "Say 'confirm' to proceed, or 'cancel' to start over.",
                "spoken": "Say confirm to proceed, or cancel to start over.",
                "mode": "active",
                "flow": "tanker",
                "flow_state": flow_state
            }

    return {"error": "invalid_step"}


def handle_grievance_flow(text: str, flow_state: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handle grievance filing flow."""
    step = flow_state.get("step", "category")

    if step == "category":
        valid_categories = ["water supply", "billing", "sewerage", "quality", "connection", "other"]
        text_lower = text.lower().strip()
        if text_lower not in valid_categories:
            return {
                "reply": "Please choose a category: water supply, billing, sewerage, quality, connection, or other.",
                "spoken": "Please choose a category: water supply, billing, sewerage, quality, connection, or other.",
                "mode": "active",
                "flow": "grievance",
                "flow_state": flow_state
            }
        flow_state["category"] = text_lower
        flow_state["step"] = "description"
        return {
            "reply": "Please describe the issue in detail.",
            "spoken": "Please describe the issue in detail.",
            "mode": "active",
            "flow": "grievance",
            "flow_state": flow_state
        }

    elif step == "description":
        flow_state["description"] = text
        flow_state["step"] = "location"
        return {
            "reply": "What's the location or address?",
            "spoken": "What's the location or address?",
            "mode": "active",
            "flow": "grievance",
            "flow_state": flow_state
        }

    elif step == "location":
        flow_state["location"] = text
        flow_state["step"] = "confirm"

        draft = {
            "category": flow_state["category"],
            "description": flow_state["description"],
            "location": flow_state["location"]
        }

        return {
            "reply": f"Grievance: {draft['category']} - {draft['description'][:50]}... at {draft['location']}. Say 'confirm' to proceed.",
            "spoken": f"Grievance: {draft['category']} at {draft['location']}. Say confirm to proceed.",
            "mode": "active",
            "flow": "grievance",
            "flow_state": flow_state,
            "draft": draft,
            "needs_confirmation": True,
            "kind": "grievance"
        }

    elif step == "confirm":
        if text.lower().strip() == "confirm":
            draft = {
                "category": flow_state["category"],
                "description": flow_state["description"],
                "location": flow_state["location"]
            }
            return {
                "reply": "Please confirm on the screen.",
                "spoken": "Please confirm on the screen.",
                "mode": "active",
                "flow": "grievance",
                "draft": draft,
                "needs_confirmation": True,
                "kind": "grievance",
                "complete": True
            }
        else:
            return {
                "reply": "Say 'confirm' to proceed, or 'cancel' to start over.",
                "spoken": "Say confirm to proceed, or cancel to start over.",
                "mode": "active",
                "flow": "grievance",
                "flow_state": flow_state
            }

    return {"error": "invalid_step"}

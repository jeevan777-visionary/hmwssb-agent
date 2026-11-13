"""
FastAPI main application - API endpoints.
Implements API-01 to API-11 from BUILD_SPEC.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .voice_assistant import (
    start_voice_session,
    handle_voice_input,
    get_session_memory,
    check_session_expiry,
    purge_session
)
from .orchestrator import handle as handle_chat
from .tools import call_tool
from .confirmations import verify_and_use_confirmation, cleanup_expired_confirmations
from .demo_data import get_demo_user_id


# Environment variables
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"
DEMO_OTP = os.getenv("DEMO_OTP", "")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "1800"))


# Check fail-closed auth (API-02)
if DEMO_MODE and not DEMO_OTP:
    raise RuntimeError(
        "DEMO_MODE is 1 but DEMO_OTP is not set. "
        "For security, set DEMO_OTP to a 4-8 digit code, or set DEMO_MODE=0. "
        "The default '000000' has been removed."
    )


# Session store (in-memory for demo)
# Key: session_id -> {user_id, created_at, sid}
SESSIONS: Dict[str, Dict[str, Any]] = {}


app = FastAPI(
    title="JAL AI - Intelligent HMWSSB Water Services Agent",
    description="Unofficial HMWSSB water services assistant (demo mode)",
    version="3.1"
)


# CORS middleware (API-01)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# Request/Response models
class OTPRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^\d{10}$", description="10-digit mobile number")


class OTPVerify(BaseModel):
    mobile: str = Field(..., pattern=r"^\d{10}$")
    otp: str = Field(..., pattern=r"^\d{4,8}$", description="4-8 digit OTP")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    lang: str = Field(default="en", pattern=r"^(en|te)$")


class VoiceStartRequest(BaseModel):
    lang: str = Field(default="en", pattern=r"^(en|te)$")


class VoiceAskRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    lang: str = Field(default="en", pattern=r"^(en|te)$")
    require_wake: bool = False


class ConfirmRequest(BaseModel):
    id: str
    decision: str = Field(..., pattern=r"^(confirm|cancel)$")


# Health endpoint (API-03)
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "demo_mode": DEMO_MODE
    }


# Auth endpoints
@app.post("/auth/request-otp")
def request_otp(req: OTPRequest):
    """
    Request OTP for mobile number.
    In demo mode, returns same response for all numbers (security by identical response).
    In production, would send SMS via provider.
    """
    # Rate limiting would go here (in-memory for demo)
    return {
        "message": "OTP sent",
        "demo_mode": DEMO_MODE
    }


@app.post("/auth/verify-otp")
def verify_otp(req: OTPVerify):
    """
    Verify OTP and create session.
    Demo mode: accepts only the configured DEMO_OTP.
    """
    if not DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OTP provider not configured"
        )

    if req.otp != DEMO_OTP:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )

    # Create session
    session_id = secrets.token_hex(16)
    sid = secrets.token_hex(16)  # Opaque session ID for voice memory
    user_id = get_demo_user_id(req.mobile)

    SESSIONS[session_id] = {
        "user_id": user_id,
        "mobile": req.mobile,
        "created_at": datetime.utcnow(),
        "sid": sid
    }

    return {
        "token": session_id,
        "user_id": user_id,
        "expires_in": SESSION_TTL_SECONDS
    }


# Dependency to get user from token
def get_current_user(authorization: str = Depends(lambda: None)) -> Dict[str, Any]:
    """Extract and validate bearer token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )

    token = authorization[7:]  # Remove "Bearer "

    if token not in SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    session = SESSIONS[token]
    age = datetime.utcnow() - session["created_at"]
    if age.total_seconds() > SESSION_TTL_SECONDS:
        del SESSIONS[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    return session


# Chat endpoint
@app.post("/chat")
def chat(req: ChatRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Handle text chat message."""
    user_id = current_user["user_id"]
    result = handle_chat(req.message, user_id, req.lang)
    return result


# Voice endpoints (API-04)
@app.post("/voice/start")
def voice_start(req: VoiceStartRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Start a voice session."""
    user_id = current_user["user_id"]
    sid = current_user["sid"]
    result = start_voice_session(user_id, sid)
    return result


@app.post("/voice/ask")
def voice_ask(req: VoiceAskRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Handle voice input."""
    user_id = current_user["user_id"]
    sid = current_user["sid"]
    result = handle_voice_input(req.text, user_id, sid, req.lang, req.require_wake)
    return result


# Confirmation endpoint (API-06)
@app.post("/confirm")
def confirm_action(req: ConfirmRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Confirm a consequential action (tanker booking or grievance filing)."""
    sid = current_user["sid"]
    result = verify_and_use_confirmation(req.id, req.decision, sid)
    return result


# Dashboard data endpoints (API-08)
@app.get("/bills")
def get_bills(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get bill history."""
    user_id = current_user["user_id"]
    result = call_tool("get_bill_history", user_id, {})
    return result


@app.get("/bills/analysis")
def get_bills_analysis(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get bill analysis (variance, anomalies, forecast, payment status)."""
    user_id = current_user["user_id"]

    variance = call_tool("calculate_bill_variance", user_id, {})
    anomalies = call_tool("detect_anomalies", user_id, {})
    forecast = call_tool("forecast_next_bill", user_id, {})
    payment = call_tool("get_payment_status", user_id, {})

    return {
        "variance": variance,
        "anomalies": anomalies,
        "forecast": forecast,
        "payment_status": payment
    }


@app.get("/rebates")
def get_rebates(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get rebate summary."""
    user_id = current_user["user_id"]
    result = call_tool("get_rebate_summary", user_id, {})
    return result


@app.get("/info/official")
def get_official_info():
    """Get official contact information (no auth required)."""
    from .demo_data import get_official_contact_information
    return get_official_contact_information()


@app.get("/tanker/requirements")
def get_tanker_requirements():
    """Get tanker booking requirements (no auth required)."""
    from .demo_data import get_tanker_booking_requirements
    return get_tanker_booking_requirements()


@app.post("/tanker/draft")
def create_tanker_draft(draft: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a tanker booking draft."""
    user_id = current_user["user_id"]
    result = call_tool("prepare_tanker_draft", user_id, draft)
    return result


@app.get("/grievance/categories")
def get_grievance_categories():
    """Get grievance categories (no auth required)."""
    from .demo_data import get_grievance_categories
    return {"categories": get_grievance_categories()}


@app.post("/grievance/draft")
def create_grievance_draft(draft: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a grievance draft."""
    user_id = current_user["user_id"]
    result = call_tool("prepare_grievance_draft", user_id, draft)
    return result


# Tracking endpoints (empty state in guided mode)
@app.get("/tanker/tracking")
def get_tanker_tracking(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get tanker booking tracking (empty in guided mode)."""
    return {
        "bookings": [],
        "message": "No tracking available: no authorised HMWSSB integration",
        "mode": "guided"
    }


@app.get("/grievances/tracking")
def get_grievance_tracking(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get grievance tracking (empty in guided mode)."""
    return {
        "grievances": [],
        "message": "No tracking available: no authorised HMWSSB integration",
        "mode": "guided"
    }


# Logout endpoint
@app.post("/auth/logout")
def logout(current_user: Dict[str, Any] = Depends(get_current_user), authorization: str = Depends(lambda: None)):
    """Logout and invalidate session."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if token in SESSIONS:
            sid = SESSIONS[token].get("sid")
            del SESSIONS[token]
            # Also purge voice memory
            if sid:
                purge_session(sid)

    return {"message": "Logged out successfully"}


# Public voice endpoint (API-11, U-14 approved by default)
@app.post("/public/voice/start")
def public_voice_start(req: VoiceStartRequest):
    """
    Public voice endpoint for pre-login orb.
    Limited to two tools: get_tanker_booking_requirements and get_official_contact_information.
    Rate-limited per IP (in-memory for demo).
    Account questions get sign-in prompt.
    """
    # Create anonymous short-lived session
    session_id = secrets.token_hex(16)
    sid = secrets.token_hex(16)

    result = start_voice_session("anonymous", sid)
    result["session_id"] = session_id
    result["note"] = "Public voice limited to general information only. Sign in for account-specific queries."

    return result


@app.post("/public/voice/ask")
def public_voice_ask(req: VoiceAskRequest):
    """
    Public voice ask endpoint.
    Same contract as authenticated voice, but with restricted tool access.
    """
    # For now, just return a message directing to sign in
    # Full implementation would allow the two public tools
    return {
        "reply": "Please sign in to access the full voice assistant. For general information, you can use the website without signing in.",
        "spoken": "Please sign in to access the full voice assistant.",
        "mode": "standby",
        "transcript": req.text
    }


# Startup event
@app.on_event("startup")
def startup():
    """Run on startup."""
    print(f"JAL AI Backend starting")
    print(f"Demo mode: {DEMO_MODE}")
    print(f"CORS origins: {CORS_ORIGINS}")


# Shutdown event
@app.on_event("shutdown")
def shutdown():
    """Run on shutdown."""
    print("JAL AI Backend shutting down")

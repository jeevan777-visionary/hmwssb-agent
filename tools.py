"""
Tools module - allowlisted tools with auth check and audit.
Verbatim from BUILD_SPEC with fixes for D-09, D-13.
"""

from typing import Dict, Any, List, Optional, Callable
from decimal import Decimal
import hashlib
import json
from datetime import datetime, timedelta


# Tool allowlist - only these tools can be called
ALLOWLIST = {
    "get_bill_history",
    "calculate_bill_variance",
    "detect_anomalies",
    "forecast_next_bill",
    "get_payment_status",
    "get_tanker_booking_requirements",
    "prepare_tanker_draft",
    "submit_tanker_booking",
    "get_grievance_categories",
    "prepare_grievance_draft",
    "submit_grievance",
    "get_official_contact_information",
    "get_rebate_summary"
}


# Audit log (in-memory for demo)
AUDIT_LOG: List[Dict[str, Any]] = []


# Duplicate submission tracking (in-memory for demo)
# Keys: (user_id, draft_hash) -> timestamp
DUPLICATE_TRACKER: Dict[str, datetime] = {}


def log_audit(tool: str, user_id: str, args: Dict[str, Any], result: Any):
    """Log tool call for audit purposes."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool,
        "user_id": user_id,
        "args": args,
        "result_type": type(result).__name__
    }
    AUDIT_LOG.append(entry)


def generate_draft_hash(draft: Dict[str, Any]) -> str:
    """Generate hash for draft deduplication."""
    draft_str = json.dumps(draft, sort_keys=True)
    return hashlib.sha256(draft_str.encode()).hexdigest()


def check_duplicate(user_id: str, draft: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
    """
    Check if this draft was already submitted by this user.
    Fix for D-09: key includes user_id.
    """
    draft_hash = generate_draft_hash(draft)
    key = f"{user_id}:{draft_hash}"

    if key in DUPLICATE_TRACKER:
        age = datetime.utcnow() - DUPLICATE_TRACKER[key]
        if age.total_seconds() < ttl_seconds:
            return True

    DUPLICATE_TRACKER[key] = datetime.utcnow()
    return False


def call_tool(tool_name: str, user_id: str, args: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Call an allowlisted tool with auth check and audit.
    Raises ValueError if tool not in allowlist.
    """
    if tool_name not in ALLOWLIST:
        raise ValueError(f"Tool '{tool_name}' is not in the allowlist")

    # Import here to avoid circular imports
    from .demo_data import (
        get_demo_bills,
        get_tanker_booking_requirements,
        get_grievance_categories,
        get_official_contact_information
    )
    from .billing_engine import (
        calculate_variance,
        detect_anomalies,
        forecast_next_bill,
        rebate_summary
    )
    from .analytics import check_data_quality
    from .integrations import DemoBilling, GuidedMode

    result = None

    try:
        if tool_name == "get_bill_history":
            bills = get_demo_bills(user_id)
            quality = check_data_quality(bills)
            result = {
                "label": "Demo data",
                "bills": bills,
                "quality_issues": quality['issues'],
                "quality": quality['quality']
            }

        elif tool_name == "calculate_bill_variance":
            bills = get_demo_bills(user_id)
            if len(bills) < 2:
                result = {"error": "insufficient_data"}
            else:
                # Fix for D-13: check adjacency
                current = bills[-1]
                previous = bills[-2]

                # Parse periods to check adjacency
                try:
                    curr_date = datetime.strptime(current['period'], '%Y-%m')
                    prev_date = datetime.strptime(previous['period'], '%Y-%m')
                    months_diff = (curr_date.year - prev_date.year) * 12 + (curr_date.month - prev_date.month)

                    if months_diff > 1:
                        result = {
                            "error": "non_adjacent_periods",
                            "message": f"Periods {previous['period']} and {current['period']} are not adjacent (gap of {months_diff - 1} month(s))",
                            "gap_months": months_diff - 1
                        }
                    else:
                        result = calculate_variance(
                            Decimal(str(current['amount'])),
                            Decimal(str(previous['amount']))
                        )
                        result["label"] = "Demo data"
                except ValueError:
                    result = {"error": "invalid_period_format"}

        elif tool_name == "detect_anomalies":
            bills = get_demo_bills(user_id)
            anomalies = detect_anomalies(bills)
            result = {
                "label": "Demo data",
                "anomalies": anomalies,
                "count": len(anomalies)
            }

        elif tool_name == "forecast_next_bill":
            bills = get_demo_bills(user_id)
            result = forecast_next_bill(bills)
            if "error" not in result:
                result["label"] = "Demo data"

        elif tool_name == "get_payment_status":
            demo_billing = DemoBilling()
            result = demo_billing.get_payment_status(user_id)

        elif tool_name == "get_tanker_booking_requirements":
            result = get_tanker_booking_requirements()

        elif tool_name == "prepare_tanker_draft":
            # Just validate and return the draft
            required_fields = ["address", "contact_number", "capacity"]
            missing = [f for f in required_fields if f not in args or not args[f]]
            if missing:
                result = {"error": "missing_fields", "missing": missing}
            else:
                result = {
                    "draft": args,
                    "ready": True,
                    "label": "Demo data"
                }

        elif tool_name == "submit_tanker_booking":
            # Check for duplicates (fix for D-09)
            if check_duplicate(user_id, args):
                result = {
                    "error": "duplicate_blocked",
                    "message": "An identical tanker request was already submitted",
                    "booked": False
                }
            else:
                # Guided mode - no actual booking
                result = GuidedMode.prepare_tanker(args)

        elif tool_name == "get_grievance_categories":
            result = {
                "label": "Demo data",
                "categories": get_grievance_categories(),
                "note": "Provisional categories - verify with official HMWSSB list"
            }

        elif tool_name == "prepare_grievance_draft":
            required_fields = ["category", "description", "location"]
            missing = [f for f in required_fields if f not in args or not args[f]]
            if missing:
                result = {"error": "missing_fields", "missing": missing}
            else:
                result = {
                    "draft": args,
                    "ready": True,
                    "label": "Demo data"
                }

        elif tool_name == "submit_grievance":
            # Check for duplicates (fix for D-09 - add duplicate guard for grievances)
            if check_duplicate(user_id, args):
                result = {
                    "error": "duplicate_blocked",
                    "message": "An identical grievance was already submitted",
                    "filed": False
                }
            else:
                # Guided mode - no actual submission
                result = GuidedMode.prepare_grievance(args)

        elif tool_name == "get_official_contact_information":
            result = get_official_contact_information()

        elif tool_name == "get_rebate_summary":
            bills = get_demo_bills(user_id)
            result = {
                "label": "Demo data",
                "rebates": rebate_summary(bills),
                "note": "Rebate treatment in billed amount is unverified"
            }

        else:
            result = {"error": "unknown_tool"}

    except Exception as e:
        result = {"error": str(e)}

    log_audit(tool_name, user_id, args, result)
    return result

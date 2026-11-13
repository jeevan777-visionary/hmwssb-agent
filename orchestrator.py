"""
Orchestrator module - rule-based routing and reply rendering.
Verbatim from BUILD_SPEC with fixes for D-05, D-06, D-07.
"""

from typing import Dict, Any, Optional, List
import re


# Intent patterns - ordered by specificity (fix for D-06)
# More specific patterns first to avoid misrouting
INTENTS = [
    # Tanker booking
    (r"^(i need|book|request|want)\s+(a\s+)?tanker", "tanker_booking"),
    (r"tanker\s+(request|booking)", "tanker_booking"),

    # Grievance
    (r"^(register|file|submit|report)\s+(a\s+)?(grievance|complaint)", "grievance"),
    (r"grievance\s+(register|file|submit)", "grievance"),
    (r"complaint\s+(register|file|submit)", "grievance"),
    (r"sewer\s+(overflow|block|leak)", "grievance"),
    (r"water\s+(dirty|contaminated|smell)", "grievance"),

    # Bill variance - be more specific to avoid catching "why is my water dirty"
    (r"why\s+(did|is)\s+my\s+bill\s+(increase|go up|change)", "bill_variance"),
    (r"bill\s+(increase|change|variance)", "bill_variance"),
    (r"why\s+is\s+my\s+bill\s+so\s+high", "bill_variance"),

    # Anomalies
    (r"(any|anything)\s+(unusual|strange|odd|wrong|anomaly)", "anomalies"),
    (r"anomaly\s+(in\s+)?bill", "anomalies"),

    # Forecast
    (r"(estimate|forecast|predict)\s+(next\s+)?bill", "forecast"),
    (r"next\s+bill\s+(estimate|forecast)", "forecast"),

    # Payment status
    (r"(did|do)\s+i\s+(owe|pay|have\s+to\s+pay)", "payment_status"),
    (r"payment\s+(status|due|owe)", "payment_status"),
    (r"outstanding\s+(balance|amount)", "payment_status"),

    # Rebate
    (r"what\s+is\s+the\s+rebate", "rebate"),
    (r"rebate\s+(on\s+)?my\s+bill", "rebate"),

    # Bill history
    (r"(show|get|list)\s+my\s+bill\s+history", "bill_history"),
    (r"bill\s+history", "bill_history"),
    (r"my\s+bills", "bill_history"),

    # Tanker requirements
    (r"tanker\s+(requirements|info|information|how)", "tanker_requirements"),

    # Grievance categories
    (r"grievance\s+(categories|types|list)", "grievance_categories"),

    # Contact info
    (r"(contact|helpline|phone|number)", "contact"),
    (r"official\s+(contact|info)", "contact"),

    # General help
    (r"help|what\s+can\s+you\s+do", "help"),
]


def route(text: str) -> str:
    """
    Route user text to an intent using pattern matching.
    Returns intent name or "unknown".
    """
    text_lower = text.lower().strip()

    for pattern, intent in INTENTS:
        if re.search(pattern, text_lower):
            return intent

    return "unknown"


def render(tool_name: str, result: Dict[str, Any], lang: str = "en") -> str:
    """
    Render tool result into human-readable text.
    Fix for D-05: every tool has a proper renderer (no str(dict)).
    Fix for D-07: remove Telugu placeholder suffix.
    """
    if "error" in result:
        return f"Sorry, I couldn't process that: {result['error']}"

    if tool_name == "get_bill_history":
        bills = result.get("bills", [])
        count = len(bills)
        issues = result.get("quality_issues", [])
        issue_text = ""
        if issues:
            issue_text = f" Note: {len(issues)} data quality issue(s) found."

        if count == 0:
            return "No billing history available."
        elif count == 1:
            return f"You have 1 billing record on file. (Demo data){issue_text}"
        else:
            latest = bills[-1]
            return f"You have {count} billing records. Your most recent bill (period {latest['period']}) is ₹{latest['amount']:.2f}. (Demo data){issue_text}"

    elif tool_name == "calculate_bill_variance":
        if "error" in result:
            return result.get("message", "Could not calculate variance.")
        if "non_adjacent_periods" in result:
            return result["message"]

        current = result["current"]
        previous = result["previous"]
        diff = result["difference"]
        percent = result["percent_change"]

        direction = "increased" if result["increase"] else "decreased"
        return f"Your bill {direction} from ₹{previous:.2f} to ₹{current:.2f}, a change of ₹{diff:.2f} ({percent:.2f}%). (Demo data)"

    elif tool_name == "detect_anomalies":
        anomalies = result.get("anomalies", [])
        count = len(anomalies)

        if count == 0:
            return "No anomalies detected in your billing history. (Demo data)"
        elif count == 1:
            a = anomalies[0]
            return f"One possible anomaly found: period {a['period']} billed ₹{a['amount']:.2f} vs typical ₹{a['median']:.2f}. This is marked as a possible anomaly, not confirmed. (Demo data)"
        else:
            return f"{count} possible anomalies found in your billing history. These are marked as possible anomalies, not confirmed. (Demo data)"

    elif tool_name == "forecast_next_bill":
        if "error" in result:
            return "I don't have enough normal billing data to forecast your next bill."

        forecast = result["forecast"]
        min_val = result["range"]["min"]
        max_val = result["range"]["max"]
        excluded = result.get("excluded_periods", [])

        base_msg = f"Your next bill is estimated at ₹{forecast:.2f}, with a likely range of ₹{min_val:.2f} to ₹{max_val:.2f}. (Demo data)"
        if excluded:
            base_msg += f" Excluded periods from calculation: {', '.join(excluded)}."
        base_msg += " Forecast based on recent history; actual may vary."

        return base_msg

    elif tool_name == "get_payment_status":
        return result.get("message", "Payment status information is not verified. Please check the official BillDesk portal.")

    elif tool_name == "get_tanker_booking_requirements":
        reqs = result.get("requirements", {})
        req_text = ", ".join([f"{k}: {v}" for k, v in reqs.items()])
        return f"To book a tanker, you'll need: {req_text}. {result.get('charges', {}).get('note', '')} (Demo data)"

    elif tool_name == "prepare_tanker_draft":
        return "Your tanker request draft is ready. Please confirm to proceed (guided mode: no actual booking will be made)."

    elif tool_name == "submit_tanker_booking":
        return result.get("message", "Tanker booking completed.")

    elif tool_name == "get_grievance_categories":
        cats = result.get("categories", [])
        cat_names = [c["name"] for c in cats]
        return f"Grievance categories: {', '.join(cat_names)}. {result.get('note', '')} (Demo data)"

    elif tool_name == "prepare_grievance_draft":
        return "Your grievance draft is ready. Please confirm to proceed (guided mode: no actual filing will be made)."

    elif tool_name == "submit_grievance":
        return result.get("message", "Grievance submitted.")

    elif tool_name == "get_official_contact_information":
        return f"HMWSSB Helpline: {result['helpline']}, Email: {result['email']}, Website: {result['website']}. {result.get('note', '')}"

    elif tool_name == "get_rebate_summary":
        rebates = result.get("rebates", [])
        if not rebates:
            return "No rebate information available."
        note = result.get("note", "")
        return f"Rebate information is available for {len(rebates)} periods. {note} (Demo data)"

    else:
        return "I understood your request but couldn't process it properly."


def handle(text: str, user_id: str, lang: str = "en") -> Dict[str, Any]:
    """
    Main handler: route text to intent, call tool, render result.
    """
    intent = route(text)

    # Import here to avoid circular imports
    from .tools import call_tool

    # Map intents to tools
    tool_map = {
        "bill_variance": "calculate_bill_variance",
        "anomalies": "detect_anomalies",
        "forecast": "forecast_next_bill",
        "payment_status": "get_payment_status",
        "bill_history": "get_bill_history",
        "tanker_booking": "get_tanker_booking_requirements",
        "tanker_requirements": "get_tanker_booking_requirements",
        "grievance": "get_grievance_categories",
        "grievance_categories": "get_grievance_categories",
        "contact": "get_official_contact_information",
        "rebate": "get_rebate_summary",
    }

    if intent in tool_map:
        tool_name = tool_map[intent]
        result = call_tool(tool_name, user_id, {})
        reply = render(tool_name, result, lang)
        return {
            "reply": reply,
            "intent": intent,
            "tool": tool_name,
            "result": result
        }
    elif intent == "help":
        return {
            "reply": "I can help you with: billing questions, bill history, anomalies, forecasts, tanker booking, grievance filing, and official contact information. Just ask in natural language.",
            "intent": "help"
        }
    else:
        return {
            "reply": "I'm not sure what you're asking. Try asking about your bill, tanker booking, or filing a grievance.",
            "intent": "unknown"
        }

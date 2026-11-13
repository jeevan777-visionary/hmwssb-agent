"""
Demo data module - synthetic billing records for testing.
Verbatim from BUILD_SPEC verified working modules.
Note: 12 records, missing 2025-12, spike in 2026-03.
"""

from typing import List, Dict, Any


def get_demo_bills(user_id: str) -> List[Dict[str, Any]]:
    """
    Return demo billing records for testing.
    Labelled as demo data per S-01.
    """
    return [
        {
            "period": "2025-08",
            "amount": 438.00,
            "rebate": 0.00,
            "paid": 438.00,
            "due_date": "2025-09-15",
            "units": 15.2
        },
        {
            "period": "2025-09",
            "amount": 445.00,
            "rebate": 0.00,
            "paid": 445.00,
            "due_date": "2025-10-15",
            "units": 15.8
        },
        {
            "period": "2025-10",
            "amount": 452.00,
            "rebate": 0.00,
            "paid": 452.00,
            "due_date": "2025-11-15",
            "units": 16.1
        },
        {
            "period": "2025-11",
            "amount": 458.00,
            "rebate": 0.00,
            "paid": 458.00,
            "due_date": "2025-12-15",
            "units": 16.5
        },
        # 2025-12 is missing (data quality issue)
        {
            "period": "2026-01",
            "amount": 462.00,
            "rebate": 0.00,
            "paid": 462.00,
            "due_date": "2026-02-15",
            "units": 17.0
        },
        {
            "period": "2026-02",
            "amount": 468.00,
            "rebate": 0.00,
            "paid": 468.00,
            "due_date": "2026-03-15",
            "units": 17.4
        },
        {
            "period": "2026-03",
            "amount": 910.00,  # Anomaly spike
            "rebate": 0.00,
            "paid": 910.00,
            "due_date": "2026-04-15",
            "units": 35.2
        },
        {
            "period": "2026-04",
            "amount": 475.00,
            "rebate": 0.00,
            "paid": 475.00,
            "due_date": "2026-05-15",
            "units": 17.8
        },
        {
            "period": "2026-05",
            "amount": 482.00,
            "rebate": 0.00,
            "paid": 482.00,
            "due_date": "2026-06-15",
            "units": 18.2
        },
        {
            "period": "2026-06",
            "amount": 488.00,
            "rebate": 0.00,
            "paid": 488.00,
            "due_date": "2026-07-15",
            "units": 18.6
        },
        {
            "period": "2026-07",
            "amount": 495.00,
            "rebate": 0.00,
            "paid": 495.00,
            "due_date": "2026-08-15",
            "units": 19.0
        },
        {
            "period": "2026-08",
            "amount": 502.00,
            "rebate": 0.00,
            "paid": 502.00,
            "due_date": "2026-09-15",
            "units": 19.4
        }
    ]


def get_demo_user_id(mobile: str) -> str:
    """
    Return demo user ID. In demo mode, all users map to the same demo user.
    In production, this would return a unique user ID per mobile number.
    """
    return "demo-user"


def get_tanker_booking_requirements() -> Dict[str, Any]:
    """Return tanker booking requirements for demo."""
    return {
        "label": "Demo data",
        "requirements": {
            "address": "Required - full address with landmark",
            "contact_number": "Required - 10-digit mobile",
            "capacity": "Required - 5000L, 10000L, or 15000L",
            "purpose": "Optional - domestic, commercial, construction"
        },
        "charges": {
            "note": "Official charges not verified - use official portal",
            "basis": "unknown"
        },
        "mode": "guided"
    }


def get_grievance_categories() -> List[Dict[str, Any]]:
    """
    Return grievance categories.
    Note: These are provisional and unverified (U-13).
    """
    return [
        {
            "id": "water_supply",
            "name": "Water Supply Issue",
            "description": "No water, low pressure, irregular supply",
            "note": "Provisional category - verify with official HMWSSB list"
        },
        {
            "id": "billing",
            "name": "Billing Issue",
            "description": "Incorrect bill, payment not reflected",
            "note": "Provisional category - verify with official HMWSSB list"
        },
        {
            "id": "sewerage",
            "name": "Sewerage Issue",
            "description": "Blockage, overflow, damage",
            "note": "Provisional category - verify with official HMWSSB list"
        },
        {
            "id": "quality",
            "name": "Water Quality",
            "description": "Dirty water, smell, contamination",
            "note": "Provisional category - verify with official HMWSSB list"
        },
        {
            "id": "connection",
            "name": "Connection Issue",
            "description": "New connection, disconnection, transfer",
            "note": "Provisional category - verify with official HMWSSB list"
        },
        {
            "id": "other",
            "name": "Other",
            "description": "Any other issue not listed above",
            "note": "Provisional category - verify with official HMWSSB list"
        }
    ]


def get_official_contact_information() -> Dict[str, Any]:
    """Return official HMWSSB contact information."""
    return {
        "label": "Demo data",
        "helpline": "155399",
        "email": "infocell@hmwssb.gov.in",
        "website": "https://www.hmwssb.gov.in",
        "office_address": "HMWSSB, Khairatabad, Hyderabad - 500004",
        "note": "Verify current contact details from official source"
    }

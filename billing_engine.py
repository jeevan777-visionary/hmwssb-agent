"""
Billing engine - deterministic Decimal math for water billing calculations.
Verbatim from BUILD_SPEC verified working modules.
"""

from decimal import Decimal, getcontext
from typing import List, Dict, Any, Optional
from datetime import datetime
import math

getcontext().prec = 28


def money(value: Any) -> Decimal:
    """Convert input to Decimal with 2 decimal places (INR). Raises on invalid input."""
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, (int, float)):
        result = Decimal(str(value))
    elif isinstance(value, str):
        result = Decimal(value.strip())
    else:
        raise TypeError(f"Cannot convert {type(value)} to money")

    # Quantize to 2 decimal places (cents/paise)
    return result.quantize(Decimal('0.01'))


def calculate_variance(current: Decimal, previous: Decimal) -> Dict[str, Any]:
    """Calculate variance between two billing periods."""
    if previous == 0:
        raise ValueError("Previous amount cannot be zero for variance calculation")

    diff = current - previous
    percent = (diff / previous) * Decimal('100')
    percent = percent.quantize(Decimal('0.01'))

    return {
        "current": float(current),
        "previous": float(previous),
        "difference": float(diff),
        "percent_change": float(percent),
        "increase": diff > 0
    }


def detect_anomalies(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect billing anomalies using median and MAD (Median Absolute Deviation).
    Returns list of records flagged as anomalies.
    """
    if len(records) < 3:
        return []

    amounts = [Decimal(str(r['amount'])) for r in records]
    n = len(amounts)

    # Calculate median
    sorted_amounts = sorted(amounts)
    if n % 2 == 0:
        median = (sorted_amounts[n//2 - 1] + sorted_amounts[n//2]) / Decimal('2')
    else:
        median = sorted_amounts[n//2]

    # Calculate MAD (Median Absolute Deviation)
    deviations = [abs(a - median) for a in amounts]
    sorted_deviations = sorted(deviations)
    if n % 2 == 0:
        mad = (sorted_deviations[n//2 - 1] + sorted_deviations[n//2]) / Decimal('2')
    else:
        mad = sorted_deviations[n//2]

    # Z-score using MAD (conservative threshold: 3.5)
    # MAD to SD conversion factor ≈ 1.4826
    if mad == 0:
        return []

    threshold = 3.5
    anomalies = []

    for record in records:
        amount = Decimal(str(record['amount']))
        z_score = (abs(amount - median) / mad) * Decimal('1.4826')
        if z_score > threshold:
            anomalies.append({
                "period": record['period'],
                "amount": float(amount),
                "median": float(median),
                "z_score": float(z_score),
                "note": "possible anomaly, not confirmed"
            })

    return anomalies


def forecast_next_bill(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Forecast next bill using simple moving average.
    Excludes anomalies from calculation.
    """
    if len(records) < 2:
        return {"error": "insufficient_data"}

    # Detect and exclude anomalies
    anomalies = detect_anomalies(records)
    anomaly_periods = {a['period'] for a in anomalies}

    # Use last 3 non-anomalous records
    normal_records = [r for r in records if r['period'] not in anomaly_periods]
    if len(normal_records) < 2:
        return {"error": "insufficient_normal_data"}

    recent = normal_records[-3:]
    amounts = [Decimal(str(r['amount'])) for r in recent]
    avg = sum(amounts) / Decimal(len(amounts))

    # Simple range estimate (±10%)
    lower = avg * Decimal('0.9')
    upper = avg * Decimal('1.1')

    return {
        "forecast": float(avg.quantize(Decimal('0.01'))),
        "range": {
            "min": float(lower.quantize(Decimal('0.01'))),
            "max": float(upper.quantize(Decimal('0.01')))
        },
        "caveat": "Forecast based on recent history; actual may vary",
        "excluded_periods": list(anomaly_periods)
    }


def rebate_summary(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate rebate summary from billing records.
    Returns per-period rebate data without net amounts (basis unknown).
    """
    summary = []
    for record in records:
        rebate = Decimal(str(record.get('rebate', 0)))
        billed = Decimal(str(record['amount']))
        paid = Decimal(str(record.get('paid', 0)))

        summary.append({
            "period": record['period'],
            "billed": float(billed),
            "rebate": float(rebate),
            "paid": float(paid),
            "basis": "unknown"  # Do not assert net treatment without verification
        })

    return summary

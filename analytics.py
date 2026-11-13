"""
Analytics module - data quality checks and billing analysis.
Verbatim from BUILD_SPEC verified working modules.
"""

from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal


def check_data_quality(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check for data quality issues in billing records.
    Returns list of issues found.
    """
    issues = []

    if not records:
        return {"issues": [], "quality": "no_data"}

    # Check for missing months
    periods = [r['period'] for r in records]
    periods.sort()

    for i in range(len(periods) - 1):
        # Parse period format YYYY-MM
        try:
            current = datetime.strptime(periods[i], '%Y-%m')
            next_p = datetime.strptime(periods[i + 1], '%Y-%m')

            # Calculate month difference
            months = (next_p.year - current.year) * 12 + (next_p.month - current.month)
            if months > 1:
                issues.append({
                    "type": "missing_month",
                    "between": f"{periods[i]} and {periods[i+1]}",
                    "gap_months": months - 1
                })
        except ValueError:
            issues.append({
                "type": "invalid_period_format",
                "period": periods[i]
            })

    # Check for zero or negative amounts
    for record in records:
        amount = Decimal(str(record.get('amount', 0)))
        if amount <= 0:
            issues.append({
                "type": "invalid_amount",
                "period": record['period'],
                "amount": float(amount)
            })

    # Check for duplicate periods
    seen = set()
    for record in records:
        if record['period'] in seen:
            issues.append({
                "type": "duplicate_period",
                "period": record['period']
            })
        seen.add(record['period'])

    return {
        "issues": issues,
        "quality": "good" if not issues else "issues_found",
        "total_records": len(records)
    }


def summarize_billing(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for billing records."""
    if not records:
        return {"error": "no_data"}

    amounts = [Decimal(str(r['amount'])) for r in records]
    total = sum(amounts)
    avg = total / Decimal(len(amounts))

    sorted_amounts = sorted(amounts)
    n = len(amounts)
    if n % 2 == 0:
        median = (sorted_amounts[n//2 - 1] + sorted_amounts[n//2]) / Decimal('2')
    else:
        median = sorted_amounts[n//2]

    return {
        "total_billed": float(total),
        "average": float(avg.quantize(Decimal('0.01'))),
        "median": float(median.quantize(Decimal('0.01'))),
        "min": float(min(amounts)),
        "max": float(max(amounts)),
        "period_count": len(records)
    }

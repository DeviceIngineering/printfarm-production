"""
Core utilities for PrintFarm production system.
"""
from decimal import Decimal, InvalidOperation
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """
    Safely convert value to Decimal.
    """
    try:
        if value is None or value == '':
            return default
        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        logger.warning(f"Failed to convert {value} to Decimal, using default {default}")
        return default

def format_decimal(value: Decimal, places: int = 2) -> str:
    """
    Format decimal for display.
    """
    if value is None:
        return "0.00"
    return f"{value:.{places}f}"

def calculate_percentage(value: Decimal, total: Decimal) -> Decimal:
    """
    Calculate percentage with safe division.
    """
    if total == 0:
        return Decimal('0')
    return (value / total) * Decimal('100')
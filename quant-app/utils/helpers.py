"""Utility helper functions"""
import pandas as pd
import numpy as np
from typing import Tuple

def calculate_returns(prices: pd.Series) -> pd.Series:
    """Calculate log returns"""
    return np.log(prices / prices.shift(1))

def format_number(value: float, decimals: int = 2) -> str:
    """Format number with thousand separators"""
    return f"{value:,.{decimals}f}"

def validate_symbol_pair(symbol1: str, symbol2: str, available: list) -> Tuple[bool, str]:
    """Validate if symbol pair is available"""
    if symbol1 not in available:
        return False, f"{symbol1} not available"
    if symbol2 not in available:
        return False, f"{symbol2} not available"
    if symbol1 == symbol2:
        return False, "Symbols must be different"
    return True, "OK"

def safe_divide(numerator, denominator, default=0):
    """Safe division returning default on zero denominator"""
    return numerator / denominator if denominator != 0 else default
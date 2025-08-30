import pandas as pd
import numpy as np

# --------------------------------------------------------------------
# --- INDICATOR 1: Relative Strength Index (RSI) ---
# --------------------------------------------------------------------
def calculate_rsi(df, period=14):
    """
    Calculates the Relative Strength Index (RSI).
    
    Args:
        df (DataFrame): DataFrame with 'Close' column
        period (int): RSI period (default: 14)
    
    Returns:
        DataFrame: Original DataFrame with 'RSI' column added
    """
    df = df.copy()
    if 'Close' not in df.columns:
        raise KeyError("DataFrame must contain a 'Close' column.")

    # Calculate price changes
    delta = df['Close'].diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate smoothed average gains and losses using EMA
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()

    # Calculate Relative Strength (RS)
    rs = avg_gain / avg_loss

    # Calculate the RSI
    rsi = 100 - (100 / (1 + rs))
    df['RSI'] = rsi
    
    return df


# --------------------------------------------------------------------
# --- INDICATOR 2: Moving Average Convergence Divergence (MACD) ---
# --------------------------------------------------------------------
def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculates the Moving Average Convergence Divergence (MACD).
    
    Args:
        df (DataFrame): DataFrame with 'Close' column
        fast_period (int): Fast EMA period (default: 12)
        slow_period (int): Slow EMA period (default: 26)
        signal_period (int): Signal line period (default: 9)
    
    Returns:
        DataFrame: Original DataFrame with MACD columns added
    """
    df = df.copy()
    if 'Close' not in df.columns:
        raise KeyError("DataFrame must contain a 'Close' column.")

    # Calculate Fast and Slow EMAs
    fast_ema = df['Close'].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df['Close'].ewm(span=slow_period, adjust=False).mean()

    # Calculate the MACD Line
    df['MACD'] = fast_ema - slow_ema

    # Calculate the Signal Line (EMA of the MACD Line)
    df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()

    # Calculate the MACD Histogram
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    return df


# Note: Only RSI and MACD indicators are included as provided by the user
# Additional indicators can be added later when needed


# --------------------------------------------------------------------
# --- INDICATOR DICTIONARY FOR MODULAR SYSTEM ---
# --------------------------------------------------------------------
INDICATORS = {
    'rsi': {
        'name': 'RSI',
        'function': calculate_rsi,
        'parameters': {
            'period': {'type': 'number', 'default': 14, 'min': 1, 'max': 100, 'label': 'Period'}
        },
        'columns': ['RSI'],
        'description': 'Relative Strength Index - Momentum oscillator'
    },
    'macd': {
        'name': 'MACD',
        'function': calculate_macd,
        'parameters': {
            'fast_period': {'type': 'number', 'default': 12, 'min': 1, 'max': 50, 'label': 'Fast Period'},
            'slow_period': {'type': 'number', 'default': 26, 'min': 1, 'max': 100, 'label': 'Slow Period'},
            'signal_period': {'type': 'number', 'default': 9, 'min': 1, 'max': 50, 'label': 'Signal Period'}
        },
        'columns': ['MACD', 'MACD_Signal', 'MACD_Histogram'],
        'description': 'Moving Average Convergence Divergence - Trend indicator'
    }
}

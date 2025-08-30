import pandas as pd
import numpy as np
import yfinance as yf

def calculate_ema_crossover(df, short_period=12, long_period=26, ma_type='ema', strategy_type='long_only'):
    """
    Calculate EMA or SMA Crossover strategy signals with corrected logic.
    
    Args:
        df: DataFrame with OHLC data
        short_period: Short-term moving average period
        long_period: Long-term moving average period
        ma_type: 'ema' or 'sma' for moving average type
        
    Returns:
        DataFrame with crossover signals added
    """
    df = df.copy()
    
    # Validate required columns
    if 'Close' not in df.columns:
        raise KeyError("DataFrame must contain a 'Close' column.")
    
    # Calculate moving averages based on type
    if ma_type.lower() == 'ema':
        df['Short_MA'] = df['Close'].ewm(span=short_period, adjust=False).mean()
        df['Long_MA'] = df['Close'].ewm(span=long_period, adjust=False).mean()
    elif ma_type.lower() == 'sma':
        df['Short_MA'] = df['Close'].rolling(window=short_period).mean()
        df['Long_MA'] = df['Close'].rolling(window=long_period).mean()
    else:
        raise ValueError("ma_type must be 'ema' or 'sma'")
    
    # Position: True if short MA > long MA
    df['Position'] = df['Short_MA'] > df['Long_MA']
    
    # Generate signals with corrected logic
    df['signal'] = 0  # Default: no signal
    
    # Buy signal: Position changes from False to True (short MA crosses above long MA)
    buy_signals = (df['Position'] & ~df['Position'].shift(1).fillna(False)).fillna(False)
    df.loc[buy_signals, 'signal'] = 1
    
    # Sell signal: Position changes from True to False (short MA crosses below long MA)
    sell_signals = (~df['Position'] & df['Position'].shift(1).fillna(False)).fillna(False)
    df.loc[sell_signals, 'signal'] = -1
    
    # Calculate positions based on signals and strategy type
    df['position'] = 0
    position = 0
    for i in range(len(df)):
        if df['signal'].iloc[i] == 1:  # Buy signal
            position = 1
        elif df['signal'].iloc[i] == -1:  # Sell signal
            if strategy_type == 'long_short':
                position = -1  # Go short for long-short strategy
            else:
                position = 0  # Exit to cash for long-only strategy
        df.iloc[i, df.columns.get_loc('position')] = position
    
    return df

def calculate_detailed_trades(df, strategy_type='long_only'):
    """
    Calculate detailed trade information for EMA/SMA crossover strategy.
    
    Args:
        df: DataFrame with signals and positions
        strategy_type: 'long_only' or 'long_short'
        
    Returns:
        List of trade dictionaries with detailed information
    """
    trades = []
    current_position = 0
    entry_price = None
    entry_date = None
    
    for idx, row in df.iterrows():
        signal = row['signal']
        price = row['Close']
        date = idx.date()
        
        if signal == 1:  # Buy signal
            # If we have an existing position, close it first
            if current_position == 1 and entry_price is not None:
                pnl = price - entry_price
                trades.append({
                    'entry_date': str(entry_date),
                    'exit_date': str(date),
                    'entry_price': entry_price,
                    'exit_price': price,
                    'action': 'BUY',
                    'pnl': pnl
                })
            
            # Start new long position
            current_position = 1
            entry_price = price
            entry_date = date
            
        elif signal == -1:  # Sell signal
            if strategy_type == 'long_short':
                # For long-short, sell signal means go short
                if current_position != 0 and entry_price is not None:
                    # Close existing position
                    if current_position == 1:  # Long position
                        pnl = price - entry_price
                        action = 'BUY'
                    else:  # Short position
                        pnl = entry_price - price
                        action = 'SELL'
                    
                    trades.append({
                        'entry_date': str(entry_date),
                        'exit_date': str(date),
                        'entry_price': entry_price,
                        'exit_price': price,
                        'action': action,
                        'pnl': pnl
                    })
                
                # Start new short position
                current_position = -1
                entry_price = price
                entry_date = date
            else:
                # For long-only, sell signal means exit position
                if current_position == 1 and entry_price is not None:
                    pnl = price - entry_price
                    trades.append({
                        'entry_date': str(entry_date),
                        'exit_date': str(date),
                        'entry_price': entry_price,
                        'exit_price': price,
                        'action': 'BUY',
                        'pnl': pnl
                    })
                    current_position = 0
                    entry_price = None
                    entry_date = None
    
    # Handle any open position at the end
    if current_position != 0 and entry_price is not None:
        final_price = df['Close'].iloc[-1]
        final_date = df.index[-1].date()
        
        if current_position == 1:  # Long position
            pnl = final_price - entry_price
            action = 'BUY'
        else:  # Short position
            pnl = entry_price - final_price
            action = 'SELL'
        
        trades.append({
            'entry_date': str(entry_date),
            'exit_date': str(final_date),
            'entry_price': entry_price,
            'exit_price': final_price,
            'action': action,
            'pnl': pnl
        })
    
    return trades

def fetch_stock_data(symbol, start_date, end_date, interval='1d'):
    """
    Fetch stock data from yfinance.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', '^NSEI')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
        
    Returns:
        DataFrame with OHLCV data
    """
    try:
        data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
        
        if data.empty:
            raise ValueError(f"No data found for {symbol} with interval {interval}")
        
        # Fix multi-level columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        return data
    except Exception as e:
        raise ValueError(f"Error fetching data for {symbol} with interval {interval}: {str(e)}")

def run_ema_crossover_backtest(symbol, start_date, end_date, short_period=12, long_period=26, 
                               ma_type='ema', initial_capital=100000, strategy_type='long_only', interval='1d'):
    """
    Run a complete EMA/SMA Crossover backtest.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        short_period: Short period for moving average
        long_period: Long period for moving average
        ma_type: Type of moving average ('ema' or 'sma')
        initial_capital: Initial capital
        strategy_type: 'long_only' or 'long_short'
        interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
        
    Returns:
        Dictionary with backtest results
    """
    # Fetch data
    df = fetch_stock_data(symbol, start_date, end_date, interval)
    
    # Calculate EMA/SMA Crossover (includes signal generation)
    df = calculate_ema_crossover(df, short_period, long_period, ma_type, strategy_type)
    
    # Calculate performance metrics
    results = calculate_performance_metrics(df, initial_capital, strategy_type)
    
    return {
        'data': df,
        'summary': results,
        'strategy_name': f'{ma_type.upper()} Crossover Strategy',
        'parameters': {
            'short_period': short_period,
            'long_period': long_period,
            'ma_type': ma_type,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'interval': interval
        }
    }

def calculate_performance_metrics(df, initial_capital, strategy_type='long_only'):
    """
    Calculate performance metrics from backtest results.
    
    Args:
        df: DataFrame with signals and positions
        initial_capital: Initial capital
        strategy_type: 'long_only' or 'long_short'
        
    Returns:
        Dictionary with performance metrics
    """
    # Calculate equity curve
    df['returns'] = df['Close'].pct_change()
    df['strategy_returns'] = df['position'].shift(1) * df['returns']
    df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
    df['equity_curve'] = initial_capital * df['cumulative_returns']
    
    # Calculate metrics
    total_return = df['cumulative_returns'].iloc[-1] - 1
    total_return_pct = total_return * 100
    
    # Buy and hold return
    buy_hold_return = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
    buy_hold_return_pct = buy_hold_return * 100
    
    # Calculate detailed trades with P&L
    trades = calculate_detailed_trades(df, strategy_type)
    
    # Number of trades
    total_trades = len(trades)
    buy_trades = len([t for t in trades if t['action'] == 'BUY'])
    sell_trades = len([t for t in trades if t['action'] == 'SELL'])
    
    # For long-short strategies, we need to count differently
    if strategy_type == 'long_short':
        # Count actual buy and sell signals from the data
        buy_signals = int((df['signal'] == 1).sum())
        sell_signals = int((df['signal'] == -1).sum())
        # For long-short, we count signals as trades
        total_trades = buy_signals + sell_signals
        buy_trades = buy_signals
        sell_trades = sell_signals
        
        # For long-short, we need to calculate actual position changes with P&L
        # Use the original calculate_detailed_trades function but modify for long-short
        trades = []
        current_position = 0
        entry_price = None
        entry_date = None
        
        for idx, row in df.iterrows():
            signal = row['signal']
            price = row['Close']
            date = idx.date()
            
            if signal == 1:  # Buy signal
                # If we have an existing short position, close it first
                if current_position == -1 and entry_price is not None:
                    pnl = entry_price - price  # Profit from short position
                    trades.append({
                        'entry_date': str(entry_date),
                        'exit_date': str(date),
                        'entry_price': entry_price,
                        'exit_price': price,
                        'action': 'SELL',
                        'pnl': pnl
                    })
                
                # Start new long position
                current_position = 1
                entry_price = price
                entry_date = date
                
            elif signal == -1:  # Sell signal
                # If we have an existing long position, close it first
                if current_position == 1 and entry_price is not None:
                    pnl = price - entry_price  # Profit from long position
                    trades.append({
                        'entry_date': str(entry_date),
                        'exit_date': str(date),
                        'entry_price': entry_price,
                        'exit_price': price,
                        'action': 'BUY',
                        'pnl': pnl
                    })
                
                # Start new short position
                current_position = -1
                entry_price = price
                entry_date = date
        
        # Handle any open position at the end
        if current_position != 0 and entry_price is not None:
            final_price = df['Close'].iloc[-1]
            final_date = df.index[-1].date()
            
            if current_position == 1:  # Long position
                pnl = final_price - entry_price
                action = 'BUY'
            else:  # Short position
                pnl = entry_price - final_price
                action = 'SELL'
            
            trades.append({
                'entry_date': str(entry_date),
                'exit_date': str(final_date),
                'entry_price': entry_price,
                'exit_price': final_price,
                'action': action,
                'pnl': pnl
            })
    
    # Calculate actual win rate from P&L
    if total_trades > 0:
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = (winning_trades / total_trades) * 100
    else:
        win_rate = 0.0
    
    # Maximum drawdown
    df['peak'] = df['equity_curve'].expanding().max()
    df['drawdown'] = (df['equity_curve'] - df['peak']) / df['peak']
    max_drawdown = df['drawdown'].min() * 100
    
    # Sharpe ratio (simplified)
    if df['strategy_returns'].std() > 0:
        sharpe_ratio = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252)
    else:
        sharpe_ratio = 0.0
    
    # Handle NaN values and convert numpy types to Python native types
    def clean_nan(value):
        if pd.isna(value) or np.isnan(value):
            return None
        # Convert numpy types to Python native types
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        elif isinstance(value, (int, float)):
            return value
        else:
            return value
    
    return {
        'initial_capital': initial_capital,
        'final_value': clean_nan(df['equity_curve'].iloc[-1]),
        'total_return': clean_nan(total_return),
        'total_return_pct': clean_nan(total_return_pct),
        'buy_hold_return': clean_nan(buy_hold_return),
        'buy_hold_return_pct': clean_nan(buy_hold_return_pct),
        'total_trades': total_trades,
        'buy_trades': buy_trades,
        'sell_trades': sell_trades,
        'win_rate': clean_nan(win_rate),
        'max_drawdown': clean_nan(max_drawdown),
        'sharpe_ratio': clean_nan(sharpe_ratio),
        'equity_curve': [{'equity_curve': clean_nan(val), 'date': str(idx.date())} for idx, val in zip(df.index, df['equity_curve'].values)],
        'trades': trades
    }

import pandas as pd
import numpy as np
import yfinance as yf
from supertrend import run_supertrend_backtest, calculate_supertrend, generate_signals as generate_supertrend_signals
from ema_crossover import run_ema_crossover_backtest, calculate_ema_crossover

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

def combine_strategies(df, strategy_results, strategy_type='long_only'):
    """
    Combine multiple strategies using cumulative signal logic.
    
    Args:
        df: Base DataFrame with OHLC data
        strategy_results: List of DataFrames with strategy signals
        strategy_type: 'long_only' or 'long_short'
        
    Returns:
        DataFrame with combined signals and positions
    """
    combined_df = df.copy()
    combined_df['combined_signal'] = 0
    
    # If only one strategy, use its signals directly
    if len(strategy_results) == 1:
        combined_df['combined_signal'] = strategy_results[0]['signal']
    else:
        # Calculate combined signal using CUMULATIVE approach with STATE TRANSITIONS
        # Track the position of each strategy over time (1=long, -1=short, 0=cash)
        signal_columns = []
        
        # Get signals from each strategy
        for i, strategy_df in enumerate(strategy_results):
            signal_col = f'signal_{i}'
            combined_df[signal_col] = strategy_df['signal']
            signal_columns.append(signal_col)
        
        # Initialize strategy positions
        strategy_positions = [0] * len(strategy_results)  # Start with no positions
        previous_combined_state = 'mixed'  # Track previous combined state
        
        # Process each day to determine combined signal
        for i in range(len(combined_df)):
            # Update strategy positions based on current signals
            for j, signal_col in enumerate(signal_columns):
                signal = combined_df[signal_col].iloc[i]
                if signal == 1:  # Buy signal
                    strategy_positions[j] = 1  # Go long
                elif signal == -1:  # Sell signal
                    if strategy_type == 'long_short':
                        strategy_positions[j] = -1  # Go short for long-short
                    else:
                        strategy_positions[j] = 0  # Exit to cash for long-only
            
            # Determine current combined state
            if strategy_type == 'long_short':
                if all(pos == 1 for pos in strategy_positions):
                    current_combined_state = 'all_long'
                elif all(pos == -1 for pos in strategy_positions):
                    current_combined_state = 'all_short'
                else:
                    current_combined_state = 'mixed'
            else:
                if all(pos == 1 for pos in strategy_positions):
                    current_combined_state = 'all_long'
                elif all(pos == 0 for pos in strategy_positions):
                    current_combined_state = 'all_cash'
                else:
                    current_combined_state = 'mixed'
            
            # Generate combined signal only on state transitions
            if current_combined_state == 'all_long' and previous_combined_state != 'all_long':
                # Transition to all long = BUY signal
                combined_df.iloc[i, combined_df.columns.get_loc('combined_signal')] = 1
            elif current_combined_state != 'all_long' and previous_combined_state == 'all_long':
                # Transition away from all long = SELL signal
                combined_df.iloc[i, combined_df.columns.get_loc('combined_signal')] = -1
            else:
                # No state transition = no signal
                combined_df.iloc[i, combined_df.columns.get_loc('combined_signal')] = 0
            
            # Update previous state for next iteration
            previous_combined_state = current_combined_state
    
    # Calculate positions based on combined signals
    combined_df['position'] = 0
    position = 0
    for i in range(len(combined_df)):
        if combined_df['combined_signal'].iloc[i] == 1:  # Buy signal
            position = 1
        elif combined_df['combined_signal'].iloc[i] == -1:  # Sell signal
            if strategy_type == 'long_short':
                position = -1  # Go short for long-short strategy
            else:
                position = 0  # Exit to cash for long-only strategy
        combined_df.iloc[i, combined_df.columns.get_loc('position')] = position
    
    return combined_df

def run_multi_strategy_backtest(symbol, start_date, end_date, strategies, initial_capital=100000, strategy_type='long_only', interval='1d'):
    """
    Run a multi-strategy backtest combining multiple strategies.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        strategies: List of strategy configurations
        initial_capital: Initial capital
        strategy_type: 'long_only' or 'long_short'
        interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
        
    Returns:
        Dictionary with backtest results
    """
    # Fetch data once for all strategies
    df = fetch_stock_data(symbol, start_date, end_date, interval)
    
    # Run individual strategies
    strategy_results = []
    for strategy_config in strategies:
        strategy_name = strategy_config.get('name') or strategy_config.get('strategy')
        
        if strategy_name == 'supertrend':
            period = strategy_config.get('period', 10)
            multiplier = strategy_config.get('multiplier', 3.0)
            
            # Calculate Supertrend
            strategy_df = calculate_supertrend(df.copy(), period, multiplier)
            strategy_df = generate_supertrend_signals(strategy_df, strategy_type)
            strategy_results.append(strategy_df)
            
        elif strategy_name == 'ema_crossover':
            short_period = strategy_config.get('shortPeriod', 12)
            long_period = strategy_config.get('longPeriod', 26)
            ma_type = strategy_config.get('maType', 'ema')
            
            # Calculate EMA/SMA Crossover (includes signal generation)
            strategy_df = calculate_ema_crossover(df.copy(), short_period, long_period, ma_type, strategy_type)
            strategy_results.append(strategy_df)
    
    # Combine strategies using cumulative signal logic
    combined_df = combine_strategies(df, strategy_results, strategy_type)
    
    # Calculate performance metrics
    results = calculate_multi_strategy_performance_metrics(combined_df, initial_capital, strategy_type)
    
    return {
        'data': combined_df,
        'summary': results,
        'strategy_name': 'Multi-Strategy Backtest',
        'parameters': {
            'strategies': strategies,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'interval': interval
        }
    }

def calculate_multi_strategy_performance_metrics(df, initial_capital, strategy_type='long_only', individual_results=None):
    """
    Calculate performance metrics for multi-strategy backtest.
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
    trades = calculate_multi_strategy_trades(df, strategy_type)
    
    # Number of trades - different logic for different strategy types
    if strategy_type == 'long_short':
        # For long-short: count all signals as trades
        signal_counts = df['combined_signal'].value_counts()
        total_trades = int(signal_counts.get(1, 0) + signal_counts.get(-1, 0))
        buy_trades = int(signal_counts.get(1, 0))
        sell_trades = int(signal_counts.get(-1, 0))
    else:
        # For long-only: count completed trades (buy-sell pairs)
        total_trades = len(trades)
        buy_trades = len([t for t in trades if t['action'] == 'BUY'])
        sell_trades = len([t for t in trades if t['action'] == 'SELL'])
    
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

def calculate_multi_strategy_trades(df, strategy_type='long_only'):
    """
    Calculate detailed trade information for multi-strategy backtest.
    """
    trades = []
    current_position = 0
    entry_price = None
    entry_date = None
    
    for idx, row in df.iterrows():
        signal = row['combined_signal']
        price = row['Close']
        date = idx.date()
        
        if signal == 1:  # Buy signal
            # If we have an existing position, close it first
            if current_position != 0 and entry_price is not None:
                if current_position == 1:  # Long position
                    pnl = price - entry_price
                    action = 'BUY'
                else:  # Short position
                    pnl = entry_price - price
                    action = 'SELL'
                
                trades.append({
                    'entry_date': str(entry_date),
                    'exit_date': str(date),
                    'entry_price': float(entry_price),
                    'exit_price': float(price),
                    'action': action,
                    'pnl': float(pnl)
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
                        'entry_price': float(entry_price),
                        'exit_price': float(price),
                        'action': action,
                        'pnl': float(pnl)
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
                        'entry_price': float(entry_price),
                        'exit_price': float(price),
                        'action': 'BUY',
                        'pnl': float(pnl)
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
            'entry_price': float(entry_price),
            'exit_price': float(final_price),
            'action': action,
            'pnl': float(pnl)
        })
    
    return trades

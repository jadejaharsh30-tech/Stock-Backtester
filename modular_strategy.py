import pandas as pd
import numpy as np
import yfinance as yf
from indicators import INDICATORS
import warnings
warnings.filterwarnings('ignore')

class ModularStrategyBuilder:
    """
    Modular Strategy Builder for creating custom trading strategies
    using combinations of technical indicators.
    """
    
    def __init__(self):
        self.indicators = INDICATORS
        self.data = None
        self.signals = None
    
    def fetch_data(self, symbol, start_date, end_date, interval='1d'):
        """
        Fetch OHLCV data from Yahoo Finance.
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                raise ValueError(f"No data found for {symbol}")
            
            # Reset index to make date a column
            data = data.reset_index()
            data['Date'] = pd.to_datetime(data['Date'])
            
            # Ensure required columns exist
            required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in data.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            self.data = data
            return data
            
        except Exception as e:
            raise Exception(f"Error fetching data for {symbol}: {str(e)}")
    
    def apply_indicators(self, df, indicator_configs):
        """
        Apply multiple indicators to the data.
        
        Args:
            indicator_configs (list): List of indicator configurations
                [{'name': 'rsi', 'params': {'period': 14}}, ...]
        """
        if df is None or df.empty:
            raise ValueError("No data loaded. Call fetch_data() first.")
        
        for config in indicator_configs:
            indicator_name = config['name']
            # Handle both 'params' and 'parameters' keys
            params = config.get('parameters', config.get('params', {}))
            
            if indicator_name not in self.indicators:
                raise ValueError(f"Unknown indicator: {indicator_name}")
            
            # Get indicator function and apply it
            indicator_func = self.indicators[indicator_name]['function']
            df = indicator_func(df, **params)
        
        return df
    
    def evaluate_condition(self, condition, row):
        """
        Evaluate a single condition against a data row.
        
        Args:
            condition (dict): Condition configuration
                {
                    'indicator': 'rsi',
                    'column': 'RSI',
                    'operator': '>',
                    'value': 70
                }
            row (Series): Data row to evaluate
        
        Returns:
            bool: True if condition is met
        """
        try:
            column = condition['column']
            operator = condition['operator']
            value = condition['value']
            
            if column not in row.index:
                return False
            
            indicator_value = row[column]
            
            if pd.isna(indicator_value):
                return False
            
            # Handle dynamic column comparisons (e.g., comparing Close with BB_Lower)
            if isinstance(value, str) and value in row.index:
                compare_value = row[value]
                if pd.isna(compare_value):
                    return False
            else:
                compare_value = value
            
            if operator == '>':
                return indicator_value > compare_value
            elif operator == '<':
                return indicator_value < compare_value
            elif operator == '>=':
                return indicator_value >= compare_value
            elif operator == '<=':
                return indicator_value <= compare_value
            elif operator == '==':
                return indicator_value == compare_value
            elif operator == '!=':
                return indicator_value != compare_value
            else:
                return False
                
        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False
    
    def evaluate_rule(self, rule, row):
        """
        Evaluate a rule (combination of conditions) against a data row.
        
        Args:
            rule (dict): Rule configuration
                {
                    'conditions': [condition1, condition2, ...],
                    'logic': 'AND' or 'OR'
                }
            row (Series): Data row to evaluate
        
        Returns:
            bool: True if rule is met
        """
        if not rule.get('conditions'):
            return False
        
        logic = rule.get('logic', 'AND')
        condition_results = []
        
        for condition in rule['conditions']:
            result = self.evaluate_condition(condition, row)
            condition_results.append(result)
        
        if logic == 'AND':
            return all(condition_results)
        elif logic == 'OR':
            return any(condition_results)
        else:
            return False
    
    def generate_signals(self, df, strategy_config, strategy_type):
        """
        Generate buy/sell signals based on strategy configuration.
        
        Args:
            strategy_config (dict): Strategy configuration
                {
                    'buyRules' or 'buy_rules': [rule1, rule2, ...],
                    'sellRules' or 'sell_rules': [rule1, rule2, ...],
                    'buyRuleLogic' or 'buy_logic': ['AND', 'OR', ...],
                    'sellRuleLogic' or 'sell_logic': ['AND', 'OR', ...]
                }
        
        Returns:
            DataFrame: Data with signals added
        """
        if df is None or df.empty:
            raise ValueError("No data loaded. Call fetch_data() first.")
        
        df['Buy_Signal'] = False
        df['Sell_Signal'] = False
        
        # Handle both camelCase and snake_case keys
        buy_rules = strategy_config.get('buyRules') or strategy_config.get('buy_rules', [])
        sell_rules = strategy_config.get('sellRules') or strategy_config.get('sell_rules', [])
        buy_logic = strategy_config.get('buyRuleLogic') or strategy_config.get('buy_logic', ['OR'])
        sell_logic = strategy_config.get('sellRuleLogic') or strategy_config.get('sell_logic', ['OR'])
        

        
        # Generate buy signals
        if buy_rules:
            for i, row in df.iterrows():
                rule_results = []
                for rule in buy_rules:
                    result = self.evaluate_rule(rule, row)
                    rule_results.append(result)
                
                # Use the first logic rule for now (simplified)
                logic = buy_logic[0] if buy_logic else 'OR'
                if logic == 'AND':
                    df.at[i, 'Buy_Signal'] = all(rule_results)
                else:  # OR
                    df.at[i, 'Buy_Signal'] = any(rule_results)
        
        # Generate sell signals
        if sell_rules:
            for i, row in df.iterrows():
                rule_results = []
                for rule in sell_rules:
                    result = self.evaluate_rule(rule, row)
                    rule_results.append(result)
                
                # Use the first logic rule for now (simplified)
                logic = sell_logic[0] if sell_logic else 'OR'
                if logic == 'AND':
                    df.at[i, 'Sell_Signal'] = all(rule_results)
                else:  # OR
                    df.at[i, 'Sell_Signal'] = any(rule_results)
        

        
        self.signals = df
        return df
    
    def run_backtest(self, symbol, start_date, end_date, strategy_config, 
                    initial_capital=100000, strategy_type='long_only'):
        """
        Run a complete backtest using the modular strategy.
        
        Args:
            symbol (str): Stock symbol
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            strategy_config (dict): Strategy configuration
            initial_capital (float): Initial capital
            strategy_type (str): 'long_only' or 'long_short'
        
        Returns:
            dict: Backtest results
        """
        try:
            # Fetch data
            data = self.fetch_data(symbol, start_date, end_date)
            
            # Apply indicators
            if strategy_config.get('indicators'):
                data = self.apply_indicators(data, strategy_config['indicators'])
            
            # Generate signals
            data = self.generate_signals(data, strategy_config, strategy_type)
            
            # Run backtest logic
            results = self._calculate_backtest_results(data, initial_capital, strategy_type, strategy_config)
            
            return results
            
        except Exception as e:
            raise Exception(f"Backtest failed: {str(e)}")
    
    def _calculate_backtest_results(self, data, initial_capital, strategy_type, strategy_config=None):
        """
        Calculate backtest results from signals.
        """
        df = data.copy()
        
        # Initialize position tracking
        position = 0  # 0: no position, 1: long, -1: short
        entry_price = 0
        entry_date = None
        trades = []
        equity_curve = []
        current_capital = initial_capital
        
        for i, row in df.iterrows():
            current_date = row['Date']
            current_price = row['Close']
            
            # Check for buy signal
            if row['Buy_Signal'] and position == 0:
                if strategy_type == 'long_only':
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                elif strategy_type == 'long_short':
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
            
            # Check for sell signal
            elif row['Sell_Signal'] and position != 0:
                if position == 1:  # Long position
                    exit_price = current_price
                    pnl = (exit_price - entry_price) / entry_price
                    trade_pnl = current_capital * pnl
                    current_capital += trade_pnl
                    
                    trades.append({
                        'entry_date': entry_date.strftime('%Y-%m-%d'),
                        'exit_date': current_date.strftime('%Y-%m-%d'),
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'action': 'BUY',
                        'pnl': trade_pnl
                    })
                    
                    position = 0
                    entry_price = 0
                    entry_date = None
                
                elif position == -1:  # Short position (for long_short)
                    exit_price = current_price
                    pnl = (entry_price - exit_price) / entry_price
                    trade_pnl = current_capital * pnl
                    current_capital += trade_pnl
                    
                    trades.append({
                        'entry_date': entry_date.strftime('%Y-%m-%d'),
                        'exit_date': current_date.strftime('%Y-%m-%d'),
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'action': 'SELL',
                        'pnl': trade_pnl
                    })
                    
                    position = 0
                    entry_price = 0
                    entry_date = None
            
            # For long_short, check for short signal
            elif strategy_type == 'long_short' and row['Sell_Signal'] and position == 0:
                position = -1
                entry_price = current_price
                entry_date = current_date
            
            # Record equity curve
            equity_curve.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'equity_curve': current_capital
            })
        
        # Close any open position at the end
        if position != 0:
            last_price = df.iloc[-1]['Close']
            if position == 1:
                pnl = (last_price - entry_price) / entry_price
                trade_pnl = current_capital * pnl
                current_capital += trade_pnl
                
                trades.append({
                    'entry_date': entry_date.strftime('%Y-%m-%d'),
                    'exit_date': df.iloc[-1]['Date'].strftime('%Y-%m-%d'),
                    'entry_price': entry_price,
                    'exit_price': last_price,
                    'action': 'BUY',
                    'pnl': trade_pnl
                })
            elif position == -1:
                pnl = (entry_price - last_price) / entry_price
                trade_pnl = current_capital * pnl
                current_capital += trade_pnl
                
                trades.append({
                    'entry_date': entry_date.strftime('%Y-%m-%d'),
                    'exit_date': df.iloc[-1]['Date'].strftime('%Y-%m-%d'),
                    'entry_price': entry_price,
                    'exit_price': last_price,
                    'action': 'SELL',
                    'pnl': trade_pnl
                })
        
        # Calculate performance metrics
        total_return = current_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # Buy and hold comparison
        buy_hold_return = ((df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close']) * 100
        
        # Calculate other metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(equity_curve) > 1:
            returns = []
            for i in range(1, len(equity_curve)):
                prev_equity = equity_curve[i-1]['equity_curve']
                curr_equity = equity_curve[i]['equity_curve']
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)
            
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Calculate maximum drawdown
        peak = initial_capital
        max_drawdown = 0
        
        for point in equity_curve:
            equity = point['equity_curve']
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'summary': {
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'buy_hold_return_pct': buy_hold_return,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'equity_curve': equity_curve,
                'trades': trades
            },
            'strategy_name': 'Modular Strategy',
            'parameters': strategy_config
        }


def run_modular_strategy_backtest(symbol, start_date, end_date, strategy_config, initial_capital=100000, strategy_type='long_only', interval='1d'):
    """
    Run a modular strategy backtest.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        strategy_config: Strategy configuration dictionary
        initial_capital: Initial capital
        strategy_type: 'long_only' or 'long_short'
        interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
        
    Returns:
        Dictionary with backtest results
    """
    # Initialize strategy builder
    builder = ModularStrategyBuilder()
    
    # Fetch data
    df = builder.fetch_data(symbol, start_date, end_date, interval)
    
    # Apply indicators
    df = builder.apply_indicators(df, strategy_config.get('indicators', []))
    
    # Generate signals
    df = builder.generate_signals(df, strategy_config, strategy_type)
    
    # Calculate performance metrics
    results = builder._calculate_backtest_results(df, initial_capital, strategy_type, strategy_config)
    
    return {
        'data': df,
        'summary': results,
        'strategy_name': 'Modular Strategy',
        'parameters': {
            'strategy_config': strategy_config,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'interval': interval
        }
    }

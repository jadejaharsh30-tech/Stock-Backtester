from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
from supertrend import run_supertrend_backtest
from ema_crossover import run_ema_crossover_backtest
from multi_strategy import run_multi_strategy_backtest
from modular_strategy import run_modular_strategy_backtest
from indicators import INDICATORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/experimental')
def experimental():
    """Serve the experimental HTML file"""
    return send_from_directory('.', 'index_experimental.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Stock Backtester API is running',
        'version': 'updated'
    })

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtest for selected strategy"""
    try:
        data = request.get_json()
        
        # Extract common parameters
        symbol = data.get('symbol')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        initial_capital = float(data.get('initialCapital', 100000))
        strategy_type = data.get('strategyType', 'long_only')
        strategy_name = data.get('strategy', 'supertrend')
        interval = data.get('interval', '1d')  # Default to daily data
        
        # Validate inputs
        if not symbol or not start_date or not end_date:
            return jsonify({'error': 'Symbol, startDate, and endDate are required'}), 400
        
        # Run backtest based on strategy
        if strategy_name == 'multi_strategy':
            strategies = data.get('strategies', [])
            if not strategies:
                return jsonify({'error': 'No strategies provided for multi-strategy backtest'}), 400
            
            try:
                results = run_multi_strategy_backtest(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    strategies=strategies,
                    initial_capital=initial_capital,
                    strategy_type=strategy_type,
                    interval=interval
                )
            except Exception as e:
                print(f"Multi-strategy error: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'Multi-strategy failed: {str(e)}'}), 500
            
        elif strategy_name == 'supertrend':
            period = int(data.get('period', 10))
            multiplier = float(data.get('multiplier', 3.0))
            
            results = run_supertrend_backtest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                multiplier=multiplier,
                initial_capital=initial_capital,
                strategy_type=strategy_type,
                interval=interval
            )
            
        elif strategy_name == 'ema_crossover':
            short_period = int(data.get('shortPeriod', 12))
            long_period = int(data.get('longPeriod', 26))
            ma_type = data.get('maType', 'ema')
            
            results = run_ema_crossover_backtest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                short_period=short_period,
                long_period=long_period,
                ma_type=ma_type,
                initial_capital=initial_capital,
                strategy_type=strategy_type,
                interval=interval
            )
            
        elif strategy_name == 'multi_strategy':
            strategies = data.get('strategies', [])
            if not strategies:
                return jsonify({'error': 'No strategies provided for multi-strategy backtest'}), 400
            
            try:
                results = run_multi_strategy_backtest(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    strategies=strategies,
                    initial_capital=initial_capital,
                    strategy_type=strategy_type,
                    interval=interval
                )
            except Exception as e:
                print(f"Multi-strategy error: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'Multi-strategy failed: {str(e)}'}), 500
            
        elif strategy_name == 'modular_strategy':
            strategy_config = data.get('strategyConfig', {})
            if not strategy_config:
                return jsonify({'error': 'No strategy configuration provided for modular strategy'}), 400
            
            results = run_modular_strategy_backtest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                strategy_config=strategy_config,
                initial_capital=initial_capital,
                strategy_type=strategy_type,
                interval=interval
            )
            
        else:
            return jsonify({'error': f'Unknown strategy: {strategy_name}'}), 400
        
        # Prepare response
        response = {
            'summary': results['summary'],
            'equity_curve': results['summary']['equity_curve'],
            'trades': results['summary']['trades'],
            'strategy_name': results['strategy_name'],
            'parameters': results['parameters']
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Backtest failed: {str(e)}'}), 500

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Get available trading strategies"""
    strategies = [
        {
            'id': 'multi_strategy',
            'name': 'Multi-Strategy Backtest',
            'description': 'Combine multiple strategies - trades execute only when ALL strategies agree',
            'parameters': []
        },
        {
            'id': 'supertrend',
            'name': 'Supertrend Strategy',
            'description': 'Trend-following strategy using ATR-based bands',
            'parameters': [
                {'name': 'period', 'label': 'ATR Period', 'type': 'number', 'default': 10, 'min': 1, 'max': 50},
                {'name': 'multiplier', 'label': 'ATR Multiplier', 'type': 'number', 'default': 3.0, 'min': 0.1, 'max': 10, 'step': 0.1}
            ]
        },
        {
            'id': 'ema_crossover',
            'name': 'EMA/SMA Crossover Strategy',
            'description': 'Moving average crossover strategy with EMA or SMA options',
            'parameters': [
                {'name': 'shortPeriod', 'label': 'Short Period', 'type': 'number', 'default': 12, 'min': 1, 'max': 100},
                {'name': 'longPeriod', 'label': 'Long Period', 'type': 'number', 'default': 26, 'min': 1, 'max': 200},
                {'name': 'maType', 'label': 'MA Type', 'type': 'select', 'options': ['ema', 'sma'], 'default': 'ema'}
            ]
        },
        {
            'id': 'modular_strategy',
            'name': 'Modular Strategy Builder',
            'description': 'Build custom strategies using combinations of technical indicators',
            'parameters': []
        }
    ]
    return jsonify(strategies)

@app.route('/api/indicators', methods=['GET'])
def get_indicators():
    """Get available technical indicators for modular strategy builder"""
    try:
        # Create JSON-serializable version of indicators (remove function objects)
        serializable_indicators = {}
        for key, indicator in INDICATORS.items():
            serializable_indicators[key] = {
                'name': indicator['name'],
                'parameters': indicator['parameters'],
                'columns': indicator['columns'],
                'description': indicator['description']
            }
        return jsonify(serializable_indicators)
    except Exception as e:
        print(f"Error in get_indicators: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get indicators: {str(e)}'}), 500

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get popular stock symbols"""
    symbols = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': '^NSEI', 'name': 'Nifty 50 (India)'},
        {'symbol': '^GSPC', 'name': 'S&P 500'},
        {'symbol': '^DJI', 'name': 'Dow Jones Industrial Average'}
    ]
    return jsonify(symbols)

if __name__ == '__main__':
    print("🚀 Starting Stock Backtester API...")
    print("📊 Backend server will run on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

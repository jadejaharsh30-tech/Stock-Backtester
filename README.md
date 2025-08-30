# 📊 Stock Backtester

A professional, feature-rich stock backtesting platform built with Python Flask and modern web technologies. Test your trading strategies with real market data and advanced analytics.

## 🌟 Features

### **📈 Multiple Trading Strategies**
- **Supertrend Strategy**: ATR-based trend-following indicator
- **EMA/SMA Crossover**: Moving average crossover with EMA/SMA options
- **Multi-Strategy Framework**: Combine multiple strategies with cumulative signal logic
- **Modular Strategy Builder**: Create custom strategies using technical indicators

### **⚙️ Advanced Features**
- **Multiple Timeframes**: Support for 1m, 3m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo
- **Long-Only & Long-Short**: Support for both trading approaches
- **Real-time Data**: Powered by yfinance API
- **Professional UI**: Clean, responsive design with interactive charts
- **Comprehensive Analytics**: Performance metrics, trade logs, equity curves

### **📊 Technical Indicators**
- **RSI (Relative Strength Index)**
- **MACD (Moving Average Convergence Divergence)**
- **Custom indicator combinations**

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8 or higher
- pip (Python package installer)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Stock-Backtester.git
   cd Stock-Backtester
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the web interface**
   - Open your browser
   - Go to: `http://localhost:5000`

## 📖 Usage Guide

### **Basic Backtesting**
1. **Enter Stock Symbol**: Use any valid stock symbol (e.g., AAPL, MSFT, TSLA)
2. **Select Date Range**: Choose start and end dates for your backtest
3. **Choose Strategy**: Select from available strategies
4. **Configure Parameters**: Adjust strategy-specific parameters
5. **Set Initial Capital**: Define your starting investment amount
6. **Run Backtest**: Click "Run Backtest" to see results

### **Multi-Strategy Backtesting**
1. **Select "Multi-Strategy Backtest"**
2. **Add Strategies**: Combine multiple strategies with different parameters
3. **Cumulative Logic**: Trades execute when all strategies align
4. **View Combined Results**: See performance of strategy combination

### **Modular Strategy Builder**
1. **Select "Modular Strategy Builder"**
2. **Add Indicators**: Choose from RSI, MACD, and more
3. **Define Rules**: Create custom buy/sell conditions
4. **Test Strategy**: Run backtest with your custom strategy

## 📊 Performance Metrics

The platform provides comprehensive performance analysis:

- **Total Return**: Overall strategy performance
- **Buy & Hold Comparison**: Strategy vs market performance
- **Trade Statistics**: Number of trades, win rate, average P&L
- **Risk Metrics**: Maximum drawdown, Sharpe ratio
- **Detailed Trade Log**: Entry/exit prices, P&L for each trade
- **Equity Curve**: Visual representation of portfolio growth

## 🛠️ Technical Architecture

### **Backend (Python Flask)**
- **Framework**: Flask web framework
- **Data Source**: yfinance for real-time market data
- **Analysis**: Pandas & NumPy for calculations
- **API**: RESTful endpoints for frontend communication

### **Frontend (HTML/CSS/JavaScript)**
- **UI Framework**: Modern responsive design
- **Charts**: Chart.js for interactive visualizations
- **Real-time Updates**: Dynamic data loading and display
- **Cross-browser**: Compatible with all modern browsers

### **Key Files**
- `app.py`: Main Flask application
- `supertrend.py`: Supertrend strategy implementation
- `ema_crossover.py`: EMA/SMA crossover strategy
- `multi_strategy.py`: Multi-strategy framework
- `modular_strategy.py`: Custom strategy builder
- `indicators.py`: Technical indicators library
- `index.html`: Main web interface

## 📈 Supported Strategies

### **Supertrend Strategy**
- **Description**: Trend-following indicator using ATR bands
- **Parameters**: ATR Period, ATR Multiplier
- **Best For**: Trend identification and momentum trading

### **EMA/SMA Crossover**
- **Description**: Moving average crossover signals
- **Parameters**: Short Period, Long Period, MA Type (EMA/SMA)
- **Best For**: Trend following and signal generation

### **Multi-Strategy Framework**
- **Description**: Combine multiple strategies with cumulative logic
- **Logic**: Trades execute when all strategies align
- **Best For**: Reducing false signals and improving accuracy

### **Modular Strategy Builder**
- **Description**: Create custom strategies using technical indicators
- **Components**: RSI, MACD, and more indicators
- **Best For**: Custom trading logic and strategy development

## 🌐 API Endpoints

### **Core Endpoints**
- `GET /api/health`: Health check
- `GET /api/strategies`: List available strategies
- `GET /api/indicators`: List available indicators
- `POST /api/backtest`: Run backtest with specified parameters

### **Strategy Endpoints**
- `POST /api/backtest` with `strategy: 'supertrend'`
- `POST /api/backtest` with `strategy: 'ema_crossover'`
- `POST /api/backtest` with `strategy: 'multi_strategy'`
- `POST /api/backtest` with `strategy: 'modular_strategy'`

## 🔧 Configuration

### **Timeframe Limits**
- **1m**: Maximum 7 days
- **5m**: Maximum 60 days
- **15m**: Maximum 60 days
- **30m**: Maximum 60 days
- **60m**: Maximum 730 days
- **1d**: No limit
- **1wk**: No limit
- **1mo**: No limit

### **Strategy Types**
- **Long-Only**: Buy and hold, exit to cash
- **Long-Short**: Buy long, sell short positions

## 📱 Multi-Device Support

- **Desktop**: Full functionality with all features
- **Tablet**: Responsive design, touch-friendly interface
- **Mobile**: Optimized for smaller screens
- **Cross-platform**: Works on Windows, macOS, Linux

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **yfinance**: For providing real-time market data
- **Chart.js**: For interactive chart visualizations
- **Flask**: For the web framework
- **Pandas & NumPy**: For data analysis and calculations

## 📞 Support

If you encounter any issues or have questions:
1. Check the documentation above
2. Review the code comments
3. Open an issue on GitHub
4. Contact the development team

---

**Happy Backtesting! 📊📈**

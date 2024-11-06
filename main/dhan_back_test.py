import requests
import pandas as pd
import numpy as np
from PyQt5 import QtWidgets, QtCore

# Dhan API Configuration
API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzMxNDY5OTMwLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMzU0NDkzOCJ9.Eq-pvWo-SHTBVFIQMurvmW5r405vDG3SxZv2TbGRLMl5cXCl7jN6upQ8J9kJ6KBi9u2ousJqU_Cnp4EOOpSDOQ'
BASE_URL = 'https://api.dhan.co'


# Fetch Historical Data from Dhan API
def fetch_data(symbol, start_date, end_date, interval="15m"):
    """Fetch historical data from Dhan API."""
    url = f"{BASE_URL}/marketdata/{symbol}/historical"
    params = {
        'interval': interval,
        'from_date': start_date,
        'to_date': end_date
    }
    headers = {'X-API-KEY': API_KEY}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data['data'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df = df[['ltp']]  # Only keep the last traded price for simplicity
    df.rename(columns={'ltp': 'close'}, inplace=True)  # Rename for consistency
    return df


# Moving Average Crossover Strategy
class MovingAverageCrossoverStrategy:
    def __init__(self, data, short_window=10, long_window=50, initial_capital=100000, share_quantity=10):
        self.data = data
        self.short_window = short_window
        self.long_window = long_window
        self.initial_capital = initial_capital
        self.share_quantity = share_quantity
        self.signals = pd.DataFrame(index=self.data.index)
        self.signals['signal'] = 0.0

        # Metrics tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.profits = []
        self.drawdowns = []

    def generate_signals(self):
        """Generates buy/sell signals based on MA crossover strategy."""
        # Calculate short and long moving averages
        self.signals['short_ma'] = self.data['close'].rolling(window=self.short_window, min_periods=1).mean()
        self.signals['long_ma'] = self.data['close'].rolling(window=self.long_window, min_periods=1).mean()

        # Generate signals based on moving average crossover
        signal_values = np.where(
            self.signals['short_ma'].values > self.signals['long_ma'].values, 1.0, 0.0
        )
        # Ensure equal lengths by aligning with the short_window start index
        self.signals.iloc[self.short_window:, self.signals.columns.get_loc('signal')] = signal_values[
                                                                                        self.short_window:]

        # Calculate changes to determine buy/sell points
        self.signals['signal'] = self.signals['signal'].diff()

        return self.signals

    def backtest(self):
        """Backtests the strategy and calculates final portfolio value and metrics."""
        capital = self.initial_capital
        peak = capital  # Track the peak for drawdown calculation
        positions = []

        for i in range(1, len(self.data)):
            if self.signals['signal'].iloc[i] == 1.0:  # Buy signal
                buy_price = self.data['close'].iloc[i].item()  # Ensure buy_price is a scalar
                positions.append(buy_price)
                print(f"Buying at {buy_price} on {self.data.index[i]}")
            elif self.signals['signal'].iloc[i] == -1.0 and positions:  # Sell signal
                sell_price = self.data['close'].iloc[i].item()  # Ensure sell_price is a scalar
                buy_price = positions.pop(0)
                profit = (sell_price - buy_price) * self.share_quantity
                capital += profit
                self.total_trades += 1
                self.total_profit += profit
                self.profits.append(profit)
                print(f"Selling at {sell_price} on {self.data.index[i]}, Profit: {profit}")

                # Track win/loss metrics
                if profit > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1

                # Track drawdown
                if capital > peak:
                    peak = capital
                drawdown = (peak - capital) / peak * 100
                self.drawdowns.append(drawdown)

        # Final metrics calculation
        win_rate = (self.winning_trades / self.total_trades) * 100 if self.total_trades > 0 else 0
        max_drawdown = max(self.drawdowns) if self.drawdowns else 0
        avg_profit = np.mean([p for p in self.profits if p > 0]) if self.winning_trades > 0 else 0
        avg_loss = np.mean([p for p in self.profits if p < 0]) if self.losing_trades > 0 else 0

        # Output results
        print("\n=== Backtest Results ===")
        print(f"Total Trades: {self.total_trades}")
        print(f"Winning Trades: {self.winning_trades}")
        print(f"Losing Trades: {self.losing_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Total Profit: {self.total_profit:.2f}")
        print(f"Max Drawdown: {max_drawdown:.2f}%")
        print(f"Average Profit per Trade: {avg_profit:.2f}")
        print(f"Average Loss per Trade: {avg_loss:.2f}")
        print(f"Final capital after backtest: {capital:.2f}")
        print(f"Final Profit/Loss: {capital - self.initial_capital:.2f}")

        return capital


# PyQt5 Interface for Input and Output
class StrategyApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moving Average Crossover Strategy")
        self.setGeometry(100, 100, 500, 400)

        # Create layout and input fields
        layout = QtWidgets.QVBoxLayout()

        self.symbol_input = QtWidgets.QLineEdit()
        self.symbol_input.setPlaceholderText("Enter stock symbol (e.g., RELIANCE)")
        layout.addWidget(self.symbol_input)

        self.start_date_input = QtWidgets.QLineEdit()
        self.start_date_input.setPlaceholderText("Enter start date (YYYY-MM-DD)")
        layout.addWidget(self.start_date_input)

        self.end_date_input = QtWidgets.QLineEdit()
        self.end_date_input.setPlaceholderText("Enter end date (YYYY-MM-DD)")
        layout.addWidget(self.end_date_input)

        self.interval_input = QtWidgets.QComboBox()
        self.interval_input.addItems(["15m", "1h", "1d"])
        layout.addWidget(self.interval_input)

        # Run button
        self.run_button = QtWidgets.QPushButton("Run Strategy")
        self.run_button.clicked.connect(self.run_strategy)
        layout.addWidget(self.run_button)

        # Output area
        self.output_area = QtWidgets.QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.setLayout(layout)

    def run_strategy(self):
        symbol = self.symbol_input.text()
        start_date = self.start_date_input.text()
        end_date = self.end_date_input.text()
        interval = self.interval_input.currentText()

        # Fetch data and run strategy
        data = fetch_data(symbol, start_date, end_date, interval)

        if data.empty:
            self.output_area.setText("No data available for the selected parameters.")
            return

        strategy = MovingAverageCrossoverStrategy(data)
        strategy.generate_signals()
        final_capital = strategy.backtest()

        # Display results
        self.output_area.setText(f"Profit/Loss: {final_capital - strategy.initial_capital:.2f}")
        self.output_area.append("\n=== Backtest Results ===")
        self.output_area.append(f"Total Trades: {strategy.total_trades}")
        self.output_area.append(f"Winning Trades: {strategy.winning_trades}")
        self.output_area.append(f"Losing Trades: {strategy.losing_trades}")
        self.output_area.append(f"Win Rate: {strategy.winning_trades / strategy.total_trades * 100:.2f}%")
        self.output_area.append(f"Total Profit: {strategy.total_profit:.2f}")
        self.output_area.append(f"Max Drawdown: {max(strategy.drawdowns):.2f}%")
        self.output_area.append(f"Average Profit per Trade: {np.mean([p for p in strategy.profits if p > 0]):.2f}")
        self.output_area.append(f"Average Loss per Trade: {np.mean([p for p in strategy.profits if p < 0]):.2f}")
        self.output_area.append(f"Final Capital: {final_capital:.2f}")


# Initialize the app
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = StrategyApp()
    window.show()
    sys.exit(app.exec_())
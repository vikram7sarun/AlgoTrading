import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Dhan API Configuration
API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzMxNDY5OTMwLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMzU0NDkzOCJ9.Eq-pvWo-SHTBVFIQMurvmW5r405vDG3SxZv2TbGRLMl5cXCl7jN6upQ8J9kJ6KBi9u2ousJqU_Cnp4EOOpSDOQ'
BASE_URL = 'https://api.dhan.co'


# Fetch Historical Data from Dhan API
def fetch_data(security_id, start_date, end_date):
    """Fetch historical data from Dhan API with all potential fields."""
    url = f"{BASE_URL}/v2/charts/historical"
    headers = {
        'Content-Type': 'application/json',
        'access-token': API_KEY
    }

    # Ensure all fields are correctly populated
    payload = {
        "securityId": security_id,  # Replace with Dhan-specific ID, e.g., "500325"
        "exchangeSegment": "NSE_EQ",  # Ensure this matches the segment for NSE stocks
        "instrument": "EQUITY",  # Instrument type
        "expiryCode": 0,  # Use 0 for non-derivative instruments
        "fromDate": start_date,
        "toDate": end_date
    }

    print("Payload:", payload)  # Debugging line to check payload
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code} - {response.text}")
        return pd.DataFrame()

    data = response.json()

    if 'timestamp' not in data:
        print(f"Unexpected response format: {data}")
        return pd.DataFrame()

    # Construct DataFrame
    df = pd.DataFrame({
        'timestamp': [datetime.fromtimestamp(ts) for ts in data['timestamp']],
        'open': data['open'],
        'high': data['high'],
        'low': data['low'],
        'close': data['close'],
        'volume': data['volume']
    })
    df.set_index('timestamp', inplace=True)
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

        # Check if there are enough rows to assign signals after short_window
        if len(self.signals) >= self.short_window:
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


# Main function for console execution
def main():
    # Use a longer date range if possible
    security_id = '500325'  # Example for Reliance; confirm with Dhan API
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year ago
    end_date = datetime.now().strftime('%Y-%m-%d')

    # Fetch data
    data = fetch_data(security_id, start_date, end_date)

    if data.empty:
        print("No data available for the selected parameters.")
        return

    # Initialize with smaller moving averages
    strategy = MovingAverageCrossoverStrategy(data, short_window=5, long_window=20)
    strategy.generate_signals()
    final_capital = strategy.backtest()
    print(f"\nFinal Profit/Loss: {final_capital - strategy.initial_capital:.2f}")


if __name__ == "__main__":
    main()
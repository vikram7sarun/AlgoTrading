import yfinance as yf
import pandas as pd
import numpy as np


# Step 1: Fetch Historical Data from Yahoo Finance
def fetch_data(symbol, start_date, end_date, interval="15m"):
    data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
    data = data[['Close']]  # Only keep the Close prices
    data.rename(columns={'Close': 'close'}, inplace=True)  # Rename for consistency
    return data


# Step 2: Define the Moving Average Crossover Strategy
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

        # Use .iloc for positional slicing here
        self.signals.iloc[self.short_window:, self.signals.columns.get_loc('signal')] = np.where(
            self.signals['short_ma'].iloc[self.short_window:] > self.signals['long_ma'].iloc[self.short_window:], 1.0,
            0.0
        )

        # Sell signal when short MA crosses below long MA
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

# Step 3: Run the Strategy with Yahoo Finance Data
def main():
    symbol = 'RELIANCE.NS'  # NSE symbol for Reliance Industries
    start_date = '2024-08-08'
    end_date = '2024-10-10'

    # Fetch data
    data = fetch_data(symbol, start_date, end_date)
    print("Fetched data:")
    print(data.head())

    # Initialize and run the strategy
    strategy = MovingAverageCrossoverStrategy(data, short_window=10, long_window=50)
    signals = strategy.generate_signals()
    final_capital = strategy.backtest()
    print(f"Profit/Loss: {final_capital - strategy.initial_capital}")


if __name__ == "__main__":
    main()

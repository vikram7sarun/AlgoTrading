from nsepy import get_history
import pandas as pd
from datetime import datetime

# Define the stock symbol, start date, and end date
symbol = 'RELIANCE'
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 6, 1)

# Fetch historical data
data = get_history(symbol=symbol, start=start_date, end=end_date)
data = data[['Close']]  # Keep only the Close prices for simplicity
data.rename(columns={'Close': 'close'}, inplace=True)  # Rename for compatibility
print(data.head())

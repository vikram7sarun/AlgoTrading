
from datetime import datetime

import pandas as pd
import requests
from dhanhq import dhanhq

# Initialize the Dhan client with your credentials
client_id = "1103544938"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzMxNDY5OTMwLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMzU0NDkzOCJ9.Eq-pvWo-SHTBVFIQMurvmW5r405vDG3SxZv2TbGRLMl5cXCl7jN6upQ8J9kJ6KBi9u2ousJqU_Cnp4EOOpSDOQ"
# Constants


# Initialize the Dhan client with your credentials
client_id = client_id
access_token = access_token
dhan = dhanhq(client_id, access_token)

# Set up the parameters
security_id = 'TCS'          # Replace with correct security ID for the instrument
exchange_segment = 'NSE_EQ'     # Segment for NSE equities
instrument_type = 'EQUITY'      # Instrument type for equity


intraday_data = dhan.historical_daily_data(
    symbol='TCS',
    exchange_segment='NSE_EQ',
    instrument_type='EQUITY',
    expiry_code=0,
    from_date='2024-10-01',
    to_date='2024-10-30'
)

# p = pd.DataFrame(intraday_data['data'])
#
# print(p)
# Check if data exists and create DataFrame
if 'data' in intraday_data and intraday_data['data']:
    p = pd.DataFrame(intraday_data['data'])

    # Convert 'timestamp' or 'start_Time' (whichever is present) to datetime if it exists
    timestamp_col = 'timestamp' if 'timestamp' in p.columns else 'start_Time'
    if timestamp_col in p.columns:
        p[timestamp_col] = pd.to_datetime(p[timestamp_col], unit='s')

    print("Data with converted time:")
    print(p)
else:
    print("No data available for the specified range.")
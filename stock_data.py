import yfinance as yf
import pandas as pd

# Select stock
stock = "RELIANCE.NS"

# Download stock data
df = yf.download(stock, start="2020-01-01", end="2025-01-01")

# Reset index
df.reset_index(inplace=True)

# Save to CSV
df.to_csv("reliance_stock_data.csv", index=False)

print("✅ Data Downloaded Successfully!")
print(df.head())
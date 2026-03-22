import pandas as pd
import yfinance as yf
import os
import time

# Load NIFTY 100 stock list
nifty_df = pd.read_csv("data/ind_nifty100list.csv")

symbols = nifty_df["Symbol"].tolist()

os.makedirs("data/nifty100_raw", exist_ok=True)

for symbol in symbols:
    stock_symbol = symbol + ".NS"
    print(f"Downloading {stock_symbol}")

    try:
        df = yf.download(stock_symbol, start="2020-01-01")

        if not df.empty:
            df.to_csv(f"data/nifty100_raw/{symbol}.csv")
            print(f"Saved {symbol}")
        else:
            print(f"No data for {symbol}")

        time.sleep(1)

    except Exception as e:
        print(f"Error with {symbol}: {e}")

print("Download complete.")
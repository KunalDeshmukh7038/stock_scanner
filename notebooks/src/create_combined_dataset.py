import pandas as pd
import ta
import os

raw_folder = "data/nifty100_raw"
combined_data = []

files = os.listdir(raw_folder)

for file in files:
    symbol = file.replace(".csv", "")
    print(f"Processing {symbol}")

    try:
        df = pd.read_csv(os.path.join(raw_folder, file))

        if df.empty:
            continue

        # Fix column issue if multi-index
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ensure Close column exists
        if "Close" not in df.columns:
            print(f"Skipping {symbol}, no Close column")
            continue

        # Convert Close to numeric
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

        # Remove bad rows
        df = df[df["Close"].notna()]

        # ---------------- Feature Engineering ----------------
        df["Return"] = df["Close"].pct_change()
        df["SMA_10"] = df["Close"].rolling(10).mean()
        df["SMA_20"] = df["Close"].rolling(20).mean()

        df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()

        macd = ta.trend.MACD(close=df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_signal"] = macd.macd_signal()

        # --- Bollinger Bands ---
        bb = ta.volatility.BollingerBands(close=df["Close"], window=20, window_dev=2)
        df["BB_upper"] = bb.bollinger_hband()
        df["BB_lower"] = bb.bollinger_lband()
        df["BB_width"] = df["BB_upper"] - df["BB_lower"]

        # --- ATR (Average True Range) ---
        df["ATR"] = ta.volatility.AverageTrueRange(
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            window=14
        ).average_true_range()

        # --- Price Change % over 5 days ---
        df["Price_change_pct"] = df["Close"].pct_change(5)

        # --- Volume Moving Average ---
        df["Vol_MA_10"] = df["Volume"].rolling(window=10).mean()

        # --- Target (1 = Up, 0 = Down) ---
        df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

        df["Symbol"] = symbol

        df.dropna(inplace=True)

        combined_data.append(df)

    except Exception as e:
        print(f"Error processing {symbol}: {e}")

# Combine all stocks
final_df = pd.concat(combined_data, ignore_index=True)

# Save dataset
os.makedirs("data/final_dataset", exist_ok=True)
final_df.to_csv("data/final_dataset/nifty100_combined.csv", index=False)

print("✅ Combined dataset created successfully!")
print("✅ Final dataset shape:", final_df.shape)

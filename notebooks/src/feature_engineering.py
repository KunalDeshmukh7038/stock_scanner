import pandas as pd
import ta
import os

def create_features(input_path, output_path):
    df = pd.read_csv(input_path)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    # --- Daily Returns ---
    df['Return'] = df['Close'].pct_change()

    # --- SMA ---
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()

    # --- RSI ---
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()

    # --- MACD ---
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()

    # --- Bollinger Bands ---
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_lower'] = bb.bollinger_lband()
    df['BB_width'] = df['BB_upper'] - df['BB_lower']

    # --- ATR (Average True Range) ---
    df['ATR'] = ta.volatility.AverageTrueRange(
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        window=14
    ).average_true_range()

    # --- Price Change % over 5 days ---
    df['Price_change_pct'] = df['Close'].pct_change(5)

    # --- Volume Moving Average ---
    df['Vol_MA_10'] = df['Volume'].rolling(window=10).mean()

    # --- Lag Features ---
    df['Lag_1'] = df['Close'].shift(1)
    df['Lag_2'] = df['Close'].shift(2)
    df['Lag_3'] = df['Close'].shift(3)

    # --- Target (1 = Up, 0 = Down) ---
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    # --- Drop NaN rows ---
    df = df.dropna()

    # --- Save to CSV ---
    df.to_csv(output_path, index=False)

    print("✅ Feature Engineering Completed Successfully!")

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    input_file = os.path.join(base_path, "data", "processed", "clean_reliance_stock_data.csv")
    output_file = os.path.join(base_path, "data", "processed", "feature_engineered_reliance.csv")

    create_features(input_file, output_file)

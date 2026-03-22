import pandas as pd
import os

print("Running preprocessing script...")

# Absolute path setup
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

input_file = os.path.join(base_path, "data", "raw", "reliance_stock_data.csv")
output_file = os.path.join(base_path, "data", "processed", "clean_reliance_stock_data.csv")

print("Input path:", input_file)
print("Output path:", output_file)

# Check if file exists
if not os.path.exists(input_file):
    print("❌ Input file NOT found!")
else:
    print("✅ Input file found!")

    df = pd.read_csv(input_file)
    print("Original Shape:", df.shape)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df = df.dropna()

    df.to_csv(output_file, index=False)

    print("✅ Cleaned file saved successfully!")
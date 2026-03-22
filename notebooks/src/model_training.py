import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_model(input_path, model_path):
    df = pd.read_csv(input_path)

    # Drop Date column
    df = df.drop(columns=['Date'])

    # Separate features and target
    X = df.drop(columns=['Target'])
    y = df['Target']

    # Time-based split (no shuffle)
    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Predict
    y_pred = model.predict(X_test)

    # Evaluate
    accuracy = accuracy_score(y_test, y_pred)
    print("Model Accuracy:", accuracy)
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # Save model
    joblib.dump(model, model_path)
    print("✅ Model saved successfully!")

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    input_file = os.path.join(base_path, "data", "processed", "feature_engineered_reliance.csv")
    model_file = os.path.join(base_path, "models", "reliance_model.pkl")

    train_model(input_file, model_file)
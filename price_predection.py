import mysql.connector
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine

# ==============================================================================
# CONFIGURATION
# ==============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Update with your MySQL password if configured
    "database": "dairy_analytics_db",
    "port": 3306,
}
TABLE_NAME = "milk_collection_records"


def train_price_prediction_model():
  """Loads historical dairy data from MySQL and trains a ML model to predict milk rate."""
  db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
  engine = create_engine(db_url)

  print("🔄 Loading historical data from database for model training...")
  try:
    # Fetch relevant columns for pricing model
    query = f"SELECT Fat_Pct, SNF_Pct, Milk_Type, Rate_Rs FROM {TABLE_NAME}"
    df = pd.read_sql(query, con=engine)
  except Exception as e:
    print(f"❌ Database error: {e}")
    return None, None

  if df.empty or len(df) < 10:
    print("⚠️ Not enough data in MySQL table to train a robust ML model.")
    return None, None

  # Drop rows with missing values
  df = df.dropna()

  # Features (X) and Target (y)
  # We use Fat_Pct, SNF_Pct, and Milk_Type (representing Breed/Type) as features
  X = df[["Fat_Pct", "SNF_Pct", "Milk_Type"]]
  y = df["Rate_Rs"]

  # Convert categorical 'Milk_Type' (Breed) into numerical dummy variables (One-Hot Encoding)
  X_encoded = pd.get_dummies(X, columns=["Milk_Type"], drop_first=True)

  # Save feature columns for matching user inputs later
  model_columns = X_encoded.columns.tolist()

  # Train Random Forest Regressor model
  print(f"🤖 Training Machine Learning model on {len(df)} records...")
  model = RandomForestRegressor(n_estimators=100, random_state=42)
  model.fit(X_encoded, y)

  print("✅ Model trained successfully!")
  return model, model_columns


def predict_price_interactive(model, model_columns):
  """Interactive CLI prompt to predict milk price based on Fat, SNF, and Breed."""
  if model is None:
    print("❌ Model is not available.")
    return

  print("\n" + "=" * 60)
  print("      KARNATAKA DAIRY - MILK PRICE PREDICTION PORTAL      ")
  print("=" * 60)

  try:
    fat_input = float(
        input("Enter Fat Percentage (e.g., 4.2): ").strip() or "4.0"
    )
    snf_input = float(input("Enter SNF Percentage (e.g., 8.5): ").strip() or "8.5")
    
    breed_input = (
        input(
            "Enter Breed / Milk Type [e.g.,  Jersey, HF]: "
        ).strip()
        or "Cow"
    )

    # Construct input dataframe matching training features
    input_data = pd.DataFrame(
        [
            {
                "Fat_Pct": fat_input,
                "SNF_Pct": snf_input,
                "Milk_Type": breed_input,
            }
        ]
    )

    # One-hot encode the user input
    input_encoded = pd.get_dummies(input_data, columns=["Milk_Type"])

    # Align input columns with the trained model's columns (fill missing dummy columns with 0)
    for col in model_columns:
      if col not in input_encoded.columns:
        input_encoded[col] = 0
    input_encoded = input_encoded[model_columns]

    # Predict rate
    predicted_rate = model.predict(input_encoded)[0]

    print("\n" + "=" * 60)
    print(f"📊 PREDICTED MILK PRICE / ಅಂದಾಜು ಹಾಲಿನ ಬೆಲೆ:")
    print("=" * 60)
    print(f" • Input Fat     : {fat_input}%")
    print(f" • Input SNF     : {snf_input}%")
    print(f" • Breed / Type  : {breed_input}")
    print("-" * 60)
    print(f"💰 Estimated Payout Rate : ₹{predicted_rate:.2f} per Liter")
    print(f"   (ಕನ್ನಡ: ಅಂದಾಜು ಪ್ರತಿ ಲೀಟರ್ ಬೆಲೆ ₹{predicted_rate:.2f})")
    print("=" * 60)

  except ValueError as ve:
    print(f"❌ Invalid numeric input: {ve}")
  except Exception as e:
    print(f"❌ Prediction error: {e}")


if __name__ == "__main__":
  trained_model, columns_meta = train_price_prediction_model()
  if trained_model:
    while True:
      predict_price_interactive(trained_model, columns_meta)
      cont = (
          input("\nWould you like to predict another price? (y/n): ")
          .strip()
          .lower()
      )
      if cont != "y":
        print("👋 Exiting Price Prediction Portal. Goodbye!")
        break
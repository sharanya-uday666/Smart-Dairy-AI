import json
import mysql.connector
from mysql.connector import Error
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

# XGBoost & LightGBM Fallbacks
try:
  from xgboost import XGBRegressor
except ImportError:
  XGBRegressor = None

try:
  from lightgbm import LGBMRegressor
except ImportError:
  LGBMRegressor = None

# ==============================================================================
# 1. DATABASE CONFIGURATION
# ==============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Update with your MySQL password if configured
    "database": "dairy_health",
    "port": 3306,
}


def init_milk_yield_table():
  """Creates the milk_yield_predictions table if it doesn't exist."""
  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        CREATE TABLE IF NOT EXISTS milk_yield_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            animal_id VARCHAR(50) NOT NULL,
            breed VARCHAR(50) NOT NULL,
            age_months INT NOT NULL,
            lactation_stage INT NOT NULL,
            previous_yield FLOAT NOT NULL,
            feed_intake_kg FLOAT NOT NULL,
            fat_pct FLOAT NOT NULL,
            snf_pct FLOAT NOT NULL,
            temperature_c FLOAT NOT NULL,
            humidity_pct FLOAT NOT NULL,
            predicted_tomorrow FLOAT NOT NULL,
            predicted_7_days JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()
  except Error as e:
    print(f"⚠️ Database Notice: {e}")


# ==============================================================================
# 2. ML ENGINE FOR KARNATAKA BREEDS
# ==============================================================================


class MilkYieldPredictor:

  def __init__(self, model_type: str = "xgboost"):
    self.model_type = model_type.lower()
    self.model_tomorrow = None
    self.model_7days = None

    self.breed_encoder = {
        "HF Crossbred": 0,
        "Jersey Crossbred": 1,
        "Gir": 2,
        "Sahiwal": 3,
        "Deoni": 4,
        "Hallikar": 5,
    }

    self.feature_names = [
        "breed_code",
        "age_months",
        "lactation_stage",
        "previous_yield",
        "feed_intake_kg",
        "fat_pct",
        "snf_pct",
        "temperature_c",
        "humidity_pct",
        "thi",
    ]

  def _compute_thi(self, temp: float, humidity: float) -> float:
    return (1.8 * temp + 32) - (
        0.55 - 0.0055 * humidity
    ) * (1.8 * temp - 26)

  def _get_model_instance(self):
    if self.model_type == "xgboost" and XGBRegressor is not None:
      return XGBRegressor(
          n_estimators=150, learning_rate=0.05, max_depth=6, random_state=42
      )
    elif self.model_type == "lightgbm" and LGBMRegressor is not None:
      return LGBMRegressor(
          n_estimators=150, learning_rate=0.05, max_depth=6, random_state=42
      )
    else:
      return RandomForestRegressor(
          n_estimators=150, max_depth=12, random_state=42
      )

  def generate_synthetic_dataset(self, n_samples: int = 4000) -> pd.DataFrame:
    np.random.seed(42)
    breed_names = list(self.breed_encoder.keys())
    breeds = np.random.choice(
        breed_names, size=n_samples, p=[0.40, 0.25, 0.15, 0.10, 0.05, 0.05]
    )
    breed_codes = [self.breed_encoder[b] for b in breeds]

    age_months = np.random.randint(24, 96, size=n_samples)
    lactation_stage = np.random.randint(1, 8, size=n_samples)

    yield_map = {
        "HF Crossbred": 18.0,
        "Jersey Crossbred": 13.0,
        "Gir": 10.0,
        "Sahiwal": 9.0,
        "Deoni": 6.0,
        "Hallikar": 4.0,
    }
    base_yield = np.array([yield_map[b] for b in breeds])

    feed_intake = np.random.uniform(10.0, 25.0, size=n_samples)
    fat_pct = np.random.uniform(3.5, 5.2, size=n_samples)
    snf_pct = np.random.uniform(8.2, 9.5, size=n_samples)

    temp_c = np.random.uniform(20.0, 39.0, size=n_samples)
    humidity = np.random.uniform(45.0, 90.0, size=n_samples)
    thi = (1.8 * temp_c + 32) - (
        0.55 - 0.0055 * humidity
    ) * (1.8 * temp_c - 26)

    heat_stress_penalty = np.where(thi > 72, (thi - 72) * 0.25, 0.0)

    previous_yield = np.clip(
        base_yield
        + (feed_intake * 0.4)
        - heat_stress_penalty
        + np.random.normal(0, 1.2, n_samples),
        2.0,
        40.0,
    )

    yield_tomorrow = (
        previous_yield * 0.88
        + (feed_intake * 0.1)
        - (heat_stress_penalty * 0.15)
        + np.random.normal(0, 0.6, n_samples)
    )

    yield_next_7_days = yield_tomorrow * 7.0 + np.random.normal(
        0, 2.5, n_samples
    )

    return pd.DataFrame({
        "breed_code": breed_codes,
        "age_months": age_months,
        "lactation_stage": lactation_stage,
        "previous_yield": previous_yield,
        "feed_intake_kg": feed_intake,
        "fat_pct": fat_pct,
        "snf_pct": snf_pct,
        "temperature_c": temp_c,
        "humidity_pct": humidity,
        "thi": thi,
        "yield_tomorrow": yield_tomorrow,
        "yield_next_7_days": yield_next_7_days,
    })

  def train_and_evaluate(self):
    df = self.generate_synthetic_dataset()
    X = df[self.feature_names]
    y_tomorrow = df["yield_tomorrow"]
    y_7days = df["yield_next_7_days"]

    X_train, X_test, y_train_t, y_test_t = train_test_split(
        X, y_tomorrow, test_size=0.2, random_state=42
    )
    _, _, y_train_7d, y_test_7d = train_test_split(
        X, y_7days, test_size=0.2, random_state=42
    )

    self.model_tomorrow = self._get_model_instance()
    self.model_7days = self._get_model_instance()

    self.model_tomorrow.fit(X_train, y_train_t)
    self.model_7days.fit(X_train, y_train_7d)

    preds_t = self.model_tomorrow.predict(X_test)
    preds_7d = self.model_7days.predict(X_test)

    return {
        "model_used": self.model_type,
        "tomorrow": {
            "MAE": round(float(mean_absolute_error(y_test_t, preds_t)), 4),
            "RMSE": round(
                float(np.sqrt(mean_squared_error(y_test_t, preds_t))), 4
            ),
            "R2": round(float(r2_score(y_test_t, preds_t)), 4),
            "MAPE_pct": round(
                float(mean_absolute_percentage_error(y_test_t, preds_t) * 100),
                2,
            ),
        },
        "next_7_days": {
            "MAE": round(float(mean_absolute_error(y_test_7d, preds_7d)), 4),
            "RMSE": round(
                float(np.sqrt(mean_squared_error(y_test_7d, preds_7d))), 4
            ),
            "R2": round(float(r2_score(y_test_7d, preds_7d)), 4),
            "MAPE_pct": round(
                float(
                    mean_absolute_percentage_error(y_test_7d, preds_7d) * 100
                ),
                2,
            ),
        },
    }

  def predict(self, input_data: dict) -> dict:
    breed_code = self.breed_encoder.get(
        input_data.get("breed", "HF Crossbred"), 0
    )
    thi = self._compute_thi(
        input_data["temperature_c"], input_data["humidity_pct"]
    )

    features = pd.DataFrame([{
        "breed_code": breed_code,
        "age_months": input_data["age_months"],
        "lactation_stage": input_data["lactation_stage"],
        "previous_yield": input_data["previous_yield"],
        "feed_intake_kg": input_data["feed_intake_kg"],
        "fat_pct": input_data["fat_pct"],
        "snf_pct": input_data["snf_pct"],
        "temperature_c": input_data["temperature_c"],
        "humidity_pct": input_data["humidity_pct"],
        "thi": thi,
    }])[self.feature_names]

    pred_tomorrow = float(self.model_tomorrow.predict(features)[0])
    pred_7day_total = float(self.model_7days.predict(features)[0])

    daily_decay = np.linspace(1.0, 0.95, 7)
    normalized_daily = (
        (daily_decay / daily_decay.sum())
        * pred_7day_total
    )
    daily_forecast = [round(float(val), 2) for val in normalized_daily]

    return {
        "predicted_yield_tomorrow_liters": round(pred_tomorrow, 2),
        "predicted_yield_next_7_days_total_liters": round(pred_7day_total, 2),
        "daily_forecast_7_days": daily_forecast,
    }

  def save_prediction_to_db(self, animal_id: str, inputs: dict, outputs: dict):
    try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor()

      query = """
            INSERT INTO milk_yield_predictions (
                animal_id, breed, age_months, lactation_stage,
                previous_yield, feed_intake_kg, fat_pct, snf_pct,
                temperature_c, humidity_pct, predicted_tomorrow, predicted_7_days
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

      values = (
          animal_id,
          inputs["breed"],
          inputs["age_months"],
          inputs["lactation_stage"],
          inputs["previous_yield"],
          inputs["feed_intake_kg"],
          inputs["fat_pct"],
          inputs["snf_pct"],
          inputs["temperature_c"],
          inputs["humidity_pct"],
          outputs["predicted_yield_tomorrow_liters"],
          json.dumps(outputs["daily_forecast_7_days"]),
      )

      cursor.execute(query, values)
      conn.commit()
      print(f"\n💾 Saved prediction record for '{animal_id}' to MySQL database.")
      cursor.close()
      conn.close()
    except Error as e:
      print(f"\n❌ Database error while saving: {e}")


# ==============================================================================
# 3. INTERACTIVE INPUT HANDLER WITH SAFE FALLBACKS
# ==============================================================================


def prompt_int(prompt_text: str, default_val: int) -> int:
  user_val = input(f"{prompt_text} [Default: {default_val}]: ").strip()
  if not user_val:
    return default_val
  try:
    return int(user_val)
  except ValueError:
    print(f"   ⚠️ Invalid integer input. Using default: {default_val}")
    return default_val


def prompt_float(prompt_text: str, default_val: float) -> float:
  user_val = input(f"{prompt_text} [Default: {default_val}]: ").strip()
  if not user_val:
    return default_val
  try:
    return float(user_val)
  except ValueError:
    print(f"   ⚠️ Invalid float input. Using default: {default_val}")
    return default_val


def get_farmer_inputs():
  print("\n" + "=" * 70)
  print("         🥛 KARNATAKA MILK YIELD PREDICTION SYSTEM           ")
  print("=" * 70)

  animal_id = (
      input("1. Cow Tag / ID number [Default: KA-COW-101]: ").strip()
      or "KA-COW-101"
  )

  print("\n2. Select Breed (ಕರ್ನಾಟಕ ತಳಿಗಳು):")
  print("   [1] HF Crossbred (ಹೆಚ್.ಎಫ್. ಕ್ರಾಸ್)")
  print("   [2] Jersey Crossbred (ಜರ್ಸಿ ಕ್ರಾಸ್)")
  print("   [3] Gir (ಗಿರ್ - A2 Milk)")
  print("   [4] Sahiwal (ಸಾಹಿವಾಲ್)")
  print("   [5] Deoni (ದೇವಣಿ - Bidar)")
  print("   [6] Hallikar (ಹಳ್ಳಿಕಾರ್ - South Karnataka)")

  b_choice = input("Select Option (1-6) [Default: 1]: ").strip() or "1"
  breed_map = {
      "1": "HF Crossbred",
      "2": "Jersey Crossbred",
      "3": "Gir",
      "4": "Sahiwal",
      "5": "Deoni",
      "6": "Hallikar",
  }
  breed = breed_map.get(b_choice, "HF Crossbred")

  age_months = prompt_int("\n3. Cow Age in Months", 42)
  lactation_stage = prompt_int("4. Lactation Stage (1-8)", 2)
  previous_yield = prompt_float("5. Yesterday's Yield (Liters)", 16.5)
  feed_intake_kg = prompt_float("6. Daily Feed/Fodder Intake (kg)", 18.0)
  fat_pct = prompt_float("7. Milk Fat Percentage (%)", 4.2)
  snf_pct = prompt_float("8. Milk SNF Percentage (%)", 8.5)
  temperature_c = prompt_float("9. Ambient Temperature (°C)", 30.0)
  humidity_pct = prompt_float("10. Humidity (%)", 65.0)

  return (
      animal_id,
      {
          "breed": breed,
          "age_months": age_months,
          "lactation_stage": lactation_stage,
          "previous_yield": previous_yield,
          "feed_intake_kg": feed_intake_kg,
          "fat_pct": fat_pct,
          "snf_pct": snf_pct,
          "temperature_c": temperature_c,
          "humidity_pct": humidity_pct,
      },
  )


# ==============================================================================
# 4. MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
  init_milk_yield_table()

  predictor = MilkYieldPredictor(model_type="xgboost")

  print("\nTraining Model on Karnataka Breed Dataset...")
  metrics = predictor.train_and_evaluate()
  print("\n" + "=" * 70)
  print("                   MODEL EVALUATION METRICS                   ")
  print("=" * 70)
  print(json.dumps(metrics, indent=2))

  # Take User Input from CLI
  animal_id, user_inputs = get_farmer_inputs()

  # Run Prediction
  prediction_output = predictor.predict(user_inputs)

  print("\n" + "=" * 70)
  print(f"       YIELD FORECAST REPORT FOR {animal_id} ({user_inputs['breed']})")
  print("=" * 70)
  print(json.dumps(prediction_output, indent=2))

  # Save to MySQL
  predictor.save_prediction_to_db(
      animal_id=animal_id, inputs=user_inputs, outputs=prediction_output
  )
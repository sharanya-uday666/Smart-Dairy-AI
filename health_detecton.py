import json
import os
import mysql.connector
from mysql.connector import Error
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.ensemble import RandomForestClassifier

# ==============================================================================
# 1. DATABASE CONFIGURATION
# ==============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "dairy_health",
    "port": 3306,
}

def save_to_database(
    animal_id: str,
    telemetry: dict,
    photo_path: str,
    base_score: float,
    visual_boost: float,
    final_risk_score: float,
    risk_level: str,
    photo_finding: str,
    anomalies: list,
    suggestions: list,
):
  """Inserts both input telemetry and output health predictions into dairy_health.health_records."""
  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO health_records (
            animal_id, milk_reduction, feed_intake, activity_dev,
            temperature, rumination_drop, history_score, photo_path,
            base_score, visual_boost, final_risk_score, risk_level,
            photo_finding, anomalies, suggestions
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

    record_values = (
        animal_id,
        telemetry["milk_reduction"],
        telemetry["feed_intake"],
        telemetry["activity_dev"],
        telemetry["temperature"],
        telemetry["rumination_drop"],
        telemetry["history_score"],
        photo_path if photo_path else None,
        base_score,
        visual_boost,
        final_risk_score,
        risk_level,
        photo_finding,
        json.dumps(anomalies),
        json.dumps(suggestions),
    )

    cursor.execute(insert_query, record_values)
    conn.commit()
    cursor.close()
    conn.close()
  except Error as e:
    print(f"Database error: {e}")

# ==============================================================================
# 2. MACHINE LEARNING ENGINE
# ==============================================================================
class HealthRiskMLModel:

  def __init__(self):
    self.model = RandomForestClassifier(n_estimators=100, random_state=42)
    self.feature_names = [
        "milk_reduction",
        "feed_intake",
        "activity_dev",
        "temperature",
        "rumination_drop",
        "history_score",
    ]

  def train(self, n_samples: int = 2000):
    np.random.seed(42)
    milk_reduction = np.random.uniform(0, 40, n_samples)
    feed_intake = np.clip(
        100
        - (milk_reduction * np.random.uniform(0.7, 1.3, n_samples))
        + np.random.normal(0, 5, n_samples),
        30,
        100,
    )
    activity_dev = np.random.uniform(-60, 60, n_samples)

    temp_c = np.random.normal(38.5, 0.4, n_samples)
    fever_mask = milk_reduction > 15
    temp_c[fever_mask] += np.random.uniform(0.4, 1.8, sum(fever_mask))

    rumination_drop = np.clip(
        milk_reduction * np.random.uniform(1.0, 1.7, n_samples)
        + np.random.normal(0, 5, n_samples),
        0,
        80,
    )
    history_score = np.random.choice([0, 1, 2], size=n_samples, p=[0.6, 0.3, 0.1])

    risk_labels = []
    for i in range(n_samples):
      score = 0
      if milk_reduction[i] > 12:
        score += 2
      if milk_reduction[i] > 22:
        score += 2
      if feed_intake[i] < 75:
        score += 2
      if temp_c[i] > 39.3 or temp_c[i] < 37.8:
        score += 3
      if rumination_drop[i] > 25:
        score += 2
      if rumination_drop[i] > 40:
        score += 2
      if abs(activity_dev[i]) > 30:
        score += 1
      if history_score[i] == 2:
        score += 1

      if score <= 2:
        risk_labels.append("LOW")
      elif score <= 5:
        risk_labels.append("MEDIUM")
      else:
        risk_labels.append("HIGH")

    X = pd.DataFrame({
        "milk_reduction": milk_reduction,
        "feed_intake": feed_intake,
        "activity_dev": activity_dev,
        "temperature": temp_c,
        "rumination_drop": rumination_drop,
        "history_score": history_score,
    })
    self.model.fit(X, pd.Series(risk_labels))

  def predict_base_risk(self, telemetry: dict) -> float:
    input_df = pd.DataFrame([telemetry])[self.feature_names]
    probs = self.model.predict_proba(input_df)[0]
    classes = list(self.model.classes_)

    med_i = classes.index("MEDIUM") if "MEDIUM" in classes else 0
    high_i = classes.index("HIGH") if "HIGH" in classes else 0

    base_score = float(probs[med_i] * 50.0 + probs[high_i] * 100.0)
    return round(base_score, 1)


def analyze_cow_photo(file_path: str) -> tuple[str, float]:
  if not file_path or not os.path.exists(file_path):
    return "No photo provided", 0.0
  try:
    img = Image.open(file_path).convert("RGB")
    img_array = np.array(img)
    if (
        float(np.mean(img_array[:, :, 0])) > 140
        and float(np.mean(img_array)) < 180
    ):
      return "Possible Skin/Mouth Redness or Inflammatory Lesion Flagged", 15.0
    return "No Major External Skin Lesions or Posture Anomalies Detected", 0.0
  except Exception:
    return "Error reading image file", 0.0
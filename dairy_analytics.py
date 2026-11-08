import mysql.connector
import pandas as pd
from sqlalchemy import create_engine

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Update with your MySQL root password if configured
    "database": "dairy_analytics_db",
    "port": 3306,
}
TABLE_NAME = "milk_collection_records"


def generate_dairy_analytics():
  # 1. Connect and Load Data from MySQL
  db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
  engine = create_engine(db_url)

  print(f"📥 Fetching records from MySQL table `{TABLE_NAME}`...")
  try:
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", con=engine)
    print(
        f"   -> Successfully loaded {len(df)} collection records.\n"
    )
  except Exception as e:
    print(f"❌ Error connecting to MySQL: {e}")
    return

  # ==========================================================================
  # 1. MONTHLY ANALYTICS (Volume, Revenue, & Quality Trends)
  # ==========================================================================
  print("=" * 70)
  print("                      1. MONTHLY ANALYTICS SUMMARY                    ")
  print("=" * 70)

  monthly_summary = (
      df.groupby("Month_Year")
      .agg(
          Total_Volume_Liters=("Qty_Ltr", "sum"),
          Total_Revenue_Rs=("Amount_Rs", "sum"),
          Avg_Fat_Pct=("Fat_Pct", "mean"),
          Avg_SNF_Pct=("SNF_Pct", "mean"),
          Avg_Rate_Rs=("Rate_Rs", "mean"),
      )
      .reset_index()
  )

  # Sort chronologically if needed (or display as grouped)
  print(monthly_summary.to_string(index=False))
  print("-" * 70)

  # ==========================================================================
  # 2. DAILY / SHIFT-WISE ANALYTICS (Morning vs Evening Collections)
  # ==========================================================================
  print("\n" + "=" * 70)
  print("                 2. DAILY / SHIFT-WISE SESSION ANALYTICS              ")
  print("=" * 70)

  shift_summary = (
      df.groupby("Shift")
      .agg(
          Total_Volume_Liters=("Qty_Ltr", "sum"),
          Avg_Volume_Per_Session=("Qty_Ltr", "mean"),
          Total_Payout_Rs=("Amount_Rs", "sum"),
          Avg_Fat_Pct=("Fat_Pct", "mean"),
      )
      .reset_index()
  )

  print(shift_summary.to_string(index=False))
  print("-" * 70)

  # ==========================================================================
  # 3. TOP FARMER / SUPPLIER PERFORMANCE ANALYTICS
  # ==========================================================================
  print("\n" + "=" * 70)
  print("                 3. TOP 5 FARMER CONTRIBUTORS (6-MONTH)               ")
  print("=" * 70)

  top_farmers = (
      df.groupby(["Code", "Name", "Milk_Type"])
      .agg(
          Total_Volume_Liters=("Qty_Ltr", "sum"),
          Total_Earnings_Rs=("Amount_Rs", "sum"),
          Avg_Fat_Pct=("Fat_Pct", "mean"),
      )
      .reset_index()
      .sort_values(by="Total_Volume_Liters", ascending=False)
      .head(5)
  )

  print(top_farmers.to_string(index=False))
  print("=" * 70)


if __name__ == "__main__":
  generate_dairy_analytics()
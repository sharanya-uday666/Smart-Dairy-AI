import os
import pandas as pd
from sqlalchemy import create_engine

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Update with your MySQL password if configured
    "database": "dairy_analytics_db",
    "port": 3306,
}
TABLE_NAME = "milk_collection_records"


def process_dairy_excel_upload(dairy_id: str, excel_file_path: str):
  # 1. Check if Excel file exists
  if not os.path.exists(excel_file_path):
    print(f"❌ Error: Excel file '{excel_file_path}' not found.")
    return

  print(
      f"📂 Reading Excel file '{excel_file_path}' for Dairy ID: [{dairy_id}]..."
  )

  # 2. Read Excel data into Pandas DataFrame
  try:
    df = pd.read_excel(excel_file_path)
    print(f"   -> Successfully loaded {len(df)} rows from Excel.")
  except Exception as e:
    print(f"❌ Error reading Excel file: {e}")
    return

  # 3. Convert and save locally as CSV (as requested)
  csv_filename = f"{dairy_id}_collection_backup.csv"
  df.to_csv(csv_filename, index=False)
  print(f"💾 Converted and saved local CSV backup as: '{csv_filename}'")

  # 4. Inject unique dairy_id column for multi-tenant separation
  df["dairy_id"] = dairy_id

  # 5. Connect to MySQL and store records
  db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
  engine = create_engine(db_url)

  try:
    print(f"🔄 Storing records into MySQL table `{TABLE_NAME}`...")
    df.to_sql(
        name=TABLE_NAME,
        con=engine,
        if_exists="append",  # Appends data without overwriting other dairies
        index=False,
        chunksize=1000,
    )
    print(f"✅ SUCCESS: All records saved to MySQL for dairy [{dairy_id}]!")
  except Exception as e:
    print(f"❌ Database error: {e}")
    return

  # 6. Generate and Print Analytics for this Specific Dairy
  print("\n" + "=" * 70)
  print(f"         INSTANT ANALYTICS REPORT FOR DAIRY: [{dairy_id}]         ")
  print("=" * 70)

  # Monthly Summary
  if "Month_Year" in df.columns:
    monthly = (
        df.groupby("Month_Year")
        .agg(
            Total_Volume_Liters=("Qty_Ltr", "sum"),
            Total_Payout_Rs=("Amount_Rs", "sum"),
            Avg_Fat_Pct=("Fat_Pct", "mean"),
        )
        .reset_index()
    )
    print("\n📅 1. MONTHLY SUMMARY:")
    print(monthly.to_string(index=False))

  # Shift-Wise Summary (Daily breakdown)
  if "Shift" in df.columns:
    shifts = (
        df.groupby("Shift")
        .agg(
            Total_Volume_Liters=("Qty_Ltr", "sum"),
            Avg_Session_Volume=("Qty_Ltr", "mean"),
            Total_Payout_Rs=("Amount_Rs", "sum"),
        )
        .reset_index()
    )
    print("\n☀️🌙 2. SHIFT-WISE (DAILY) SUMMARY:")
    print(shifts.to_string(index=False))

  print("=" * 70)


# ==============================================================================
# MAIN EXECUTION INTERFACE
# ==============================================================================
if __name__ == "__main__":
  print("=" * 50)
  print("      KARNATAKA DAIRY COOPERATIVE ONBOARDING PORTAL      ")
  print("=" * 50)

  # Simulated user input for a new dairy owner
  user_dairy_id = (
      input("Enter Dairy / Society ID [e.g., MYSORE-SOC-03]: ").strip()
      or "MYSORE-SOC-03"
  )
  user_excel_path = (
      input(
          "Enter path to Excel file [e.g., dairy_data.xlsx]: "
      ).strip()
      or "sample_dairy.xlsx"
  )

  # Run the full pipeline
  process_dairy_excel_upload(user_dairy_id, user_excel_path)
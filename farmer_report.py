import os
import mysql.connector
import pandas as pd
from sqlalchemy import create_engine
from twilio.rest import Client
import streamlit as st

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

# --- TWILIO SMS API CONFIGURATION (Your Active Credentials) ---
TWILIO_ACCOUNT_SID = st.secrets["twilio"]["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["twilio"]["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = st.secrets["twilio"]["TWILIO_PHONE_NUMBER"]  # Your Twilio Trial Phone Number


def generate_feed_suggestions_bilingual(avg_fat: float, avg_snf: float):
  """Generates veterinary and nutritional suggestions in both English and Kannada."""
  eng_suggestions = []
  kan_suggestions = []

  # Fat-based evaluation
  if avg_fat < 3.5:
    eng_suggestions.append(
        "Low Fat (< 3.5%): Add more dry fodder (straw) and bypass fat."
    )
    kan_suggestions.append(
        "ಕಡಿಮೆ ಕೊಬ್ಬು (< 3.5%): ಒಣಮೇವು (ಹುಲ್ಲು) ಮತ್ತು ಬೈಪಾಸ್ ಕೊಬ್ಬನ್ನು ಮೇವಿಗೆ ಸೇರಿಸಿ."
    )
  elif avg_fat >= 4.5:
    eng_suggestions.append("Excellent Fat level! Maintain current ratio.")
    kan_suggestions.append(
        "ಅತ್ಯುತ್ತಮ ಕೊಬ್ಬಿನಾಂಶ! ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಮೇವಿನ ಪ್ರಮಾಣವನ್ನು ಮುಂದುವರಿಸಿ."
    )
  else:
    eng_suggestions.append(
        "Fat level is normal. Ensure balanced morning/evening feeding."
    )
    kan_suggestions.append(
        "ಕೊಬ್ಬು ಸಾಮಾನ್ಯವಾಗಿದೆ. ಬೆಳಿಗ್ಗೆ ಮತ್ತು ಸಂಜೆ ಸಮತೋಲಿತ ಮೇವು ನೀಡಿ."
    )

  # SNF-based evaluation
  if avg_snf < 8.5:
    eng_suggestions.append(
        "Low SNF (< 8.5%): Increase green fodder and clean drinking water."
    )
    kan_suggestions.append(
        "ಕಡಿಮೆ SNF (< 8.5%): ಹಸಿ ಮೇವು ಮತ್ತು ಶುದ್ಧ ಕುಡಿಯುವ ನೀರನ್ನು ಹೆಚ್ಚಿಸಿ."
    )
  else:
    eng_suggestions.append("SNF level is good. Keep up proper hydration.")
    kan_suggestions.append(
        "SNF ಉತ್ತಮವಾಗಿದೆ. ಹೈನುಗಾರಿಕೆಯಲ್ಲಿ ಸ್ವಚ್ಛತೆ ಕಾಪಾಡಿ."
    )

  return " | ".join(eng_suggestions), " | ".join(kan_suggestions)


def send_sms_via_twilio(phone_number: str, message_body: str):
  """Sends SMS securely using the Twilio API and returns a tuple (success, info)."""
  clean_phone = phone_number.strip().replace("+", "")
  if len(clean_phone) == 10:
    clean_phone = "+91" + clean_phone
  elif not clean_phone.startswith("+"):
    clean_phone = "+" + clean_phone

  # Simulation fallback if testing or if credentials are default
  if (
      TWILIO_ACCOUNT_SID == "YOUR_TWILIO_ACCOUNT_SID"
      or not TWILIO_ACCOUNT_SID
  ):
    print("\n" + "=" * 65)
    print("⚠️ [SIMULATION FALLBACK] Twilio message simulated successfully:")
    print(f"To: {clean_phone}\nMessage: {message_body}")
    print("=" * 65)
    return True, "SIMULATION_SUCCESS"

  try:
    print(f"\n📲 Dispatches SMS to {clean_phone} via Twilio Secure Gateway...")
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        body=message_body, from_=TWILIO_PHONE_NUMBER, to=clean_phone
    )

    print(f"✅ SUCCESS: SMS sent! Twilio Message SID: {message.sid}")
    return True, message.sid
  except Exception as e:
    print(f"❌ Twilio Gateway Error: {e}")
    return False, str(e)


def process_farmer_reports():
  db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

  try:
    engine = create_engine(db_url)
  except Exception as e:
    print(f"❌ Database connection error: {e}")
    return

  print("=" * 65)
  print("       KARNATAKA DAIRY - BILINGUAL DAILY & MONTHLY REPORT PORTAL       ")
  print("=" * 65)

  # 1. Select Farmer by Name or ID
  search_input = input("Enter Farmer Name or Farmer ID/Code : ").strip()
  if not search_input:
    print("❌ Error: Search input cannot be empty.")
    return

  if search_input.isdigit():
    base_query = f"SELECT * FROM {TABLE_NAME} WHERE Code = {int(search_input)}"
  else:
    base_query = f"SELECT * FROM {TABLE_NAME} WHERE Name LIKE '%{search_input}%'"

  try:
    df = pd.read_sql(base_query, con=engine)
  except Exception as e:
    print(f"❌ Database query error: {e}")
    return

  if df.empty:
    print(f"⚠️ No records found for '{search_input}'. Please check the input.")
    return

  farmer_code = df["Code"].iloc[0]
  farmer_name = df["Name"].iloc[0]

  print(f"\n👤 Found Farmer: {str(farmer_name).upper()} (ID: {farmer_code})")
  print("-" * 65)

  # 2. Choose Report Type
  print("Select Report Type:")
  print("  [1] Daily / Shift-wise Report (ದೈನಂದಿನ / ಶಿಫ್ಟ್ ವರದಿ)")
  print("  [2] Monthly Cumulative Report (ಮಾಸಿಕ ಒಟ್ಟು ವರದಿ)")
  report_choice = input("Enter choice (1 or 2) [Default: 1]: ").strip() or "1"

  sms_text = ""

  if report_choice == "1":
    # --- DAILY / SHIFT REPORT WITH DATE/MONTH & SHIFT FILTER ---
    print("\n--- Filter Options ---")
    if "Month_Year" in df.columns:
      print(
          "Available Months/Periods in data:",
          df["Month_Year"].dropna().unique().tolist(),
      )
    if "Shift" in df.columns:
      print("Available Shifts in data:", df["Shift"].dropna().unique().tolist())

    target_month = input("Enter Month/Period  or press Enter to skip: ").strip()
    target_shift = (
        input("Enter Shift (Morning / Evening) or press Enter to skip: ")
        .strip()
        .capitalize()
    )

    filtered_df = df.copy()
    if target_month and "Month_Year" in filtered_df.columns:
      filtered_df = filtered_df[filtered_df["Month_Year"] == target_month]
    if target_shift and "Shift" in filtered_df.columns:
      filtered_df = filtered_df[filtered_df["Shift"] == target_shift]

    if filtered_df.empty:
      print("⚠️ No collection records match your specified filters.")
      return

    total_liters = filtered_df["Qty_Ltr"].sum()
    total_earnings = filtered_df["Amount_Rs"].sum()
    avg_fat = filtered_df["Fat_Pct"].mean()
    avg_snf = filtered_df["SNF_Pct"].mean()
    avg_rate = filtered_df["Rate_Rs"].mean()
    sessions_count = len(filtered_df)

    eng_advice, kan_advice = generate_feed_suggestions_bilingual(avg_fat, avg_snf)

    print("\n" + "=" * 65)
    print(f"       DAILY / SHIFT REPORT: {str(farmer_name).upper()} (ID: {farmer_code})")
    print(f"       ಫಾರ್ಮರ್ ದಿನದ / ಶಿಫ್ಟ್ ವರದಿ")
    print("=" * 65)
    print(f" • Filter Criteria   : Period: {target_month or 'All'} | Shift: {target_shift or 'All'}")
    print(f" • Sessions Logged   : {sessions_count}")
    print(f" • Milk Volume       : {total_liters:.2f} Liters")
    print(f" • Total Payout      : ₹{total_earnings:.2f}")
    print(f" • Average Fat       : {avg_fat:.2f}%")
    print(f" • Average SNF       : {avg_snf:.2f}%")
    print(f" • Average Rate      : ₹{avg_rate:.2f} / Liter")
    print("-" * 65)
    print(" 💡 English Advice (ಇಂಗ್ಲಿಷ್ ಸಲಹೆ):")
    print(f"    {eng_advice}")
    print(" 💡 ಕನ್ನಡ ಸಲಹೆ (Kannada Advice) :")
    print(f"    {kan_advice}")
    print("=" * 65)

    # Bilingual SMS body preparation
    sms_text = (
        f"Nandini Dairy Daily Report: Hi {farmer_name}, Vol:{total_liters:.1f}L, "
        f"Earn:Rs{total_earnings:.0f}, Fat:{avg_fat:.1f}%, SNF:{avg_snf:.1f}%. "
        f"Tip (Eng): {eng_advice} | ಸಲಹೆ (Kan): {kan_advice}"
    )

  else:
    # --- MONTHLY REPORT WITH MONTH FILTER ---
    if "Month_Year" not in df.columns:
      print("⚠️ 'Month_Year' column not found in database records.")
      return

    print("Available Months:", df["Month_Year"].dropna().unique().tolist())
    target_month = input("Enter specific Month to View or press Enter for All: ").strip()

    filtered_df = df.copy()
    if target_month:
      filtered_df = filtered_df[filtered_df["Month_Year"] == target_month]

    if filtered_df.empty:
      print(f"⚠️ No records found for month '{target_month}'.")
      return

    monthly_grouped = (
        filtered_df.groupby("Month_Year")
        .agg(
            Sessions=("Qty_Ltr", "count"),
            Total_Volume=("Qty_Ltr", "sum"),
            Total_Payout=("Amount_Rs", "sum"),
            Avg_Fat=("Fat_Pct", "mean"),
            Avg_SNF=("SNF_Pct", "mean"),
            Avg_Rate=("Rate_Rs", "mean"),
        )
        .reset_index()
    )

    print("\n" + "=" * 65)
    print(f"       MONTHLY CUMULATIVE REPORT: {str(farmer_name).upper()} (ID: {farmer_code})")
    print(f"       ಮಾಸಿಕ ಒಟ್ಟು ವರದಿ")
    print("=" * 65)

    m_vol, m_earn, m_fat, m_snf, m_per, m_eng, m_kan = 0, 0, 0, 0, "", "", ""
    for index, row in monthly_grouped.iterrows():
      m_per = row["Month_Year"]
      m_vol = row["Total_Volume"]
      m_earn = row["Total_Payout"]
      m_fat = row["Avg_Fat"]
      m_snf = row["Avg_SNF"]
      m_rate = row["Avg_Rate"]
      m_eng, m_kan = generate_feed_suggestions_bilingual(m_fat, m_snf)

      print(f" 📅 Month/Period: {m_per}")
      print(f"   • Sessions Logged : {row['Sessions']}")
      print(f"   • Total Volume    : {m_vol:.2f} Liters")
      print(f"   • Total Payout    : ₹{m_earn:.2f}")
      print(f"   • Average Fat/SNF : {m_fat:.2f}% Fat | {m_snf:.2f}% SNF")
      print(f"   • Average Rate    : ₹{m_rate:.2f} / Liter")
      print(f"   ---------------------------------------------")
      print(f"   💡 English Tip    : {m_eng}")
      print(f"   💡 ಕನ್ನಡ ಸಲಹೆ      : {m_kan}")
      print("=" * 65)

    # Bilingual SMS body preparation for monthly view
    sms_text = (
        f"Nandini Monthly Report ({m_per}): Hi {farmer_name}, Vol:{m_vol:.1f}L, "
        f"Earn:Rs{m_earn:.0f}, Fat:{m_fat:.1f}%, SNF:{m_snf:.1f}%. "
        f"Tip (Eng): {m_eng} | ಸಲಹೆ (Kan): {m_kan}"
    )

  # 3. Get Mobile Number and Send SMS via Twilio
  farmer_phone = input("Enter Farmer's 10-digit Mobile Number : ").strip()

  success, sid_or_info = send_sms_via_twilio(farmer_phone, sms_text)
  if success:
    print(f"🚀 SMS Dispatched Successfully! Status/SID: {sid_or_info}")
  else:
    print(f"❌ Failed to Send SMS: {sid_or_info}")


if __name__ == "__main__":
  process_farmer_reports()
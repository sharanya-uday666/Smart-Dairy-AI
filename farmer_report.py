import pandas as pd
from sqlalchemy import create_engine, text, URL

# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "dairy_analytics_db",
    "port": 3306
}

TABLE_NAME = "milk_collection_records"

# =========================================================
# SMS CONFIGURATION
# TWILIO IS DISABLED
# =========================================================

SMS_ENABLED = False

def send_sms_via_twilio(phone_number, message_body):
    """
    SMS notifications are disabled.
    No Twilio account or credentials are required.
    """
    return False, "SMS notifications are disabled."


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_database_engine():

    database_url = URL.create(
        "mysql+mysqlconnector",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"]
    )

    return create_engine(database_url)


# =========================================================
# ENGLISH AND KANNADA FEED SUGGESTIONS
# =========================================================

def generate_feed_suggestions_bilingual(avg_fat, avg_snf):

    eng_suggestions = []
    kan_suggestions = []

    # Fat evaluation
    if pd.isna(avg_fat):
        eng_suggestions.append("Fat data is unavailable.")
        kan_suggestions.append("ಕೊಬ್ಬಿನಾಂಶದ ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ.")

    elif avg_fat < 3.5:

        eng_suggestions.append(
            "Low Fat: Provide balanced feed and consult a veterinarian."
        )

        kan_suggestions.append(
            "ಕಡಿಮೆ ಕೊಬ್ಬು: ಸಮತೋಲಿತ ಮೇವು ನೀಡಿ ಮತ್ತು ಪಶುವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ."
        )

    elif avg_fat >= 4.5:

        eng_suggestions.append(
            "Excellent Fat level. Maintain the current feeding routine."
        )

        kan_suggestions.append(
            "ಅತ್ಯುತ್ತಮ ಕೊಬ್ಬಿನಾಂಶ. ಪ್ರಸ್ತುತ ಮೇವಿನ ಕ್ರಮವನ್ನು ಮುಂದುವರಿಸಿ."
        )

    else:

        eng_suggestions.append(
            "Fat level is normal. Maintain balanced feeding."
        )

        kan_suggestions.append(
            "ಕೊಬ್ಬಿನಾಂಶ ಸಾಮಾನ್ಯವಾಗಿದೆ. ಸಮತೋಲಿತ ಮೇವು ನೀಡಿ."
        )

    # SNF evaluation
    if pd.isna(avg_snf):
        eng_suggestions.append("SNF data is unavailable.")
        kan_suggestions.append("SNF ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ.")

    elif avg_snf < 8.5:

        eng_suggestions.append(
            "Low SNF: Provide green fodder and clean drinking water."
        )

        kan_suggestions.append(
            "ಕಡಿಮೆ SNF: ಹಸಿ ಮೇವು ಮತ್ತು ಶುದ್ಧ ಕುಡಿಯುವ ನೀರನ್ನು ನೀಡಿ."
        )

    else:

        eng_suggestions.append(
            "SNF level is good. Maintain proper hydration."
        )

        kan_suggestions.append(
            "SNF ಉತ್ತಮವಾಗಿದೆ. ಸಾಕಷ್ಟು ಶುದ್ಧ ನೀರನ್ನು ನೀಡಿ."
        )

    return (
        " | ".join(eng_suggestions),
        " | ".join(kan_suggestions)
    )


# =========================================================
# FETCH FARMER RECORDS
# =========================================================

def get_farmer_records(search_input):

    engine = get_database_engine()

    try:

        if search_input.isdigit():

            query = text(
                f"SELECT * FROM {TABLE_NAME} WHERE Code = :code"
            )

            df = pd.read_sql(
                query,
                engine,
                params={"code": int(search_input)}
            )

        else:

            query = text(
                f"SELECT * FROM {TABLE_NAME} WHERE Name LIKE :name"
            )

            df = pd.read_sql(
                query,
                engine,
                params={"name": f"%{search_input}%"}
            )

        return df

    finally:
        engine.dispose()


# =========================================================
# PREPARE DATA
# =========================================================

def prepare_farmer_data(df):

    numeric_columns = [
        "Qty_Ltr",
        "Amount_Rs",
        "Fat_Pct",
        "SNF_Pct",
        "Rate_Rs"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# =========================================================
# DAILY AND SHIFT-WISE REPORT
# =========================================================

def generate_daily_report(df, farmer_name, farmer_code):

    filtered_df = df.copy()

    if "Month_Year" in df.columns:

        print("\nAvailable Months:")
        print(df["Month_Year"].dropna().unique().tolist())

        target_month = input(
            "Enter Month or press Enter for all: "
        ).strip()

        if target_month:

            filtered_df = filtered_df[
                filtered_df["Month_Year"].astype(str) == target_month
            ]

    if "Shift" in df.columns:

        print("\nAvailable Shifts:")
        print(df["Shift"].dropna().unique().tolist())

        target_shift = input(
            "Enter Morning/Evening or press Enter for all: "
        ).strip()

        if target_shift:

            filtered_df = filtered_df[
                filtered_df["Shift"].astype(str).str.lower()
                == target_shift.lower()
            ]

    if filtered_df.empty:

        print("No records found for the selected filters.")
        return

    total_liters = filtered_df["Qty_Ltr"].sum()
    total_earnings = filtered_df["Amount_Rs"].sum()

    avg_fat = filtered_df["Fat_Pct"].mean()
    avg_snf = filtered_df["SNF_Pct"].mean()
    avg_rate = filtered_df["Rate_Rs"].mean()

    sessions = len(filtered_df)

    eng_advice, kan_advice = (
        generate_feed_suggestions_bilingual(avg_fat, avg_snf)
    )

    print("\n" + "=" * 60)
    print("SMART DAIRY - DAILY FARMER REPORT")
    print("ಸ್ಮಾರ್ಟ್ ಡೈರಿ - ದೈನಂದಿನ ವರದಿ")
    print("=" * 60)

    print("Farmer Name:", farmer_name)
    print("Farmer ID:", farmer_code)

    print("Sessions:", sessions)
    print(f"Milk Volume: {total_liters:.2f} Liters")
    print(f"Total Earnings: Rs. {total_earnings:.2f}")
    print(f"Average Fat: {avg_fat:.2f}%")
    print(f"Average SNF: {avg_snf:.2f}%")
    print(f"Average Rate: Rs. {avg_rate:.2f}")

    print("\nEnglish Suggestions:")
    print(eng_advice)

    print("\nKannada Suggestions:")
    print(kan_advice)

    print("=" * 60)


# =========================================================
# MONTHLY CUMULATIVE REPORT
# =========================================================

def generate_monthly_report(df, farmer_name, farmer_code):

    if "Month_Year" not in df.columns:

        print("Month_Year column is missing.")
        return

    print("\nAvailable Months:")
    print(df["Month_Year"].dropna().unique().tolist())

    target_month = input(
        "Enter Month or press Enter for all: "
    ).strip()

    filtered_df = df.copy()

    if target_month:

        filtered_df = filtered_df[
            filtered_df["Month_Year"].astype(str) == target_month
        ]

    if filtered_df.empty:

        print("No monthly records found.")
        return

    monthly_data = (
        filtered_df.groupby("Month_Year")
        .agg(
            Sessions=("Qty_Ltr", "count"),
            Total_Volume=("Qty_Ltr", "sum"),
            Total_Payout=("Amount_Rs", "sum"),
            Avg_Fat=("Fat_Pct", "mean"),
            Avg_SNF=("SNF_Pct", "mean"),
            Avg_Rate=("Rate_Rs", "mean")
        )
        .reset_index()
    )

    print("\n" + "=" * 60)
    print("SMART DAIRY - MONTHLY FARMER REPORT")
    print("ಸ್ಮಾರ್ಟ್ ಡೈರಿ - ಮಾಸಿಕ ವರದಿ")
    print("=" * 60)

    print("Farmer Name:", farmer_name)
    print("Farmer ID:", farmer_code)

    for _, row in monthly_data.iterrows():

        eng_advice, kan_advice = (
            generate_feed_suggestions_bilingual(
                row["Avg_Fat"],
                row["Avg_SNF"]
            )
        )

        print("\nMonth:", row["Month_Year"])

        print("Sessions:", row["Sessions"])

        print(
            f"Total Milk: {row['Total_Volume']:.2f} Liters"
        )

        print(
            f"Total Earnings: Rs. {row['Total_Payout']:.2f}"
        )

        print(
            f"Average Fat: {row['Avg_Fat']:.2f}%"
        )

        print(
            f"Average SNF: {row['Avg_SNF']:.2f}%"
        )

        print(
            f"Average Rate: Rs. {row['Avg_Rate']:.2f}"
        )

        print("\nEnglish Advice:")
        print(eng_advice)

        print("\nKannada Advice:")
        print(kan_advice)

        print("-" * 60)


# =========================================================
# MAIN FARMER REPORT FUNCTION
# =========================================================

def process_farmer_reports():

    print("\n" + "=" * 60)
    print("KARNATAKA SMART DAIRY")
    print("BILINGUAL FARMER REPORT PORTAL")
    print("=" * 60)

    search_input = input(
        "\nEnter Farmer Name or Farmer ID: "
    ).strip()

    if not search_input:

        print("Please enter a Farmer Name or ID.")
        return

    try:

        df = get_farmer_records(search_input)

        if df.empty:

            print("No farmer records found.")
            return

        df = prepare_farmer_data(df)

        required_columns = [
            "Code",
            "Name",
            "Qty_Ltr",
            "Amount_Rs",
            "Fat_Pct",
            "SNF_Pct",
            "Rate_Rs"
        ]

        missing = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing:

            print("Missing database columns:", missing)
            return

        farmer_code = df["Code"].iloc[0]
        farmer_name = df["Name"].iloc[0]

        print("\nFarmer Found:", farmer_name)
        print("Farmer ID:", farmer_code)

        print("\nSelect Report Type:")
        print("1. Daily / Shift-wise Report")
        print("2. Monthly Cumulative Report")

        choice = input("Enter choice (1 or 2): ").strip()

        if choice == "1":

            generate_daily_report(
                df,
                farmer_name,
                farmer_code
            )

        elif choice == "2":

            generate_monthly_report(
                df,
                farmer_name,
                farmer_code
            )

        else:

            print("Invalid choice.")
            return

        print("\nSMS notifications are disabled.")
        print("Farmer report generation completed.")

    except Exception as error:

        print("Error:", str(error))


# =========================================================
# PROGRAM ENTRY POINT
# =========================================================

if __name__ == "__main__":

    process_farmer_reports()

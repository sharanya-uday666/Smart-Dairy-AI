import pandas as pd
from sqlalchemy import create_engine, text, URL

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Enter your MySQL password if required
    "database": "dairy_analytics_db",
    "port": 3306,
}

TABLE_NAME = "milk_collection_records"

# ============================================================
# SMS CONFIGURATION
# SMS IS DISABLED - NO TWILIO ACCOUNT REQUIRED
# ============================================================

SMS_ENABLED = False


def send_sms_via_twilio(phone_number, message_body):
    """
    SMS is disabled because Twilio is not configured.
    The remaining project features work independently.
    """
    return False, "SMS notifications are disabled."


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_engine():

    database_url = URL.create(
        drivername="mysql+mysqlconnector",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
    )

    return create_engine(database_url)


# ============================================================
# BILINGUAL FEED SUGGESTIONS
# ============================================================

def generate_feed_suggestions_bilingual(avg_fat, avg_snf):

    eng_suggestions = []
    kan_suggestions = []

    # Fat evaluation
    if avg_fat < 3.5:

        eng_suggestions.append(
            "Low Fat: Add more dry fodder and consult a veterinarian."
        )

        kan_suggestions.append(
            "ಕಡಿಮೆ ಕೊಬ್ಬು: ಒಣಮೇವು ಸೇರಿಸಿ ಮತ್ತು ಪಶುವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ."
        )

    elif avg_fat >= 4.5:

        eng_suggestions.append(
            "Excellent Fat level! Maintain the current feeding routine."
        )

        kan_suggestions.append(
            "ಅತ್ಯುತ್ತಮ ಕೊಬ್ಬಿನಾಂಶ! ಪ್ರಸ್ತುತ ಮೇವಿನ ಕ್ರಮವನ್ನು ಮುಂದುವರಿಸಿ."
        )

    else:

        eng_suggestions.append(
            "Fat level is normal. Maintain balanced feeding."
        )

        kan_suggestions.append(
            "ಕೊಬ್ಬಿನಾಂಶ ಸಾಮಾನ್ಯವಾಗಿದೆ. ಸಮತೋಲಿತ ಮೇವು ನೀಡಿ."
        )

    # SNF evaluation
    if avg_snf < 8.5:

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


# ============================================================
# FETCH FARMER RECORDS
# ============================================================

def get_farmer_records(search_input):

    engine = get_database_engine()

    try:

        if search_input.isdigit():

            query = text(
                f"SELECT * FROM {TABLE_NAME} WHERE Code = :farmer_code"
            )

            df = pd.read_sql(
                query,
                con=engine,
                params={"farmer_code": int(search_input)}
            )

        else:

            query = text(
                f"SELECT * FROM {TABLE_NAME} WHERE Name LIKE :farmer_name"
            )

            df = pd.read_sql(
                query,
                con=engine,
                params={"farmer_name": f"%{search_input}%"}
            )

        return df

    finally:
        engine.dispose()


# ============================================================
# PREPARE NUMERIC DATA
# ============================================================

def prepare_farmer_data(df):

    numeric_columns = [
        "Qty_Ltr",
        "Amount_Rs",
        "Fat_Pct",
        "SNF_Pct",
        "Rate_Rs",
    ]

    for column in numeric_columns:

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column], errors="coerce"
            )

    return df


# ============================================================
# DAILY / SHIFT-WISE REPORT
# ============================================================

def generate_daily_report(df, farmer_name, farmer_code):

    print("\nAvailable Months:")

    if "Month_Year" in df.columns:
        print(df["Month_Year"].dropna().unique().tolist())

    print("\nAvailable Shifts:")

    if "Shift" in df.columns:
        print(df["Shift"].dropna().unique().tolist())

    target_month = input(
        "\nEnter Month/Period or press Enter for all: "
    ).strip()

    target_shift = input(
        "Enter Shift (Morning/Evening) or press Enter for all: "
    ).strip().capitalize()

    filtered_df = df.copy()

    if target_month and "Month_Year" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Month_Year"].astype(str) == target_month
        ]

    if target_shift and "Shift" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Shift"].astype(str).str.capitalize()
            == target_shift
        ]

    if filtered_df.empty:

        print("No records found for the selected filters.")
        return

    total_liters = filtered_df["Qty_Ltr"].sum()
    total_earnings = filtered_df["Amount_Rs"].sum()
    avg_fat = filtered_df["Fat_Pct"].mean()
    avg_snf = filtered_df["SNF_Pct"].mean()
    avg_rate = filtered_df["Rate_Rs"].mean()

    sessions_count = len(filtered_df)

    eng_advice, kan_advice = generate_feed_suggestions_bilingual(
        avg_fat, avg_snf
    )

    print("\n" + "=" * 60)

    print("DAILY / SHIFT-WISE FARMER REPORT")
    print("ದೈನಂದಿನ / ಶಿಫ್ಟ್ ವರದಿ")

    print("=" * 60)

    print(f"Farmer Name       : {farmer_name}")
    print(f"Farmer ID         : {farmer_code}")

    print(f"Selected Month    : {target_month or 'All'}")
    print(f"Selected Shift    : {target_shift or 'All'}")

    print(f"Sessions Logged   : {sessions_count}")
    print(f"Milk Volume       : {total_liters:.2f} Liters")
    print(f"Total Earnings    : Rs. {total_earnings:.2f}")
    print(f"Average Fat       : {avg_fat:.2f}%")
    print(f"Average SNF       : {avg_snf:.2f}%")
    print(f"Average Rate      : Rs. {avg_rate:.2f}")

    print("-" * 60)

    print("English Suggestions:")
    print(eng_advice)

    print("\nKannada Suggestions:")
    print(kan_advice)

    print("=" * 60)


# ============================================================
# MONTHLY CUMULATIVE REPORT
# ============================================================

def generate_monthly_report(df, farmer_name, farmer_code):

    if "Month_Year" not in df.columns:

        print("Month_Year column is missing.")
        return

    print("\nAvailable Months:")

    print(df["Month_Year"].dropna().unique().tolist())

    target_month = input(
        "\nEnter Month or press Enter for all: "
    ).strip()

    filtered_df = df.copy()

    if target_month:

        filtered_df = filtered_df[
            filtered_df["Month_Year"].astype(str) == target_month
        ]

    if filtered_df.empty:

        print("No monthly records found.")
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

    print("\n" + "=" * 60)

    print("MONTHLY CUMULATIVE FARMER REPORT")
    print("ಮಾಸಿಕ ಒಟ್ಟು ವರದಿ")

    print("=" * 60)

    print(f"Farmer Name : {farmer_name}")
    print(f"Farmer ID   : {farmer_code}")

    for _, row in monthly_grouped.iterrows():

        eng_advice, kan_advice = generate_feed_suggestions_bilingual(
            row["Avg_Fat"], row["Avg_SNF"]
        )

        print("\nMonth:", row["Month_Year"])

        print(f"Sessions       : {row['Sessions']}")
        print(f"Total Volume   : {row['Total_Volume']:.2f} Liters")
        print(f"Total Earnings : Rs. {row['Total_Payout']:.2f}")
        print(f"Average Fat    : {row['Avg_Fat']:.2f}%")
        print(f"Average SNF    : {row['Avg_SNF']:.2f}%")
        print(f"Average Rate   : Rs. {row['Avg_Rate']:.2f}")

        print("\nEnglish Advice:")
        print(eng_advice)

        print("\nKannada Advice:")
        print(kan_advice)

        print("-" * 60)


# ============================================================
# MAIN FARMER REPORT FUNCTION
# ============================================================

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

        required_columns = [
            "Code",
            "Name",
            "Qty_Ltr",
            "Amount_Rs",
            "Fat_Pct",
            "SNF_Pct",
            "Rate_Rs",
        ]

        missing_columns = [
            col for col in required_columns if col not in df.columns
        ]

        if missing_columns:

            print("Missing database columns:", missing_columns)
            return

        df = prepare_farmer_data(df)

        farmer_code = df["Code"].iloc[0]
        farmer_name = df["Name"].iloc[0]

        print("\nFarmer Found:", farmer_name)
        print("Farmer ID:", farmer_code)

        print("\nSelect Report Type:")

        print("1. Daily / Shift-wise Report")
        print("2. Monthly Cumulative Report")

        report_choice = input(
            "\nEnter your choice (1 or 2): "
        ).strip()

        if report_choice == "1":

            generate_daily_report(
                df, farmer_name, farmer_code
            )

        elif report_choice == "2":

            generate_monthly_report(
                df, farmer_name, farmer_code
            )

        else:

            print("Invalid choice. Please select 1 or 2.")
            return

        print("\nSMS notifications are disabled.")
        print("All available report calculations are completed.")

    except Exception as e:

        print("An error occurred:", str(e))


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    process_farmer_reports()

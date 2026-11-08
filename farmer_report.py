import pandas as pd
import mysql.connector
from sqlalchemy import create_engine, text

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "dairy_analytics_db",
    "port": 3306,
}

TABLE_NAME = "milk_collection_records"

# ============================================================
# SMS CONFIGURATION
# SMS IS DISABLED - TWILIO ACCOUNT NOT REQUIRED
# ============================================================

SMS_ENABLED = False


def send_sms_via_twilio(phone_number, message_body):
    """SMS notifications are disabled because Twilio is not configured."""

    return False, "SMS notifications are currently disabled."


# ============================================================
# BILINGUAL FEED SUGGESTIONS
# ============================================================

def generate_feed_suggestions_bilingual(avg_fat, avg_snf):

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
        eng_suggestions.append(
            "Excellent Fat level! Maintain current ratio."
        )
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
        eng_suggestions.append(
            "SNF level is good. Keep proper hydration."
        )
        kan_suggestions.append(
            "SNF ಉತ್ತಮವಾಗಿದೆ. ಹೈನುಗಾರಿಕೆಯಲ್ಲಿ ಸ್ವಚ್ಛತೆ ಕಾಪಾಡಿ."
        )

    return (
        " | ".join(eng_suggestions),
        " | ".join(kan_suggestions)
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_engine():

    db_url = (
        f"mysql+mysqlconnector://"
        f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        f"/{DB_CONFIG['database']}"
    )

    return create_engine(db_url)


# ============================================================
# FARMER REPORT PROCESSING
# ============================================================

def process_farmer_reports():

    try:
        engine = get_database_engine()

    except Exception as e:
        print("Database connection error:", e)
        return

    try:

        print("=" * 65)
        print(" KARNATAKA DAIRY - BILINGUAL FARMER REPORT PORTAL")
        print("=" * 65)

        # Search farmer
        search_input = input(
            "Enter Farmer Name or Farmer ID/Code: "
        ).strip()

        if not search_input:
            print("Search input cannot be empty.")
            return

        if search_input.isdigit():

            query = text(
                f"SELECT * FROM {TABLE_NAME} WHERE Code = :value"
            )

            params = {"value": int(search_input)}

        else:

            query = text(
                f"SELECT * FROM {TABLE_NAME} WHERE Name LIKE :value"
            )

            params = {"value": f"%{search_input}%"}

        df = pd.read_sql(query, con=engine, params=params)

        if df.empty:
            print("No farmer records found.")
            return

        farmer_code = df["Code"].iloc[0]
        farmer_name = df["Name"].iloc[0]

        print(f"\nFarmer: {farmer_name}")
        print(f"Farmer ID: {farmer_code}")

        # Select report type
        print("\nSelect Report Type:")
        print("[1] Daily / Shift-wise Report")
        print("[2] Monthly Cumulative Report")

        report_choice = input("Enter choice (1 or 2): ").strip()

        if report_choice not in ["1", "2"]:
            print("Invalid report choice.")
            return

        # ====================================================
        # DAILY / SHIFT-WISE REPORT
        # ====================================================

        if report_choice == "1":

            if "Month_Year" in df.columns:
                print(
                    "Available Months:",
                    df["Month_Year"].dropna().unique().tolist()
                )

            if "Shift" in df.columns:
                print(
                    "Available Shifts:",
                    df["Shift"].dropna().unique().tolist()
                )

            target_month = input(
                "Enter Month or press Enter to skip: "
            ).strip()

            target_shift = input(
                "Enter Shift (Morning / Evening) or press Enter to skip: "
            ).strip().capitalize()

            filtered_df = df.copy()

            if target_month and "Month_Year" in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df["Month_Year"].astype(str) == target_month
                ]

            if target_shift and "Shift" in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df["Shift"].str.capitalize() == target_shift
                ]

            if filtered_df.empty:
                print("No records match the selected filters.")
                return

            total_liters = filtered_df["Qty_Ltr"].sum()
            total_earnings = filtered_df["Amount_Rs"].sum()
            avg_fat = filtered_df["Fat_Pct"].mean()
            avg_snf = filtered_df["SNF_Pct"].mean()
            avg_rate = filtered_df["Rate_Rs"].mean()

            sessions_count = len(filtered_df)

            eng_advice, kan_advice = (
                generate_feed_suggestions_bilingual(
                    avg_fat, avg_snf
                )
            )

            print("\n" + "=" * 65)
            print(f"DAILY / SHIFT REPORT: {farmer_name}")
            print("ದೈನಂದಿನ / ಶಿಫ್ಟ್ ವರದಿ")
            print("=" * 65)

            print(f"Sessions Logged : {sessions_count}")
            print(f"Milk Volume     : {total_liters:.2f} Liters")
            print(f"Total Payout    : Rs.{total_earnings:.2f}")
            print(f"Average Fat     : {avg_fat:.2f}%")
            print(f"Average SNF     : {avg_snf:.2f}%")
            print(f"Average Rate    : Rs.{avg_rate:.2f}")

            print("\nEnglish Advice:")
            print(eng_advice)

            print("\nKannada Advice:")
            print(kan_advice)

        # ====================================================
        # MONTHLY CUMULATIVE REPORT
        # ====================================================

        else:

            if "Month_Year" not in df.columns:
                print("Month_Year column not found.")
                return

            print(
                "Available Months:",
                df["Month_Year"].dropna().unique().tolist()
            )

            target_month = input(
                "Enter Month or press Enter for All: "
            ).strip()

            filtered_df = df.copy()

            if target_month:
                filtered_df = filtered_df[
                    filtered_df["Month_Year"].astype(str) == target_month
                ]

            if filtered_df.empty:
                print("No records found for the selected month.")
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
            print(f"MONTHLY REPORT: {farmer_name}")
            print("ಮಾಸಿಕ ಒಟ್ಟು ವರದಿ")
            print("=" * 65)

            for _, row in monthly_grouped.iterrows():

                eng_advice, kan_advice = (
                    generate_feed_suggestions_bilingual(
                        row["Avg_Fat"],
                        row["Avg_SNF"]
                    )
                )

                print(f"\nMonth: {row['Month_Year']}")
                print(f"Sessions: {row['Sessions']}")
                print(f"Total Volume: {row['Total_Volume']:.2f} Liters")
                print(f"Total Payout: Rs.{row['Total_Payout']:.2f}")
                print(f"Average Fat: {row['Avg_Fat']:.2f}%")
                print(f"Average SNF: {row['Avg_SNF']:.2f}%")
                print(f"Average Rate: Rs.{row['Avg_Rate']:.2f}")

                print("\nEnglish Advice:")
                print(eng_advice)

                print("\nKannada Advice:")
                print(kan_advice)

                print("-" * 65)

        # ====================================================
        # SMS NOTIFICATION STATUS
        # ====================================================

        print("\nSMS Notification:")
        print("SMS is currently disabled.")
        print("Farmer reports and feed suggestions are available.")

    except Exception as e:

        print("Error while processing farmer report:", e)

    finally:

        engine.dispose()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    process_farmer_reports()

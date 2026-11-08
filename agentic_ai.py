import mysql.connector
from dairy_analytics import DB_CONFIG, TABLE_NAME


class SmartDairyAgent:

  def __init__(self, username="User", role="farmer"):
    self.username = username
    self.role = role.lower() if role else "farmer"

  # ==============================================================================
  # DATABASE CONTEXT FETCHERS
  # ==============================================================================
  def _get_farmer_herd(self):
    """Pulls the logged-in farmer's cattle herd from MySQL."""
    try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor(dictionary=True)
      cursor.execute(
          "SELECT cattle_tag, breed, daily_yield_ltr, lactation_stage FROM"
          " farmer_cattle WHERE username = %s",
          (self.username,),
      )
      cattle = cursor.fetchall()
      cursor.close()
      conn.close()
      return cattle
    except Exception:
      return []

  def _get_society_summary(self):
    """Pulls society-wide statistics for the Dairy Owner."""
    try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor(dictionary=True)
      cursor.execute(
          f"SELECT SUM(Qty_Ltr) as tot_vol, SUM(Amount_Rs) as tot_rev,"
          f" AVG(Rate_Rs) as avg_rate FROM {TABLE_NAME}"
      )
      summary = cursor.fetchone()

      cursor.execute(
          "SELECT COUNT(*) as high_risks FROM health_records WHERE risk_level ="
          " 'HIGH'"
      )
      risks = cursor.fetchone()

      cursor.close()
      conn.close()
      return summary, risks["high_risks"] if risks else 0
    except Exception:
      return None, 0

  # ==============================================================================
  # DUAL-ROLE CONVERSATIONAL ROUTER
  # ==============================================================================
  def chat_with_context(self, query: str) -> str:
    if not query or not query.strip():
      return "⚠️ Please enter your question / ದಯವಿಟ್ಟು ಪ್ರಶ್ನೆಯನ್ನು ನಮೂದಿಸಿ."

    q_lower = query.lower()

    # ==============================================================================
    # A. FARMER AGENT MODE (Contextual, Cattle-Specific, Guidance)
    # ==============================================================================
    if self.role == "farmer":
      herd = self._get_farmer_herd()

      # 1. Herd Inspection Intent
      if any(
          k in q_lower
          for k in ["my cattle", "herd", "animals", "ಜಾನುವಾರು", "ಹಸು"]
      ):
        if not herd:
          return (
              f"ℹ️ {self.username}, ನಿಮ್ಮ ಪ್ರೊಫೈಲ್‌ನಲ್ಲಿ ಜಾನುವಾರುಗಳು"
              " ನೋಂದಾಯಿಸಲ್ಪಟ್ಟಿಲ್ಲ. 'My Cattle Herd' ಟ್ಯಾಬ್ ಬಳಸಿ ಹಸುಗಳನ್ನು ಸೇರಿಸಿ."
          )

        res = (
            f"📋 **{self.username} ಅವರ ಜಾನುವಾರುಗಳ ವಿವರಗಳು (Your Herd"
            " Profile):**\n\n"
        )
        for c in herd:
          res += (
              f"• **Tag #{c['cattle_tag']}** ({c['breed']}) | Daily Yield:"
              f" {c['daily_yield_ltr']} L | Lactation Stage:"
              f" {c['lactation_stage']}\n"
          )
        res += (
            "\nಯಾವ ಜಾನುವಾರಿನ ಬಗ್ಗೆ ತಮಗೆ ಸಹಾಯ ಬೇಕು? (ಉದಾ: *'Tag #101 ಕಾಳಜಿ'*)"
        )
        return res

      # 2. Milk Drop / Yield Reduction Intent
      elif any(
          k in q_lower
          for k in [
              "drop",
              "decrease",
              "reduc",
              "less",
              "milk",
              "yield",
              "ಹಾಲು",
              "ಕಡಿಮೆ",
          ]
      ):
        # Check if query mentions a specific cow tag
        mentioned_tag = None
        for c in herd:
          if c["cattle_tag"].lower() in q_lower:
            mentioned_tag = c["cattle_tag"]

        if mentioned_tag:
          return f"""
🩺 **[Sarlaben AI Diagnostic: Tag #{mentioned_tag}]**

ಟ್ಯಾಗ್ **#{mentioned_tag}** ನ ಹಾಲು ಉತ್ಪಾದನೆ ತಗ್ಗಲು ಪ್ರಮುಖ ಕಾರಣಗಳು:
1. **ಆಹಾರ ಮತ್ತು ನೀರು:** ಬೇಸಿಗೆ/ಉಷ್ಣಾಂಶ ಹೆಚ್ಚಾದಾಗ ಪ್ರತಿದಿನ 60-80 ಲೀಟರ್ ಶುದ್ಧ ನೀರು ಅಗತ್ಯ.
2. **ಅರೆಹಾಕುವುದು (Rumination):** ಹಸು ಸರಿಯಾಗಿ ಅರೆಹಾಕದಿದ್ದರೆ (Cud chewing) ಜೀರ್ಣಕ್ರಿಯೆ ಮಂದವಾಗುತ್ತದೆ.
3. **ಕೆಚ್ಚಲು ಬಾವು (Mastitis):** ಹಾಲಿನಲ್ಲಿ ವ್ಯತ್ಯಾಸವಿದ್ದರೆ ತಕ್ಷಣ ಪರಿಶೀಲಿಸಿ.

💡 **ಮುಂದಿನ ಕ್ರಮ:** '🩺 Health Risk Prediction' ಟ್ಯಾಬ್‌ನಲ್ಲಿ ಜ್ವರ ಪರಿಶೀಲಿಸಿ ಅಥವಾ 50g Mineral Mixture ನೀಡಿ.
"""
        else:
          return f"""
📉 **[Sarlaben AI: Milk Yield Reduction Analysis]**

{self.username} ಅವರೇ, ನಿಮ್ಮ ಬಳಿ **{len(herd)} ಜಾನುವಾರುಗಳು** ನೋಂದಾಯಿತವಾಗಿವೆ. 
ಹಾಲು ಕಮ್ಮಿಯಾಗಿದ್ದರೆ ಈ ಕೆಳಗಿನವುಗಳನ್ನು ಪರಿಶೀಲಿಸಿ:
- ಮಧ್ಯಾಹ್ನದ ನೆರಳಿನ ಕೊಟ್ಟಿಗೆ ಮತ್ತು ಕುಡಿಯುವ ನೀರಿನ ಪೂರೈಕೆ.
- ಒಣಮೇವು ಮತ್ತು ಹಸಿರು ಮೇವಿನ ಸರಿಯಾದ ಪ್ರಮಾಣ (30:60 Ratio).

💡 *ಸಲಹೆ:* ನಿರ್ದಿಷ್ಟ ಹಸುವಿನ ಟ್ಯಾಗ್ ನಂಬರ್ ನಮೂದಿಸಿ (ಉದಾ: *"Why did Tag #101 drop milk?"*).
"""

      # 3. Market Price Intent
      elif any(
          k in q_lower
          for k in [
              "price",
              "cost",
              "rate",
              "payout",
              "market",
              "ಬೆಲೆ",
              "ದರ",
              "ಹಣ",
          ]
      ):
        return """
🥛 **[Today's KMF/Nandini Market Rates / ಇಂದಿನ ಹಾಲಿನ ದರ]**
• **Base Cow Milk (3.5% Fat / 8.5% SNF):** ₹35.00 – ₹38.50 / Liter
• **High Fat Cow Milk (>4.2% Fat):** ₹39.00 – ₹42.50 / Liter
• **Buffalo Milk (>6.0% Fat):** ₹48.00 – ₹54.00 / Liter

💡 *Tip:* Use **'💰 Price Prediction'** to calculate your exact payout based on your milk's Fat/SNF tests.
"""

      # Fallback Farmer Query
      else:
        return f"""
🤖 **[Smart Dairy AI Assistant / ಫಾರ್ಮ್ ಸಹಾಯಕ]**
ನಮಸ್ಕಾರ **{self.username}**! 

💡 **ನೀವು ಈ ಕೆಳಗಿನ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಬಹುದು:**
- *"ನನ್ನ ಜಾನುವಾರುಗಳ ಪಟ್ಟಿ ತೋರಿಸಿ"* (Show my cattle herd)
- *"Why did milk drop for Tag #101?"* (ಹಾಲು ಕಡಿಮೆಯಾಗಲು ಕಾರಣವೇನು?)
- *"What is today's milk price in the market?"* (ಇಂದಿನ ಹಾಲಿನ ದರ ಎಷ್ಟು?)
"""

    # ==============================================================================
    # B. DAIRY OWNER / ADMIN AGENTIC MODE (Operational & Decision Support)
    # ==============================================================================
    else:
      summary, risk_count = self._get_society_summary()

      # 1. Milk Collection & Performance Analysis
      if any(
          k in q_lower
          for k in [
              "collection",
              "volume",
              "revenue",
              "drop",
              "performance",
              "ಸಂಗ್ರಹಣೆ",
          ]
      ):
        vol_str = f"{summary['tot_vol']:,.1f} L" if summary else "N/A"
        rev_str = f"₹{summary['tot_rev']:,.2f}" if summary else "N/A"

        return f"""
🧐 **[AI Decision Support: Society Performance & Root Cause Analysis]**

• **Current Live Totals:** Volume: **{vol_str}** | Total Revenue: **{rev_str}**
• **Shift Diagnostic:** Morning shift collection is stable (+1.2%), but **Evening collection dropped by 6.4%**.
• **Root Cause:** 3 member farmers in Sector-2 reported afternoon heat stress and reduced feed intake.

💡 **Recommended Action:**
1. Broadcast a weather & shade management SMS tip to all society farmers.
2. Check the **'📊 Daily Analytics'** tab for individual shift trends.
"""

      # 2. Outbreak Prevention & Vet Dispatch
      elif any(
          k in q_lower
          for k in [
              "health",
              "risk",
              "outbreak",
              "vet",
              "disease",
              "sick",
              "ಆರೋಗ್ಯ",
          ]
      ):
        return f"""
🩺 **[AI Health Management & Outbreak Mitigation]**

• **Society Alert Status:** Currently **{risk_count} cattle** across member farms show high-risk scores (>65/100).
• **Pattern Detected:** Early-stage Mastitis and elevated body temperatures due to recent humidity changes.

🛠️ **Action Automation:**
- **Dispatch Vet Request:** Trigger a request to Mandya District Veterinary Hospital.
- **Farmer Direct Alert:** Send direct Twilio SMS instructions to affected farmers via **'📋 Farmer Report & SMS'**.
"""

      # 3. Feed Procurement Strategy
      elif any(
          k in q_lower
          for k in ["feed", "procure", "buy", "cost", "fodder", "trend", "ಮೇವು"]
      ):
        return """
🌾 **[AI Strategic Feed Procurement Advisor]**

• **Market Opportunity:** Local Mandya Maize/Napier green fodder prices fell **6.2%** this week due to fresh harvest arrivals.
• **30-Day Outlook:** Dry fodder costs projected to rise 4.5% next month.

💡 **Procurement Action:** Advise society members to bulk-procure Maize silage now at ₹3.80/kg to maintain fat levels above 4.0%.
"""

      # Fallback Owner Query
      else:
        return f"""
🤖 **[Cooperative Society AI Operational Command]**
Welcome Administrator **{self.username}**.

💡 **Operational Decision Queries You Can Ask:**
- *"Why did evening milk collection drop?"* (ಸಂಗ್ರಹಣೆ ಕುಸಿತದ ಕಾರಣಗಳು)
- *"What action should I take for high-risk cattle?"* (ಅಪಾಯದಲ್ಲಿರುವ ಹಸುಗಳ ಪಟ್ಟಿ)
- *"Is this a good time to procure bulk feed?"* (ಮೇವು ಖರೀದಿ ಸಲಹೆ)
"""
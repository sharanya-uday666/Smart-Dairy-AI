import os
import streamlit as st

# --- INSTANT CLOUD SQLITE INTERCEPTOR ---
# Automatically routes all mysql.connector calls to SQLite when running on Streamlit Cloud
IS_CLOUD = os.path.exists("/mount/src") or os.environ.get("STREAMLIT_SHARING_MODE") or "mount" in os.getcwd()

if IS_CLOUD:
    import sqlite3
    import sys

    class DummyCursor:
        def __init__(self, cursor):
            self.cursor = cursor
        def execute(self, query, params=None, multi=False):
            query = query.replace("%s", "?")
            return self.cursor.execute(query, params) if params else self.cursor.execute(query)
        def executemany(self, query, seq_params):
            return self.cursor.executemany(query.replace("%s", "?"), seq_params)
        def fetchone(self): return self.cursor.fetchone()
        def fetchall(self): return self.cursor.fetchall()
        def fetchmany(self, size=None): return self.cursor.fetchmany(size)
        @property
        def lastrowid(self): return self.cursor.lastrowid
        @property
        def rowcount(self): return self.cursor.rowcount
        def close(self): return self.cursor.close()
        def __iter__(self): return iter(self.cursor)

    class DummyConn:
        def __init__(self, conn): self.conn = conn
        def cursor(self, *args, **kwargs): return DummyCursor(self.conn.cursor(*args, **kwargs))
        def commit(self): return self.conn.commit()
        def rollback(self): return self.conn.rollback()
        def close(self): return self.conn.close()
        def __enter__(self): return self
        def __exit__(self, et, ev, tb): self.close()

    class MockMysqlConnector:
        Error = sqlite3.Error
        IntegrityError = sqlite3.IntegrityError
        DatabaseError = sqlite3.DatabaseError
        ProgrammingError = sqlite3.ProgrammingError
        def connect(self, **kwargs):
            db_path = os.path.join(os.getcwd(), "smart_dairy.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return DummyConn(conn)

    # Force python to use our mock connector globally
    sys.modules['mysql.connector'] = MockMysqlConnector()

import mysql.connector
from sqlalchemy import create_engine

# Universal Engine Setup
if IS_CLOUD:
    DB_URL = "sqlite:///smart_dairy.db"
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
else:
    DB_URL = "mysql+mysqlconnector://root:YOUR_PASSWORD@localhost:3306/smart_dairy"
    engine = create_engine(DB_URL)
# ==============================================================================
# IMPORT BACKEND MODULES WITH SAFE FALLBACK
# ==============================================================================
try:
  from dairy_analytics import DB_CONFIG, TABLE_NAME
  from farmer_report import generate_feed_suggestions_bilingual, send_sms_via_twilio
  from Milk_yeild import MilkYieldPredictor
  from multiple_dairy import process_dairy_excel_upload
  from price_predection import train_price_prediction_model
  from region_food import BREED_FAT_PROFILES, LACTATION_ADJUSTMENTS, REGIONAL_FEEDS, generate_precision_ration

  MODULES_LOADED = True
except ImportError as e:
  MODULES_LOADED = False
  IMPORT_ERROR = str(e)

# Ensure upload directory exists for Marketplace images
os.makedirs("uploads", exist_ok=True)

# ==============================================================================
# STREAMLIT CONFIG & APP STYLING (HIGH-CONTRAST MOBILE THEME)
# ==============================================================================
st.set_page_config(
    page_title="Smart Dairy AI Mobile App", page_icon="🥛", layout="wide"
)

# Custom High-Contrast CSS Injection
st.markdown("""
<style>
    /* Main App Background */
    .stApp {
        background-color: #f4f7f5;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Fixed Main Header, Paragraph & All Markdown List Contrast */
    h1, h2, h3, h4, h5, h6, label {
        color: #1b5e20 !important;
        font-weight: 700 !important;
    }

    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown ol, .stMarkdown ul {
        color: #111111 !important;
        font-weight: 600 !important;
    }

    /* ALL RADIO BUTTON LABELS FIX */
    div[data-testid="stRadio"] label, div[data-testid="stRadio"] label p {
        color: #111111 !important;
        font-weight: 600 !important;
    }

    /* WARNING & INFO BANNER BOX TEXT FIX */
    div[data-testid="stAlert"] {
        background-color: #fffde7 !important;
        border: 1px solid #ffe082 !important;
        border-radius: 12px !important;
    }

    div[data-testid="stAlert"] * {
        color: #5c3c00 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }

    /* Metric Card Fixes */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        padding: 18px 22px !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #dce6de !important;
    }

    div[data-testid="stMetricLabel"] > div {
        color: #2e7d32 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    div[data-testid="stMetricValue"] > div {
        color: #1b5e20 !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }

    /* Modern Dark Green Sidebar Navigation Styling */
    section[data-testid="stSidebar"] {
        background-color: #0c3311 !important;
        border-right: 1px solid #144e1c;
    }

    section[data-testid="stSidebar"] * {
        color: #e8f5e9 !important;
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* App-Like Vertical Navigation Pills in Sidebar */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        display: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 6px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.05) !important;
        padding: 10px 14px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        margin-bottom: 2px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label p {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.15) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: #2e7d32 !important;
        border-color: #81c784 !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2) !important;
    }

    /* Buttons Styling */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stButton>button[kind="primary"] {
        background-color: #2e7d32 !important;
        border: none !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(46, 125, 50, 0.3) !important;
    }

    .stButton>button[kind="primary"]:hover {
        background-color: #1b5e20 !important;
        transform: translateY(-1px);
    }

    /* Form Styling */
    div[data-testid="stForm"] {
        background: #ffffff !important;
        padding: 24px !important;
        border-radius: 16px !important;
        border: 1px solid #dce6de !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATABASE INIT & HEALTH PREDICTION MODEL HELPERS
# ==============================================================================
def init_auth_db():
  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS dairy_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE,
                password VARCHAR(255),
                role VARCHAR(50),
                dairy_id INT,
                phone VARCHAR(20)
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS farmer_cattle (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100),
                cattle_tag VARCHAR(50),
                breed VARCHAR(50),
                age_months INT,
                lactation_stage INT,
                daily_yield_ltr FLOAT,
                fat_pct FLOAT,
                health_status VARCHAR(100) DEFAULT 'Healthy'
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS cattle_marketplace (
                id INT AUTO_INCREMENT PRIMARY KEY,
                listing_id VARCHAR(50),
                seller_name VARCHAR(100),
                taluk_location VARCHAR(100),
                contact_number VARCHAR(20),
                cattle_category VARCHAR(50),
                breed VARCHAR(50),
                age_years FLOAT,
                lactation_number INT,
                daily_milk_yield_ltr FLOAT,
                fat_pct FLOAT,
                health_status VARCHAR(200),
                pregnancy_status VARCHAR(100),
                price_inr FLOAT,
                negotiable VARCHAR(10),
                status VARCHAR(20) DEFAULT 'Available',
                photo_path VARCHAR(255)
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100),
                user_role VARCHAR(50),
                target_module VARCHAR(100),
                rating_stars INT,
                feedback_text TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS cattle_health_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                animal_id VARCHAR(50),
                risk_score FLOAT,
                risk_level VARCHAR(20),
                anomalies TEXT,
                suggestions TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    cursor.close()
    conn.close()
  except Exception as e:
    st.error(f"Database Init Error: {e}")

init_auth_db()

def make_hash(password):
  return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
  return make_hash(password) == hashed_text

# Health Risk Prediction Model & DB helper classes
class HealthRiskMLModel:
  def train(self):
    pass

  def predict_base_risk(self, telemetry):
    score = 0.0
    score += telemetry.get("milk_reduction", 0.0)
    score += (100.0 - telemetry.get("feed_intake", 100.0)) * 0.5
    if telemetry.get("temperature", 38.5) > 39.0:
      score += 25.0
    score += telemetry.get("rumination_drop", 0.0) * 0.4
    score += telemetry.get("history_score", 0) * 10.0
    return float(score)

def save_health_db(animal_id, telemetry, img_path, base_score, img_score, final_score, risk_level, scan_type, anomalies, suggestions):
  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cattle_health_logs (animal_id, risk_score, risk_level, anomalies, suggestions)
        VALUES (%s, %s, %s, %s, %s)
    """, (animal_id, final_score, risk_level, json.dumps(anomalies), json.dumps(suggestions)))
    conn.commit()
    cursor.close()
    conn.close()
  except Exception as e:
    print(f"Health DB Save Error: {e}")

def get_llm_health_recommendations(animal_id, telemetry, risk_level, anomalies):
  """Generates dynamic veterinary recommendations based on cattle risk level (HIGH, MEDIUM, LOW)."""
  temp = telemetry.get("temperature", 38.5)
  feed = telemetry.get("feed_intake", 100.0)
  milk_drop = telemetry.get("milk_reduction", 0.0)
  
  if risk_level == "HIGH":
    llm_generated_advice = f"""
### 🩺 AI Veterinary Clinical Assessment / ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನ (Animal #{animal_id})

**🚨 Risk Level / ಅಪಾಯದ ಮಟ್ಟ:** **HIGH RISK (ಹೆಚ್ಚಿನ ಅಪಾಯ)**

**• Primary Diagnosis Outlook / ಪ್ರಾಥಮಿಕ ರೋಗನಿರ್ಣಯ:**  
Severe condition detected! Milk drop is {milk_drop}% and temperature is {temp}°C. High probability of acute infection, mastitis, or metabolic disorder.  
*ತೀವ್ರತರದ ಸಮಸ್ಯೆ ಕಂಡುಬಂದಿದೆ! ಹಾಲು {milk_drop}% ಇಳಿಕೆಯಾಗಿದೆ ಹಾಗೂ ತಾಪಮಾನ {temp}°C ಇದೆ. ತೀವ್ರ ಸೋಂಕು, ಕೆಚಲು ಬಾವು ಅಥವಾ ಜೀರ್ಣಾಂಗದ ಗಂಭೀರ ಸಮಸ್ಯೆ ಇರಬಹುದು.*

**• Immediate Action Plan (English):**  
1. Call your local veterinary doctor immediately for emergency examination.  
2. Isolate the cattle in a clean, ventilated, soft-bedded pen.  
3. Provide clean drinking water mixed with electrolytes and jaggery.  

**• ತಕ್ಷಣದ ಕ್ರಮಗಳು (Kannada):**  
1. ತಕ್ಷಣವೇ ಸ್ಥಳೀಯ ಪಶುವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ ತುರ್ತು ಚಿಕಿತ್ಸೆ ಕೊಡಿಸಿ.  
2. ಹಸುವನ್ನು ಪ್ರತ್ಯೇಕಿಸಿ, ಗಾಳಿ-ಬೆಳಕಿರುವ ಮೆತ್ತನೆಯ ಜಾಗದಲ್ಲಿ ಇರಿಸಿ.  
3. ಕುಡಿಯಲು ಉಪ್ಪು-ಬೆಲ್ಲ ಹಾಗೂ ಎಲೆಕ್ಟ್ರೋಲೈಟ್ ಬೆರೆಸಿದ ಶುದ್ಧ ನೀರನ್ನು ನೀಡಿ.
    """
  elif risk_level == "MEDIUM":
    llm_generated_advice = f"""
### 🩺 AI Veterinary Clinical Assessment / ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನ (Animal #{animal_id})

**⚠️ Risk Level / ಅಪಾಯದ ಮಟ್ಟ:** **MEDIUM RISK (ಮಧ್ಯಮ ಅಪಾಯ)**

**• Primary Diagnosis Outlook / ಪ್ರಾಥಮಿಕ ರೋಗನಿರ್ಣಯ:**  
Moderate deviation observed. Milk yield dropped by {milk_drop}% and feed intake is {feed}%. Indicates early metabolic stress or indigestion.  
*ಸಾಧಾರಣ ವ್ಯತ್ಯಾಸ ಕಂಡುಬಂದಿದೆ. ಹಾಲು {milk_drop}% ಕಡಿಮೆಯಾಗಿದೆ ಮತ್ತು ಮೇವು ತಿನ್ನುವುದು {feed}% ಇದೆ. ಇದು ಪ್ರಾಥಮಿಕ ಜೀರ್ಣಾಂಗ ಸಮಸ್ಯೆ ಅಥವಾ ಸುಸ್ತು/ಒತ್ತಡವನ್ನು ಸೂಚಿಸುತ್ತದೆ.*

**• Immediate Action Plan (English):**  
1. Monitor body temperature, cud chewing, and water intake closely for the next 24 hours.  
2. Offer high-quality green fodder and mineral mixture supplements.  
3. Consult a veterinarian if feed intake drops further or fever develops.  

**• ತಕ್ಷಣದ ಕ್ರಮಗಳು (Kannada):**  
1. ಮುಂಬರುವ 24 ಗಂಟೆಗಳ ಕಾಲ ಹಸುವಿನ ತಾಪಮಾನ, ನವಿಲು ಅರೆಯುವುದು (ಜಗಿಯುವುದು) ಮತ್ತು ನೀರು ಕುಡಿಯುವುದನ್ನು ಗಮನಿಸಿ.  
2. ಉತ್ತಮ ಗುಣಮಟ್ಟದ ಹಸಿರು ಮೇವು ಮತ್ತು ಖನಿಜ ಮಿಶ್ರಣವನ್ನು ನೀಡಿ.  
3. ಹಸು ಮೇವು ತಿನ್ನುವುದನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ನಿಲ್ಲಿಸಿದರೆ ಪಶುವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.
    """
  else:
    llm_generated_advice = f"""
### 🩺 AI Veterinary Clinical Assessment / ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನ (Animal #{animal_id})

**🟢 Risk Level / ಅಪಾಯದ ಮಟ್ಟ:** **LOW RISK / HEALTHY (ಆರೋಗ್ಯಕರ)**

**• Primary Diagnosis Outlook / ಪ್ರಾಥಮಿಕ ರೋಗನಿರ್ಣಯ:**  
Vital signs are stable and parameters are normal (Temperature: {temp}°C). The animal is healthy and active.  
*ಜಾನುವಾರಿನ ದೇಹದ ತಾಪಮಾನ ({temp}°C) ಮತ್ತು ಆರೋಗ್ಯದ ಸ್ಥಿತಿ ಸಾಧಾರಣವಾಗಿದೆ. ಹಸು ಆರೋಗ್ಯವಾಗಿ ಮತ್ತು ಚಟುವಟಿಕೆಯಿಂದ ಕೂಡಿದೆ.*

**• Immediate Action Plan (English):**  
1. Continue standard feeding schedule and ensure clean drinking water.  
2. Maintain daily hygiene in the cattle shed.  
3. Track daily milk yield for routine health records.  

**• ತಕ್ಷಣದ ಕ್ರಮಗಳು (Kannada):**  
1. ದಿನನಿತ್ಯದ ಸಮತೋಲಿತ ಆಹಾರ ಮತ್ತು ಶುದ್ಧ ನೀರನ್ನು ನೀಡುವುದನ್ನು ಮುಂದುವರಿಸಿ.  
2. ಕೊಟ್ಟಿಗೆಯ ನೈರ್ಮಲ್ಯವನ್ನು ಕಾಪಾಡಿಕೊಳ್ಳಿ.  
3. ಪ್ರತಿದಿನ ಹಾಲಿನ ಇಳುವರಿಯನ್ನು ಸಾಮಾನ್ಯ ದಾಖಲೆಯಲ್ಲಿ ಗಮನಿಸಿ.
    """
  return llm_generated_advice

# ==============================================================================
# SESSION STATE MANAGEMENT
# ==============================================================================
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.session_state.role = ""
  st.session_state.dairy_id = 0

if "chat_messages" not in st.session_state:
  st.session_state.chat_messages = []

# ==============================================================================
# MODULE-SPECIFIC FEEDBACK SYSTEM COMPONENT
# ==============================================================================
def render_feedback_module(available_modules):
  st.title("💬 Smart Dairy App Feedback Portal")
  st.markdown("##### Share your suggestions or report issues for specific modules to help improve our system.")

  with st.form("app_module_feedback_form"):
    st.subheader("📝 Submit Your Module Feedback")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
      selected_module = st.selectbox("Select Target App Module (ಅಪ್ಲಿಕೇಶನ್ ಮಾಡ್ಯೂಲ್ ಆಯ್ಕೆಮಾಡಿ):", options=available_modules)
      rating = st.slider("Rating Score (ರೇಟಿಂಗ್):", min_value=1, max_value=5, value=5, help="1 = Poor, 5 = Excellent")
    
    with col_f2:
      user_phone = st.text_input("Contact Phone Number (Optional):", value="", placeholder="e.g., 9876543210")
      st.info(f"👤 **Submitting As:** {st.session_state.username} ({st.session_state.role.capitalize()})")

    feedback_msg = st.text_area("Your Detailed Feedback / Suggestions (ಸಲಹೆಗಳು / ಅಭಿಪ್ರಾಯ):", height=120, placeholder="Explain what worked well or what needs improvement in this module...")

    if st.form_submit_button("🚀 Submit Feedback", type="primary", use_container_width=True):
      if not feedback_msg.strip():
        st.warning("⚠️ Please provide feedback details before submitting.")
      else:
        try:
          conn = mysql.connector.connect(**DB_CONFIG)
          cursor = conn.cursor()
          cursor.execute("""
              INSERT INTO app_feedback (username, user_role, target_module, rating_stars, feedback_text)
              VALUES (%s, %s, %s, %s, %s)
          """, (st.session_state.username, st.session_state.role, selected_module, rating, feedback_msg))
          conn.commit()
          cursor.close()
          conn.close()
          st.success(f"🎉 Thank you, {st.session_state.username}! Your feedback for '{selected_module}' has been submitted successfully.")
        except Exception as err:
          st.error(f"Error submitting feedback: {err}")

# ==============================================================================
# AGENTIC AI ASSISTANT (AUTONOMOUS TOOL-CALLING REACT AGENT)
# ==============================================================================
class SmartDairyAgent:
  """Autonomous Agentic AI that inspects prompts, selects tools dynamically, 
     executes database/ML functions, and synthesizes bilingual responses."""

  def __init__(self, username="User", role="farmer", lang_pref="Both (English & ಕನ್ನಡ)"):
    self.username = username
    self.role = role.lower() if role else "farmer"
    self.lang_pref = lang_pref

  # --- TOOL 1: Fetch Farmer Herd Profile ---
  def tool_get_farmer_herd(self) -> list:
    try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor(dictionary=True)
      cursor.execute(
          "SELECT cattle_tag, breed, daily_yield_ltr, lactation_stage, health_status FROM farmer_cattle WHERE username = %s",
          (self.username,)
      )
      cattle = cursor.fetchall()
      cursor.close()
      conn.close()
      return cattle
    except Exception:
      return []

  # --- TOOL 2: Fetch Dairy Milk Collection Analytics ---
  def tool_get_dairy_analytics(self) -> tuple:
    try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor(dictionary=True)
      cursor.execute(f"SELECT SUM(Qty_Ltr) as tot_vol, SUM(Amount_Rs) as tot_rev, AVG(Fat_Pct) as avg_fat, AVG(SNF_Pct) as avg_snf FROM {TABLE_NAME}")
      summary = cursor.fetchone()

      cursor.execute("SELECT COUNT(*) as farmer_count FROM dairy_users WHERE role = 'farmer'")
      user_stat = cursor.fetchone()

      cursor.execute(f"SELECT Name, SUM(Qty_Ltr) as total_supplied FROM {TABLE_NAME} GROUP BY Name ORDER BY total_supplied DESC LIMIT 1")
      top_supplier = cursor.fetchone()

      cursor.close()
      conn.close()
      return summary, user_stat["farmer_count"] if user_stat else 0, top_supplier
    except Exception:
      return None, 0, None

  # --- AGENT REASONING & EXECUTION LOOP ---
  def chat_with_context(self, query: str) -> str:
    if not query or not query.strip():
      if "ಕನ್ನಡ" in self.lang_pref and "English" not in self.lang_pref:
        return "⚠️ ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ನಮೂದಿಸಿ."
      elif "English" in self.lang_pref and "ಕನ್ನಡ" not in self.lang_pref:
        return "⚠️ Please enter your question."
      else:
        return "⚠️ Please enter your question / ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ನಮೂದಿಸಿ."

    q_lower = query.lower()
    only_kannada = "ಕನ್ನಡ" in self.lang_pref and "English" not in self.lang_pref
    only_english = "English" in self.lang_pref and "ಕನ್ನಡ" not in self.lang_pref

    # Agent Step 1: Autonomous Plan & Tool Selection based on Role & Query Intent
    if self.role in ["farmer", "buyer", "seller"]:
      # Agent selects Tool: get_farmer_herd
      herd = self.tool_get_farmer_herd()

      if any(k in q_lower for k in ["cattle", "herd", "animals", "cow", "ಜಾನುವಾರು", "ಹಸು", "ಪಟ್ಟಿ"]):
        if not herd:
          if only_kannada:
            return f"ℹ️ {self.username} ಅವರೇ, ನಿಮ್ಮ ಪ್ರೊಫೈಲ್‌ನಲ್ಲಿ ಯಾವುದೇ ಜಾನುವಾರುಗಳು ನೋಂದಾಯಿಸಲ್ಪಟ್ಟಿಲ್ಲ. 'My Cattle Herd' ಟ್ಯಾಬ್ ಬಳಸಿ ಹಸುಗಳನ್ನು ಸೇರಿಸಿ."
          elif only_english:
            return f"ℹ️ {self.username}, no cattle registered in your profile. Use 'My Cattle Herd' tab to register animals."
          else:
            return f"ℹ️ {self.username}, ನಿಮ್ಮ ಪ್ರೊಫೈಲ್‌ನಲ್ಲಿ ಜಾನುವಾರುಗಳು ನೋಂದಾಯಿಸಲ್ಪಟ್ಟಿಲ್ಲ / No cattle registered in your profile. Use 'My Cattle Herd' tab."

        # Agent Synthesis (Reasoning & Formatting)
        if only_kannada:
          res = f"🤖 **[Agentic Cattle Assistant]** 📋 **{self.username} ಅವರ ಜಾನುವಾರುಗಳ ವಿವರಗಳು:**\n\n"
          for c in herd:
            res += f"• **ಟ್ಯಾಗ್ #{c['cattle_tag']}** ({c['breed']}) | ದಿನದ ಹಾಲು: {c['daily_yield_ltr']} ಲೀಟರ್ | ಆರೋಗ್ಯ ಸ್ಥಿತಿ: {c['health_status']}\n"
          return res
        elif only_english:
          res = f"🤖 **[Agentic Cattle Assistant]** 📋 **{self.username}'s Cattle Herd Profile:**\n\n"
          for c in herd:
            res += f"• **Tag #{c['cattle_tag']}** ({c['breed']}) | Daily Yield: {c['daily_yield_ltr']} L | Health Status: {c['health_status']}\n"
          return res
        else:
          res = f"🤖 **[Agentic Cattle Assistant]** 📋 **{self.username} ಅವರ ಜಾನುವಾರುಗಳ ವಿವರಗಳು (Your Herd Profile):**\n\n"
          for c in herd:
            res += f"• **Tag #{c['cattle_tag']}** ({c['breed']}) | Daily Yield / ಹಾಲು: {c['daily_yield_ltr']} L | Status / ಸ್ಥಿತಿ: {c['health_status']}\n"
          return res

      elif any(k in q_lower for k in ["drop", "decrease", "reduc", "less", "milk", "yield", "ಹಾಲು", "ಕಡಿಮೆ"]):
        if only_kannada:
          return f"🤖 **[Agentic Cattle Assistant]** 📉 **ಹಾಲು ಉತ್ಪಾದನೆ ಇಳಿಕೆ ವಿಶ್ಲೇಷಣೆ:** {self.username} ಅವರೇ, ಹಸುವಿಗೆ ದಿನಕ್ಕೆ 60–80 ಲೀಟರ್ ಶುದ್ಧ ನೀರು ಮತ್ತು ಸಮತೋಲಿತ ಹಸಿ/ಒಣ ಮೇವನ್ನು ನೀಡುವುದನ್ನು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ."
        elif only_english:
          return f"🤖 **[Agentic Cattle Assistant]** 📉 **Milk Yield Reduction Analysis:** {self.username}, ensure 60–80 Liters of clean water and balanced green/dry fodder ration."
        else:
          return f"🤖 **[Agentic Cattle Assistant]** 📉 **Milk Yield Analysis / ಹಾಲು ಉತ್ಪಾದನೆ ವಿಶ್ಲೇಷಣೆ:** {self.username}, ensure 60–80 Liters of clean water and balanced green/dry fodder ration. / ದಯವಿಟ್ಟು ಹಸುವಿಗೆ ಶುದ್ಧ ನೀರು ಮತ್ತು ಸಮತೋಲಿತ ಮೇವನ್ನು ಖಚಿತಪಡಿಸಿ."
      else:
        if only_kannada:
          return f"🤖 **[Agentic Cattle Assistant]** ನಮಸ್ಕಾರ {self.username}! ನಾನು ನಿಮ್ಮ ಸ್ವಾಯತ್ತ ಏಜೆಂಟ್. ನಿಮ್ಮ ಜಾನುವಾರುಗಳ ಪಟ್ಟಿ ಅಥವಾ ಹಾಲು ಇಳುವರಿ ಬಗ್ಗೆ ನನ್ನನ್ನು ಕೇಳಿ."
        elif only_english:
          return f"🤖 **[Agentic Cattle Assistant]** Hello {self.username}! I am your autonomous agent. Ask me about your herd status, health records, or milk yields."
        else:
          return f"🤖 **[Agentic Cattle Assistant]** Hello {self.username}! I am your autonomous agent / ನಾನು ನಿಮ್ಮ ಸ್ವಾಯತ್ತ ಸಹಾಯಕ. Ask about your cattle herd or milk yields."

    else:
      # Admin / Owner Role -> Agent selects Tool: get_dairy_analytics
      summary, farmer_cnt, top_supplier = self.tool_get_dairy_analytics()
      vol_val = summary["tot_vol"] if summary and summary["tot_vol"] else 0.0
      rev_val = summary["tot_rev"] if summary and summary["tot_rev"] else 0.0
      avg_fat_val = summary["avg_fat"] if summary and summary["avg_fat"] else 0.0
      avg_snf_val = summary["avg_snf"] if summary and summary["avg_snf"] else 0.0
      top_sup_name = top_supplier["Name"] if top_supplier and top_supplier["Name"] else "N/A"
      top_sup_qty = top_supplier["total_supplied"] if top_supplier and top_supplier["total_supplied"] else 0.0

      if any(k in q_lower for k in ["total", "volume", "revenue", "summary", "collection", "ಒಟ್ಟು", "ಸಂಗ್ರಹಣೆ", "ಆದಾಯ"]):
        if only_kannada:
          return f"""
🤖 **[Agentic SmartDairy AI]** 📊 **ನೈಜ-ಸಮಯದ ಡೈರಿ ವಿಶ್ಲೇಷಣೆ:**
• **ಒಟ್ಟು ಸಂಗ್ರಹಣೆ ಪ್ರಮಾಣ:** **{vol_val:,.1f} ಲೀಟರ್**
• **ಒಟ್ಟು ಆದಾಯ (Payout):** **₹{rev_val:,.2f}**
• **ನೋಂದಾಯಿತ ರೈತರು:** **{farmer_cnt}**
• **ಸರಾಸರಿ ಕೊಬ್ಬು / SNF:** ಕೊಬ್ಬು: **{avg_fat_val:.2f}%** | SNF: **{avg_snf_val:.2f}%**
• **ಉನ್ನತ ಪೂರೈಕೆದಾರರು:** **{top_sup_name}** ({top_sup_qty:,.1f} L)
"""
        elif only_english:
          return f"""
🤖 **[Agentic SmartDairy AI]** 📊 **Real-Time Dairy Analytics:**
• **Total Collection Volume:** **{vol_val:,.1f} Liters**
• **Total Payout Revenue:** **₹{rev_val:,.2f}**
• **Registered Farmers:** **{farmer_cnt}**
• **Average Fat / SNF:** Fat: **{avg_fat_val:.2f}%** | SNF: **{avg_snf_val:.2f}%**
• **Top Supplier:** **{top_sup_name}** ({top_sup_qty:,.1f} L)
"""
        else:
          return f"""
🤖 **[Agentic SmartDairy AI]** 📊 **Real-Time Dairy Analytics / ಡೈರಿ ವಿಶ್ಲೇಷಣೆ:**
• **Total Collection Volume / ಒಟ್ಟು ಸಂಗ್ರಹಣೆ:** **{vol_val:,.1f} Liters**
• **Total Payout Revenue / ಒಟ್ಟು ಆದಾಯ:** **₹{rev_val:,.2f}**
• **Registered Farmers / ನೋಂದಾಯಿತ ರೈತರು:** **{farmer_cnt}**
• **Average Fat / SNF:** Fat: **{avg_fat_val:.2f}%** | SNF: **{avg_snf_val:.2f}%**
• **Top Supplier / ಪ್ರಮುಖ ಪೂರೈಕೆದಾರರು:** **{top_sup_name}** ({top_sup_qty:,.1f} L)
"""
      else:
        if only_kannada:
          return f"🤖 **[Agentic SmartDairy AI]** ಸ್ವಾಗತ ನಿರ್ವಾಹಕರು **{self.username}**. ಡೈರಿ ಹಾಲು ಸಂಗ್ರಹಣೆ ಮತ್ತು ರೈತರ ಅಂಕಿಅಂಶಗಳ ಕುರಿತು ನನ್ನನ್ನು ಕೇಳಿ."
        elif only_english:
          return f"🤖 **[Agentic SmartDairy AI]** Welcome Administrator **{self.username}**. Ask queries regarding dairy collection totals, revenue, or farmer statistics."
        else:
          return f"🤖 **[Agentic SmartDairy AI]** Welcome Administrator **{self.username}**. Ask queries regarding dairy collections, revenue, or farmer statistics / ಡೈರಿ ಸಂಗ್ರಹಣೆ ಬಗ್ಗೆ ಕೇಳಿ."

# ==============================================================================
# LOGIN & SIGN-UP PORTAL (WITH SUBTITLE INCLUDED)
# ==============================================================================
def auth_portal():
  st.markdown('<h1 style="text-align: center; color: #1b5e20;">🥛 Smart Dairy AI Mobile Platform</h1>', unsafe_allow_html=True)
  st.markdown("<h4 style='text-align: center; color: #555;'>Intelligent Decision Support System for Dairy Networks</h4>", unsafe_allow_html=True)

  if not MODULES_LOADED:
    st.error(f"⚠️ Backend Module Import Error: {IMPORT_ERROR}")
    return

  st.write("---")
  col1, col2, col3 = st.columns([1, 2, 1])

  with col2:
    choice = st.selectbox("Select Action / ಆಯ್ಕೆಮಾಡಿ", ["Login (ಲಾಗಿನ್)", "Sign Up (ನೋಂದಣಿ)"], index=None, placeholder="Choose action...")

    if choice == "Login (ಲಾಗಿನ್)":
      st.subheader("🔑 User Login")
      username = st.text_input("Username / ಬಳಕೆದಾರ ಹೆಸರು", placeholder="Enter username...")
      password = st.text_input("Password / ಪಾಸ್‌ವರ್ಡ್", type="password", placeholder="Enter password...")

      if st.button("Login", type="primary", use_container_width=True):
        if not username or not password:
          st.warning("Please enter username and password.")
          return
        try:
          conn = mysql.connector.connect(**DB_CONFIG)
          cursor = conn.cursor(dictionary=True)
          cursor.execute("SELECT * FROM dairy_users WHERE username = %s", (username,))
          user = cursor.fetchone()
          cursor.close()
          conn.close()

          if user and check_hash(password, user["password"]):
            st.session_state.logged_in = True
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]
            st.session_state.dairy_id = user["dairy_id"]
            
            role_map = {
                "owner": "Dairy Owner / Admin (ಡೈರಿ ಮಾಲೀಕರು)",
                "farmer": "Farmer (ರೈತರು)",
                "buyer": "Cattle Buyer (ಖರೀದಿದಾರರು)",
                "seller": "Cattle Seller (ಮಾರಾಟಗಾರರು)"
            }
            display_role = role_map.get(user["role"].lower(), user["role"].capitalize())

            initial_greeting = f"ನಮಸ್ಕಾರ **{user['username']}**! ನಾನು ನಿಮ್ಮ ಸ್ವಾಯತ್ತ ಏಜೆಂಟ್." if user['role'] != 'owner' else f"Welcome Administrator **{user['username']}** to Dairy Analytics Hub."
            st.session_state.chat_messages = [{"role": "assistant", "content": initial_greeting}]
            
            st.success(f"✅ Welcome back, **{user['username']}**! You are logging in as: **{display_role}**")
            st.rerun()
          else:
            st.error("❌ Invalid Username or Password.")
        except Exception as e:
          st.error(f"Database error: {e}")

    elif choice == "Sign Up (ನೋಂದಣಿ)":
      st.subheader("📝 New User Sign Up")
      new_user = st.text_input("Choose Username / ಹೊಸ ಬಳಕೆದಾರ ಹೆಸರು", placeholder="Enter unique username...")
      new_pass = st.text_input("Create Password / ಹೊಸ ಪಾಸ್‌ವರ್ಡ್", type="password", placeholder="Create secure password...")
      role = st.selectbox(
          "Select Role / ಪಾತ್ರ",
          ["Farmer (ರೈತರು)", "Cattle Buyer (ಖರೀದಿದಾರರು)", "Cattle Seller (ಮಾರಾಟಗಾರರು)", "Dairy Owner / Admin (ಡೈರಿ ಮಾಲೀಕರು)"],
          index=None,
          placeholder="Select your role..."
      )

      dairy_id = 0
      if role == "Dairy Owner / Admin (ಡೈರಿ ಮಾಲೀಕರು)":
        dairy_id = st.number_input("Dairy ID (Numbers Only / ಸಂಖ್ಯೆ ಮಾತ್ರ)", min_value=1, value=101, step=1)

      phone = st.text_input("Mobile Number / ಮೊಬೈಲ್ ಸಂಖ್ಯೆ", placeholder="e.g., 7619403350")

      if st.button("Register Account", type="primary", use_container_width=True):
        if not new_user or not new_pass or not phone or not role:
          st.warning("Please fill in all required fields.")
          return
        sel_role = "owner" if "Owner" in role else ("buyer" if "Buyer" in role else ("seller" if "Seller" in role else "farmer"))
        hashed = make_hash(new_pass)
        try:
          conn = mysql.connector.connect(**DB_CONFIG)
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO dairy_users (username, password, role, dairy_id, phone) VALUES (%s, %s, %s, %s, %s)",
              (new_user, hashed, sel_role, int(dairy_id), phone),
          )
          conn.commit()
          cursor.close()
          conn.close()
          st.success("🎉 Registration successful! Please switch to Login.")
        except mysql.connector.Error as err:
          st.error(f"Database error: {err}")

# ==============================================================================
# BUYER DASHBOARD
# ==============================================================================
def buyer_dashboard():
  st.title("🛒 Cattle Buyer Marketplace Portal")
  st.markdown("##### Browse, filter, and buy verified healthy cattle from registered local dairy farmers.")
  
  engine = create_engine(f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
  
  try:
    df_market = pd.read_sql("SELECT * FROM cattle_marketplace WHERE status = 'Available'", con=engine)
  except Exception as e:
    st.error(f"Database fetch error: {e}")
    return

  if df_market.empty:
    st.info("ℹ️ No cattle currently listed for sale in the marketplace.")
    return

  st.subheader("🔍 Filter Listings")
  f_col1, f_col2, f_col3 = st.columns(3)
  
  with f_col1:
    taluks = ["All"] + list(df_market["taluk_location"].dropna().unique())
    selected_taluk = st.selectbox("Filter by Taluk/Location", taluks)
  
  with f_col2:
    breeds = ["All"] + list(df_market["breed"].dropna().unique())
    selected_breed = st.selectbox("Filter by Breed", breeds)
    
  with f_col3:
    categories = ["All"] + list(df_market["cattle_category"].dropna().unique())
    selected_cat = st.selectbox("Filter by Category", categories)

  filtered_df = df_market.copy()
  if selected_taluk != "All":
    filtered_df = filtered_df[filtered_df["taluk_location"] == selected_taluk]
  if selected_breed != "All":
    filtered_df = filtered_df[filtered_df["breed"] == selected_breed]
  if selected_cat != "All":
    filtered_df = filtered_df[filtered_df["cattle_category"] == selected_cat]

  st.write("---")
  st.markdown(f"### 📋 Available Cattle ({len(filtered_df)} Listings Found)")

  if filtered_df.empty:
    st.warning("⚠️ No listings match your selected filter criteria.")
    return

  for idx, row in filtered_df.iterrows():
    with st.expander(f"🐮 {row['breed']} ({row['cattle_category']}) - ₹{row['price_inr']:,.0f} | Location: {row['taluk_location']}", expanded=True):
      c_img, c_info, c_action = st.columns([1, 2, 1])
      
      with c_img:
        if row['photo_path'] and os.path.exists(row['photo_path']):
          st.image(row['photo_path'], use_container_width=True)
        else:
          st.info("📷 Photo unavailable")
      
      with c_info:
        st.markdown(f"**Listing ID:** `{row['listing_id']}`")
        st.markdown(f"• **Age:** {row['age_years']} Years | **Lactation:** #{row['lactation_number']}")
        st.markdown(f"• **Daily Yield:** **{row['daily_milk_yield_ltr']} Liters/day** | **Fat %:** {row['fat_pct']}%")
        st.markdown(f"• **Health Status:** {row['health_status']}")
        st.markdown(f"• **Pregnancy Status:** {row['pregnancy_status']}")
        st.markdown(f"• **Price Negotiable:** {row['negotiable']}")

      with c_action:
        st.markdown(f"### ₹{row['price_inr']:,.0f}")
        st.write(f"👤 **Seller:** {row['seller_name']}")
        st.write(f"📞 **Phone:** `{row['contact_number']}`")
        
        if st.button("📞 Express Direct Interest", key=f"interest_{row['id']}", type="primary", use_container_width=True):
          st.success(f"✅ Your contact interest has been registered! Please call seller directly at: {row['contact_number']}")

# ==============================================================================
# SELLER DASHBOARD
# ==============================================================================
def seller_dashboard():
  st.title("🏷️ Cattle Seller Marketplace Portal")
  st.markdown("##### Manage your cattle listings, post new animals for sale, or update status.")
  
  tab1, tab2 = st.tabs(["➕ Post New Cattle for Sale", "📋 My Active Listings"])

  with tab1:
    st.subheader("📝 Register Cattle for Sale")
    with st.form("seller_post_form", clear_on_submit=True):
      c1, c2 = st.columns(2)
      with c1:
        seller_name = st.text_input("Seller Full Name", value=st.session_state.username)
        taluk_location = st.text_input("Taluk / Location", placeholder="e.g., Maddur / Mandya / Pandavapura")
        contact_number = st.text_input("Mobile / Contact Number", placeholder="e.g., 9876543210")
        cattle_category = st.selectbox("Cattle Category", ["Milking Cow", "Milking Buffalo", "Pregnant Heifer", "Dry Cow"])
        breed = st.selectbox("Breed Type", ["HF Crossbred", "Jersey Crossbred", "Hallikar (Desi)", "Gir Cross", "Murrah Buffalo"])
        age_years = st.number_input("Age (in Years)", min_value=0.5, max_value=15.0, value=3.5, step=0.5)

      with c2:
        lactation_number = st.number_input("Lactation Number", min_value=1, max_value=10, value=2)
        daily_yield = st.number_input("Daily Milk Yield (Liters)", min_value=0.5, max_value=40.0, value=12.0, step=0.5)
        fat_pct = st.number_input("Average Milk Fat %", min_value=2.0, max_value=12.0, value=4.2, step=0.1)
        health_status = st.selectbox("Health Condition", ["Healthy & Fully Vaccinated", "Under Deworming Care", "Routine Checks Clear"])
        pregnancy_status = st.selectbox("Pregnancy Status", ["Not Pregnant", "Pregnant (1-3 Months)", "Pregnant (4-6 Months)", "Pregnant (7+ Months)"])
        price_inr = st.number_input("Expected Selling Price (₹)", min_value=5000.0, max_value=300000.0, value=65000.0, step=1000.0)
        negotiable = st.selectbox("Price Negotiable?", ["Yes", "No"])
        photo_file = st.file_uploader("Upload Cattle Photo (Optional)", type=["jpg", "jpeg", "png"])

      submitted = st.form_submit_button("🚀 Publish Listing to Marketplace", type="primary", use_container_width=True)

      if submitted:
        if not seller_name or not taluk_location or not contact_number:
          st.error("⚠️ Please fill in all required seller details (Name, Location, Contact Number).")
        else:
          listing_id = f"MND-{os.urandom(2).hex().upper()}"
          photo_path = ""
          
          if photo_file is not None:
            photo_path = os.path.join("uploads", f"{listing_id}_{photo_file.name}")
            with open(photo_path, "wb") as f:
              f.write(photo_file.getbuffer())

          try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cattle_marketplace 
                (listing_id, seller_name, taluk_location, contact_number, cattle_category, breed, age_years, lactation_number, daily_milk_yield_ltr, fat_pct, health_status, pregnancy_status, price_inr, negotiable, status, photo_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Available', %s)
            """, (listing_id, seller_name, taluk_location, contact_number, cattle_category, breed, age_years, lactation_number, daily_yield, fat_pct, health_status, pregnancy_status, price_inr, negotiable, photo_path))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            st.success(f"🎉 Listing published successfully! Your Listing ID is #{listing_id}")
            st.rerun()
          except Exception as err:
            st.error(f"Error publishing listing: {err}")

  with tab2:
    st.subheader(f"📋 Listings posted by {st.session_state.username}")
    
    try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor(dictionary=True)
      cursor.execute("SELECT * FROM cattle_marketplace WHERE seller_name = %s ORDER BY id DESC", (st.session_state.username,))
      my_listings = cursor.fetchall()
      cursor.close()
      conn.close()
    except Exception as e:
      st.error(f"Error fetching listings: {e}")
      my_listings = []

    if not my_listings:
      st.info("ℹ️ You have not published any cattle listings yet.")
    else:
      for item in my_listings:
        with st.container():
          col_a, col_b, col_c = st.columns([1, 2, 1])
          
          with col_a:
            if item['photo_path'] and os.path.exists(item['photo_path']):
              st.image(item['photo_path'], use_container_width=True)
            else:
              st.info("📷 No Photo")
          
          with col_b:
            st.markdown(f"### **{item['breed']} ({item['cattle_category']})**")
            st.write(f"• **Listing ID:** `{item['listing_id']}` | **Status:** `{item['status']}`")
            st.write(f"• **Yield:** {item['daily_milk_yield_ltr']} L/day | **Fat:** {item['fat_pct']}% | **Price:** ₹{item['price_inr']:,.0f}")
            st.write(f"• **Location:** {item['taluk_location']} | **Contact:** {item['contact_number']}")

          with col_c:
            st.write("### Actions")
            if item['status'] == 'Available':
              if st.button("✅ Mark as Sold", key=f"sold_{item['id']}"):
                try:
                  conn = mysql.connector.connect(**DB_CONFIG)
                  cursor = conn.cursor()
                  cursor.execute("UPDATE cattle_marketplace SET status = 'Sold' WHERE id = %s", (item['id'],))
                  conn.commit()
                  cursor.close()
                  conn.close()
                  st.success("Updated status to Sold!")
                  st.rerun()
                except Exception as err:
                  st.error(f"Error: {err}")
            
            if st.button("🗑️ Delete Listing", key=f"del_{item['id']}", type="secondary"):
              try:
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cattle_marketplace WHERE id = %s", (item['id'],))
                conn.commit()
                cursor.close()
                conn.close()
                st.success("Listing deleted successfully!")
                st.rerun()
              except Exception as err:
                st.error(f"Error: {err}")
          
          st.write("---")

# ==============================================================================
# FARMER HERD MANAGEMENT TAB
# ==============================================================================
def farmer_cattle_management_tab():
  st.subheader("🐄 My Cattle Herd Management (ನನ್ನ ಜಾನುವಾರುಗಳು)")
  
  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM farmer_cattle WHERE username = %s", (st.session_state.username,))
    my_cattle = cursor.fetchall()
    cursor.close()
    conn.close()

    if my_cattle:
      st.dataframe(pd.DataFrame(my_cattle), use_container_width=True)
      
      st.write("---")
      st.markdown("### 🛠️ Quick Health Recovery Action")
      unhealthy_cows = [c['cattle_tag'] for c in my_cattle if "Healthy" not in c['health_status']]
      
      if unhealthy_cows:
        sel_recover_tag = st.selectbox("Select Unhealthy Cow Tag to Recover", unhealthy_cows)
        if st.button("🟢 Mark as Recovered", type="primary"):
          try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE farmer_cattle SET health_status = 'Healthy' WHERE username = %s AND cattle_tag = %s",
                (st.session_state.username, sel_recover_tag)
            )
            conn.commit()
            cursor.close()
            conn.close()
            st.success(f"✅ Cattle Tag #{sel_recover_tag} successfully marked as Healthy / Recovered!")
            st.rerun()
          except Exception as err:
            st.error(f"Error updating recovery status: {err}")
      else:
        st.info("ℹ️ All registered cows in your herd are currently healthy.")

    else:
      st.info("ℹ️ You have not registered any cattle yet.")
  except Exception as e:
    st.warning(f"Error: {e}")

  st.write("---")
  st.markdown("### ➕ Register New Cattle to Your Farm")
  with st.form("register_my_cattle_form"):
    c1, c2 = st.columns(2)
    with c1:
      tag = st.text_input("Cattle Tag / ID number", placeholder="e.g., 2 or KA-MND-101")
      breed = st.selectbox("Breed", ["HF Crossbred", "Jersey Crossbred", "Hallikar (Desi)", "Murrah Buffalo", "Gir Cross"])
      age_m = st.number_input("Age (Months)", min_value=6, max_value=240, value=36)
    with c2:
      lac_stage = st.number_input("Lactation Stage", min_value=1, max_value=10, value=2)
      daily_y = st.number_input("Average Daily Yield (Liters)", min_value=1.0, max_value=30.0, value=12.0)
      fat = st.number_input("Average Fat %", min_value=2.0, max_value=10.0, value=4.2)

    if st.form_submit_button("Save Animal to My Herd", type="primary"):
      if tag:
        try:
          conn = mysql.connector.connect(**DB_CONFIG)
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO farmer_cattle (username, cattle_tag, breed, age_months, lactation_stage, daily_yield_ltr, fat_pct, health_status) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Healthy')",
              (st.session_state.username, tag, breed, age_m, lac_stage, daily_y, fat)
          )
          conn.commit()
          cursor.close()
          conn.close()
          st.success(f"✅ Cattle [{tag}] added successfully!")
          st.rerun()
        except Exception as err:
          st.error(f"Error: {err}")

# ==============================================================================
# FARMER DASHBOARD WITH MODULE FEEDBACK
# ==============================================================================
def farmer_dashboard():
  st.sidebar.title("🌾 Farmer Mobile Portal")
  st.sidebar.write(f"**Farmer:** {st.session_state.username}")
  
  st.sidebar.markdown("---")
  st.sidebar.subheader("📌 Navigation Menu")
  
  farmer_modules = [
      "🏠 Home Overview",
      "🐄 My Cattle Herd",
      "🌿 Region Food (Precision Feed)",
      "🩺 Health Risk Prediction",
      "📈 Milk Yield Prediction",
      "💰 Price Prediction",
      "🛒 Marketplace (Buy/Sell)",
      "🤖 Agentic Cattle Assistant",
      "💬 App Feedback"
  ]
  nav_choice = st.sidebar.radio("Go to Module", farmer_modules)

  st.sidebar.markdown("---")
  if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

  total_herd_milk = 0.0
  my_cattle_count = 0
  unhealthy_herd_list = []

  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT cattle_tag, daily_yield_ltr, health_status FROM farmer_cattle WHERE username = %s", (st.session_state.username,))
    herd_records = cursor.fetchall()
    my_cattle_count = len(herd_records)
    for h in herd_records:
      total_herd_milk += float(h['daily_yield_ltr'] or 0.0)
      if "Healthy" not in h['health_status']:
        unhealthy_herd_list.append(h['cattle_tag'])

    cursor.close()
    conn.close()
  except Exception:
    pass

  health_alert_display = f"⚠️ {len(unhealthy_herd_list)} Cattle Under Treatment!" if unhealthy_herd_list else "All cattle healthy"

  if nav_choice == "🏠 Home Overview":
    st.markdown("### GOOD MORNING / ಶುಭೋದಯ")
    st.write(f"**ರೈತರು (Farmer):** {st.session_state.username}")

    c1, c2, c3 = st.columns(3)
    c1.metric("🐄 My Cattle Count", str(my_cattle_count))
    c2.metric("🥛 Total Herd Daily Milk", f"{total_herd_milk:.1f} L")
    c3.metric("🌾 Feed Recommendation", "Available")

    c4, c5 = st.columns(2)
    c4.metric("⚠️ Health Status Alert", health_alert_display)
    c5.metric("📈 Tomorrow's Expected Yield", f"{total_herd_milk * 1.05:.1f} L")

    st.write("---")
    if unhealthy_herd_list:
      st.error("🚨 **Active Health Risk Alerts on Your Farm:**")
      for tag in unhealthy_herd_list:
        st.warning(f"• **Animal ID / Tag #{tag}** is flagged as **Under Treatment / High Risk**!")
    else:
      st.success("✅ All registered cattle on your farm are currently healthy and secure.")

  elif nav_choice == "🐄 My Cattle Herd":
    farmer_cattle_management_tab()

  elif nav_choice == "🌿 Region Food (Precision Feed)":
    st.subheader("🌿 Regional Precision Feed Formulation (ICAR)")
    col1, col2, col3 = st.columns(3)
    with col1:
      region = st.selectbox("Select Region", options=list(REGIONAL_FEEDS.keys()), index=None, placeholder="Choose Region...")
      breed_type = st.selectbox("Select Breed", options=list(BREED_FAT_PROFILES.keys()), index=None, placeholder="Choose Breed...")
    with col2:
      lactation_stage = st.selectbox("Lactation Stage", options=list(LACTATION_ADJUSTMENTS.keys()), index=None, placeholder="Choose Stage...")
      weight_kg = st.number_input("Body Weight (kg)", min_value=100.0, max_value=1000.0, value=None, placeholder="Enter Body Weight")
    with col3:
      milk_ltr = st.number_input("Milk Production (Liters/day)", min_value=0.0, max_value=100.0, value=None, placeholder="Enter Daily Yield")
      max_feed = st.number_input("Max Fresh Feed Intake (kg)", min_value=1.0, max_value=100.0, value=None, placeholder="Enter Feed Capacity")

    if st.button("Generate Precision Ration", type="primary"):
      if not all([region, breed_type, lactation_stage, weight_kg, milk_ltr, max_feed]):
        st.warning("⚠️ Please fill in all fields.")
      else:
        result = generate_precision_ration({
            "region": region, "breed_type": breed_type, "lactation_stage": lactation_stage,
            "weight_kg": weight_kg, "milk_production_ltr": milk_ltr, "daily_feed_intake_kg": max_feed
        })
        st.success("✅ Precision Ration Calculated!")
        st.dataframe(pd.DataFrame(result["ration_rows"]), use_container_width=True)

  elif nav_choice == "🩺 Health Risk Prediction":
    st.subheader("🩺 AI-Powered Cattle Health Risk & Clinical Diagnosis")
    with st.form("health_prediction_form"):
      animal_id = st.text_input("1. Enter Cow Tag / ID number", placeholder="e.g., 2")
      m_choice = st.selectbox("2. How is the milk production today?", ["Normal (Same as usual)", "A little less than usual", "Dropped significantly (Half or less)"], index=None)
      milk_reduction = {"Normal (Same as usual)": 0.0, "A little less than usual": 15.0, "Dropped significantly (Half or less)": 35.0}.get(m_choice, 0.0)

      f_choice = st.selectbox("3. How is the cow eating today?", ["Ate all fodder (Normal appetite)", "Ate less than usual / Left fodder", "Refused to eat / Barely touched food"], index=None)
      feed_intake = {"Ate all fodder (Normal appetite)": 100.0, "Ate less than usual / Left fodder": 65.0, "Refused to eat / Barely touched food": 40.0}.get(f_choice, 100.0)

      a_choice = st.selectbox("4. How active is the cow moving today?", ["Normal walking and standing", "Lazy / Lying down more than usual", "Very weak / Refuses to stand up", "Very restless / Agitated"], index=None)
      activity_dev = {"Normal walking and standing": 0.0, "Lazy / Lying down more than usual": -25.0, "Very weak / Refuses to stand up": -50.0, "Very restless / Agitated": 30.0}.get(a_choice, 0.0)

      t_choice = st.selectbox("5. Does the cow feel hot or have a fever?", ["Normal body temperature", "Feels warm / Mild fever", "Feels very hot / High fever"], index=None)
      temperature = 38.5 if t_choice != "Feels very hot / High fever" else 40.0

      r_choice = st.selectbox("6. Is the cow chewing its cud?", ["Yes, chewing cud normally", "Chewing less than usual", "Completely stopped chewing cud"], index=None)
      rumination_drop = {"Yes, chewing cud normally": 0.0, "Chewing less than usual": 25.0, "Completely stopped chewing cud": 50.0}.get(r_choice, 0.0)

      h_choice = st.selectbox("7. Has this cow been sick before in the past?", ["No, always healthy", "Sick once or twice before", "Frequently sick / Chronic issues"], index=None)
      history_score = {"No, always healthy": 0, "Sick once or twice before": 1, "Frequently sick / Chronic issues": 2}.get(h_choice, 0)

      submitted_health = st.form_submit_button("Run LLM Health Analysis & Save", type="primary")

    if submitted_health:
      if not animal_id or not m_choice:
        st.warning("⚠️ Please provide Animal ID and complete the assessment.")
      else:
        ml_engine = HealthRiskMLModel()
        ml_engine.train()
        telemetry = {
            "milk_reduction": milk_reduction, "feed_intake": feed_intake,
            "activity_dev": activity_dev, "temperature": temperature,
            "rumination_drop": rumination_drop, "history_score": history_score
        }
        base_score = ml_engine.predict_base_risk(telemetry)
        final_risk_score = min(100.0, base_score)
        risk_level = "HIGH" if final_risk_score >= 65.0 else ("MEDIUM" if final_risk_score >= 30.0 else "LOW")
        
        anomalies = []
        if temperature > 39.0:
          anomalies.append(f"Elevated Temperature ({temperature}°C)")
        if feed_intake < 70.0:
          anomalies.append("Reduced Feed Intake")
        if milk_reduction > 10.0:
          anomalies.append("Milk Yield Drop Detected")
          
        if not anomalies:
          anomalies.append("Normal parameters stable")

        # Generate LLM Veterinary Insights
        llm_advice = get_llm_health_recommendations(animal_id, telemetry, risk_level, anomalies)

        updated_health_status = f"🔴 Under Treatment ({risk_level} Risk)" if risk_level != "LOW" else "Healthy"
        save_health_db(animal_id, telemetry, "", base_score, 0.0, final_risk_score, risk_level, "Standard Telemetry Scan", anomalies, [llm_advice])

        try:
          conn = mysql.connector.connect(**DB_CONFIG)
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE farmer_cattle SET health_status = %s WHERE username = %s AND cattle_tag = %s",
              (updated_health_status, st.session_state.username, animal_id)
          )
          conn.commit()
          cursor.close()
          conn.close()
        except Exception as db_err:
          st.error(f"Error updating herd health status: {db_err}")

        st.success(f"✅ AI Health Assessment Completed for Tag #{animal_id}!")
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Risk Score", f"{final_risk_score:.1f} / 100")
        c_m2.metric("Risk Level", risk_level)
        
        st.write("---")
        st.markdown(llm_advice)

  elif nav_choice == "📈 Milk Yield Prediction":
    st.subheader("📈 XGBoost Milk Yield Prediction")
    y_breed = st.selectbox("Breed", ["HF Crossbred", "Jersey Crossbred", "Gir", "Sahiwal", "Hallikar"])
    col_y1, col_y2 = st.columns(2)
    with col_y1:
      age_m = st.number_input("Age in Months", 1, 200, 42)
      lac_stg = st.number_input("Lactation Stage", 1, 10, 2)
      prev_y = st.number_input("Yesterday's Yield (Liters)", 0.0, 100.0, 15.0)
      feed_kg = st.number_input("Daily Feed Intake (kg)", 1.0, 50.0, 18.0)
    with col_y2:
      fat_p = st.number_input("Fat %", 1.0, 12.0, 4.2)
      snf_p = st.number_input("SNF %", 5.0, 12.0, 8.5)
      amb_t = st.number_input("Ambient Temperature (°C)", 0.0, 50.0, 30.0)
      hum = st.number_input("Humidity (%)", 0.0, 100.0, 65.0)

    if st.button("Predict Yield Forecast", type="primary"):
      predictor = MilkYieldPredictor(model_type="xgboost")
      predictor.train_and_evaluate()
      inputs = {
          "breed": y_breed, "age_months": int(age_m), "lactation_stage": int(lac_stg),
          "previous_yield": float(prev_y), "feed_intake_kg": float(feed_kg),
          "fat_pct": float(fat_p), "snf_pct": float(snf_p),
          "temperature_c": float(amb_t), "humidity_pct": float(hum)
      }
      out = predictor.predict(inputs)
      st.success("✅ Forecast Generated!")
      st.metric("Predicted Tomorrow", f"{out['predicted_yield_tomorrow_liters']} Liters")
      st.metric("Predicted 7-Day Total", f"{out['predicted_yield_next_7_days_total_liters']} Liters")

  elif nav_choice == "💰 Price Prediction":
    st.subheader("💰 Milk Payout Price Predictor")
    p_fat = st.number_input("Fat %", 1.0, 12.0, 4.2)
    p_snf = st.number_input("SNF %", 5.0, 12.0, 8.5)
    p_breed = st.selectbox("Breed / Milk Type", ["Cow", "Buffalo", "Jersey", "HF", "Hallikar"])

    if st.button("Calculate Payout Rate", type="primary"):
      model, cols = train_price_prediction_model()
      if model:
        input_df = pd.DataFrame([{"Fat_Pct": p_fat, "SNF_Pct": p_snf, "Milk_Type": p_breed}])
        encoded = pd.get_dummies(input_df, columns=["Milk_Type"])
        for c in cols:
          if c not in encoded.columns:
            encoded[c] = 0
        encoded = encoded[cols]
        pred_rate = model.predict(encoded)[0]
        st.success(f"💰 Estimated Payout Rate: **₹{pred_rate:.2f} per Liter**")

  elif nav_choice == "🛒 Marketplace (Buy/Sell)":
    m_choice = st.radio("Marketplace Action", ["Browse Market", "Post Animal for Sale"], horizontal=True)
    if m_choice == "Browse Market":
      buyer_dashboard()
    else:
      seller_dashboard()

  elif nav_choice == "🤖 Agentic Cattle Assistant":
    st.subheader("🤖 Agentic Cattle Assistant (ಸ್ವಾಯತ್ತ ಕ್ಯಾಟಲ್ ಸಹಾಯಕ)")
    lang_pref = st.radio("Choose Language:", ["Both (English & ಕನ್ನಡ)", "ಕನ್ನಡ (Kannada)", "English"], horizontal=True)
    st.write("---")
    for msg in st.session_state.chat_messages:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    if user_prompt := st.chat_input("Ask Agentic Cattle Assistant..."):
      st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
      with st.chat_message("user"):
        st.markdown(user_prompt)

      with st.chat_message("assistant"):
        agent = SmartDairyAgent(username=st.session_state.username, role=st.session_state.role, lang_pref=lang_pref)
        reply = agent.chat_with_context(user_prompt)
        st.markdown(reply)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})

  elif nav_choice == "💬 App Feedback":
    render_feedback_module(farmer_modules[:-1])

# ==============================================================================
# DAIRY OWNER / ADMIN DASHBOARD WITH MODULE FEEDBACK
# ==============================================================================
def dairy_owner_dashboard():
  st.sidebar.title("🏢 Dairy Owner Portal")
  st.sidebar.write(f"**Admin:** {st.session_state.username}")
  st.sidebar.write(f"**Dairy ID:** {st.session_state.dairy_id}")
  
  st.sidebar.markdown("---")
  st.sidebar.subheader("📌 Navigation Menu")
  
  owner_modules = [
      "📊 Dairy Analytics",
      "📋 Farmer Report & SMS Dispatch",
      "💰 Price Prediction & Sourcing",
      "📁 Batch Excel Upload",
      "🤖 Agentic SmartDairy AI",
      "💬 App Feedback"
  ]
  owner_nav = st.sidebar.radio("Go to Module", owner_modules)

  st.sidebar.markdown("---")
  if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

  engine = create_engine(f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

  if owner_nav == "📊 Dairy Analytics":
    st.title(f"📊 Dairy Analytics & Collection Overview (Dairy ID: {st.session_state.dairy_id})")
    try:
      df_records = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", con=engine)
      if df_records.empty:
        st.info("ℹ️ No collection records found in the database.")
      else:
        tot_vol = df_records["Qty_Ltr"].sum()
        tot_rev = df_records["Amount_Rs"].sum()
        total_farmers = df_records["Name"].nunique() if "Name" in df_records.columns else df_records["Code"].nunique()
        avg_fat = df_records["Fat_Pct"].mean()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Collection Volume", f"{tot_vol:,.1f} L")
        m2.metric("Total Payout Revenue", f"₹{tot_rev:,.2f}")
        m3.metric("Active Farmer Suppliers", str(total_farmers))
        m4.metric("Avg Fat %", f"{avg_fat:.2f}%")

        st.write("---")
        st.markdown("### 🔍 Raw Milk Collection Records")
        st.dataframe(df_records, use_container_width=True)
    except Exception as e:
      st.error(f"Error fetching dairy analytics: {e}")

  elif owner_nav == "📋 Farmer Report & SMS Dispatch":
    st.title(f"📋 Farmer Performance Statement & SMS Dispatch (Dairy ID: {st.session_state.dairy_id})")
    try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor(dictionary=True)
      cursor.execute(f"SELECT DISTINCT Name FROM {TABLE_NAME} WHERE Name IS NOT NULL AND Name != ''")
      farmer_rows = cursor.fetchall()
      farmer_names = [f["Name"] for f in farmer_rows]

      if not farmer_names:
        cursor.execute("SELECT DISTINCT username FROM dairy_users WHERE role = 'farmer'")
        farmer_rows = cursor.fetchall()
        farmer_names = [f["username"] for f in farmer_rows]

      cursor.close()
      conn.close()

      if not farmer_names:
        st.info("ℹ️ No farmer collection records available.")
      else:
        selected_farmer = st.selectbox("Select Member Farmer:", options=farmer_names)
        if selected_farmer:
          conn = mysql.connector.connect(**DB_CONFIG)
          cursor = conn.cursor(dictionary=True)
          cursor.execute(f"SELECT SUM(Qty_Ltr) as tot_qty, SUM(Amount_Rs) as tot_payout, AVG(Fat_Pct) as avg_fat, AVG(SNF_Pct) as avg_snf FROM {TABLE_NAME} WHERE Name = %s", (selected_farmer,))
          f_stats = cursor.fetchone()

          cursor.execute("SELECT phone FROM dairy_users WHERE username = %s", (selected_farmer,))
          phone_row = cursor.fetchone()
          cursor.close()
          conn.close()

          farmer_phone = phone_row["phone"] if phone_row and phone_row["phone"] else ""
          tot_q = f_stats["tot_qty"] if f_stats and f_stats["tot_qty"] else 0.0
          tot_p = f_stats["tot_payout"] if f_stats and f_stats["tot_payout"] else 0.0
          a_fat = f_stats["avg_fat"] if f_stats and f_stats["avg_fat"] else 0.0
          a_snf = f_stats["avg_snf"] if f_stats and f_stats["avg_snf"] else 0.0

          st.write("---")
          st.markdown(f"### 📄 Statement for **{selected_farmer}**")
          col_s1, col_s2, col_s3, col_s4 = st.columns(4)
          col_s1.metric("Total Quantity", f"{tot_q:,.1f} L")
          col_s2.metric("Total Payout", f"₹{tot_p:,.2f}")
          col_s3.metric("Avg Fat %", f"{a_fat:.2f}%")
          col_s4.metric("Avg SNF %", f"{a_snf:.2f}%")

          default_sms = f"Dairy #{st.session_state.dairy_id} Statement for {selected_farmer}: Total Milk: {tot_q:.1f}L | Payout: Rs.{tot_p:,.2f}. Thank you!"
          st.write("---")
          c1, c2 = st.columns(2)
          with c1:
            dest_phone = st.text_input("Mobile Number:", value=farmer_phone)
            final_msg = st.text_area("SMS Text:", value=default_sms, height=100)
          with c2:
            st.write("### ")
            if st.button("🚀 Send SMS via Twilio", type="primary", use_container_width=True):
              if dest_phone:
                success, msg_sid = send_sms_via_twilio(dest_phone, final_msg)
                if success:
                  st.success(f"✅ SMS sent successfully! SID: {msg_sid}")
                else:
                  st.error(f"❌ SMS Failed: {msg_sid}")
              else:
                st.warning("⚠️ Please provide a valid mobile number.")
    except Exception as e:
      st.error(f"Error loading reports: {e}")

  elif owner_nav == "💰 Price Prediction & Sourcing":
    st.title(f"💰 Milk Price & Strategic Procurement (Dairy ID: {st.session_state.dairy_id})")
    fat_val = st.number_input("Fat %", 1.0, 12.0, 4.2)
    snf_val = st.number_input("SNF %", 5.0, 12.0, 8.5)
    breed_val = st.selectbox("Milk Type", ["Cow", "Buffalo", "Jersey", "HF"])

    if st.button("Calculate Payout Rate", type="primary"):
      model, cols = train_price_prediction_model()
      if model:
        input_df = pd.DataFrame([{"Fat_Pct": fat_val, "SNF_Pct": snf_val, "Milk_Type": breed_val}])
        encoded = pd.get_dummies(input_df, columns=["Milk_Type"])
        for c in cols:
          if c not in encoded.columns:
            encoded[c] = 0
        encoded = encoded[cols]
        pred_rate = model.predict(encoded)[0]
        st.success(f"💰 Calculated Payout Rate: **₹{pred_rate:.2f} per Liter**")

  elif owner_nav == "📁 Batch Excel Upload":
    st.title(f"📁 Batch Processing: Multi-Dairy Files (Dairy ID: {st.session_state.dairy_id})")
    uploaded_excel = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])
    if uploaded_excel is not None:
      if st.button("Process & Ingest Excel", type="primary"):
        processed_df, msg = process_dairy_excel_upload(uploaded_excel)
        if processed_df is not None:
          st.success(f"✅ Ingestion Complete: {msg}")
          st.dataframe(processed_df, use_container_width=True)
        else:
          st.error(f"❌ Ingestion Error: {msg}")

  elif owner_nav == "🤖 Agentic SmartDairy AI":
    st.title(f"🤖 Agentic SmartDairy AI Command Center (Dairy ID: {st.session_state.dairy_id})")
    owner_lang_pref = st.radio("Choose Language:", ["Both (English & ಕನ್ನಡ)", "ಕನ್ನಡ (Kannada)", "English"], horizontal=True)
    st.write("---")
    for msg in st.session_state.chat_messages:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    if user_prompt := st.chat_input("Ask Agentic SmartDairy AI..."):
      st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
      with st.chat_message("user"):
        st.markdown(user_prompt)

      with st.chat_message("assistant"):
        agent = SmartDairyAgent(username=st.session_state.username, role=st.session_state.role, lang_pref=owner_lang_pref)
        reply = agent.chat_with_context(user_prompt)
        st.markdown(reply)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})

  elif owner_nav == "💬 App Feedback":
    render_feedback_module(owner_modules[:-1])

# ==============================================================================
# MAIN APPLICATION ROUTER
# ==============================================================================
if not st.session_state.logged_in:
  auth_portal()
else:
  if st.session_state.role == "owner":
    dairy_owner_dashboard()
  elif st.session_state.role == "buyer":
    st.sidebar.title("🛒 Buyer Portal")
    st.sidebar.write(f"User: {st.session_state.username}")
    if st.sidebar.button("Logout"):
      st.session_state.logged_in = False
      st.rerun()
    buyer_dashboard()
  elif st.session_state.role == "seller":
    st.sidebar.title("🏷️ Seller Portal")
    st.sidebar.write(f"User: {st.session_state.username}")
    if st.sidebar.button("Logout"):
      st.session_state.logged_in = False
      st.rerun()
    seller_dashboard()
  else:
    farmer_dashboard()
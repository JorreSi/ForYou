import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Love Letters", page_icon="💌", layout="centered")

# --- FORCEER DARK MODE ---
st.markdown("""
<style>
    /* Algemeen lettertype: Georgia */
    html, body, [class*="css"], .stTextInput, .stTextArea {
        font-family: 'Georgia', serif;
        color: #fafafa;
    }
    .stApp {
        background-color: #0e1117;
    }
    
    /* De titel styling: Goud */
    h1, h2, h3 {
        font-family: 'Garamond', serif;
        color: #d4af37 !important;
        text-shadow: 1px 1px 2px #000000;
        font-weight: normal;
    }

    /* Input velden donker maken */
    .stTextInput > div > div > input {
        color: #fafafa;
        background-color: #262730;
    }
    .stTextArea > div > div > textarea {
        color: #fafafa;
        background-color: #262730;
    }

    /* NAVIGATIE MENU (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 22px !important;
        font-family: 'Garamond', serif !important;
        font-weight: bold !important;
        color: #8B0000 !important;
        margin: 0 10px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #d4af37 !important;
        border-bottom-color: #d4af37 !important;
    }

    /* Briefpapier effect */
    .letter-paper {
        background-color: #262626;
        padding: 30px;
        border-radius: 5px;
        border: 1px solid #444;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        font-size: 18px;
        line-height: 1.6;
        color: #e0e0e0;
        font-style: italic;
        margin-top: 15px;
    }

    /* Verberg standaard elementen */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS VERBINDING ---
def get_db_connection():
    # We halen de JSON sleutel uit de secrets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Hier laden we de 'google_credentials' string die we in Secrets hebben geplakt
    creds_dict = json.loads(st.secrets["google_credentials"])
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Open de sheet met de exacte naam
    sheet = client.open("love_letters_db").sheet1
    return sheet

def load_letters():
    try:
        sheet = get_db_connection()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Als de sheet leeg is of kolommen mist, geef leeg frame terug
        if df.empty or "Author" not in df.columns:
            return pd.DataFrame(columns=["Date", "Author", "Title", "Message"])
            
        return df
    except Exception as e:
        st.error(f"Kan geen verbinding maken met de database: {e}")
        return pd.DataFrame(columns=["Date", "Author", "Title", "Message"])

def save_letter(author, title, message):
    try:
        sheet = get_db_connection()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Voeg een nieuwe rij toe aan Google Sheets
        sheet.append_row([date_str, author, title, message])
        return True
    except Exception as e:
        st.error(f"Fout bij opslaan: {e}")
        return False

# --- LOGIN ---
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    def password_entered():
        if st.session_state["input_password"] == st.secrets["password_jorre"]:
            st.session_state["authenticated"] = True
            st.session_state["user_name"] = "Jorre"
            st.session_state["partner_name"] = "Alevtina" 
        elif st.session_state["input_password"] == st.secrets["password_alevtina"]:
            st.session_state["authenticated"] = True
            st.session_state["user_name"] = "Alevtina"
            st.session_state["partner_name"] = "Jorre"
        else:
            st.error("Incorrect password.")

    if not st.session_state["authenticated"]:
        st.markdown("<br><br><h2 style='text-align: center;'>🔐 Enter the secret phrase</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.text_input("", type="password", on_change=password_entered, key="input_password", label_visibility="collapsed")
        return False
    
    return True

# --- HOOFD PROGRAMMA ---

if check_login():
    me = st.session_state["user_name"]
    partner = st.session_state["partner_name"]

    st.markdown(f"<h3 style='text-align: center;'>Eternally Yours, {me}</h3>", unsafe_allow_html=True)
    st.write("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["💌 Latest Letter", "✒️ Write New", "🗄️ Archive"])

    # --- TAB 1: LATEST LETTER ---
    with tab1:
        df = load_letters()
        # Filter op partner
        if not df.empty and "Author" in df.columns:
            partner_letters = df[df["Author"] == partner]
            
            if not partner_letters.empty:
                last_letter = partner_letters.iloc[-1]
                
                st.markdown(f"<h1 style='text-align: center;'>New Letter Arrived</h1>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                with st.expander(f"🌹 {last_letter['Title']}", expanded=False):
                    st.write(f"<div style='text-align: center; color: grey; margin-bottom: 20px;'>Received on {last_letter['Date']}</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="letter-paper">
                        {str(last_letter['Message']).replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br><div style='text-align: center;'>🖤</div>", unsafe_allow_html=True)
            else:
                st.info(f"No letters from {partner} yet. Maybe you should write one first?")
        else:
            st.info("Database is empty or loading...")

    # --- TAB 2: WRITE NEW ---
    with tab2:
        st.subheader(f"Writing to {partner}...")

        st.info("💡 Tip: Gebruik **dubbele sterretjes** voor vetgedrukt en _lage streepjes_ voor cursief.")
        
        with st.form("letter_form"):
            title = st.text_input("Subject / Title", placeholder="e.g. My endless love...")
            message = st.text_area("Your Message", height=300, label_visibility="collapsed", placeholder="My Dearest...")
            
            sent = st.form_submit_button("Send 🕊️")
            
            if sent:
                if message and title:
                    with st.spinner("Sending to the cloud..."):
                        if save_letter(me, title, message):
                            st.success("Sent! Saved safely in the cloud ☁️")
                            st.balloons()
                            # Wacht even zodat ze de ballonnen zien
                            import time
                            time.sleep(2)
                            st.rerun()
                else:
                    st.warning("A letter needs both a Title and a Message.")

    # --- TAB 3: ARCHIVE ---
    with tab3:
        st.subheader("Memories")
        df = load_letters()
        
        if not df.empty and "Author" in df.columns:
            # We draaien de volgorde om (nieuwste boven)
            for index, row in df.iloc[::-1].iterrows():
                icon = "🖤" if row['Author'] == me else "🌹"
                
                with st.expander(f"{icon} {row['Title']} ({row['Date']})"):
                    st.markdown(f"**From:** {row['Author']}")
                    st.markdown(f"""
                    <div class="letter-paper" style="margin-top: 5px; padding: 15px; font-size: 16px;">
                        {str(row['Message']).replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("No memories stored yet.")

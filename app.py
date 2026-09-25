import os
import re
import sqlite3
import streamlit as st
from dotenv import load_dotenv
import anthropic

# 1. Environment & Setup
load_dotenv()
st.set_page_config(page_title="ScamBait AI", page_icon="🎣", layout="wide")

def inject_custom_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #07111f;
            --bg-2: #0d1b2a;
            --panel: rgba(15, 23, 42, 0.82);
            --panel-strong: rgba(15, 23, 42, 0.96);
            --border: rgba(148, 163, 184, 0.18);
            --text: #e2e8f0;
            --muted: #9aa9be;
            --green: #4ade80;
            --cyan: #38bdf8;
            --amber: #fbbf24;
            --red: #f87171;
            --violet: #a78bfa;
            --shadow: 0 20px 50px rgba(2, 6, 23, 0.45);
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 30%),
                radial-gradient(circle at top right, rgba(167, 139, 250, 0.15), transparent 28%),
                linear-gradient(135deg, var(--bg) 0%, var(--bg-2) 100%);
            color: var(--text);
        }

        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 4rem;
            max-width: 1500px;
        }

        [data-testid="stSidebar"] {
            background: rgba(7, 17, 31, 0.9);
            border-right: 1px solid var(--border);
            box-shadow: var(--shadow);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem;
        }

        .stSelectbox > div > div {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text);
        }

        .stTextInput > div > div, .stTextArea > div > div {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border);
            border-radius: 12px;
        }

        .stTabs [role="tablist"] {
            gap: 0.75rem;
            margin-bottom: 1rem;
        }

        .stTabs [role="tab"] {
            height: 42px;
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid var(--border);
            color: var(--muted);
            padding: 0 1rem;
        }

        .stTabs [role="tab"][aria-selected="true"] {
            background: linear-gradient(90deg, rgba(56, 189, 248, 0.18), rgba(167, 139, 250, 0.18));
            border-color: rgba(56, 189, 248, 0.4);
            color: var(--text);
            box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.2);
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.72));
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow);
        }

        div[data-testid="stMetric"] label {
            color: var(--muted);
            font-weight: 600;
        }

        div[data-testid="stMetric"] > div {
            background: transparent;
        }

        div[data-testid="stMetric"] > div > div > div {
            color: var(--text);
            font-size: 1.7rem;
            font-weight: 700;
        }

        [data-testid="stChatMessage"] {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            margin: 0.5rem 0 0.8rem 0;
            box-shadow: 0 10px 25px rgba(2, 6, 23, 0.18);
        }

        [data-testid="stChatMessage"] p {
            margin-bottom: 0.2rem;
            color: var(--text);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 20px;
        }

        .app-hero {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            padding: 1.2rem 1.3rem 1rem 1.3rem;
            margin-bottom: 1rem;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.7));
            box-shadow: var(--shadow);
        }

        .section-label {
            display: inline-block;
            margin-bottom: 0.5rem;
            padding: 0.35rem 0.7rem;
            font-size: 0.72rem;
            letter-spacing: 0.08rem;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--cyan);
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 999px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            background: rgba(74, 222, 128, 0.12);
            border: 1px solid rgba(74, 222, 128, 0.25);
            color: var(--green);
            font-size: 0.8rem;
            font-weight: 700;
        }

        .status-pill::before {
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 10px rgba(74, 222, 128, 0.9);
        }

        h1 {
            margin: 0;
            color: var(--text);
            letter-spacing: -0.04em;
            line-height: 1.1;
        }

        .caption-soft {
            color: var(--muted);
            font-size: 0.92rem;
            margin-top: 0.25rem;
        }

        .stDownloadButton > button, .stButton > button {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(167, 139, 250, 0.2));
            border: 1px solid rgba(56, 189, 248, 0.28);
            color: var(--text);
            font-weight: 700;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(56, 189, 248, 0.12);
        }

        .stDownloadButton > button:hover, .stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.4);
        }

        .dataframe {
            border-radius: 18px;
            overflow: hidden;
        }

        .stDataFrame {
            border-radius: 16px;
            border: 1px solid var(--border);
            overflow: hidden;
        }

        .stToast {
            background: rgba(15, 23, 42, 0.96);
            border: 1px solid rgba(56, 189, 248, 0.25);
            color: var(--text);
        }

        @media (max-width: 900px) {
            .app-hero {
                flex-direction: column;
                align-items: flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# 2. Database Helper Functions
def init_db():
    conn = sqlite3.connect("blocklist.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS blocklist
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  data_type TEXT,
                  value TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_to_blocklist(data_type, value):
    conn = sqlite3.connect("blocklist.db")
    c = conn.cursor()
    c.execute("INSERT INTO blocklist (data_type, value) VALUES (?, ?)", (data_type, value))
    conn.commit()
    conn.close()

def get_blocklist():
    conn = sqlite3.connect("blocklist.db")
    c = conn.cursor()
    c.execute("SELECT data_type, value, timestamp FROM blocklist ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# Initialize Database
init_db()

# Apply custom styling
inject_custom_css()

# 3. Threat Intelligence Extraction Function
def extract_threat_intel(text):
    upi_pattern = r'[a-zA-Z0-9.\-_]+@[a-zA-Z]+'
    phone_pattern = r'\b(?:\+91[\-\s]?)?[6-9]\d{9}\b'
    ifsc_pattern = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
    url_pattern = r'https?://[^\s]+'
    
    extracted = []
    
    for upi in re.findall(upi_pattern, text):
        save_to_blocklist("UPI ID", upi)
        extracted.append(("UPI ID", upi))
    for phone in re.findall(phone_pattern, text):
        save_to_blocklist("Phone Number", phone)
        extracted.append(("Phone Number", phone))
    for ifsc in re.findall(ifsc_pattern, text):
        save_to_blocklist("Bank IFSC Code", ifsc)
        extracted.append(("Bank IFSC Code", ifsc))
    for url in re.findall(url_pattern, text):
        save_to_blocklist("Phishing Link", url)
        extracted.append(("Phishing Link", url))
        
    return extracted

# 4. Sidebar - Dynamic Persona Selector
st.sidebar.title("🎭 Persona Settings")
st.sidebar.caption("Choose how the AI should behave while wasting the scammer’s time.")
persona_choice = st.sidebar.selectbox(
    "Select AI Bait Persona:",
    ["Confused Senior Citizen (Uncle Ramesh)", "Naïve Student (Priya)", "Busy Corporate Employee"]
)

PROMPTS = {
    "Confused Senior Citizen (Uncle Ramesh)": "You are Ramesh, a 68-year-old retired clerk. You are bad with smartphones, misread buttons, and speak with extreme politeness.",
    "Naïve Student (Priya)": "You are Priya, a 19-year-old student looking for part-time work. You get easily excited but confused by payment gateways and bank OTPs.",
    "Busy Corporate Employee": "You are an overworked manager answering while in meetings. You reply hastily, make typos, and constantly ask them to repeat instructions."
}

SYSTEM_PROMPT = PROMPTS[persona_choice] + "\nGOAL: Waste the scammer's time. NEVER share real financial details or credentials."

st.sidebar.markdown("---")
st.sidebar.caption("Operational notes")
st.sidebar.write("• Auto-extracts UPI, phones, IFSC, URLs")
st.sidebar.write("• Saves intel to shared database")
st.sidebar.write("• Keeps persona consistent across turns")

# 5. Dashboard Metrics Header
st.markdown(
    """
    <div class="app-hero">
        <div>
            <div class="section-label">AI Operations Console</div>
            <h1>🎣 ScamBait: AI Scammer Time-Waster</h1>
            <div class="caption-soft">Active offense tool that strings scammers along and extracts operational data.</div>
        </div>
        <div class="status-pill">Live • Intel capture active</div>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)
turns_count = len(st.session_state.get("messages", [])) // 2
time_wasted = turns_count * 2  # Est. 2 mins wasted per turn

col1.metric(label="⏱️ Est. Scammer Time Drained", value=f"{time_wasted} Mins")
col2.metric(label="💬 Conversational Turns", value=turns_count)
col3.metric(label="🚨 Extracted Intel Records", value=len(get_blocklist()))
st.divider()

# 6. Main Tabs
tab1, tab2 = st.tabs(["💬 Active Engagement Loop", "🛡️ Shared Blocklist Database"])

# Tab 1: Interactive Chat Loop
with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "assistant"
        avatar = "😈" if msg["role"] == "user" else "👴"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input Box
    if scammer_input := st.chat_input("Paste incoming scammer message here..."):
        st.session_state.messages.append({"role": "user", "content": scammer_input})
        with st.chat_message("user", avatar="😈"):
            st.markdown(scammer_input)

        # Run Extraction
        intel = extract_threat_intel(scammer_input)
        if intel:
            for item_type, val in intel:
                st.toast(f"🚨 Extracted & Saved: {item_type} -> {val}", icon="⚠️")

        # Generate AI Persona Response
        with st.chat_message("assistant", avatar="👴"):
            api_key = os.getenv("ANTHROPIC_API_KEY")
            
            if api_key and api_key != "your_actual_anthropic_api_key_here":
                client = anthropic.Anthropic(api_key=api_key)
                formatted_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=300,
                    system=SYSTEM_PROMPT,
                    messages=formatted_msgs
                )
                reply = response.content[0].text
            else:
                reply = "Hello sir? I am trying to open my UPI app but my glasses are missing. Which button should I press?"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

    # Download Evidence Report Button
    if st.session_state.get("messages"):
        st.divider()
        report_text = f"=== SCAMBAIT INCIDENT EVIDENCE REPORT ===\nTotal Conversation Turns: {turns_count}\n\nEXTRACTED INTEL:\n"
        for item_type, val, ts in get_blocklist():
            report_text += f"- [{item_type}] {val} (Recorded: {ts})\n"
            
        report_text += "\n=== CONVERSATION LOG ===\n"
        for m in st.session_state.messages:
            role = "SCAMMER" if m["role"] == "user" else "AI PERSONA"
            report_text += f"{role}: {m['content']}\n"

        st.download_button(
            label="📄 Export Official Cybercrime Evidence Report",
            data=report_text,
            file_name="scambait_evidence_report.txt",
            mime="text/plain"
        )

# Tab 2: Shared Blocklist View
with tab2:
    st.subheader("Extracted Threat Intelligence Database")
    blocklist_data = get_blocklist()
    
    if blocklist_data:
        st.dataframe(
            blocklist_data,
            column_config={
                "0": "Category",
                "1": "Extracted Identifier",
                "2": "Timestamp"
            },
            use_container_width=True
        )
    else:
        st.info("No threat data extracted yet. Start a chat loop to auto-capture details.")
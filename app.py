import os
import re
import sqlite3
import streamlit as st
from dotenv import load_dotenv
import anthropic

# 1. Environment & Setup
load_dotenv()
st.set_page_config(page_title="ScamBait AI", page_icon="🎣", layout="wide")

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

# 5. Dashboard Metrics Header
st.title("🎣 ScamBait: AI Scammer Time-Waster")
st.caption("Active offense tool that strings scammers along and extracts operational data.")

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
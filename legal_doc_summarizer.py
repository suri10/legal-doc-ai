import streamlit as st
import fitz  # PyMuPDF
import docx
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

# Load environment variables if running locally
load_dotenv()

# Streamlit secrets fallback
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# UI Setup
st.set_page_config(page_title="Legal Document Summarizer & Clause Flagging", layout="wide")
st.title("📄 Legal Document Analyzer")
st.markdown("Upload one or more legal documents (PDF, DOCX, or TXT). This app will generate a clause-by-clause summary and flag risky clauses like **non-compete**, **indemnity**, etc.")

uploaded_files = st.file_uploader("Upload file(s)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

RISK_KEYWORDS = [
    "non-compete", "non compete", "indemnity", "termination", "jurisdiction",
    "confidential", "penalty", "liability", "arbitration", "exclusivity"
]

def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    elif file.name.endswith(".docx"):
        return "\n".join([para.text for para in docx.Document(file).paragraphs])
    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    return ""

def summarize_clauses_with_groq(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "user", "content": f"""
You are a legal assistant AI. Break the following legal document into numbered clauses. 
For each clause:
- Summarize it briefly.
- Flag if it contains any of the following risk keywords: {', '.join(RISK_KEYWORDS)}.

Document Text:
{text}

Format the output like:
1. **Clause summary**: ...
   **Risky**: Yes/No (keyword if any)
"""}
        ],
        "temperature": 0.3
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.json()["choices"][0]["message"]["content"].strip()

def store_in_supabase(filename, content, summary):
    data = {
        "filename": filename,
        "content": content,
        "summary": summary
    }
    response = supabase.table("summaries").insert(data).execute()
    return response

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"Analyzing: {uploaded_file.name}..."):
            full_text = extract_text(uploaded_file)
            summary = summarize_clauses_with_groq(full_text)

            st.subheader(f"🧾 Summary for: {uploaded_file.name}")
            st.markdown(summary)

            # Store in Supabase
            store_in_supabase(uploaded_file.name, full_text, summary)

            # Download option
            st.download_button(
                label="Download Summary",
                data=summary,
                file_name=f"{uploaded_file.name}_summary.txt",
                mime="text/plain"
            )

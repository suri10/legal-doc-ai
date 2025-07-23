import streamlit as st
import fitz  # PyMuPDF
import docx
import os
from dotenv import load_dotenv
import openai

# Load environment variables if not on Streamlit Cloud
load_dotenv()

# Get Groq API key from Streamlit secrets or environment variable
openai.api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
openai.base_url = "https://api.groq.com/openai/v1"  # Important override for Groq

# UI
st.set_page_config(page_title="Legal Document Summarizer & Clause Flagging", layout="wide")
st.title("📄 Legal Document Analyzer")
st.markdown(
    "Upload a legal document (PDF, DOCX, or TXT), and this app will generate a clause-by-clause summary "
    "and flag risky clauses like **non-compete**, **indemnity**, etc."
)

uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"])

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
    else:
        return ""

def summarize_clauses(text):
    prompt = f"""You are a legal assistant AI. Break the following legal document into numbered clauses. 
For each clause:
- Summarize it briefly.
- Flag if it contains any of the following risk keywords: {', '.join(RISK_KEYWORDS)}.
Document Text:
{text}
Format the output like:
1. **Clause summary**: ...
   **Risky**: Yes/No (keyword if any)
"""
    response = openai.ChatCompletion.create(
        model="llama3-70b-8192",  # Groq-compatible model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

if uploaded_file:
    with st.spinner("Reading and analyzing document..."):
        full_text = extract_text(uploaded_file)
        summary = summarize_clauses(full_text)
        st.subheader("🧾 Summary and Clause Risk Flags")
        st.markdown(summary)

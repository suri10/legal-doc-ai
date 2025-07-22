import streamlit as st
import fitz  # PyMuPDF
import docx
import os
from dotenv import load_dotenv
import openai

# Use secrets if available (for Streamlit Cloud), else fallback to local .env
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

# UI
st.set_page_config(page_title="Legal Document Summarizer & Clause Flagging", layout="wide")
st.title("📄 Legal Document Analyzer")
st.markdown("Upload a legal document (PDF, DOCX, or TXT), and this app will generate a clause-by-clause summary and flag risky clauses like **non-compete**, **indemnity**, etc.")

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
        model="gpt-4",
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

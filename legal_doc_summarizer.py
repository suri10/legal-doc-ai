import streamlit as st
import fitz  # PyMuPDF for PDFs
import docx
import re

# Set up UI
st.set_page_config(page_title="Legal Doc Analyzer", layout="wide")
st.title("📄 Legal Document Summarizer & Risk Flagger")

uploaded_file = st.file_uploader("Upload Legal Document", type=["pdf", "docx", "txt"])

# Clause keyword flags
clause_keywords = {
    "Term": ["term", "duration", "valid"],
    "Confidentiality": ["confidential", "disclose", "information"],
    "Governing Law": ["law", "jurisdiction"],
    "Obligations": ["obligation", "security", "use"],
    "Exclusions": ["exclusion", "public", "third party", "not apply"],
}

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(file):
    document = docx.Document(file)
    return "\n".join([para.text for para in document.paragraphs])

def extract_text_from_txt(file):
    return file.read().decode("utf-8")

def flag_clause(text):
    clause_text_lower = text.lower()
    for label, keywords in clause_keywords.items():
        if any(k in clause_text_lower for k in keywords):
            return label, False
    return "❌ Possibly Missing Critical Context", True

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1].lower()

    if file_type == "pdf":
        text = extract_text_from_pdf(uploaded_file)
    elif file_type == "docx":
        text = extract_text_from_docx(uploaded_file)
    elif file_type == "txt":
        text = extract_text_from_txt(uploaded_file)
    else:
        st.error("Unsupported file format.")
        st.stop()

    st.subheader("📜 Clause-by-Clause Review")

    clauses = re.split(r"\n(?=[A-Z].{3,})", text.strip())
    for i, clause in enumerate(clauses):
        clause = clause.strip()
        if not clause:
            continue
        label, is_flagged = flag_clause(clause)
        if is_flagged:
            st.markdown(f"### 🚩 Clause {i+1} — {label}")
            st.error(clause)
        else:
            st.markdown(f"### ✅ Clause {i+1} — {label}")
            st.info(clause)

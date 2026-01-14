import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Fusion Doc Merger",
    page_icon="⚡",
    layout="centered"
)

# --- 2. ADVANCED CSS STYLING (The "Cool" Part) ---
st.markdown("""
    <style>
    /* RESET & BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }

    /* HEADINGS */
    h1 {
        font-weight: 800;
        background: -webkit-linear-gradient(0deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
    }
    p.subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 40px;
    }

    /* GLASS CARDS (Upload Sections) */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border-color: rgba(129, 140, 248, 0.5);
    }
    .card-title {
        color: #e2e8f0;
        font-weight: 600;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.9rem;
    }

    /* CUSTOMIZE STREAMLIT UPLOADERS */
    div[data-testid="stFileUploader"] {
        width: 100%;
    }
    div[data-testid="stFileUploader"] section {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px dashed #475569;
    }
    div[data-testid="stFileUploader"] section:hover {
        background-color: rgba(255, 255, 255, 0.1);
        border-color: #818cf8;
    }
    /* Force text color in uploader to be white */
    div[data-testid="stFileUploader"] span {
        color: #e2e8f0 !important;
    }
    div[data-testid="stFileUploader"] small {
        color: #94a3b8 !important;
    }

    /* RADIO BUTTONS */
    div[role="radiogroup"] {
        background: rgba(30, 41, 59, 0.4);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        justify-content: center;
    }
    div[role="radiogroup"] label {
        color: white !important;
        font-weight: 500;
        padding: 0 20px;
    }

    /* MAIN ACTION BUTTON */
    .stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        padding: 18px 30px;
        font-size: 18px;
        font-weight: 700;
        border-radius: 12px;
        width: 100%;
        margin-top: 20px;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.5);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 20px 25px -5px rgba(79, 70, 229, 0.6);
        color: white;
    }
    .stButton > button:active {
        transform: scale(0.98);
    }

    /* DOWNLOAD BUTTONS */
    .stDownloadButton > button {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        transition: all 0.2s;
    }
    .stDownloadButton > button:hover {
        border-color: #818cf8;
        color: #818cf8;
        background-color: #0f172a;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SECURE LOGIC ---
def get_visible_content_bottom(page):
    max_y = 0
    for block in page.get_text("blocks"):
        if block[3] > max_y: max_y = block[3]
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if r.y1 > max_y: max_y = r.y1
    if max_y == 0: return page.rect.height * 0.15
    return max_y

def process_merge(header_file, data_file, mode):
    # Secure Temp Files
    t_header = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    t_data = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    out_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    out_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name

    try:
        t_header.write(header_file.getbuffer()); t_header.close()
        t_data.write(data_file.getbuffer()); t_data.close()

        try:
            header_doc = fitz.open(t_header.name)
            data_doc = fitz.open(t_data.name)
        except:
            return None, None, "File Corrupt or Locked."

        out_doc = fitz.open()
        header_page = header_doc[0]
        page_width = header_page.rect.width
        page_height = header_page.rect.height
        
        start_y = get_visible_content_bottom(header_page) + 20 
        
        apply_all = (mode == "Apply to All Pages")
        
        for i in range(len(data_doc)):
            if i == 0 or apply_all:
                page = out_doc.new_page(width=page_width, height=page_height)
                page.show_pdf_page(fitz.Rect(0,0,page_width,page_height), header_doc, 0)
                page.show_pdf_page(fitz.Rect(0,start_y,page_width,page_height), data_doc, i)
            else:
                out_doc.insert_pdf(data_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        header_doc.close(); data_doc.close(); out_doc.close()

        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        return out_pdf, out_docx, None

    except Exception as e:
        return None, None, str(e)
    finally:
        if os.path.exists(t_header.name): os.remove(t_header.name)
        if os.path.exists(t_data.name): os.remove(t_data.name)

# --- 4. THE UI LAYOUT ---

st.markdown("<h1>⚡ FUSION DOC MERGER</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>The professional way to brand your documents.</p>", unsafe_allow_html=True)

# Layout: 2 Columns for Uploads
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class='glass-card'>
        <div class='card-title'>1. Upload Letterhead</div>
    </div>
    """, unsafe_allow_html=True)
    up_h = st.file_uploader("Header", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("""
    <div class='glass-card'>
        <div class='card-title'>2. Upload Content</div>
    </div>
    """, unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type="pdf", label_visibility="collapsed", key="d")

st.write("") # Gap

# Settings Section
st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 0.8rem; margin-bottom: 5px;'>CONFIGURATION</div>", unsafe_allow_html=True)
merge_mode = st.radio(
    "Settings",
    ["Apply to First Page Only", "Apply to All Pages"],
    horizontal=True,
    label_visibility="collapsed"
)

st.write("") # Gap

# Action Button
if st.button("INITIALIZE MERGE 🚀"):
    if up_h and up_d:
        with st.status("Processing Data...", expanded=True) as status:
            st.write("🔹 Securely reading files...")
            time.sleep(0.3)
            st.write("🔹 Calculating layout vectors...")
            
            pdf, docx, err = process_merge(up_h, up_d, merge_mode)
            
            if err:
                status.update(label="Failed", state="error")
                st.error(f"Error: {err}")
            else:
                status.update(label="Complete!", state="complete", expanded=False)
                st.balloons()
                
                # Success Area
                st.markdown("""
                <div style='background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; padding: 15px; border-radius: 10px; text-align: center; margin-top: 20px;'>
                    <h3 style='color: #10b981; margin:0;'>✅ Success! Files Ready.</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Downloads
                st.write("")
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ Download PDF", f, "Merged.pdf", "application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ Download Word", f, "Merged.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                # Cleanup
                os.remove(pdf); os.remove(docx)
    else:
        st.toast("⚠️ Please upload both files first!", icon="⚠️")

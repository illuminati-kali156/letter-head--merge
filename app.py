import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CYBER MERGE TOOL",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CYBER THEME CSS ---
st.markdown("""
    <style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* HEADERS */
    h1, h2, h3 {
        color: #00ff41 !important;
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* FILE UPLOADER */
    div[data-testid="stFileUploader"] {
        border: 1px solid #00ff41;
        background-color: #1c1f26;
        padding: 15px;
        border-radius: 5px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #1c1f26;
    }
    div[data-testid="stFileUploader"] span {
        color: #ffffff !important; 
    }
    
    /* RADIO BUTTONS */
    div[role="radiogroup"] label {
        color: white !important;
        background-color: #1c1f26;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    div[role="radiogroup"] {
        background-color: transparent;
    }
    
    /* BUTTONS */
    .stButton>button {
        width: 100%;
        background-color: transparent;
        color: #00ff41;
        border: 2px solid #00ff41;
        font-weight: bold;
        padding: 15px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        border-radius: 0px;
    }
    .stButton>button:hover {
        background-color: #00ff41;
        color: black;
        box-shadow: 0 0 20px #00ff41;
    }

    /* DOWNLOAD BUTTONS */
    .stDownloadButton>button {
        background-color: #1c1f26;
        color: white;
        border: 1px solid white;
    }
    .stDownloadButton>button:hover {
        border-color: #00ff41;
        color: #00ff41;
    }
    
    /* TEXT ELEMENTS */
    .instruction-text {
        color: #cccccc;
        font-size: 14px;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGIC FUNCTIONS ---

def get_visible_content_bottom(page):
    """Scans a PDF page to find the lowest content."""
    max_y = 0
    # Check Text
    for block in page.get_text("blocks"):
        if block[3] > max_y: max_y = block[3]
    # Check Images
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if r.y1 > max_y: max_y = r.y1
    # Fallback
    if max_y == 0: return page.rect.height * 0.15
    return max_y

def process_merge(header_file, data_file, mode):
    # Temp filenames
    t_header = "temp_header.pdf"
    t_data = "temp_data.pdf"
    out_pdf = "Final_Output.pdf"
    out_docx = "Final_Output.docx"

    with open(t_header, "wb") as f: f.write(header_file.getbuffer())
    with open(t_data, "wb") as f: f.write(data_file.getbuffer())

    try:
        header_doc = fitz.open(t_header)
        data_doc = fitz.open(t_data)
        out_doc = fitz.open()

        header_page = header_doc[0]
        page_width = header_page.rect.width
        page_height = header_page.rect.height
        
        header_bottom = get_visible_content_bottom(header_page)
        start_y = header_bottom + 20 
        
        full_rect = fitz.Rect(0, 0, page_width, page_height)
        data_rect = fitz.Rect(0, start_y, page_width, page_height)

        # Logic based on Radio Button Selection
        apply_all = (mode == "All Pages")

        for i in range(len(data_doc)):
            # Apply Header if it's Page 1 OR if User selected "All Pages"
            if i == 0 or apply_all:
                new_page = out_doc.new_page(width=page_width, height=page_height)
                new_page.show_pdf_page(full_rect, header_doc, 0) # Background
                new_page.show_pdf_page(data_rect, data_doc, i)   # Foreground
            else:
                # Copy original page as-is
                out_doc.insert_pdf(data_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        header_doc.close(); data_doc.close(); out_doc.close()

        # Word Conversion
        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        if os.path.exists(t_header): os.remove(t_header)
        if os.path.exists(t_data): os.remove(t_data)

        return out_pdf, out_docx

    except Exception as e:
        st.error(f"SYSTEM ERROR: {e}")
        return None, None

# --- UI LAYOUT ---

st.markdown("# 🖥️ CYBER DOCUMENT MERGER")
st.markdown("### // SYSTEM STATUS: ONLINE")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("<p class='instruction-text'>[INPUT 1] UPLOAD LETTERHEAD</p>", unsafe_allow_html=True)
    up_h = st.file_uploader("HEADER", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<p class='instruction-text'>[INPUT 2] UPLOAD CONTENT DATA</p>", unsafe_allow_html=True)
    up_d = st.file_uploader("DATA", type="pdf", label_visibility="collapsed", key="d")

st.divider()

# --- RADIO BUTTONS ---
st.markdown("<p class='instruction-text'>[CONFIGURATION] SELECT HEADER MODE</p>", unsafe_allow_html=True)
merge_mode = st.radio(
    "Select Header Mode",
    ["First Page Only", "All Pages"],
    label_visibility="collapsed"
)

st.write("") # Spacer

# --- EXECUTE BUTTON ---
if st.button(">>> INITIALIZE MERGE SEQUENCE <<<"):
    if up_h and up_d:
        with st.status("PROCESSING DATA STREAM...", expanded=True) as status:
            st.write("Reading Binary Data...")
            time.sleep(0.5)
            st.write("Analyzing Vector Layout...")
            time.sleep(0.5)
            st.write("Compiling PDF Structure...")
            
            pdf_path, docx_path = process_merge(up_h, up_d, merge_mode)
            
            if pdf_path:
                status.update(label="OPERATION SUCCESSFUL", state="complete", expanded=False)
                
                st.success("✅ DATA MERGE COMPLETE.")
                st.balloons()
                
                c1, c2 = st.columns(2)
                with c1:
                    with open(pdf_path, "rb") as f:
                        st.download_button("⬇ DOWNLOAD PDF", f, "Merged_Secure.pdf", "application/pdf")
                with c2:
                    with open(docx_path, "rb") as f:
                        st.download_button("⬇ DOWNLOAD WORD", f, "Merged_Editable.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.error("⚠️ INPUT ERROR: MISSING REQUIRED FILES")

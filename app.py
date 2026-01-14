import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Smart Merge Tool",
    page_icon="📄",
    layout="centered"
)

# --- MODERN UI CSS ---
st.markdown("""
    <style>
    /* General Background */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Card Container for Uploads */
    .upload-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    
    /* Headers */
    h1 {
        color: #1a1a1a;
        font-weight: 700;
        text-align: center;
        letter-spacing: -0.5px;
    }
    h3 {
        color: #4a4a4a;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    /* Customizing Streamlit's File Uploader */
    div[data-testid="stFileUploader"] {
        padding: 10px;
    }
    
    /* Primary Button Styling */
    .stButton>button {
        background-color: #2563eb; /* Royal Blue */
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: 600;
        font-size: 16px;
        border: none;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 6px 8px rgba(37, 99, 235, 0.3);
        transform: translateY(-1px);
    }
    
    /* Radio Button Container */
    .radio-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    
    /* Download Button Styling */
    .stDownloadButton>button {
        background-color: white;
        color: #1a1a1a;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-weight: 500;
    }
    .stDownloadButton>button:hover {
        border-color: #2563eb;
        color: #2563eb;
        background-color: #eff6ff;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGIC FUNCTIONS (Unchanged) ---

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

        apply_all = (mode == "All Pages")

        for i in range(len(data_doc)):
            if i == 0 or apply_all:
                new_page = out_doc.new_page(width=page_width, height=page_height)
                new_page.show_pdf_page(full_rect, header_doc, 0)
                new_page.show_pdf_page(data_rect, data_doc, i)
            else:
                out_doc.insert_pdf(data_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        header_doc.close(); data_doc.close(); out_doc.close()

        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        if os.path.exists(t_header): os.remove(t_header)
        if os.path.exists(t_data): os.remove(t_data)

        return out_pdf, out_docx

    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

# --- UI LAYOUT ---

st.markdown("<h1>📄 Document Merger Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; margin-bottom: 30px;'>Combine your Letterhead & Content seamlessly.</p>", unsafe_allow_html=True)

# 1. UPLOAD SECTION (Two Cards)
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="upload-card"><h3>1. Letterhead PDF</h3>', unsafe_allow_html=True)
    up_h = st.file_uploader("Upload Letterhead", type="pdf", label_visibility="collapsed", key="h")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="upload-card"><h3>2. Content PDF</h3>', unsafe_allow_html=True)
    up_d = st.file_uploader("Upload Content", type="pdf", label_visibility="collapsed", key="d")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. SETTINGS SECTION
st.markdown('<div class="radio-container"><h3>⚙️ Configuration</h3>', unsafe_allow_html=True)
merge_mode = st.radio(
    "How should the letterhead be applied?",
    ["First Page Only", "All Pages"],
    horizontal=True
)
st.markdown('</div>', unsafe_allow_html=True)

st.write("") # Spacer

# 3. ACTION BUTTON
if st.button("Merge & Convert Files"):
    if up_h and up_d:
        with st.status("Processing...", expanded=True) as status:
            st.write("Analyzing Document Structure...")
            time.sleep(0.5)
            st.write("Merging Layers...")
            
            pdf_path, docx_path = process_merge(up_h, up_d, merge_mode)
            
            if pdf_path:
                status.update(label="Complete!", state="complete", expanded=False)
                st.balloons()
                
                # Success Message Area
                st.success("✅ Files generated successfully!")
                
                # Download Buttons
                d_col1, d_col2 = st.columns(2)
                with d_col1:
                    with open(pdf_path, "rb") as f:
                        st.download_button("Download PDF", f, "Merged_Doc.pdf", "application/pdf", use_container_width=True)
                with d_col2:
                    with open(docx_path, "rb") as f:
                        st.download_button("Download Word Doc", f, "Merged_Doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else:
        st.warning("⚠️ Please upload both the Letterhead and Content files to continue.")

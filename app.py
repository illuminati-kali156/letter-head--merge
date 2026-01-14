import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time

# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="Pro Letterhead Merger",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR "SLEEK" LOOK ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f9f9f9;
    }
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #333;
        text-align: center;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .sub-text {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
    }
    div[data-testid="stFileUploader"] {
        border: 1px dashed #4CAF50;
        padding: 10px;
        border-radius: 10px;
        background-color: white;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 15px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- CORE LOGIC ---

def get_visible_content_bottom(page):
    """Scans a PDF page to find the lowest content."""
    max_y = 0
    # Check Text Blocks
    for block in page.get_text("blocks"):
        if block[3] > max_y: max_y = block[3]
    # Check Drawings/Images
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if r.y1 > max_y: max_y = r.y1
    # Fallback
    if max_y == 0: return page.rect.height * 0.15
    return max_y

def process_merge(header_file, data_file, apply_to_all_pages):
    # Temp filenames
    t_header = "temp_header.pdf"
    t_data = "temp_data.pdf"
    out_pdf = "Final_Output.pdf"
    out_docx = "Final_Output.docx"

    # Save uploaded files
    with open(t_header, "wb") as f: f.write(header_file.getbuffer())
    with open(t_data, "wb") as f: f.write(data_file.getbuffer())

    try:
        header_doc = fitz.open(t_header)
        data_doc = fitz.open(t_data)
        out_doc = fitz.open()

        # Layout calculations from Page 1 of Header
        header_page = header_doc[0]
        page_width = header_page.rect.width
        page_height = header_page.rect.height
        
        # Calculate split point
        header_bottom = get_visible_content_bottom(header_page)
        start_y = header_bottom + 20 
        
        # Defined Zones
        full_rect = fitz.Rect(0, 0, page_width, page_height)       # For Header
        data_rect = fitz.Rect(0, start_y, page_width, page_height) # For Content (Shifted)

        # --- MERGING PROCESS ---
        
        # Loop through ALL pages of the Data PDF
        for i in range(len(data_doc)):
            
            # Logic: Should we apply header to this page?
            # Yes if it's Page 1 (index 0) OR if 'apply_to_all_pages' is True
            apply_header_here = (i == 0) or apply_to_all_pages

            if apply_header_here:
                # 1. Create a new blank page
                new_page = out_doc.new_page(width=page_width, height=page_height)
                
                # 2. Draw Header (Background)
                new_page.show_pdf_page(full_rect, header_doc, 0)
                
                # 3. Draw Data (Shifted Down)
                new_page.show_pdf_page(data_rect, data_doc, i)
            
            else:
                # Just copy the original page as-is (No header, no shift)
                out_doc.insert_pdf(data_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        header_doc.close()
        data_doc.close()
        out_doc.close()

        # --- WORD CONVERSION ---
        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        # Cleanup
        if os.path.exists(t_header): os.remove(t_header)
        if os.path.exists(t_data): os.remove(t_data)

        return out_pdf, out_docx

    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

# --- WEB INTERFACE ---

st.markdown("<h1 class='main-header'>✨ Smart Letterhead Merger</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-text'>Combine your Letterhead & Content into a perfect PDF + Word Doc.</p>", unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 1️⃣ Upload Header")
    up_h = st.file_uploader("Upload Letterhead PDF", type="pdf", label_visibility="collapsed")

with col2:
    st.markdown("### 2️⃣ Upload Content")
    up_d = st.file_uploader("Upload Content PDF", type="pdf", label_visibility="collapsed")

# --- OPTIONS SECTION ---
st.write("")
st.markdown("### ⚙️ Settings")
# The cool toggle switch
apply_all = st.toggle("Apply Letterhead to ALL pages?", value=False, help="If on, the header will appear on every page. If off, only on the first page.")

st.write("") # Spacer

# --- ACTION BUTTON ---
if st.button("🚀 Merge & Convert Files"):
    if up_h and up_d:
        
        # Animation: Progress Bar
        progress_text = "Analyzing Layout & Merging..."
        my_bar = st.progress(0, text=progress_text)

        # Step 1
        time.sleep(0.5)
        my_bar.progress(30, text="Detecting Header Space...")
        
        # Step 2: Processing
        pdf_path, docx_path = process_merge(up_h, up_d, apply_all)
        
        # Step 3: Finish
        my_bar.progress(100, text="Finalizing...")
        time.sleep(0.3)
        my_bar.empty() # Remove progress bar

        if pdf_path and docx_path:
            st.balloons() # <--- COOL ANIMATION
            st.success("✅ Success! Your files are ready.")
            
            # Two columns for download buttons
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                with open(pdf_path, "rb") as f:
                    st.download_button("⬇️ Download PDF", f, "Merged_Doc.pdf", "application/pdf")
            
            with d_col2:
                with open(docx_path, "rb") as f:
                    st.download_button("⬇️ Download Word Doc", f, "Merged_Doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.toast("⚠️ Please upload both files first!", icon="⚠️")

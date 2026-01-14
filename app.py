import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter

# --- CORE LOGIC (Adapted for Web) ---

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

def process_merge(header_file, data_file):
    # Temp filenames
    t_header = "temp_header.pdf"
    t_data = "temp_data.pdf"
    out_pdf = "Final_Output.pdf"
    out_docx = "Final_Output.docx"

    # Save uploaded files to disk
    with open(t_header, "wb") as f: f.write(header_file.getbuffer())
    with open(t_data, "wb") as f: f.write(data_file.getbuffer())

    try:
        # --- PHASE 1: MERGE ---
        header_doc = fitz.open(t_header)
        data_doc = fitz.open(t_data)
        out_doc = fitz.open()

        header_page = header_doc[0]
        page_width = header_page.rect.width
        page_height = header_page.rect.height
        
        # Calculate split point
        header_bottom = get_visible_content_bottom(header_page)
        start_y = header_bottom + 20 

        # Page 1
        merged_page = out_doc.new_page(width=page_width, height=page_height)
        merged_page.show_pdf_page(merged_page.rect, header_doc, 0)
        data_rect = fitz.Rect(0, start_y, page_width, page_height)
        merged_page.show_pdf_page(data_rect, data_doc, 0)

        # Other Pages
        if len(data_doc) > 1:
            out_doc.insert_pdf(data_doc, from_page=1, to_page=len(data_doc)-1)

        out_doc.save(out_pdf)
        header_doc.close()
        data_doc.close()
        out_doc.close()

        # --- PHASE 2: WORD CONVERSION ---
        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        # Cleanup inputs
        os.remove(t_header)
        os.remove(t_data)

        return out_pdf, out_docx

    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

# --- WEB INTERFACE ---

st.set_page_config(page_title="Letterhead Merger", layout="centered")

st.title("📄 Smart Letterhead Merger")
st.write("Upload your Header and Content files. The tool will auto-merge them and give you an editable Word Doc.")

col1, col2 = st.columns(2)
with col1:
    up_h = st.file_uploader("1. Header PDF", type="pdf")
with col2:
    up_d = st.file_uploader("2. Content PDF", type="pdf")

if st.button("🚀 Merge & Convert", type="primary"):
    if up_h and up_d:
        with st.spinner("Processing... Please wait..."):
            pdf_path, docx_path = process_merge(up_h, up_d)
            
            if pdf_path and docx_path:
                st.success("✅ Done! Download your files below:")
                
                # Download Buttons
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f, "Merged_Document.pdf", "application/pdf")
                
                with open(docx_path, "rb") as f:
                    st.download_button("Download Word Doc", f, "Merged_Document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("⚠️ Please upload both files first.")

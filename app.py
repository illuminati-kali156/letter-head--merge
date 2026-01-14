import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile # <--- SECURITY FIX

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Smart Merge Tool", page_icon="🔒", layout="centered")

# --- UI CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; font-family: sans-serif; }
    .upload-card { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    h1 { text-align: center; color: #1a1a1a; }
    .stButton>button { background-color: #2563eb; color: white; border-radius: 8px; height: 50px; font-weight: 600; width: 100%; border: none; }
    .stButton>button:hover { background-color: #1d4ed8; }
    </style>
""", unsafe_allow_html=True)

# --- SECURE LOGIC ---

def get_visible_content_bottom(page):
    """Scans a PDF page to find the lowest content."""
    max_y = 0
    for block in page.get_text("blocks"):
        if block[3] > max_y: max_y = block[3]
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if r.y1 > max_y: max_y = r.y1
    if max_y == 0: return page.rect.height * 0.15
    return max_y

def process_merge(header_file, data_file, mode):
    # 1. SECURITY: Create Unique Temp Files
    # delete=False is required because we need to close the file to let PyMuPDF open it
    t_header = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    t_data = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    
    # Define output paths (also unique logic recommended, but local path ok for Streamlit return)
    out_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    out_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name

    try:
        # Write uploaded binary data to the unique temp files
        t_header.write(header_file.getbuffer())
        t_data.write(data_file.getbuffer())
        
        # Close the file handles so other libraries can access them
        t_header.close()
        t_data.close()

        # --- BUG CHECK: Open Files Safely ---
        try:
            header_doc = fitz.open(t_header.name)
            data_doc = fitz.open(t_data.name)
        except Exception:
            return None, None, "Files are corrupt or Password Protected. Please unlock them first."

        out_doc = fitz.open()

        # Layout Calc
        header_page = header_doc[0]
        page_width = header_page.rect.width
        page_height = header_page.rect.height
        header_bottom = get_visible_content_bottom(header_page)
        start_y = header_bottom + 20 

        # Rectangles
        full_rect = fitz.Rect(0, 0, page_width, page_height)
        data_rect = fitz.Rect(0, start_y, page_width, page_height)

        apply_all = (mode == "All Pages")

        # --- MERGE LOOP ---
        for i in range(len(data_doc)):
            if i == 0 or apply_all:
                new_page = out_doc.new_page(width=page_width, height=page_height)
                new_page.show_pdf_page(full_rect, header_doc, 0)
                new_page.show_pdf_page(data_rect, data_doc, i)
            else:
                out_doc.insert_pdf(data_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        
        # Close handles
        header_doc.close()
        data_doc.close()
        out_doc.close()

        # Word Conversion
        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        return out_pdf, out_docx, None # None = No Error

    except Exception as e:
        return None, None, str(e)
        
    finally:
        # 2. SECURITY: Force Cleanup
        # Regardless of errors, delete the temp input files
        if os.path.exists(t_header.name): os.remove(t_header.name)
        if os.path.exists(t_data.name): os.remove(t_data.name)

# --- UI ---

st.markdown("<h1>🔒 Secure Document Merger</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Your files are processed securely in isolated sessions.</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="upload-card"><h3>1. Letterhead PDF</h3>', unsafe_allow_html=True)
    up_h = st.file_uploader("Upload Letterhead", type="pdf", label_visibility="collapsed", key="h")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="upload-card"><h3>2. Content PDF</h3>', unsafe_allow_html=True)
    up_d = st.file_uploader("Upload Content", type="pdf", label_visibility="collapsed", key="d")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
merge_mode = st.radio("Configuration", ["First Page Only", "All Pages"], horizontal=True)
st.write("")

if st.button("Merge Files"):
    if up_h and up_d:
        with st.status("Processing Securely...", expanded=True) as status:
            st.write("Creating Isolated Session...")
            time.sleep(0.3)
            st.write("Merging Data...")
            
            pdf_path, docx_path, error_msg = process_merge(up_h, up_d, merge_mode)
            
            if error_msg:
                status.update(label="Error Failed", state="error", expanded=True)
                st.error(f"❌ Error: {error_msg}")
            else:
                status.update(label="Complete!", state="complete", expanded=False)
                st.balloons()
                st.success("✅ Secure Merge Complete.")
                
                c1, c2 = st.columns(2)
                with c1:
                    with open(pdf_path, "rb") as f:
                        st.download_button("Download PDF", f, "Merged_Doc.pdf", "application/pdf", use_container_width=True)
                with c2:
                    with open(docx_path, "rb") as f:
                        st.download_button("Download Word", f, "Merged_Doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                # Cleanup Output files after reading
                os.remove(pdf_path)
                os.remove(docx_path)
    else:
        st.warning("⚠️ Please upload both files.")

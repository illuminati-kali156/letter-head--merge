import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile
import hashlib
import io
from PIL import Image

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Super AAI Bio Energy",
    page_icon="🌾",
    layout="centered"
)

# --- 2. SESSION STATE ---
if "auth_status" not in st.session_state:
    st.session_state.auth_status = "locked"
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []
if "login_msg" not in st.session_state:
    st.session_state.login_msg = ""

# --- 3. FARM THEME & VISIBILITY CSS ---
st.markdown("""
    <style>
    /* GLOBAL */
    .stApp {
        background: linear-gradient(to bottom, #87CEEB 0%, #E0F7FA 50%, #e8f5e9 100%);
        font-family: 'Verdana', sans-serif;
        color: #1b5e20;
    }

    /* CURSOR */
    button:hover {
        cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='40' height='48' viewport='0 0 100 100' style='fill:black;font-size:24px;'><text y='50%'>🚜</text></svg>") 16 0, auto; 
    }

    /* ANIMATIONS */
    @keyframes leaf-fall {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 0; }
        10% { opacity: 1; }
        100% { transform: translateY(110vh) rotate(360deg); opacity: 0; }
    }
    .leaf {
        position: fixed;
        font-size: 20px;
        color: #2e7d32;
        animation: leaf-fall 10s linear infinite;
        z-index: 1;
        pointer-events: none;
    }

    /* CARDS */
    .farm-card {
        background: rgba(255, 255, 255, 0.95);
        border: 2px solid #a5d6a7;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        text-align: center;
        margin-bottom: 20px;
    }

    /* TEXT & INPUTS */
    h1 { color: #1b5e20; font-weight: 800; text-shadow: 2px 2px 4px rgba(255,255,255,0.8); }
    p, label { color: #2e7d32 !important; font-weight: 600; }
    
    .stTextInput input {
        background-color: #ffffff !important;
        border: 2px solid #4caf50 !important;
        color: #1b5e20 !important;
        text-align: center;
        font-weight: bold;
    }

    /* BUTTONS */
    .stButton button {
        background: linear-gradient(145deg, #66bb6a, #43a047);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 15px 32px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.3);
    }

    /* --- UPLOAD BOX VISIBILITY FIX --- */
    
    /* 1. Force the Upload Box Background to White */
    div[data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 2px dashed #1b5e20 !important;
        padding: 15px;
        border-radius: 10px;
    }

    /* 2. Force Instruction Text ("Drag and drop") to Dark Green */
    div[data-testid="stFileUploader"] section {
        color: #1b5e20 !important;
    }
    div[data-testid="stFileUploader"] section span {
        color: #1b5e20 !important;
        font-weight: bold !important;
    }
    
    /* 3. Force Small Text ("Limit 200MB") to Grey */
    div[data-testid="stFileUploader"] section small {
        color: #666666 !important;
    }

    /* 4. Force Uploaded File Name to BLACK */
    div[data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 14px !important;
    }

    /* 5. Force the "Browse files" button */
    div[data-testid="stFileUploader"] button {
        background-color: #4caf50 !important;
        color: white !important;
        border: none !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>

    <div class="leaf" style="left: 10%; animation-duration: 8s;">🍃</div>
    <div class="leaf" style="left: 30%; animation-duration: 12s; font-size: 24px;">🍂</div>
    <div class="leaf" style="left: 70%; animation-duration: 10s;">🍃</div>
""", unsafe_allow_html=True)

# --- 4. BACKEND LOGIC (SMART IMAGE HANDLER) ---

def get_visible_content_bottom(page):
    """Finds the lowest point of content on a PDF page."""
    max_y = 0
    try:
        for block in page.get_text("blocks"):
            if block[3] > max_y: max_y = block[3]
        for img in page.get_images(full=True):
            for r in page.get_image_rects(img[0]):
                if r.y1 > max_y: max_y = r.y1
    except:
        pass
    if max_y == 0: return page.rect.height * 0.15
    return max_y

def convert_to_pdf_doc(uploaded_file):
    """
    Helper: Takes any uploaded file (PDF, PNG, JPG) and returns a PyMuPDF Document object.
    """
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()
    uploaded_file.seek(0) # Reset pointer

    # 1. If PDF, open directly
    if filename.endswith(".pdf"):
        try:
            return fitz.open(stream=file_bytes, filetype="pdf")
        except:
            return None

    # 2. If Image, convert to PDF in memory
    if filename.endswith((".png", ".jpg", ".jpeg")):
        try:
            # Use PyMuPDF to open image and convert to PDF
            img_doc = fitz.open(stream=file_bytes, filetype=filename.split('.')[-1])
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()
            return fitz.open("pdf", pdf_bytes)
        except:
            return None
    
    return None

def generate_preview(header_file, data_file, y_offset, header_scale, use_standard):
    try:
        # Convert inputs to standardized PDF Docs (Handles Images automatically)
        h_doc = convert_to_pdf_doc(header_file)
        d_doc = convert_to_pdf_doc(data_file)

        if not h_doc or not d_doc:
            return None

        # Create output canvas
        out_doc = fitz.open()
        h_page = h_doc[0]
        w, h = h_page.rect.width, h_page.rect.height
        
        # Positioning
        if use_standard:
            start_y = 130 + y_offset
        else:
            base_y = get_visible_content_bottom(h_page)
            start_y = base_y + 10 + y_offset 

        scaled_h = h * (header_scale / 100.0)
        
        # Create Page 1
        p = out_doc.new_page(width=w, height=h)
        
        # Draw Header
        p.show_pdf_page(fitz.Rect(0, 0, w, scaled_h), h_doc, 0)
        
        # Draw Body
        p.show_pdf_page(fitz.Rect(0, start_y, w, h), d_doc, 0)
        
        # Render Image
        pix = p.get_pixmap(dpi=100) 
        img_data = pix.tobytes("png")
        
        h_doc.close(); d_doc.close(); out_doc.close()
        return img_data

    except Exception as e:
        print(f"Preview Error: {e}")
        return None

def process_merge(header_file, data_file, mode, y_offset, header_scale, use_standard):
    t_header = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    t_data = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    out_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    out_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
    clean_paths = [t_header.name, t_data.name]

    try:
        # Check for DOCX (Server limitation)
        if data_file.name.lower().endswith(".docx"):
            return None, None, "Please upload PDF or Image. (Word conversion requires dedicated server)"

        # Convert inputs to PDF Docs
        h_doc = convert_to_pdf_doc(header_file)
        d_doc = convert_to_pdf_doc(data_file)

        if not h_doc or not d_doc:
            return None, None, "Could not read files. Ensure they are valid PDF or Images."

        out_doc = fitz.open()
        h_page = h_doc[0]
        w, h = h_page.rect.width, h_page.rect.height
        
        # Positioning Logic
        if use_standard:
            start_y = 130 + y_offset 
        else:
            base_y = get_visible_content_bottom(h_page)
            start_y = base_y + 10 + y_offset 
        
        scaled_h = h * (header_scale / 100.0)
        apply_all = (mode == "Apply to All Pages")

        # Merge Loop
        for i in range(len(d_doc)):
            if i == 0 or apply_all:
                p = out_doc.new_page(width=w, height=h)
                p.show_pdf_page(fitz.Rect(0, 0, w, scaled_h), h_doc, 0)
                p.show_pdf_page(fitz.Rect(0, start_y, w, h), d_doc, i)
            else:
                out_doc.insert_pdf(d_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        h_doc.close(); d_doc.close(); out_doc.close()

        # Create Word version
        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        return out_pdf, out_docx, None

    except Exception as e:
        return None, None, str(e)
    finally:
        for p in clean_paths:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

# --- 5. AUTH & PUZZLE ---

def verify_password_hash(input_pass):
    CORRECT_HASH = "628e41e64c14ca3498d99dad723852dc446fd56dc555a3f5a91117da51d90469"
    return hashlib.sha256(input_pass.strip().encode()).hexdigest() == CORRECT_HASH

def check_password_callback():
    if verify_password_hash(st.session_state.password_input):
        st.session_state.auth_status = "puzzle"
        st.session_state.login_msg = ""
    else:
        st.session_state.login_msg = "❌ Incorrect Password (चुकीचा पासवर्ड)"

def puzzle_click(icon):
    st.session_state.puzzle_sequence.append(icon)
    target = ["🌽", "🫧", "⚡"]
    current_idx = len(st.session_state.puzzle_sequence) - 1
    
    if current_idx >= len(target):
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ Resetting...", icon="🔄")
        return

    if st.session_state.puzzle_sequence[current_idx] != target[current_idx]:
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ Wrong Step! (चुकीची पायरी)", icon="❌")
        return

    if len(st.session_state.puzzle_sequence) == 3:
        st.session_state.auth_status = "unlocked"

# --- 6. LOGIN UI ---

if st.session_state.auth_status != "unlocked":
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='farm-card'>", unsafe_allow_html=True)
        st.markdown("<h1>🌾 Bio-Energy Farm</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.9em;'>Super AAI Bio Energy Pvt Ltd</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.auth_status == "locked":
            st.text_input("Enter Passkey (पासवर्ड)", type="password", key="password_input", on_change=check_password_callback)
            if st.session_state.login_msg: st.error(st.session_state.login_msg)

        elif st.session_state.auth_status == "puzzle":
            st.markdown("### 🚜 Start Process")
            st.caption("Feedstock → Digestion → Energy")
            
            seq = st.session_state.puzzle_sequence
            l_corn = "✅ 🌽" if "🌽" in seq else "🌽"
            l_bub  = "✅ 🫧" if "🫧" in seq else "🫧"
            l_bolt = "✅ ⚡" if "⚡" in seq else "⚡"
            
            c1, c2, c3 = st.columns(3)
            with c1: st.button(l_corn, on_click=puzzle_click, args=("🌽",), disabled="🌽" in seq, use_container_width=True)
            with c2: st.button(l_bub, on_click=puzzle_click, args=("🫧",), disabled="🫧" in seq, use_container_width=True)
            with c3: st.button(l_bolt, on_click=puzzle_click, args=("⚡",), disabled="⚡" in seq, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. DASHBOARD ---

st.markdown("<h1 style='text-align:center;'>Super AAI BIO Energy PVT LTD</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Secure Document Portal</p>", unsafe_allow_html=True)

if st.sidebar.button("🔒 Logout"):
    st.session_state.auth_status = "locked"
    st.session_state.puzzle_sequence = []
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='farm-card'><h3>📄 Letterhead</h3><p>Upload Header (PDF/IMG)</p></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("Header", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed", key="h")
with col2:
    st.markdown("<div class='farm-card'><h3>📝 Content</h3><p>Upload Body (PDF/IMG)</p></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed", key="d")

# --- SETTINGS SECTION ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='farm-card'>", unsafe_allow_html=True)
st.markdown("### ⚙️ Layout & Tools")

tab1, tab2 = st.tabs(["📏 Layout", "📐 Header Sizer"])

with tab1:
    mode = st.radio("Header Mode", ["Apply to First Page Only", "Apply to All Pages"], horizontal=True)
    st.markdown("---")
    use_standard = st.checkbox("✅ Use Industry Standard Gap (1.8 inches)", value=False)
    y_offset = st.slider("Fine-Tune Position (+/-)", min_value=-100, max_value=200, value=0)

with tab2:
    st.info("Shrink the header if it looks too big.")
    header_scale = st.slider("Header Size %", min_value=50, max_value=100, value=100)

st.markdown("---")
custom_name = st.text_input("Output Filename:", value="Bio_Farm_Doc")

if st.button("👁️ Show Preview (प्रीव्ह्यू पहा)"):
    if up_h and up_d:
        with st.spinner("Generating Preview..."):
            img_bytes = generate_preview(up_h, up_d, y_offset, header_scale, use_standard)
            if img_bytes:
                st.image(img_bytes, caption="Page 1 Preview", use_container_width=True)
            else:
                st.error("Preview failed. Ensure valid files.")
    else:
        st.warning("Upload files first!")

st.markdown("</div>", unsafe_allow_html=True)

# GENERATE
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚜 GENERATE DOCUMENT (फाइल बनवा)"):
    if up_h and up_d:
        with st.status("Processing... (प्रक्रिया सुरू आहे)", expanded=True) as status:
            st.write("🌿 Reading Files...")
            time.sleep(0.5)
            st.write("⚙️ Merging...")
            
            pdf, docx, err = process_merge(up_h, up_d, mode, y_offset, header_scale, use_standard)
            
            if err:
                status.update(label="Error", state="error")
                st.error(f"Error: {err}")
            else:
                status.update(label="Success!", state="complete", expanded=False)
                clean_name = "".join(x for x in custom_name if x.isalnum() or x in "_-")
                if not clean_name: clean_name = "Document"
                
                st.balloons()
                st.success("✅ Files Ready!")
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ Download PDF", f, file_name=f"{clean_name}.pdf", mime="application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ Download Word", f, file_name=f"{clean_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                os.remove(pdf); os.remove(docx)
    else:
        st.warning("⚠️ Please upload both files!")

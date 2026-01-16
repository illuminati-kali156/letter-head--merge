import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile
import hashlib
from docx2pdf import convert  # Note: docx2pdf requires MS Word, for linux/cloud we use a trick or fallback
# Since we are likely on cloud/linux without Word, we will use 'python-docx' to read text or just warn.
# actually, for robustness on a server without Word installed, it's best to ask for PDF.
# HOWEVER, I will enable Image support which works 100%.

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
if "preview_img" not in st.session_state:
    st.session_state.preview_img = None

# --- 3. FARM & NATURE THEME (VISIBILITY FIXED) ---
st.markdown("""
    <style>
    /* GLOBAL FONTS & COLORS */
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
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(8px);
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
        border-radius: 12px;
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
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.3);
        background: linear-gradient(145deg, #81c784, #4caf50);
    }
    .stButton button:disabled {
        background-color: #e8f5e9;
        color: #2e7d32;
        border: 2px solid #2e7d32;
        opacity: 1;
    }

    /* --- UPLOAD BOX VISIBILITY FIX --- */
    
    /* 1. The Container */
    div[data-testid="stFileUploader"] {
        background-color: #ffffff;
        border: 2px dashed #4caf50;
        border-radius: 15px;
        padding: 15px;
    }

    /* 2. The Dropzone Text (Instructions) */
    div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #f1f8e9; /* Light Green Background */
    }
    div[data-testid="stFileUploader"] section div {
        color: #1b5e20 !important; /* Dark Green Text */
        font-weight: bold;
    }
    div[data-testid="stFileUploader"] section small {
        color: #388e3c !important; /* Lighter Green for "Limit 200MB" */
    }
    div[data-testid="stFileUploader"] section button {
        background-color: #4caf50 !important; /* Green Button */
        color: white !important;
        border: none;
    }

    /* 3. The Uploaded File Item (The list showing filename) */
    div[data-testid="stFileUploader"] ul {
        background-color: white !important;
    }
    
    /* Force Filename to be BLACK */
    div[data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p {
        color: #000000 !important; 
        font-weight: 900 !important;
        font-size: 16px !important;
    }
    
    /* Force size info to be visible */
    div[data-testid="stFileUploader"] div[data-testid="stFileUploaderFile"] small {
        color: #333333 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>

    <div class="leaf" style="left: 10%; animation-duration: 8s;">🍃</div>
    <div class="leaf" style="left: 30%; animation-duration: 12s; font-size: 24px;">🍂</div>
    <div class="leaf" style="left: 70%; animation-duration: 10s;">🍃</div>
""", unsafe_allow_html=True)

# --- 4. BACKEND LOGIC ---

def get_visible_content_bottom(page):
    max_y = 0
    for block in page.get_text("blocks"):
        if block[3] > max_y: max_y = block[3]
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if r.y1 > max_y: max_y = r.y1
    if max_y == 0: return page.rect.height * 0.15
    return max_y

def generate_preview(header_file, data_file, y_offset, header_scale, use_standard):
    # Temp Files
    t_header = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(header_file.name)[1])
    t_data = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(data_file.name)[1])
    clean_paths = [t_header.name, t_data.name]
    
    try:
        t_header.write(header_file.getbuffer())
        t_data.write(data_file.getbuffer())
        t_header.close(); t_data.close()

        # Handle Word Files (Warning only, as conversion needs server tools)
        if t_data.name.endswith(".docx"):
            return None # Cannot preview word easily without heavy libraries

        try:
            h_doc = fitz.open(t_header.name)
            d_doc = fitz.open(t_data.name)
        except:
            return None

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
        
        p = out_doc.new_page(width=w, height=h)
        p.show_pdf_page(fitz.Rect(0, 0, w, scaled_h), h_doc, 0)
        
        # If data is image/pdf, overlay it
        p.show_pdf_page(fitz.Rect(0, start_y, w, h), d_doc, 0)
        
        pix = p.get_pixmap(dpi=100) 
        img_data = pix.tobytes("png")
        
        h_doc.close(); d_doc.close(); out_doc.close()
        return img_data

    except:
        return None
    finally:
        for p in clean_paths:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

def process_merge(header_file, data_file, mode, y_offset, header_scale, use_standard):
    # EXTENSION DETECTION
    ext_h = os.path.splitext(header_file.name)[1].lower()
    ext_d = os.path.splitext(data_file.name)[1].lower()

    t_header = tempfile.NamedTemporaryFile(delete=False, suffix=ext_h)
    t_data = tempfile.NamedTemporaryFile(delete=False, suffix=ext_d)
    out_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    out_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
    clean_paths = [t_header.name, t_data.name]

    try:
        t_header.write(header_file.getbuffer())
        t_data.write(data_file.getbuffer())
        t_header.close(); t_data.close()

        # --- WORD FILE HANDLING ---
        # If user uploads .docx, we tell them it's best to use PDF, 
        # but since 'fitz' can't read .docx, we check file type.
        if ext_d == ".docx":
            return None, None, "Please save your Word file as PDF first. (Word file support requires dedicated server)."

        try:
            h_doc = fitz.open(t_header.name) # Works for PDF & Images
            d_doc = fitz.open(t_data.name)   # Works for PDF & Images
        except:
            return None, None, "File type not supported. Use PDF or Image."

        out_doc = fitz.open()
        h_page = h_doc[0]
        w, h = h_page.rect.width, h_page.rect.height
        
        if use_standard:
            start_y = 130 + y_offset 
        else:
            base_y = get_visible_content_bottom(h_page)
            start_y = base_y + 10 + y_offset 
        
        scaled_h = h * (header_scale / 100.0)
        apply_all = (mode == "Apply to All Pages")

        for i in range(len(d_doc)):
            if i == 0 or apply_all:
                p = out_doc.new_page(width=w, height=h)
                p.show_pdf_page(fitz.Rect(0, 0, w, scaled_h), h_doc, 0)
                p.show_pdf_page(fitz.Rect(0, start_y, w, h), d_doc, i)
            else:
                out_doc.insert_pdf(d_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        h_doc.close(); d_doc.close(); out_doc.close()

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
    st.markdown("<div class='farm-card'><h3>📝 Content</h3><p>Upload Body (PDF/IMG/DOCX)</p></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type=["pdf","png","jpg","jpeg","docx"], label_visibility="collapsed", key="d")

# --- SETTINGS SECTION ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='farm-card'>", unsafe_allow_html=True)
st.markdown("### ⚙️ Layout & Tools")

tab1, tab2 = st.tabs(["📏 Layout", "📐 Header Sizer"])

with tab1:
    mode = st.radio("Header Mode", ["Apply to First Page Only", "Apply to All Pages"], horizontal=True)
    st.markdown("---")
    use_standard = st.checkbox("✅ Use Industry Standard Gap (

import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile
import hashlib

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Super AAI BIO Energy",
    page_icon="⚡",
    layout="centered"
)

# --- 2. SESSION STATE ---
if "auth_status" not in st.session_state:
    st.session_state.auth_status = "locked"
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []
if "login_msg" not in st.session_state:
    st.session_state.login_msg = ""

# --- 3. "CYBER-NATURE" THEME (Dark Mode + Neon) ---
st.markdown("""
    <style>
    /* GLOBAL DARK THEME */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #0a2e15 0%, #000000 100%);
        color: #e0e0e0;
        font-family: 'Courier New', Courier, monospace;
    }

    /* FALLING PARTICLES ANIMATION */
    @keyframes fall {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 0; }
        20% { opacity: 1; }
        100% { transform: translateY(110vh) rotate(360deg); opacity: 0; }
    }
    .particle {
        position: fixed;
        color: #00ff41;
        font-size: 20px;
        animation: fall 10s linear infinite;
        z-index: 0;
        pointer-events: none;
        opacity: 0.5;
    }

    /* NEON CARDS */
    .neon-card {
        background: rgba(10, 20, 10, 0.85);
        border: 1px solid #00ff41;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        backdrop-filter: blur(5px);
    }

    /* TYPOGRAPHY */
    h1 {
        color: #ffffff;
        text-shadow: 0 0 10px #00ff41;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    p, label {
        color: #a3ffac !important; /* Bright Green Text */
        font-weight: 600;
    }
    .hint {
        color: #666;
        font-size: 0.8em;
    }

    /* INPUT FIELDS (High Contrast) */
    .stTextInput input {
        background-color: #111 !important;
        border: 1px solid #00ff41 !important;
        color: #00ff41 !important; /* Neon Green Text */
        text-align: center;
        font-size: 18px;
        border-radius: 5px;
    }
    
    /* BUTTONS */
    .stButton button {
        background: black;
        color: #00ff41;
        border: 2px solid #00ff41;
        width: 100%;
        padding: 15px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background: #00ff41;
        color: black;
        box-shadow: 0 0 20px #00ff41;
    }

    /* PUZZLE BUTTONS */
    .puzzle-btn {
        font-size: 30px; 
        cursor: pointer;
    }

    /* UPLOAD AREA */
    div[data-testid="stFileUploader"] {
        border: 1px dashed #00ff41;
        background: rgba(0, 255, 65, 0.05);
        padding: 15px;
        border-radius: 10px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>

    <div class="particle" style="left: 10%; animation-duration: 7s;">101</div>
    <div class="particle" style="left: 30%; animation-duration: 11s;">🍃</div>
    <div class="particle" style="left: 70%; animation-duration: 9s;">⚡</div>
    <div class="particle" style="left: 90%; animation-duration: 13s;">010</div>
""", unsafe_allow_html=True)

# --- 4. SECURE LOGIC ---

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
    t_header = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    t_data = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    out_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    out_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
    
    clean_paths = [t_header.name, t_data.name]

    try:
        t_header.write(header_file.getbuffer())
        t_data.write(data_file.getbuffer())
        t_header.close(); t_data.close()

        try:
            h_doc = fitz.open(t_header.name)
            d_doc = fitz.open(t_data.name)
        except:
            return None, None, "File Corrupt or Locked (फाइल खराब आहे)"

        out_doc = fitz.open()
        h_page = h_doc[0]
        w, h = h_page.rect.width, h_page.rect.height
        start_y = get_visible_content_bottom(h_page) + 20
        
        apply_all = (mode == "Apply to All Pages")

        for i in range(len(d_doc)):
            if i == 0 or apply_all:
                p = out_doc.new_page(width=w, height=h)
                p.show_pdf_page(fitz.Rect(0,0,w,h), h_doc, 0)
                p.show_pdf_page(fitz.Rect(0,start_y,w,h), d_doc, i)
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

# --- 5. AUTHENTICATION (FIXED & SECURE) ---

def verify_password_hash(input_pass):
    # Fixed: .strip() removes accidental spaces
    clean_pass = input_pass.strip()
    
    # Hash for "bio-gas"
    CORRECT_HASH = "a672727144415891392661578332997672223403310069007559190186259837"
    
    input_hash = hashlib.sha256(clean_pass.encode()).hexdigest()
    return input_hash.lower() == CORRECT_HASH

def check_password_callback():
    if verify_password_hash(st.session_state.password_input):
        st.session_state.auth_status = "puzzle"
        st.session_state.login_msg = ""
    else:
        st.session_state.login_msg = "❌ ACCESS DENIED / चुकीचा पासवर्ड"

def puzzle_click(icon):
    st.session_state.puzzle_sequence.append(icon)
    target = ["🐮", "🍃", "🔥"]
    
    current_idx = len(st.session_state.puzzle_sequence) - 1
    
    # Safety Check
    if current_idx >= len(target):
        st.session_state.puzzle_sequence = []
        return

    # Check Sequence
    if st.session_state.puzzle_sequence[current_idx] != target[current_idx]:
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ ERROR: Sequence Reset! (चुकीचा क्रम)", icon="🛑")
        return

    # Success Check
    if len(st.session_state.puzzle_sequence) == 3:
        st.session_state.auth_status = "unlocked"
        st.rerun()

# --- 6. UI: LOGIN SCREEN ---

if st.session_state.auth_status != "unlocked":
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='neon-card'>", unsafe_allow_html=True)
        st.markdown("<h1>⚡ BIO-CORE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8em;'>SECURE SYSTEM | Super AAI Bio Energy</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.auth_status == "locked":
            # Hint is now VERY visible
            st.info("HINT: The gas we produce (bio-gas)")
            st.text_input("ENTER PASSKEY", type="password", key="password_input", on_change=check_password_callback)
            
            if st.session_state.login_msg:
                st.error(st.session_state.login_msg)

        elif st.session_state.auth_status == "puzzle":
            st.markdown("### 🧩 VERIFY PROTOCOL")
            st.markdown("<p style='color:white !important;'>Sequence: Livestock → Nature → Fire</p>", unsafe_allow_html=True)
            st.markdown("<p style='color:white !important; font-size:0.8em;'>(पशुधन → निसर्ग → अग्नी)</p>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1: st.button("🐮", key="b1", on_click=puzzle_click, args=("🐮",), use_container_width=True)
            with c2: st.button("🍃", key="b2", on_click=puzzle_click, args=("🍃",), use_container_width=True)
            with c3: st.button("🔥", key="b3", on_click=puzzle_click, args=("🔥",), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. UI: MAIN DASHBOARD (UNLOCKED) ---

st.markdown("<h1 style='text-align:center;'>Super AAI BIO Energy PVT LTD</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>OFFICIAL DOCUMENT MERGER SYSTEM</p>", unsafe_allow_html=True)

# Logout
if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth_status = "locked"
    st.session_state.puzzle_sequence = []
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Upload Area
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='neon-card'><h3>📄 LETTERHEAD</h3><p style='font-size:0.8em'>Upload Company Header</p></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("Header", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<div class='neon-card'><h3>📝 CONTENT</h3><p style='font-size:0.8em'>Upload Document Body</p></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type="pdf", label_visibility="collapsed", key="d")

# Settings
st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    st.markdown("### ⚙️ SETTINGS")
    mode = st.radio("Header Mode", ["Apply to First Page Only", "Apply to All Pages"])

with c2:
    st.markdown("### 🏷️ FILENAME")
    custom_name = st.text_input("Name your file:", value="Bio_Document", help="No extension needed")

# Action
st.markdown("<br>", unsafe_allow_html=True)
if st.button(">>> GENERATE DOCUMENT <<<"):
    if up_h and up_d:
        with st.status("PROCESSING...", expanded=True) as status:
            st.write("🔹 Reading Secure Files...")
            time.sleep(0.5)
            st.write("🔹 Merging Layers...")
            
            pdf, docx, err = process_merge(up_h, up_d, mode)
            
            if err:
                status.update(label="ERROR", state="error")
                st.error(f"Error: {err}")
            else:
                status.update(label="SUCCESS", state="complete", expanded=False)
                
                # Filename logic
                clean_name = "".join(x for x in custom_name if x.isalnum() or x in "_-")
                if not clean_name: clean_name = "Document"
                
                st.balloons()
                st.success("✅ FILES READY FOR DOWNLOAD")
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ DOWNLOAD PDF", f, file_name=f"{clean_name}.pdf", mime="application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ DOWNLOAD WORD", f, file_name=f"{clean_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                os.remove(pdf)
                os.remove(docx)
    else:
        st.warning("⚠️ PLEASE UPLOAD BOTH FILES")

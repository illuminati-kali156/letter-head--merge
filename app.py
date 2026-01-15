import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile

# --- 1. CORE CONFIGURATION ---
st.set_page_config(
    page_title="SUPER AAI | BIO-CORE",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE MANAGEMENT ---
if "auth_status" not in st.session_state:
    st.session_state.auth_status = "locked"  # locked, puzzle, unlocked
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []
if "console_log" not in st.session_state:
    st.session_state.console_log = ["System Initialized...", "Waiting for Authorization..."]

# --- 3. ULTRA-MODERN CSS ENGINE ---
st.markdown("""
    <style>
    /* --- ANIMATED BACKGROUND: BIO-ENERGY PULSE --- */
    @keyframes gradient-move {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); opacity: 0; }
        50% { opacity: 0.6; }
        100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; }
    }

    .stApp {
        background: linear-gradient(-45deg, #022c22, #064e3b, #14532d, #000000);
        background-size: 400% 400%;
        animation: gradient-move 15s ease infinite;
        font-family: 'Rajdhani', 'Segoe UI', sans-serif; /* Tech font feel */
        color: #dcfce7;
    }

    /* --- FLOATING BIO-PARTICLES (CSS) --- */
    .particle {
        position: fixed;
        bottom: -10vh;
        background: radial-gradient(circle, rgba(74,222,128,0.4) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        pointer-events: none;
        animation: float 15s infinite linear;
        z-index: 0;
    }

    /* --- GLASS TERMINAL CARDS --- */
    .bio-card {
        background: rgba(6, 78, 59, 0.25);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(52, 211, 153, 0.2);
        box-shadow: 0 0 40px rgba(0, 0, 0, 0.6);
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
    }
    
    /* SCANNER LINE EFFECT */
    .bio-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, #34d399, transparent);
        animation: scan 3s linear infinite;
        opacity: 0.3;
    }
    @keyframes scan { 0% {top:0;} 100% {top:100%;} }

    /* --- TYPOGRAPHY --- */
    h1 {
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 4px;
        background: linear-gradient(to right, #ffffff, #4ade80);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(74, 222, 128, 0.5);
    }
    .status-text {
        font-family: 'Courier New', monospace;
        color: #34d399;
        font-size: 0.8rem;
    }

    /* --- UI ELEMENTS --- */
    .stTextInput input {
        background: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid #059669 !important;
        color: #34d399 !important;
        text-align: center;
        letter-spacing: 2px;
        font-family: 'Courier New', monospace;
    }
    
    .stButton button {
        background: transparent;
        border: 2px solid #34d399;
        color: #34d399;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 15px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 4px;
        position: relative;
        overflow: hidden;
    }
    
    .stButton button:hover {
        background: #34d399;
        color: black;
        box-shadow: 0 0 30px rgba(52, 211, 153, 0.6);
        transform: scale(1.02);
    }

    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* UPLOAD ZONES */
    div[data-testid="stFileUploader"] {
        border: 1px dashed #059669;
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 10px;
    }
    </style>

    <div class="particle" style="width: 20px; height: 20px; left: 10%; animation-duration: 12s;"></div>
    <div class="particle" style="width: 50px; height: 50px; left: 30%; animation-duration: 18s; animation-delay: 2s;"></div>
    <div class="particle" style="width: 10px; height: 10px; left: 70%; animation-duration: 9s; animation-delay: 1s;"></div>
    <div class="particle" style="width: 30px; height: 30px; left: 90%; animation-duration: 15s;"></div>
    <div class="particle" style="width: 60px; height: 60px; left: 50%; animation-duration: 22s; animation-delay: 5s;"></div>
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
    # Secure Temp Files
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
            return None, None, "DATA CORRUPTION DETECTED"

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

# --- 5. AUTHENTICATION HANDLERS ---

def check_password_callback():
    if st.session_state.password_input == "bio-gas":
        st.session_state.auth_status = "puzzle"
        st.session_state.console_log.append("> PASSWORD ACCEPTED.")
        st.session_state.console_log.append("> INITIATING BIO-METRIC PUZZLE...")
    else:
        st.session_state.console_log.append("> ERROR: INVALID CREDENTIALS.")
        st.toast("⛔ ACCESS DENIED", icon="🛑")

def puzzle_click(icon):
    st.session_state.puzzle_sequence.append(icon)
    st.session_state.console_log.append(f"> INPUT RECEIVED: {icon}")
    
    target = ["🍃", "⚡", "🔥"]
    idx = len(st.session_state.puzzle_sequence) - 1
    
    # Check Step
    if st.session_state.puzzle_sequence[idx] != target[idx]:
        st.session_state.puzzle_sequence = []
        st.session_state.console_log.append("> SEQUENCE MISMATCH. RESETTING...")
        st.toast("⚠️ SEQUENCE FAILED", icon="🔄")
        return

    # Check Completion
    if len(st.session_state.puzzle_sequence) == 3:
        st.session_state.auth_status = "unlocked"
        st.session_state.console_log.append("> AUTHORIZATION GRANTED.")
        st.session_state.console_log.append("> WELCOME, ADMIN.")

# --- 6. UI: LOGIN PHASE ---

if st.session_state.auth_status != "unlocked":
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='bio-card'>", unsafe_allow_html=True)
        st.markdown("<h1>BIO-CORE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='letter-spacing: 2px; font-size: 0.8em; color: #34d399;'>SUPER AAI ENERGY SYSTEMS</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # TERMINAL LOG
        log_text = "<br>".join(st.session_state.console_log[-4:])
        st.markdown(f"""
        <div style='background:black; color:#00ff41; font-family:monospace; padding:10px; border-radius:5px; text-align:left; font-size:0.8em; margin-bottom:15px; border:1px solid #004400;'>
            {log_text}<span style='animation: blink 1s infinite;'>_</span>
        </div>
        """, unsafe_allow_html=True)

        # PHASE 1: PASSWORD
        if st.session_state.auth_status == "locked":
            st.text_input("ENTER ACCESS PROTOCOL", type="password", key="password_input", on_change=check_password_callback)
            st.caption("Passkey: bio-gas")

        # PHASE 2: PUZZLE
        elif st.session_state.auth_status == "puzzle":
            st.markdown("<p style='color:#34d399; font-weight:bold;'>VERIFY SEQUENCE: NATURE > POWER > HEAT</p>", unsafe_allow_html=True)
            st.caption("(निसर्ग → ऊर्जा → अग्नी)")
            
            c1, c2, c3 = st.columns(3)
            with c1: st.button("⚡", key="b1", on_click=puzzle_click, args=("⚡",), use_container_width=True)
            with c2: st.button("🔥", key="b2", on_click=puzzle_click, args=("🔥",), use_container_width=True)
            with c3: st.button("🍃", key="b3", on_click=puzzle_click, args=("🍃",), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. UI: DASHBOARD PHASE (Unlocked) ---

# Header
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
st.markdown("<h1>BIO-CORE DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("<p class='status-text'>SYSTEM ONLINE | SECURE CONNECTION ESTABLISHED</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Logout
if st.sidebar.button("🔒 TERMINATE SESSION"):
    st.session_state.auth_status = "locked"
    st.session_state.puzzle_sequence = []
    st.session_state.console_log = ["System Initialized..."]
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Main Interface
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='bio-card'><h3>SOURCE HEADER</h3><p style='font-size:0.8em; color:#6ee7b7'>PDF FORMAT REQ.</p></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("HEADER", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<div class='bio-card'><h3>CONTENT DATA</h3><p style='font-size:0.8em; color:#6ee7b7'>PDF FORMAT REQ.</p></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("DATA", type="pdf", label_visibility="collapsed", key="d")

# Settings
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:#34d399; font-family:monospace;'>[ MERGE CONFIGURATION ]</div>", unsafe_allow_html=True)
mode = st.radio("Settings", ["Apply to First Page Only", "Apply to All Pages"], horizontal=True, label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ACTION
if st.button(">>> INITIATE FUSION PROTOCOL <<<"):
    if up_h and up_d:
        # Custom Progress UI
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.markdown("<p style='text-align:center; color:#34d399;'>ANALYZING VECTOR PATHS...</p>", unsafe_allow_html=True)
        time.sleep(0.5)
        progress_bar.progress(40)
        
        status_text.markdown("<p style='text-align:center; color:#34d399;'>MERGING BIOMETRIC LAYERS...</p>", unsafe_allow_html=True)
        time.sleep(0.5)
        progress_bar.progress(80)
        
        pdf, docx, err = process_merge(up_h, up_d, mode)
        progress_bar.progress(100)
        time.sleep(0.2)
        progress_bar.empty()
        status_text.empty()

        if err:
            st.error(f"SYSTEM FAILURE: {err}")
        else:
            st.markdown("""
            <div style='background: rgba(6, 78, 59, 0.8); border: 2px solid #34d399; padding: 20px; border-radius: 15px; text-align: center; margin-top: 20px; box-shadow: 0 0 30px rgba(52, 211, 153, 0.4);'>
                <h2 style='color: #ffffff; margin:0; text-shadow: 0 0 10px #fff;'>✅ FUSION COMPLETE</h2>
                <p style='color: #a7f3d0;'>Output files generated successfully.</p>
            </div>
            <br>
            """, unsafe_allow_html=True)
            
            d1, d2 = st.columns(2)
            with d1:
                with open(pdf, "rb") as f:
                    st.download_button("⬇ DOWNLOAD PDF COMPOSITE", f, "Bio_Fusion_Doc.pdf", "application/pdf", use_container_width=True)
            with d2:
                with open(docx, "rb") as f:
                    st.download_button("⬇ DOWNLOAD WORD EDITABLE", f, "Bio_Fusion_Doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            
            os.remove(pdf); os.remove(docx)

    else:
        st.toast("⚠️ INPUT MISSING: UPLOAD BOTH FILES", icon="⚠️")

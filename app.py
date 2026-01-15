import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Super AAI Bio Energy",
    page_icon="🍃",
    layout="centered"
)

# --- 2. SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []
if "show_puzzle" not in st.session_state:
    st.session_state.show_puzzle = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""

# --- 3. ADVANCED CSS (Animations & Design) ---
st.markdown("""
    <style>
    /* GLOBAL THEME */
    .stApp {
        background: radial-gradient(circle at center, #1a2e1a 0%, #050a05 100%);
        color: #e2e8f0;
        font-family: 'Segoe UI', sans-serif;
    }

    /* FALLING LEAVES ANIMATION */
    @keyframes falling {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 0; }
        20% { opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
    
    .leaf {
        position: fixed;
        top: -10%;
        color: rgba(72, 187, 120, 0.2);
        font-size: 20px;
        animation: falling 8s linear infinite;
        z-index: 0;
        pointer-events: none;
    }
    
    /* GLASSMORPHISM CARDS */
    .glass-panel {
        background: rgba(20, 30, 20, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(72, 187, 120, 0.3);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        text-align: center;
        margin-bottom: 20px;
    }

    /* TITLES */
    h1 {
        background: linear-gradient(to right, #4ade80, #22c55e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: 1px;
        text-align: center;
    }

    /* CUSTOM INPUT FIELDS */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid #22c55e !important;
        color: #4ade80 !important;
        text-align: center;
        border-radius: 10px;
    }

    /* PUZZLE BUTTONS GRID */
    .puzzle-grid {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin-top: 20px;
    }
    
    /* STREAMLIT BUTTON OVERRIDE */
    .stButton button {
        background: linear-gradient(135deg, #14532d 0%, #166534 100%);
        border: 1px solid #4ade80;
        color: white;
        font-weight: bold;
        border-radius: 12px;
        padding: 15px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 0 15px rgba(74, 222, 128, 0.6);
        color: #fff;
        border-color: #fff;
    }
    
    /* UPLOADERS */
    div[data-testid="stFileUploader"] section {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px dashed #4ade80;
    }
    div[data-testid="stFileUploader"] span { color: #86efac !important; }

    /* HIDE SIDEBAR NAVIGATION */
    [data-testid="stSidebarNav"] {display: none;}
    </style>
    
    <div class="leaf" style="left: 10%; animation-duration: 7s;">🍃</div>
    <div class="leaf" style="left: 30%; animation-duration: 9s; font-size: 30px;">🍂</div>
    <div class="leaf" style="left: 70%; animation-duration: 6s;">🍃</div>
    <div class="leaf" style="left: 90%; animation-duration: 11s; font-size: 25px;">🍂</div>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---

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
        t_header.close()
        t_data.close()

        try:
            h_doc = fitz.open(t_header.name)
            d_doc = fitz.open(t_data.name)
        except:
            return None, None, "File Corrupt (फाइल खराब आहे)"

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

# --- 5. AUTHENTICATION LOGIC (Callback Safe) ---

def check_password_callback():
    """Validates password without using st.rerun()"""
    if st.session_state.password_input == "bio-gas":
        st.session_state.show_puzzle = True
        st.session_state.login_error = ""
    else:
        st.session_state.login_error = "❌ Invalid Access Code / चुकीचा कोड"

def puzzle_click(icon):
    """Handles puzzle logic"""
    st.session_state.puzzle_sequence.append(icon)
    target = ["🍃", "⚡", "🔥"]
    
    idx = len(st.session_state.puzzle_sequence) - 1
    
    # Wrong move?
    if st.session_state.puzzle_sequence[idx] != target[idx]:
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ Wrong Sequence! Resetting... (चुकीचा क्रम)", icon="🔄")
        return

    # Complete?
    if len(st.session_state.puzzle_sequence) == 3:
        st.session_state.authenticated = True
        # Note: We don't need st.rerun() here because the main script 
        # will pick up the 'authenticated' state change on the next pass.

# --- 6. MAIN APP FLOW ---

if not st.session_state.authenticated:
    # --- LOGIN SCREEN ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.markdown("<h1>Super AAI Bio Energy</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#86efac; font-size: 0.9em;'>SECURE PORTAL | सुरक्षित पोर्टल</p>", unsafe_allow_html=True)
        st.markdown("---")

        if not st.session_state.show_puzzle:
            # PASSWORD INPUT
            st.text_input(
                "ACCESS CODE (पासवर्ड)", 
                type="password", 
                key="password_input",
                on_change=check_password_callback
            )
            if st.session_state.login_error:
                st.error(st.session_state.login_error)
        else:
            # PUZZLE INTERFACE
            st.info("Security Verification: Nature → Energy → Fire")
            st.caption("(निसर्ग → ऊर्जा → अग्नी)")
            
            # Custom grid for big buttons
            c1, c2, c3 = st.columns(3)
            with c1:
                st.button("⚡", key="btn_bolt", on_click=puzzle_click, args=("⚡",), use_container_width=True)
            with c2:
                st.button("🔥", key="btn_fire", on_click=puzzle_click, args=("🔥",), use_container_width=True)
            with c3:
                st.button("🍃", key="btn_leaf", on_click=puzzle_click, args=("🍃",), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # Stops the rest of the app from loading until authenticated

# --- 7. DASHBOARD (After Login) ---

st.markdown("<h1>Super AAI Bio Energy</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#86efac;'>Document Management System | फाइल व्यवस्थापन</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Logout Button
if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.authenticated = False
    st.session_state.show_puzzle = False
    st.session_state.puzzle_sequence = []
    st.rerun()

# Upload Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='glass-panel'><h3>Letterhead</h3><p style='color:#86efac; font-size:0.8em;'>(लेटरहेड PDF)</p></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("Upload Header", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<div class='glass-panel'><h3>Content Data</h3><p style='color:#86efac; font-size:0.8em;'>(मजकूर PDF)</p></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Upload Content", type="pdf", label_visibility="collapsed", key="d")

st.markdown("<br>", unsafe_allow_html=True)

# Settings
st.markdown("<div style='text-align:center; color: #a3e635; margin-bottom:10px;'>CONFIGURATION (सेटिंग्ज)</div>", unsafe_allow_html=True)
mode = st.radio("Settings", ["Apply to First Page Only", "Apply to All Pages"], horizontal=True, label_visibility="collapsed")

# Process Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("GENERATE DOCUMENT (फाइल तयार करा)"):
    if up_h and up_d:
        with st.status("Processing Request...", expanded=True) as status:
            st.write("🌿 Reading Secure Data...")
            time.sleep(0.5)
            st.write("⚡ Merging Layers...")
            
            pdf, docx, err = process_merge(up_h, up_d, mode)
            
            if err:
                status.update(label="Error", state="error")
                st.error(f"Failed: {err}")
            else:
                status.update(label="Complete!", state="complete", expanded=False)
                
                st.markdown("""
                <div style='background: rgba(34, 197, 94, 0.2); border: 1px solid #22c55e; padding: 15px; border-radius: 12px; text-align: center;'>
                    <h3 style='color: #4ade80; margin:0;'>✅ Document Ready!</h3>
                </div>
                <br>
                """, unsafe_allow_html=True)
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ PDF DOWNLOAD", f, "Final_Doc.pdf", "application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ WORD DOWNLOAD", f, "Final_Doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                os.remove(pdf); os.remove(docx)
    else:
        st.warning("⚠️ Please upload both files! (कृपया दोन्ही फाइल अपलोड करा)")

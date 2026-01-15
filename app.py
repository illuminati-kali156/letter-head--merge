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

# --- 3. CYBER-NATURE THEME ---
st.markdown("""
    <style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #0f2e18 0%, #000000 100%);
        color: #e0e0e0;
        font-family: 'Courier New', Courier, monospace;
    }

    /* NEON CARDS */
    .neon-card {
        background: rgba(10, 20, 10, 0.9);
        border: 1px solid #00ff41;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.15);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
    }

    /* TEXT STYLES */
    h1 { color: #fff; text-shadow: 0 0 10px #00ff41; font-weight: 800; letter-spacing: 2px; }
    p, label { color: #a3ffac !important; font-weight: 600; }
    
    /* INPUTS */
    .stTextInput input {
        background-color: #000 !important;
        border: 1px solid #00ff41 !important;
        color: #00ff41 !important;
        text-align: center;
        font-weight: bold;
    }

    /* BUTTONS - DEFAULT */
    .stButton button {
        background: transparent;
        color: #00ff41;
        border: 1px solid #00ff41;
        width: 100%;
        padding: 15px;
        font-weight: bold;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background: #00ff41;
        color: black;
        box-shadow: 0 0 15px #00ff41;
    }

    /* UPLOAD AREA */
    div[data-testid="stFileUploader"] {
        border: 1px dashed #00ff41;
        background: rgba(0, 255, 65, 0.05);
        padding: 10px;
        border-radius: 10px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
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

# --- 5. AUTH & PUZZLE (FIXED) ---

def verify_password_hash(input_pass):
    # Hash for "bio-energy"
    CORRECT_HASH = "628e41e64c14ca3498d99dad723852dc446fd56dc555a3f5a91117da51d90469"
    return hashlib.sha256(input_pass.strip().encode()).hexdigest() == CORRECT_HASH

def check_password_callback():
    # REMOVED st.rerun() to fix the "No-op" error. 
    # Streamlit automatically updates after this function finishes.
    if verify_password_hash(st.session_state.password_input):
        st.session_state.auth_status = "puzzle"
        st.session_state.login_msg = ""
    else:
        st.session_state.login_msg = "❌ ACCESS DENIED / चुकीचा पासवर्ड"

def puzzle_click(icon):
    # Add to sequence
    st.session_state.puzzle_sequence.append(icon)
    
    # Target: Feedstock -> Digestion -> Energy
    target = ["🌽", "🫧", "⚡"]
    
    current_idx = len(st.session_state.puzzle_sequence) - 1
    
    # 1. Check Bounds
    if current_idx >= len(target):
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ System Reset", icon="🔄")
        return

    # 2. Check Logic
    if st.session_state.puzzle_sequence[current_idx] != target[current_idx]:
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ Sequence Error! Resetting...", icon="❌")
        return

    # 3. Success?
    if len(st.session_state.puzzle_sequence) == 3:
        st.session_state.auth_status = "unlocked"
        # No st.rerun() needed here either, the state change triggers the UI update

# --- 6. LOGIN UI ---

if st.session_state.auth_status != "unlocked":
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='neon-card'>", unsafe_allow_html=True)
        st.markdown("<h1>⚡ BIO-CORE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8em;'>Super AAI Bio Energy Pvt Ltd</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.auth_status == "locked":
            # PHASE 1: PASSWORD
            st.text_input("ENTER PASSKEY", type="password", key="password_input", on_change=check_password_callback)
            if st.session_state.login_msg:
                st.error(st.session_state.login_msg)

        elif st.session_state.auth_status == "puzzle":
            # PHASE 2: REACTOR SEQUENCE
            st.markdown("### 🧬 INITIATE REACTOR")
            st.caption("Sequence: Feedstock → Digestion → Energy")
            st.caption("(कच्चा माल → प्रक्रिया → ऊर्जा)")
            
            # Draw buttons. If selected, we show a CHECKMARK to keep it "Selected"
            seq = st.session_state.puzzle_sequence
            
            # Determine labels based on selection state
            lbl_corn = "✅ 🌽" if "🌽" in seq else "🌽"
            lbl_bub  = "✅ 🫧" if "🫧" in seq else "🫧"
            lbl_bolt = "✅ ⚡" if "⚡" in seq else "⚡"
            
            # Disable buttons if already clicked to prevent double clicks
            dis_corn = "🌽" in seq
            dis_bub  = "🫧" in seq
            dis_bolt = "⚡" in seq

            c1, c2, c3 = st.columns(3)
            with c1: 
                st.button(lbl_corn, on_click=puzzle_click, args=("🌽",), disabled=dis_corn, use_container_width=True)
            with c2: 
                st.button(lbl_bub, on_click=puzzle_click, args=("🫧",), disabled=dis_bub, use_container_width=True)
            with c3: 
                st.button(lbl_bolt, on_click=puzzle_click, args=("⚡",), disabled=dis_bolt, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. MAIN DASHBOARD ---

st.markdown("<h1 style='text-align:center;'>Super AAI BIO Energy PVT LTD</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>OFFICIAL DOCUMENT MERGER SYSTEM</p>", unsafe_allow_html=True)

# Logout
if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth_status = "locked"
    st.session_state.puzzle_sequence = []
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Uploads
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
    custom_name = st.text_input("Output Filename:", value="Bio_Document")

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
                st.success("✅ FILES READY")
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ PDF", f, file_name=f"{clean_name}.pdf", mime="application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ WORD", f, file_name=f"{clean_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                os.remove(pdf)
                os.remove(docx)
    else:
        st.warning("⚠️ PLEASE UPLOAD BOTH FILES")

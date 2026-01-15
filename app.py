import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Bio-Energy Secure Portal",
    page_icon="⚡",
    layout="centered"
)

# --- 2. SESSION STATE (Memory) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "show_puzzle" not in st.session_state:
    st.session_state.show_puzzle = False
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []

# --- 3. CSS STYLING (Fixed & Polished) ---
st.markdown("""
    <style>
    /* Background & Font */
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #1e1b4b 100%);
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }

    /* Login Container (Centered & Glass) */
    .login-box {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        text-align: center;
        margin-top: 20px;
    }

    /* Glass Cards for Uploads */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: rgba(255,255,255,0.05);
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
        text-align: center;
    }
    
    /* Buttons */
    .stButton button {
        width: 100%;
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        padding: 12px;
        font-weight: bold;
        border-radius: 8px;
        transition: transform 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.02);
        color: white;
    }
    
    /* Puzzle Buttons (Make them look clickable) */
    .puzzle-btn button {
        background: rgba(255,255,255,0.1) !important;
        font-size: 24px;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION LOGIC (Password + Puzzle) ---

def check_password():
    # Password Check
    if st.session_state.password_input == "bio-gas":
        st.session_state.show_puzzle = True
        st.session_state.error_msg = None
    else:
        st.session_state.error_msg = "❌ ACCESS DENIED / प्रवेश नाकारला"

def puzzle_click(icon):
    st.session_state.puzzle_sequence.append(icon)
    
    # CORRECT SEQUENCE: Leaf -> Lightning -> Fire
    target_sequence = ["🍃", "⚡", "🔥"]
    
    # Check if the user made a mistake instantly
    current_index = len(st.session_state.puzzle_sequence) - 1
    
    if st.session_state.puzzle_sequence[current_index] != target_sequence[current_index]:
        # Wrong Step -> Reset Immediately
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ Wrong Sequence! Resetting... (चुकीचा क्रम)", icon="🔄")
    
    elif len(st.session_state.puzzle_sequence) == 3:
        # Correct Sequence Complete -> Unlock
        st.balloons()
        st.session_state.authenticated = True
        st.rerun()

# --- 5. LOGIN SCREEN UI ---

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h2>🔒 Secure Portal</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94a3b8;'> बायो एनर्जी (Bio Energy) Pvt Ltd</p>", unsafe_allow_html=True)

        if not st.session_state.show_puzzle:
            st.text_input("Enter Passkey / पासवर्ड", type="password", key="password_input", on_change=check_password)
            if "error_msg" in st.session_state and st.session_state.error_msg:
                st.error(st.session_state.error_msg)
        
        else:
            st.markdown("---")
            st.markdown("#### 🧩 Security Verification")
            st.caption("Complete the cycle: Nature → Energy → Fire")
            st.caption("(निसर्ग → ऊर्जा → अग्नी)")
            
            # Puzzle Buttons
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="puzzle-btn">', unsafe_allow_html=True)
                st.button("⚡", key="p_bolt", on_click=puzzle_click, args=("⚡",))
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="puzzle-btn">', unsafe_allow_html=True)
                st.button("🔥", key="p_fire", on_click=puzzle_click, args=("🔥",))
                st.markdown('</div>', unsafe_allow_html=True)
            with c3:
                st.markdown('<div class="puzzle-btn">', unsafe_allow_html=True)
                st.button("🍃", key="p_leaf", on_click=puzzle_click, args=("🍃",))
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    
    # Stop app here if not logged in
    st.stop()


# ==================================================
#    MAIN APP LOGIC (Only loads after login)
# ==================================================

def get_visible_content_bottom(page):
    """Scans page to find where header ends."""
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
    # We use delete=False so we can close them and let PyMuPDF open them by name
    t_header = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    t_data = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    
    # Define outputs (also temp files to prevent conflicts)
    out_pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    out_docx_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name

    paths_to_clean = [t_header.name, t_data.name]

    try:
        # Write bytes to temp files
        t_header.write(header_file.getbuffer())
        t_data.write(data_file.getbuffer())
        
        # Close file handles immediately so OS releases lock
        t_header.close()
        t_data.close()

        # Open with PyMuPDF
        try:
            header_doc = fitz.open(t_header.name)
            data_doc = fitz.open(t_data.name)
        except Exception:
            return None, None, "File Corrupt or Locked (फाइल खराब आहे)."

        out_doc = fitz.open()
        
        # Layout Analysis
        header_page = header_doc[0]
        w = header_page.rect.width
        h = header_page.rect.height
        
        start_y = get_visible_content_bottom(header_page) + 20 
        
        # Merge Logic
        apply_all = (mode == "All Pages")

        for i in range(len(data_doc)):
            if i == 0 or apply_all:
                page = out_doc.new_page(width=w, height=h)
                page.show_pdf_page(fitz.Rect(0,0,w,h), header_doc, 0)
                page.show_pdf_page(fitz.Rect(0,start_y,w,h), data_doc, i)
            else:
                out_doc.insert_pdf(data_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf_path)
        
        # Close docs
        header_doc.close(); data_doc.close(); out_doc.close()

        # Word Conversion
        cv = Converter(out_pdf_path)
        cv.convert(out_docx_path)
        cv.close()

        return out_pdf_path, out_docx_path, None

    except Exception as e:
        return None, None, str(e)
        
    finally:
        # 2. SECURITY: Guaranteed Cleanup
        # This runs even if the app crashes, ensuring no user files stay on server
        for path in paths_to_clean:
            if os.path.exists(path):
                try: os.remove(path)
                except: pass


# --- MAIN INTERFACE ---

st.markdown("<h1>⚡ Fusion Doc Merger</h1>", unsafe_allow_html=True)
st.caption("Authorized Access Only | बायो एनर्जी प्रायव्हेट लिमिटेड")

col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='glass-card'><b>1. Upload Letterhead</b><br><small>(लेटरहेड)</small></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("Header", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<div class='glass-card'><b>2. Upload Content</b><br><small>(मजकूर)</small></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type="pdf", label_visibility="collapsed", key="d")

st.write("")
merge_mode = st.radio("Settings (सेटिंग्ज)", ["Apply to First Page Only", "Apply to All Pages"], horizontal=True)

if st.button("MERGE FILES (फाइल तयार करा) 🚀"):
    if up_h and up_d:
        with st.status("Processing (प्रक्रिया सुरू आहे)...", expanded=True) as status:
            st.write("🔹 Reading Secure Data...")
            time.sleep(0.3)
            st.write("🔹 Merging Documents...")
            
            pdf, docx, err = process_merge(up_h, up_d, merge_mode)
            
            if err:
                status.update(label="Failed", state="error")
                st.error(f"Error: {err}")
            else:

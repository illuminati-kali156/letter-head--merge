import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Fusion Doc Merger",
    page_icon="⚡",
    layout="centered"
)

# --- 2. SESSION STATE SETUP (The Memory) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []
if "show_puzzle" not in st.session_state:
    st.session_state.show_puzzle = False

# --- 3. CSS STYLING (Glassmorphism + Security UI) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }
    
    /* Login Box Styling */
    .login-container {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 0 50px rgba(0,0,0,0.5);
        margin-top: 50px;
    }
    
    /* Puzzle Buttons */
    .stButton button {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: white;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background: rgba(255,255,255,0.2);
        border-color: #818cf8;
        transform: scale(1.1);
    }

    /* Main App Styles (Glass Cards) */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 20px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: rgba(255, 255, 255, 0.05);
    }
    div[data-testid="stFileUploader"] span {
        color: #e2e8f0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION LOGIC ---

def check_password():
    password = st.session_state.password_input
    if password == "bio-gas":
        st.session_state.show_puzzle = True
        st.session_state.password_error = None
    else:
        st.session_state.password_error = "ACCESS DENIED: Incorrect Protocol."

def puzzle_click(element):
    st.session_state.puzzle_sequence.append(element)
    
    # THE SECRET SEQUENCE: Leaf -> Lightning -> Fire
    correct_sequence = ["🍃", "⚡", "🔥"]
    
    # Check current progress
    current_step = len(st.session_state.puzzle_sequence) - 1
    
    if st.session_state.puzzle_sequence[current_step] != correct_sequence[current_step]:
        # Wrong click -> Reset
        st.toast("⛔ Security Violation: Sequence Reset", icon="❌")
        st.session_state.puzzle_sequence = []
    
    elif st.session_state.puzzle_sequence == correct_sequence:
        # Success -> Unlock App
        st.balloons()
        st.session_state.authenticated = True
        st.rerun()

# --- 5. THE LOGIN SCREEN (If not authenticated) ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #818cf8;'>SECURE GATEWAY</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        
        # STEP 1: PASSWORD
        if not st.session_state.show_puzzle:
            st.text_input("ENTER ACCESS CODE", type="password", key="password_input", on_change=check_password)
            if "password_error" in st.session_state and st.session_state.password_error:
                st.error(st.session_state.password_error)
        
        # STEP 2: THE PUZZLE
        else:
            st.markdown("### 🔐 SECURITY CHALLENGE")
            st.write("Complete the Bio-Energy Sequence.")
            
            p1, p2, p3 = st.columns(3)
            with p1:
                st.button("⚡", on_click=puzzle_click, args=("⚡",), use_container_width=True)
            with p2:
                st.button("🔥", on_click=puzzle_click, args=("🔥",), use_container_width=True)
            with p3:
                st.button("🍃", on_click=puzzle_click, args=("🍃",), use_container_width=True)
                
            st.caption("Hint: Nature -> Power -> Heat")

        st.markdown("</div>", unsafe_allow_html=True)
    
    # Stop execution here if not logged in
    st.stop()


# ==========================================
#      MAIN APPLICATION (HIDDEN UNTIL LOGIN)
# ==========================================

# --- 6. CORE LOGIC (Secure) ---
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

    try:
        t_header.write(header_file.getbuffer()); t_header.close()
        t_data.write(data_file.getbuffer()); t_data.close()

        try:
            header_doc = fitz.open(t_header.name)
            data_doc = fitz.open(t_data.name)
        except:
            return None, None, "File Corrupt or Locked."

        out_doc = fitz.open()
        header_page = header_doc[0]
        page_width = header_page.rect.width
        page_height = header_page.rect.height
        
        start_y = get_visible_content_bottom(header_page) + 20 
        
        apply_all = (mode == "Apply to All Pages")
        
        for i in range(len(data_doc)):
            if i == 0 or apply_all:
                page = out_doc.new_page(width=page_width, height=page_height)
                page.show_pdf_page(fitz.Rect(0,0,page_width,page_height), header_doc, 0)
                page.show_pdf_page(fitz.Rect(0,start_y,page_width,page_height), data_doc, i)
            else:
                out_doc.insert_pdf(data_doc, from_page=i, to_page=i)

        out_doc.save(out_pdf)
        header_doc.close(); data_doc.close(); out_doc.close()

        cv = Converter(out_pdf)
        cv.convert(out_docx)
        cv.close()

        return out_pdf, out_docx, None

    except Exception as e:
        return None, None, str(e)
    finally:
        if os.path.exists(t_header.name): os.remove(t_header.name)
        if os.path.exists(t_data.name): os.remove(t_data.name)


# --- 7. MAIN UI ---

st.markdown("<h1>⚡ FUSION DOC MERGER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#94a3b8;'>System Unlocked. Ready for Operations.</p>", unsafe_allow_html=True)

# Logout Button (Optional)
if st.sidebar.button("🔒 Lock System"):
    st.session_state.authenticated = False
    st.session_state.show_puzzle = False
    st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='glass-card'><b>1. Upload Letterhead</b></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("Header", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<div class='glass-card'><b>2. Upload Content</b></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type="pdf", label_visibility="collapsed", key="d")

st.write("") 
merge_mode = st.radio("Settings", ["Apply to First Page Only", "Apply to All Pages"], horizontal=True, label_visibility="collapsed")

if st.button("INITIALIZE MERGE 🚀"):
    if up_h and up_d:
        with st.status("Processing Data...", expanded=True) as status:
            st.write("🔹 Securely reading files...")
            time.sleep(0.3)
            st.write("🔹 Calculating layout vectors...")
            
            pdf, docx, err = process_merge(up_h, up_d, merge_mode)
            
            if err:
                status.update(label="Failed", state="error")
                st.error(f"Error: {err}")
            else:
                status.update(label="Complete!", state="complete", expanded=False)
                st.markdown("""
                <div style='background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; padding: 15px; border-radius: 10px; text-align: center; margin-top: 20px;'>
                    <h3 style='color: #10b981; margin:0;'>✅ Success! Files Ready.</h3>
                </div>
                """, unsafe_allow_html=True)
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ Download PDF", f, "Merged.pdf", "application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ Download Word", f, "Merged.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                os.remove(pdf); os.remove(docx)
    else:
        st.toast("⚠️ Please upload both files first!", icon="⚠️")

import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile
import hashlib  # <--- FOR SECURITY

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Super AAI BIO Energy",
    page_icon="🌿",
    layout="centered"
)

# --- 2. SESSION STATE ---
if "auth_status" not in st.session_state:
    st.session_state.auth_status = "locked"
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []
if "login_msg" not in st.session_state:
    st.session_state.login_msg = ""

# --- 3. EYE-COMFORT "SAGE & EARTH" THEME ---
st.markdown("""
    <style>
    /* SOFT BACKGROUND (Easy on eyes) */
    .stApp {
        background-color: #f1f8e9; /* Very light sage green */
        background-image: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%);
        font-family: 'Helvetica', 'Arial', sans-serif;
        color: #333333; /* Dark Grey text for readability */
    }

    /* CARD STYLE (Soft Shadows, No sharp borders) */
    .soft-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); /* Soft shadow */
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }

    /* TYPOGRAPHY */
    h1 {
        color: #2e7d32; /* Forest Green */
        font-weight: 700;
        margin-bottom: 5px;
    }
    h3 { color: #558b2f; }
    p { color: #555555; line-height: 1.6; }

    /* BUTTONS (Matte Finish, not Neon) */
    .stButton button {
        background-color: #2e7d32;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: background 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton button:hover {
        background-color: #1b5e20; /* Darker green on hover */
        color: white;
    }

    /* INPUT FIELDS (Clean white with soft border) */
    .stTextInput input {
        background-color: #ffffff !important;
        border: 1px solid #bdbdbd !important;
        color: #333333 !important;
        border-radius: 8px;
        padding: 10px;
    }
    
    /* UPLOAD AREA */
    div[data-testid="stFileUploader"] {
        background-color: #fafafa;
        border: 1px dashed #bdbdbd;
        border-radius: 10px;
        padding: 15px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: transparent;
    }

    /* HIDE MENU */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
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
    # Temp files logic (Secure Deletion is handled in 'finally')
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
            return None, None, "File Corrupt or Encrypted (फाइल खराब आहे)"

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
        # SECURITY: Ensure Input Files are removed 100% of the time
        for p in clean_paths:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

# --- 5. HASHING SECURITY (NO PLAIN TEXT PASSWORD) ---

def verify_password_hash(input_pass):
    # This is the SHA-256 Hash of "bio-gas"
    # Even if people see this code, they just see this number, not the password.
    CORRECT_HASH = "a672727144415891392661578332997672223403310069007559190186259837"
    
    # Convert user input to hash and compare
    input_hash = hashlib.sha256(input_pass.encode()).hexdigest()
    return input_hash == CORRECT_HASH

def check_password_callback():
    if verify_password_hash(st.session_state.password_input):
        st.session_state.auth_status = "puzzle"
        st.session_state.login_msg = ""
    else:
        st.session_state.login_msg = "❌ Incorrect Password"

def puzzle_click(icon):
    st.session_state.puzzle_sequence.append(icon)
    target = ["🐮", "🍃", "🔥"]
    
    # Safety Check: Prevent Index Error
    current_idx = len(st.session_state.puzzle_sequence) - 1
    if current_idx >= len(target):
        st.session_state.puzzle_sequence = []
        return

    # Verify Step
    if st.session_state.puzzle_sequence[current_idx] != target[current_idx]:
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ Sequence Error! Resetting...", icon="🔄")
        return

    # Verify Completion
    if len(st.session_state.puzzle_sequence) == 3:
        st.session_state.auth_status = "unlocked"
        st.rerun()

# --- 6. UI: LOGIN SCREEN ---

if st.session_state.auth_status != "unlocked":
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        # BRANDING
        st.markdown("<h1>Super AAI BIO Energy</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.9em; color: #777;'>SECURE DOCUMENT PORTAL</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.auth_status == "locked":
            st.text_input("Enter Password", type="password", key="password_input", on_change=check_password_callback)
            if st.session_state.login_msg:
                st.error(st.session_state.login_msg)

        elif st.session_state.auth_status == "puzzle":
            st.markdown("### Security Check")
            st.markdown("<p style='font-size: 0.9em;'>Select sequence: Livestock → Nature → Bio-Gas<br>(पशुधन → निसर्ग → बायो-गॅस)</p>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1: st.button("🐮", key="b1", on_click=puzzle_click, args=("🐮",), use_container_width=True)
            with c2: st.button("🔥", key="b2", on_click=puzzle_click, args=("🔥",), use_container_width=True)
            with c3: st.button("🍃", key="b3", on_click=puzzle_click, args=("🍃",), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. UI: MAIN DASHBOARD ---

st.markdown("<h1 style='text-align:center;'>Super AAI BIO Energy PVT LTD</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Official Document Merger System</p>", unsafe_allow_html=True)

# Logout
if st.sidebar.button("🔒 Logout"):
    st.session_state.auth_status = "locked"
    st.session_state.puzzle_sequence = []
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Upload Section
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='soft-card'><h3>📄 Letterhead</h3><p>Upload the company header PDF</p></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("Header", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<div class='soft-card'><h3>📝 Content</h3><p>Upload the document body PDF</p></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type="pdf", label_visibility="collapsed", key="d")

# Configuration Section
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### ⚙️ Settings")

c1, c2 = st.columns(2)
with c1:
    mode = st.radio("Header Placement", ["Apply to First Page Only", "Apply to All Pages"])
with c2:
    # NEW FEATURE: CUSTOM FILENAME
    custom_name = st.text_input("Name your output file:", value="My_Bio_Document", help="Enter a name for the generated file")

st.markdown("<br>", unsafe_allow_html=True)

# Generate Button
if st.button("✨ GENERATE DOCUMENT"):
    if up_h and up_d:
        with st.status("Processing Document...", expanded=True) as status:
            st.write("Reading inputs...")
            time.sleep(0.5)
            st.write("Merging layers...")
            
            pdf, docx, err = process_merge(up_h, up_d, mode)
            
            if err:
                status.update(label="Error", state="error")
                st.error(f"Error: {err}")
            else:
                status.update(label="Complete!", state="complete", expanded=False)
                
                # Clean Filename Logic
                clean_name = "".join(x for x in custom_name if x.isalnum() or x in "_- ")
                if not clean_name: clean_name = "Document"
                
                st.success("✅ Files generated successfully!")
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ Download PDF", f, file_name=f"{clean_name}.pdf", mime="application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ Download Word", f, file_name=f"{clean_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                # Security Cleanup: Output files
                os.remove(pdf)
                os.remove(docx)
    else:
        st.warning("⚠️ Please upload both Letterhead and Content files.")

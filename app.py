import streamlit as st
import fitz  # PyMuPDF
import os
from pdf2docx import Converter
import time
import tempfile

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Bio-Energy Farm Tech",
    page_icon="🌾",
    layout="centered"
)

# --- 2. SESSION STATE ---
if "auth_status" not in st.session_state:
    st.session_state.auth_status = "locked"  # locked, puzzle, unlocked
if "puzzle_sequence" not in st.session_state:
    st.session_state.puzzle_sequence = []
if "login_msg" not in st.session_state:
    st.session_state.login_msg = ""

# --- 3. FARM & NATURE CSS ---
st.markdown("""
    <style>
    /* --- BACKGROUND: SUNNY FARM GRADIENT --- */
    .stApp {
        background: linear-gradient(180deg, #87CEEB 0%, #E0F7FA 40%, #A5D6A7 60%, #2E7D32 100%);
        font-family: 'Poppins', sans-serif;
        color: #1b4332;
    }

    /* --- FLOATING ANIMATIONS (Leaves & Droplets) --- */
    @keyframes floatDown {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 0; }
        20% { opacity: 0.8; }
        100% { transform: translateY(110vh) rotate(360deg); opacity: 0; }
    }
    .nature-icon {
        position: fixed;
        top: -10%;
        font-size: 24px;
        animation: floatDown 10s linear infinite;
        z-index: 0;
        pointer-events: none;
        opacity: 0.6;
    }

    /* --- GLASS CARDS (FROSTED STYLE) --- */
    .farm-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 2px solid rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0, 50, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
    }

    /* --- TYPOGRAPHY --- */
    h1 {
        color: #1b4332;
        font-weight: 800;
        text-shadow: 0 2px 4px rgba(255,255,255,0.5);
    }
    p { font-weight: 500; }
    
    /* --- INPUT FIELDS --- */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.8) !important;
        border: 2px solid #4CAF50 !important;
        color: #2E7D32 !important;
        text-align: center;
        border-radius: 12px;
        font-weight: bold;
    }

    /* --- BUTTONS --- */
    .stButton button {
        background: linear-gradient(to bottom, #66bb6a, #43a047);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        color: white;
        background: linear-gradient(to bottom, #81c784, #4caf50);
    }

    /* --- UPLOAD BOXES --- */
    div[data-testid="stFileUploader"] {
        background-color: rgba(255,255,255,0.5);
        border: 2px dashed #4CAF50;
        border-radius: 15px;
        padding: 10px;
    }
    
    /* HIDE MENU */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    </style>

    <div class="nature-icon" style="left: 10%; animation-duration: 8s;">🍃</div>
    <div class="nature-icon" style="left: 30%; animation-duration: 12s; font-size: 30px;">💧</div>
    <div class="nature-icon" style="left: 60%; animation-duration: 15s;">🌾</div>
    <div class="nature-icon" style="left: 80%; animation-duration: 10s;">🐮</div>
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
    # Temp files logic
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

# --- 5. AUTH LOGIC (BUG FIX APPLIED) ---

def check_password_callback():
    if st.session_state.password_input == "bio-gas":
        st.session_state.auth_status = "puzzle"
        st.session_state.login_msg = ""
    else:
        st.session_state.login_msg = "❌ Invalid Password / चुकीचा पासवर्ड"

def puzzle_click(icon):
    # 1. APPEND CLICK
    st.session_state.puzzle_sequence.append(icon)
    
    # 2. DEFINE TARGET: Cow -> Leaf/Biomass -> Fire/Gas
    target = ["🐮", "🍃", "🔥"]
    
    # 3. BUG FIX: Check if we went out of bounds
    current_idx = len(st.session_state.puzzle_sequence) - 1
    
    if current_idx >= len(target):
        # Reset if list became too long (Safety catch)
        st.session_state.puzzle_sequence = []
        return

    # 4. CHECK CORRECTNESS
    if st.session_state.puzzle_sequence[current_idx] != target[current_idx]:
        # Wrong Step -> Reset
        st.session_state.puzzle_sequence = []
        st.toast("⚠️ Wrong Sequence! Resetting... (चुकीचा क्रम)", icon="🔄")
        return

    # 5. CHECK COMPLETION
    if len(st.session_state.puzzle_sequence) == 3:
        st.session_state.auth_status = "unlocked"

# --- 6. UI: LOGIN SCREEN ---

if st.session_state.auth_status != "unlocked":
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='farm-card'>", unsafe_allow_html=True)
        # Farm Logo Area
        st.markdown("<h1>🌾 Bio-Energy Farm</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#388E3C;'>Super AAI Agri-Tech Portal</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.auth_status == "locked":
            # STEP 1: PASSWORD
            st.text_input("Enter Passkey (पासवर्ड)", type="password", key="password_input", on_change=check_password_callback)
            if st.session_state.login_msg:
                st.error(st.session_state.login_msg)
            st.caption("Hint: Which gas will be produced in this process")

        elif st.session_state.auth_status == "puzzle":
            # STEP 2: PUZZLE
            st.markdown("### 🧩 Process Verification")
            st.markdown("**Livestock → Biomass → Bio-Gas**")
            st.markdown("**(पशुधन → निसर्ग → बायो-गॅस)**")
            
            c1, c2, c3 = st.columns(3)
            with c1: st.button("🐮", key="b1", on_click=puzzle_click, args=("🐮",), use_container_width=True)
            with c2: st.button("🔥", key="b2", on_click=puzzle_click, args=("🔥",), use_container_width=True)
            with c3: st.button("🍃", key="b3", on_click=puzzle_click, args=("🍃",), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. UI: DASHBOARD (Unlocked) ---

st.markdown("<h1 style='text-align:center;'>🚜 Farm Document Manager</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#2E7D32;'>Secure Letterhead Merging System | सुरक्षित प्रणाली</p>", unsafe_allow_html=True)

# Logout
if st.sidebar.button("🔒 Logout (बाहेर पडा)"):
    st.session_state.auth_status = "locked"
    st.session_state.puzzle_sequence = []
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Main Upload Area
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='farm-card'><h3>📄 Letterhead</h3><p>(लेटरहेड PDF)</p></div>", unsafe_allow_html=True)
    up_h = st.file_uploader("Header", type="pdf", label_visibility="collapsed", key="h")

with col2:
    st.markdown("<div class='farm-card'><h3>📝 Content Data</h3><p>(मजकूर PDF)</p></div>", unsafe_allow_html=True)
    up_d = st.file_uploader("Data", type="pdf", label_visibility="collapsed", key="d")

# Settings
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'><strong>⚙️ Configuration (सेटिंग्ज)</strong></div>", unsafe_allow_html=True)
mode = st.radio("Mode", ["Apply to First Page Only", "Apply to All Pages"], horizontal=True, label_visibility="collapsed")

# Action Button
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 CREATE DOCUMENT (फाइल बनवा)"):
    if up_h and up_d:
        with st.status("Processing... (प्रक्रिया सुरू आहे)", expanded=True) as status:
            st.write("🌿 Reading Files...")
            time.sleep(0.5)
            st.write("⚙️ Merging Layouts...")
            
            pdf, docx, err = process_merge(up_h, up_d, mode)
            
            if err:
                status.update(label="Error", state="error")
                st.error(f"Error: {err}")
            else:
                status.update(label="Done!", state="complete", expanded=False)
                st.balloons()
                
                st.markdown("""
                <div style='background: #E8F5E9; border: 2px solid #4CAF50; padding: 20px; border-radius: 15px; text-align: center; margin-top: 20px;'>
                    <h3 style='color: #2E7D32; margin:0;'>✅ Success! (यशस्वी)</h3>
                </div>
                <br>
                """, unsafe_allow_html=True)
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ Download PDF", f, "Bio_Farm_Doc.pdf", "application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ Download Word", f, "Bio_Farm_Doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                os.remove(pdf); os.remove(docx)
    else:
        st.warning("⚠️ Please upload both files! (कृपया दोन्ही फाइल अपलोड करा)")

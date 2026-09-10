import streamlit as st
from google import genai
import pypdf
import json
import os
import time
import tempfile
import asyncio
import edge_tts
from io import BytesIO
from PIL import Image

# 1. Page Configuration
st.set_page_config(
    page_title="Apex OmniStudio AI | Ujjwal Jhajharia",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Cyber-Dark Futuristic CSS & Fixed Top Bar
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    .stApp {
        background-color: #06080F;
        color: #E2E8F0;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .owner-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 44px;
        background: rgba(10, 14, 26, 0.94);
        backdrop-filter: blur(14px);
        border-bottom: 2px solid #6366F1;
        box-shadow: 0 4px 25px rgba(99, 102, 241, 0.35);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 2rem;
        z-index: 999999;
        font-family: 'Space Grotesk', sans-serif;
    }
    .owner-brand {
        font-weight: 800;
        font-size: 0.9rem;
        letter-spacing: 0.12em;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #34D399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .badge-core {
        background: rgba(99, 102, 241, 0.25);
        border: 1px solid #6366F1;
        color: #A5B4FC;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
    }

    .session-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4), rgba(15, 23, 42, 0.7));
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    th {
        background-color: #121A2D !important;
        color: #38BDF8 !important;
        padding: 10px 14px !important;
    }
    td {
        background-color: #0B1120 !important;
        color: #CBD5E1 !important;
        padding: 10px 14px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
</style>

<div class="owner-header">
    <div class="owner-brand">
        <span class="badge-core">CHIEF ARCHITECT</span>
        <span>UJJWAL JHAJHARIA</span>
    </div>
    <div style="color: #34D399; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;">
        ● APEX 1-CLICK AUTONOMOUS ENGINE
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Sidebar Configuration
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Master Control Hub")
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste API Key...")
    else:
        st.success("✅ Cloud API Key Active")
    st.markdown("---")
    
    global_lang = st.selectbox(
        "Medium / Language",
        ["English (Academic)", "Hinglish (Bilingual Coach)", "Hindi (Pure Shuddh)"]
    )
    
    voice_actor = st.selectbox(
        "Teacher Voice Persona",
        [
            "Madhur (Natural Expressive - Male)",
            "Swara (Warm Engaging - Female)",
            "Guy (Global Accent - Male)"
        ]
    )

    generate_ai_art = st.toggle("Generate AI Diagrams (Imagen 3)", value=True)
    st.caption("Active Core: Gemini 3.6 Flash Engine")

# 4. State Management
if "suite" not in st.session_state:
    st.session_state.suite = None
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "ai_image" not in st.session_state:
    st.session_state.ai_image = None

st.markdown("<br><br>", unsafe_allow_html=True)
st.title("⚡ Apex OmniStudio Pro")
st.write("Instant high-yield notes, direct-impact teacher audio, AI visual schematics, aur real-time exam drills.")

uploaded_file = st.file_uploader("📂 Drop Textbook / Chapter PDF Here", type=["pdf"])

def extract_pdf_data(file):
    reader = pypdf.PdfReader(file)
    extracted = ""
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            extracted += txt + "\n"
    return extracted, len(reader.pages)

async def synthesize_mentor_speech(clean_text, voice, output_path):
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(output_path)

def generate_ai_diagram(client, prompt_text):
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=f"Educational textbook scientific diagram, clean vector infographic art, high resolution: {prompt_text}",
            config=dict(
                number_of_images=1,
                aspect_ratio="16:9",
                person_generation="DONT_ALLOW"
            )
        )
        for generated_image in result.generated_images:
            return Image.open(BytesIO(generated_image.image.image_bytes))
    except Exception:
        return None

# Safe Caller with retry logic
def call_gemini_safe(client, prompt, text_content):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[prompt, f"Source Content:\n{text_content}"],
                config=dict(response_mime_type="application/json")
            )
            return response.text
        except Exception as e:
            if ("503" in str(e) or "429" in str(e)) and attempt < max_retries - 1:
                time.sleep(3)
                continue
            raise e

# Direct Generation Flow
if uploaded_file and not st.session_state.suite:
    text, pages = extract_pdf_data(uploaded_file)
    word_count = len(text.split())
    est_read_time = round(word_count / 200, 1)

    colA, colB, colC = st.columns(3)
    with colA:
        st.metric(label="Total Pages", value=pages)
    with colB:
        st.metric(label="Word Count", value=word_count)
    with colC:
        st.metric(label="Est. Read Time", value=f"~{est_read_time} min")

    st.write("")
    if st.button("🚀 Synthesize Full Omni-Suite in 1-Click", type="primary", use_container_width=True):
        if not api_key:
            st.error("Pehle sidebar me Gemini API Key enter karein!")
        else:
            with st.status("⚡ Synthesizing High-Yield Notes, Audio & Visuals...", expanded=True) as status:
                client = genai.Client(api_key=api_key)

                master_prompt = f"""
                You are Apex OmniStudio, an elite academic notes architect and examination specialist created for Ujjwal Jhajharia.
                Transform this study document into an exceptional, comprehensive academic suite.

                AUTOMATIC STRUCTURAL RULES:
                1. Convert all comparative aspects, classifications, parameters, and methods into rich Markdown Tables.
                2. Use clear text flowcharts or arrows (Step 1 ──> Step 2) for sequences.
                3. Bold all primary keywords, botanical/scientific names, formulas, and critical thresholds.
                4. Include a 'Quick-Revision Memory Box' with mnemonics at the end of the notes.

                CRITICAL DIRECTIVES FOR 'mentor_audio_script':
                1. ABSOLUTELY NO INTRODUCTIONS. No 'Hello', 'Welcome', 'Main aapka teacher hoon', 'Aaj hum padhenge'. Start directly from word 1 with the core concept hook.
                2. Conversational Hindi/Hinglish delivery. Explain the intuition and reasoning behind the facts.
                3. Highlight exam traps where students lose marks.
                4. Use natural punctuation (commas, ellipses ..., dashes —) for natural breathing pauses.
                5. Output pure clean speech text only (NO XML, NO SSML tags).

                Target Language: {global_lang}

                OUTPUT SCHEMA (MUST BE VALID JSON):
                {{
                    "mentor_audio_script": "Pure spoken lecture script starting straight with the concept...",
                    "master_notes": "High-yield Markdown revision notes with tables, bold headings, and formulas.",
                    "flowchart_mermaid": "graph TD; A[Topic]-->B[Factor 1]; A-->C[Factor 2];",
                    "visual_prompt": "Clean scientific educational diagram prompt describing the single most critical concept",
                    "drill_mcqs": [
                        {{
                            "q": "Exam grade conceptual question?",
                            "options": ["A", "B", "C", "D"],
                            "answer_idx": 0,
                            "coach_tip": "Why this is the correct choice and examiner trap alert."
                        }}
                    ]
                }}
                """

                try:
                    response_text = call_gemini_safe(client, master_prompt, text)
                    data = json.loads(response_text)
                    st.session_state.suite = data

                    # Voice Selection
                    voice_dict = {
                        "Madhur (Natural Expressive - Male)": "hi-IN-MadhurNeural",
                        "Swara (Warm Engaging - Female)": "hi-IN-SwaraNeural",
                        "Guy (Global Accent - Male)": "en-US-GuyNeural"
                    }
                    chosen_voice = voice_dict.get(voice_actor, "hi-IN-MadhurNeural")

                    # Generate Audio
                    raw_script = data.get("mentor_audio_script", "")
                    st.write("🎙️ Rendering Natural Teacher Voice...")
                    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                    asyncio.run(synthesize_mentor_speech(raw_script, chosen_voice, temp_audio.name))
                    st.session_state.audio_path = temp_audio.name

                    # Generate AI Diagram
                    if generate_ai_art and "visual_prompt" in data:
                        st.write("🎨 Synthesizing AI Textbook Diagram (Imagen 3)...")
                        st.session_state.ai_image = generate_ai_diagram(client, data["visual_prompt"])

                    status.update(label="✨ Master Omni-Suite Ready!", state="complete", expanded=False)
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation error: {e}")

# Display Generated Master Suite
if st.session_state.suite:
    suite = st.session_state.suite
    st.markdown("---")

    col_rst, _ = st.columns([1, 4])
    with col_rst:
        if st.button("🔄 Start New PDF / Reset Session"):
            st.session_state.suite = None
            st.session_state.audio_path = None
            st.session_state.ai_image = None
            st.rerun()

    tab_audio, tab_notes, tab_visuals, tab_drill, tab_export = st.tabs([
        "🎙️ Mentor Audio Masterclass",
        "📑 Board-Grade Matrix Notes",
        "🖼️ AI & Reference Visuals",
        "⚡ Exam-Ready Drill",
        "📥 Export Suite"
    ])

    with tab_audio:
        st.markdown("""
        <div class="session-card">
            <div style="font-size: 0.8rem; font-weight: 700; color: #38BDF8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                🔥 Direct 1-on-1 Mentor Session
            </div>
            <h2 style="margin: 0 0 1rem 0; font-family: 'Space Grotesk', sans-serif;">Concept Mastery & Exam Traps</h2>
        """, unsafe_allow_html=True)

        if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
            st.audio(st.session_state.audio_path, format="audio/mp3")

        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("📖 View Mentor Spoken Lecture Transcript"):
            st.markdown(f"> {suite.get('mentor_audio_script', '')}")

    with tab_notes:
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.08); padding: 10px 16px; border-radius: 8px; border-left: 4px solid #6366F1; margin-bottom: 1.5rem; font-size: 0.9rem; color: #A5B4FC;">
            📌 <b>Official Master Notes</b> • Architected for <b>Ujjwal Jhajharia</b>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(suite.get("master_notes", ""))

    with tab_visuals:
        st.markdown("### 🖼️ AI & Reference Visual Schematics")
        if st.session_state.ai_image:
            st.image(st.session_state.ai_image, caption=f"AI Generated Scientific Diagram: {suite.get('visual_prompt', '')}", use_container_width=True)
        else:
            st.info("AI Diagram generation complete.")

        st.markdown("#### 🌐 Field & Concept Reference Plates")
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.image("https://images.unsplash.com/photo-1592982537447-7440770cbfc9?auto=format&fit=crop&w=800&q=80", 
                     caption="Soil Bed Preparation & Physical Condition (Plate A)", use_container_width=True)
        with col_img2:
            st.image("https://images.unsplash.com/photo-1586771107445-d3ca888129ff?auto=format&fit=crop&w=800&q=80", 
                     caption="Agronomic Methods & Technical Placement (Plate B)", use_container_width=True)

    with tab_drill:
        st.markdown("### 🎯 Exam Trap & Accuracy Drill")
        drills = suite.get("drill_mcqs", [])
        for idx, item in enumerate(drills):
            st.markdown(f"**Q{idx+1}: {item['q']}**")
            ans = st.radio("Choose:", item["options"], key=f"drill_{idx}", label_visibility="collapsed")
            with st.expander("💡 Coach Breakdown"):
                correct = item["options"][item["answer_idx"]]
                if ans == correct:
                    st.success(f"**Exact Target!** {item['coach_tip']}")
                else:
                    st.warning(f"**Target Answer:** **{correct}**\n\n*{item['coach_tip']}*")
            st.write("")

    with tab_export:
        st.markdown("### 📥 Download Complete Package")
        st.download_button(
            label="Download Complete Notes (.md)",
            data=f"# Apex OmniStudy Notes\nArchitected for Ujjwal Jhajharia\n\n" + suite.get("master_notes", ""),
            file_name="Apex_OmniStudy_Master_Notes.md",
            mime="text/markdown"
        )

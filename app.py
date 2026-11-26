import os
import sys
import subprocess
import streamlit as st

# បង្កើតថតបណ្ដោះអាសន្ន /tmp/g_pkgs ដើម្បីគេចផុតពីការចាក់សោសិទ្ធិ (Permissions) របស់ Streamlit
PKG_DIR = "/tmp/g_pkgs"
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

try:
    from google import genai
    from google.genai import types
except ImportError:
    with st.spinner("កំពុងរៀបចំប្រព័ន្ធ Google GenAI SDK សូមរង់ចាំបន្តិច..."):
        os.makedirs(PKG_DIR, exist_ok=True)
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--target", PKG_DIR,
            "--no-deps",
            "google-genai"
        ])
    from google import genai
    from google.genai import types

import time

st.set_page_config(page_title="Music Studio kh - Veo Video Generator", layout="centered")
st.title("🎬 ផលិតវីដេអូ AI (YouTube & TikTok)")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")

# ផ្នែកទី ១៖ ជ្រើសរើសទំហំវីដេអូ (YouTube ឬ TikTok)
st.subheader("📐 ជំហានទី ១៖ ជ្រើសរើសទំហំវីដេអូ")
aspect_choice = st.selectbox(
    "ជ្រើសរើសខ្នាតវីដេអូសម្រាប់ផុស៖",
    [
        "16:9 (វីដេអូផ្តេក - YouTube វែង / Facebook)",
        "9:16 (វីដេអូបញ្ឈរ - TikTok / YouTube Shorts / Reels)"
    ]
)
selected_ratio = "16:9" if "16:9" in aspect_choice else "9:16"

# ផ្នែកទី ២៖ ប្រើ Gemini ជំនាន់ចុងក្រោយ ជួយសរសេរ Prompt
st.subheader("✨ ជំហានទី ២៖ ឱ្យ Gemini 2.5 ជួយសរសេរ Prompt")
idea_kh = st.text_input(
    "សរសេរគំនិតវីដេអូខ្លីៗ (ខ្មែរ ឬអង់គ្លេស)៖",
    placeholder="ឧទាហរណ៍៖ នារីខ្មែរស្លៀកឈុតប្រពៃណីដើរក្នុងចម្ការដូងពេលថ្ងៃលិច"
)

gemini_model = st.selectbox(
    "ជ្រើសរើសម៉ូដែល Gemini (ជំនាន់ចុងក្រោយ)៖",
    ["gemini-2.5-pro", "gemini-2.5-flash"]
)

if "generated_prompt" not in st.session_state:
    st.session_state.generated_prompt = ""

if st.button("🪄 បង្កើត Prompt លម្អិតជាមួយ Gemini"):
    if not api_key or not idea_kh:
        st.warning("សូមបញ្ចូល API Key និងគំនិតវីដេអូជាមុនសិន!")
    else:
        try:
            client = genai.Client(api_key=api_key)
            framing_desc = "16:9 horizontal widescreen YouTube cinematic framing" if selected_ratio == "16:9" else "9:16 vertical TikTok framing"
            with st.spinner("Gemini 2.5 កំពុងសរសេរ Prompt វីដេអូ..."):
                res = client.models.generate_content(
                    model=gemini_model,
                    contents=(
                        f"Write a detailed, cinematic English video generation prompt for Veo AI based on this idea: '{idea_kh}'. "
                        f"Describe camera movement, lighting, realistic details, and {framing_desc}. "
                        "Output ONLY the English prompt without extra explanation."
                    )
                )
                st.session_state.generated_prompt = res.text.strip()
        except Exception as e:
            st.error(f"មានបញ្ហា Gemini៖ {e}")

# ផ្នែកទី ៣៖ ផលិតវីដេអូជាមួយ Veo 3
st.subheader("🎥 ជំហានទី ៣៖ ផលិតវីដេអូ")
prompt = st.text_area(
    "ការពិពណ៌នាវីដេអូ (Prompt ជាភាសាអង់គ្លេស)៖",
    value=st.session_state.generated_prompt,
    height=130
)

veo_model = st.selectbox(
    "ជ្រើសរើសម៉ូដែល Veo 3៖",
    ["veo-3.0-fast-generate-001", "veo-3.0-generate-001"]
)

if st.button("🚀 បង្កើតវីដេអូឥឡូវនេះ"):
    if not api_key or not prompt:
        st.warning("សូមបញ្ចូល API Key និងសរសេរ Prompt ជាមុនសិន!")
    else:
        try:
            client = genai.Client(api_key=api_key)
            with st.spinner(f"កំពុងផលិតវីដេអូខ្នាត {selected_ratio} សូមរង់ចាំប្រហែល ១-២ នាទី..."):
                operation = client.models.generate_videos(
                    model=veo_model,
                    prompt=prompt,
                    config=types.GenerateVideosConfig(
                        aspect_ratio=selected_ratio,
                        person_generation="allow_adult",
                    ),
                )
                
                while not operation.done:
                    time.sleep(10)
                    operation = client.operations.get(operation)
                
                if operation.response and operation.response.generated_videos:
                    video = operation.response.generated_videos[0]
                    client.files.download(file=video.video)
                    video.video.save("output.mp4")
                    
                    st.success(f"ផលិតវីដេអូខ្នាត {selected_ratio} បានជោគជ័យ!")
                    st.video("output.mp4")
                    with open("output.mp4", "rb") as file:
                        st.download_button(
                            label="⬇️ ទាញយកវីដេអូចូល iPhone",
                            data=file,
                            file_name=f"music_studio_veo_{selected_ratio.replace(':', 'x')}.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("មិនអាចបង្កើតវីដេអូបានទេ សូមពិនិត្យ Prompt ម្ដងទៀត។")
        except Exception as e:
            st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")


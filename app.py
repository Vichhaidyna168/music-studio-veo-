import subprocess
import sys
import streamlit as st

# បង្ខំឱ្យដំឡើង google-genai ដោយស្វ័យប្រវត្តិ ប្រសិនបើ Streamlit មិនទាន់បានដំឡើង
try:
    from google import genai
    from google.genai import types
except ImportError:
    with st.spinner("កំពុងដំឡើងប្រព័ន្ធ Google GenAI SDK សូមរង់ចាំបន្តិច..."):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "google-genai"])
    from google import genai
    from google.genai import types

import time

st.set_page_config(page_title="VCY Veo Video Generator", layout="centered")
st.title("🎬 បង្កើតវីដេអូ AI (9:16) ជាមួយ Gemini 2.5 & Veo 3")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")

# ផ្នែកទី ១៖ ប្រើ Gemini ជំនាន់ចុងក្រោយ ជួយសរសេរ Prompt វីដេអូ
st.subheader("✨ ជំហានទី ១៖ ឱ្យ Gemini ជំនាន់ចុងក្រោយជួយសរសេរ Prompt")
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
            with st.spinner("Gemini កំពុងសរសេរ Prompt វីដេអូ..."):
                res = client.models.generate_content(
                    model=gemini_model,
                    contents=(
                        f"Write a detailed, cinematic English video generation prompt for Veo AI based on this idea: '{idea_kh}'. "
                        "Describe camera movement, lighting, realistic details, and 9:16 vertical framing. "
                        "Output ONLY the English prompt without extra explanation."
                    )
                )
                st.session_state.generated_prompt = res.text.strip()
        except Exception as e:
            st.error(f"មានបញ្ហា Gemini៖ {e}")

# ផ្នែកទី ២៖ ផលិតវីដេអូជាមួយ Veo 3
st.subheader("🎥 ជំហានទី ២៖ ផលិតវីដេអូ")
prompt = st.text_area(
    "ការពិពណ៌នាវីដេអូ (Prompt ជាភាសាអង់គ្លេស)៖",
    value=st.session_state.generated_prompt,
    height=130
)

veo_model = st.selectbox(
    "ជ្រើសរើសម៉ូដែល Veo៖",
    ["veo-3.0-fast-generate-001", "veo-3.0-generate-001"]
)

if st.button("🚀 បង្កើតវីដេអូឥឡូវនេះ"):
    if not api_key or not prompt:
        st.warning("សូមបញ្ចូល API Key និងសរសេរ Prompt ជាមុនសិន!")
    else:
        try:
            client = genai.Client(api_key=api_key)
            with st.spinner("កំពុងផលិតវីដេអូ សូមរង់ចាំប្រហែល ១-២ នាទី..."):
                operation = client.models.generate_videos(
                    model=veo_model,
                    prompt=prompt,
                    config=types.GenerateVideosConfig(
                        aspect_ratio="9:16",
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
                    
                    st.success("ផលិតវីដេអូបានជោគជ័យ!")
                    st.video("output.mp4")
                    with open("output.mp4", "rb") as file:
                        st.download_button(
                            label="⬇️ ទាញយកវីដេអូចូល iPhone",
                            data=file,
                            file_name="vcy_veo_video.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("មិនអាចបង្កើតវីដេអូបានទេ សូមពិនិត្យ Prompt ម្ដងទៀត។")
        except Exception as e:
            st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")


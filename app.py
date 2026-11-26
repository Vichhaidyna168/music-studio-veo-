import os
import sys
import subprocess
import urllib.request
import datetime
import streamlit as st

PKG_DIR = "/tmp/g_pkgs"
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

if not os.path.exists(os.path.join(PKG_DIR, "pydantic")):
    with st.spinner("កំពុងរៀបចំប្រព័ន្ធ VCY Flow Studio..."):
        os.makedirs(PKG_DIR, exist_ok=True)
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--target", PKG_DIR,
            "--no-deps",
            "google-genai", "pydantic", "pydantic-core", "annotated-types",
            "typing-extensions", "typing-inspection", "httpx", "httpcore",
            "anyio", "sniffio", "h11", "certifi", "idna", "google-auth",
            "cachetools", "pyasn1", "pyasn1-modules", "rsa", "requests",
            "urllib3", "charset-normalizer", "tenacity", "pillow"
        ])

import google
google_pkg_path = os.path.join(PKG_DIR, "google")
if hasattr(google, "__path__") and google_pkg_path not in google.__path__:
    google.__path__.insert(0, google_pkg_path)

from google import genai
from google.genai import types
import time

st.set_page_config(page_title="VCY Flow Studio", layout="centered")

# រចនាផ្ទៃខាងក្រោយខ្មៅ និងប៊ូតុងជ្រុងមូលដូច Google Flow
st.markdown("""
<style>
    .stApp { background-color: #0e0e0e; color: #ffffff; }
    .stButton>button {
        border-radius: 14px;
        background-color: #1f1f1f;
        color: #cccccc;
        border: 1px solid #333333;
        font-weight: 600;
        padding: 8px 4px;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: #ffffff;
        border-color: #666666;
    }
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
        background-color: #1c1c1c !important;
        border-radius: 14px !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

if "projects" not in st.session_state:
    now_str = datetime.datetime.now().strftime("វិច្ឆិកា %d, %I:%M %p")
    st.session_state.projects = {now_str: []}
if "current_project" not in st.session_state:
    st.session_state.current_project = list(st.session_state.projects.keys())[0]
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "workspace"
if "filter_tab" not in st.session_state:
    st.session_state.filter_tab = "ទាំងអស់"

if "media_mode" not in st.session_state:
    st.session_state.media_mode = "វីដេអូ"
if "aspect_ratio" not in st.session_state:
    st.session_state.aspect_ratio = "9:16"
if "batch_count" not in st.session_state:
    st.session_state.batch_count = 1

# របារខាងលើ (Header)
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    if st.session_state.view_mode == "workspace":
        st.markdown(f"### ← {st.session_state.current_project}")
    else:
        st.markdown("### 🎬 VCY Flow Studio")
with col_h2:
    if st.session_state.view_mode == "workspace":
        if st.button("📁 គម្រោង", key="btn_go_projects", use_container_width=True):
            st.session_state.view_mode = "projects"
            st.rerun()
    else:
        if st.button("+ ថ្មី", key="btn_new_project", use_container_width=True):
            new_name = datetime.datetime.now().strftime("គម្រោង %d/%m %I:%M:%S")
            st.session_state.projects[new_name] = []
            st.session_state.current_project = new_name
            st.session_state.view_mode = "workspace"
            st.rerun()

api_key = st.text_input("🔑 Gemini API Key របស់អ្នក៖", type="password", key="input_api_key")

# ---------------------------------------------------------
# ទំព័រទី ១៖ បញ្ជីគម្រោង
# ---------------------------------------------------------
if st.session_state.view_mode == "projects":
    st.subheader("គម្រោងរបស់អ្នក")
    for proj_name, items in reversed(list(st.session_state.projects.items())):
        vid_count = sum(1 for x in items if x["type"] == "video")
        img_count = sum(1 for x in items if x["type"] == "image")
        if st.button(f"📁 {proj_name}   (🎬 {vid_count}  |  🖼️ {img_count})", key=f"proj_{proj_name}", use_container_width=True):
            st.session_state.current_project = proj_name
            st.session_state.view_mode = "workspace"
            st.rerun()

# ---------------------------------------------------------
# ទំព័រទី ២៖ បន្ទប់ផលិតស្នាដៃ
# ---------------------------------------------------------
else:
    # របារតម្រៀប ទាំងអស់ | រូបភាព | វីដេអូ (ដាក់ Key ផ្សេងគ្នាដើម្បីកុំឱ្យជាន់គ្នា)
    st.session_state.filter_tab = st.radio(
        "តម្រៀបបង្ហាញ៖",
        ["ទាំងអស់", "🖼️ រូបភាព", "🎥 វីដេអូ"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_filter_tab"
    )

    items = st.session_state.projects[st.session_state.current_project]
    if "រូបភាព" in st.session_state.filter_tab:
        items = [i for i in items if i["type"] == "image"]
    elif "វីដេអូ" in st.session_state.filter_tab:
        items = [i for i in items if i["type"] == "video"]

    if items:
        cols = st.columns(2)
        for idx, item in enumerate(items):
            with cols[idx % 2]:
                if item["type"] == "video":
                    st.video(item["path"])
                    with open(item["path"], "rb") as f:
                        st.download_button("⬇️ Save", f, file_name=os.path.basename(item["path"]), key=f"dl_v_{idx}", use_container_width=True)
                else:
                    st.image(item["path"], use_container_width=True)
                    with open(item["path"], "rb") as f:
                        st.download_button("⬇️ Save", f, file_name=os.path.basename(item["path"]), key=f"dl_i_{idx}", use_container_width=True)

    st.markdown("---")
    st.markdown("### តើអ្នកចង់បង្កើតអ្វី?")
    user_prompt = st.text_area(
        "ការពិពណ៌នា៖",
        placeholder="សរសេរគំនិតវីដេអូ ឬរូបភាពនៅទីនេះ...",
        height=85,
        label_visibility="collapsed",
        key="txt_user_prompt"
    )

    uploaded_img = st.file_uploader("➕ បញ្ចូលរូបភាពតួអង្គ (Image-to-Video / ស្រេចចិត្ត)", type=["png", "jpg", "jpeg"], key="up_ref_img")

    col_status, col_send = st.columns([3, 1])
    with col_status:
        icon_m = "🎥" if st.session_state.media_mode == "វីដេអូ" else "🖼️"
        st.markdown(f"**កំពុងរើស៖** `{icon_m} {st.session_state.media_mode}` • `{st.session_state.aspect_ratio}` • `x{st.session_state.batch_count}`")
    with col_send:
        run_btn = st.button("➡️ បង្កើត", key="btn_run_generate", use_container_width=True)

    # ---------------------------------------------------------
    # ផ្ទាំងប៊ូតុងកំណត់ទាំង ៤ ជួរ (ដាក់ Key ដាច់ដោយឡែកទាំងអស់)
    # ---------------------------------------------------------
    with st.container(border=True):
        st.caption("ការបង្កើតនឹងប្រើប្រាស់ Gemini API Key ផ្ទាល់ខ្លួនរបស់អ្នក")
        
        # ជួរទី ១៖ រូបភាព | វីដេអូ
        m1, m2 = st.columns(2)
        with m1:
            lbl_img = "✅ 🖼️ រូបភាព" if st.session_state.media_mode == "រូបភាព" else "🖼️ រូបភាព"
            if st.button(lbl_img, key="mode_btn_image", use_container_width=True):
                st.session_state.media_mode = "រូបភាព"
                st.rerun()
        with m2:
            lbl_vid = "✅ 🎥 វីដេអូ" if st.session_state.media_mode == "វីដេអូ" else "🎥 វីដេអូ"
            if st.button(lbl_vid, key="mode_btn_video", use_container_width=True):
                st.session_state.media_mode = "វីដេអូ"
                if st.session_state.aspect_ratio not in ["16:9", "9:16"]:
                    st.session_state.aspect_ratio = "9:16"
                st.rerun()

        # ជួរទី ២៖ ខ្នាតទំហំ (16:9, 4:3, 1:1, 3:4, 9:16)
        if st.session_state.media_mode == "វីដេអូ":
            r1, r2 = st.columns(2)
            with r1:
                lbl_169 = "✅ ▭ 16:9" if st.session_state.aspect_ratio == "16:9" else "▭ 16:9"
                if st.button(lbl_169, key="vid_rat_169", use_container_width=True):
                    st.session_state.aspect_ratio = "16:9"
                    st.rerun()
            with r2:
                lbl_916 = "✅ ▯ 9:16" if st.session_state.aspect_ratio == "9:16" else "▯ 9:16"
                if st.button(lbl_916, key="vid_rat_916", use_container_width=True):
                    st.session_state.aspect_ratio = "9:16"
                    st.rerun()
        else:
            ratios = ["16:9", "4:3", "1:1", "3:4", "9:16"]
            r_cols = st.columns(5)
            for idx, r in enumerate(ratios):
                with r_cols[idx]:
                    lbl_r = f"✅ {r}" if st.session_state.aspect_ratio == r else r
                    if st.button(lbl_r, key=f"img_rat_{r}", use_container_width=True):
                        st.session_state.aspect_ratio = r
                        st.rerun()

        # ជួរទី ៣៖ ចំនួនផលិត x1 | x2 | x3 | x4
        x_cols = st.columns(4)
        for idx, count in enumerate([1, 2, 3, 4]):
            with x_cols[idx]:
                lbl_x = f"✅ x{count}" if st.session_state.batch_count == count else f"x{count}"
                if st.button(lbl_x, key=f"batch_cnt_{count}", use_container_width=True):
                    st.session_state.batch_count = count
                    st.rerun()

        # ជួរទី ៤៖ ជ្រើសរើសម៉ូដែល AI
        if st.session_state.media_mode == "វីដេអូ":
            selected_model = st.selectbox(
                "ម៉ូដែលវីដេអូ៖",
                ["veo-3.0-fast-generate-001", "veo-3.0-generate-001"],
                format_func=lambda x: "🎬 Veo 3.0 - Fast (Lite)" if "fast" in x else "🎬 Veo 3.0 - Standard (Pro)",
                label_visibility="collapsed",
                key="sel_model_video"
            )
        else:
            selected_model = st.selectbox(
                "ម៉ូដែលរូបភាព៖",
                ["imagen-3.0-generate-002", "gemini-2.5-flash-image"],
                format_func=lambda x: "🍌 Imagen 3 (គុណភាពខ្ពស់)" if "imagen" in x else "🍌 Nano Banana (Gemini 2.5 Image)",
                label_visibility="collapsed",
                key="sel_model_image"
            )

    # ---------------------------------------------------------
    # ដំណើរការផលិតនៅពេលចុចប៊ូតុង ➡️ បង្កើត
    # ---------------------------------------------------------
    if run_btn:
        if not api_key or not user_prompt:
            st.warning("សូមបញ្ចូល API Key និងសរសេរការពិពណ៌នាជាមុនសិន!")
        else:
            try:
                client = genai.Client(api_key=api_key)
                with st.spinner("Gemini 2.5 កំពុងរៀបចំ Prompt..."):
                    p_res = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=(
                            f"Translate and expand this idea into a detailed cinematic English prompt for AI generation: '{user_prompt}'. "
                            f"Target aspect ratio: {st.session_state.aspect_ratio}. Output ONLY the English prompt."
                        )
                    )
                    final_prompt = p_res.text.strip()

                ts = int(time.time())
                # ផលិតរូបភាព
                if st.session_state.media_mode == "រូបភាព":
                    with st.spinner(f"កំពុងបង្កើតរូបភាព x{st.session_state.batch_count}..."):
                        if "imagen" in selected_model:
                            img_res = client.models.generate_images(
                                model=selected_model,
                                prompt=final_prompt,
                                config=types.GenerateImagesConfig(
                                    number_of_images=st.session_state.batch_count,
                                    aspect_ratio=st.session_state.aspect_ratio,
                                )
                            )
                            for i, g_img in enumerate(img_res.generated_images):
                                img_path = f"/tmp/img_{ts}_{i}.png"
                                g_img.image.save(img_path)
                                st.session_state.projects[st.session_state.current_project].append({
                                    "type": "image", "path": img_path
                                })
                        else:
                            for i in range(st.session_state.batch_count):
                                res = client.models.generate_content(
                                    model="gemini-2.5-flash-image",
                                    contents=final_prompt,
                                    config=types.GenerateContentConfig(
                                        response_modalities=["IMAGE"],
                                        image_config=types.ImageConfig(aspect_ratio=st.session_state.aspect_ratio)
                                    )
                                )
                                for part in res.candidates[0].content.parts:
                                    if part.inline_data:
                                        img_path = f"/tmp/img_{ts}_{i}.png"
                                        with open(img_path, "wb") as f:
                                            f.write(part.inline_data.data)
                                        st.session_state.projects[st.session_state.current_project].append({
                                            "type": "image", "path": img_path
                                        })
                        st.rerun()

                # ផលិតវីដេអូ
                else:
                    img_bytes = uploaded_img.read() if uploaded_img is not None else None
                    img_mime = uploaded_img.type if uploaded_img is not None else None
                    
                    for i in range(st.session_state.batch_count):
                        with st.spinner(f"កំពុងផលិតវីដេអូទី {i+1}/{st.session_state.batch_count} ({st.session_state.aspect_ratio})..."):
                            if img_bytes:
                                image_part = types.Image(image_bytes=img_bytes, mime_type=img_mime)
                                operation = client.models.generate_videos(
                                    model=selected_model,
                                    prompt=final_prompt,
                                    image=image_part,
                                    config=types.GenerateVideosConfig(
                                        aspect_ratio=st.session_state.aspect_ratio,
                                        person_generation="allow_adult",
                                    ),
                                )
                            else:
                                operation = client.models.generate_videos(
                                    model=selected_model,
                                    prompt=final_prompt,
                                    config=types.GenerateVideosConfig(
                                        aspect_ratio=st.session_state.aspect_ratio,
                                        person_generation="allow_adult",
                                    ),
                                )

                            while not operation.done:
                                time.sleep(10)
                                operation = client.operations.get(operation)

                            if operation.response and operation.response.generated_videos:
                                video_uri = operation.response.generated_videos[0].video.uri
                                vid_path = f"/tmp/vid_{ts}_{i}.mp4"
                                req = urllib.request.Request(video_uri, headers={"x-goog-api-key": api_key})
                                with urllib.request.urlopen(req) as resp, open(vid_path, "wb") as out_file:
                                    out_file.write(resp.read())

                                st.session_state.projects[st.session_state.current_project].append({
                                    "type": "video", "path": vid_path
                                })
                    st.rerun()

            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")


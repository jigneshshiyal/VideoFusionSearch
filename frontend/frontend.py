import streamlit as st
import requests
import urllib.parse
import streamlit.components.v1 as components

API_URL = "http://localhost:8000"  # Backend endpoint

st.set_page_config(page_title="Multimodal Video Search", layout="centered")
st.title("🎬 Multimodal Video Search")

# -------- Session State --------
if "embedding_done" not in st.session_state:
    st.session_state.embedding_done = False
if "video_url" not in st.session_state:
    st.session_state.video_url = ""
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "selected_timestamp" not in st.session_state:
    st.session_state.selected_timestamp = None

# -------- Step 1: Embedding --------
st.header("Step 1: Generate Embeddings")
embed_url = st.text_input("Enter YouTube URL to Embed", value=st.session_state.video_url)

if st.button("Generate Embeddings"):
    if not embed_url.strip():
        st.warning("Please enter a valid YouTube URL.")
    else:
        with st.spinner("Generating embeddings..."):
            res = requests.post(f"{API_URL}/embed", data={"url": embed_url})
            if res.status_code == 200:
                st.success("Embeddings created successfully.")
                st.session_state.embedding_done = True
                st.session_state.video_url = embed_url
                st.session_state.last_results = []
                st.session_state.selected_timestamp = None
            else:
                st.error(f"Embedding failed: {res.json().get('detail', 'Unknown error')}")

# -------- Step 2: Search --------
st.header("Step 2: Search Video Content")

search_url = st.text_input("YouTube URL to Search", value=st.session_state.video_url)
n_results = st.slider("Number of results", 1, 10, 5)
search_query_type = st.selectbox("Search query type", ["text", "image"])
output_from = st.selectbox("Return results from", ["text", "image", "both"])

# Query inputs
query_text = ""
image_file = None
image_url = ""

if search_query_type == "text":
    query_text = st.text_input("Enter your text query")

elif search_query_type == "image":
    st.markdown("**Provide an image query:**")
    image_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
    image_url = st.text_input("Or enter image URL")

# Button to perform search
if st.button("Search"):
    if not search_url.strip():
        st.warning("Please enter the video URL.")
    elif search_query_type == "text" and not query_text.strip():
        st.warning("Please enter a text query.")
    elif search_query_type == "image" and not (image_file or image_url.strip()):
        st.warning("Please upload an image or enter an image URL.")
    else:
        with st.spinner("Searching..."):
            files = {}
            data = {
                "video_url": search_url,
                "n_results": n_results,
                "search_query_type": search_query_type,
                "output_from": output_from,
            }

            if search_query_type == "text":
                data["query"] = query_text
            elif search_query_type == "image":
                if image_file:
                    files["image_file"] = (image_file.name, image_file, image_file.type)
                elif image_url.strip():
                    data["image_url"] = image_url

            response = requests.post(f"{API_URL}/search", data=data, files=files)

            if response.status_code == 200:
                timestamps = response.json().get("results", [])
                st.session_state.last_results = timestamps
                st.session_state.selected_timestamp = None
                if not timestamps:
                    st.info("No results found.")
                else:
                    st.success(f"Found {len(timestamps)} matching timestamps.")
            else:
                st.error(f"Search failed: {response.json().get('detail', 'Unknown error')}")

# -------- Show Video and Timestamps --------
video_id = None
if "youtube.com" in st.session_state.video_url:
    parsed = urllib.parse.urlparse(st.session_state.video_url)
    query_params = urllib.parse.parse_qs(parsed.query)
    video_id = query_params.get("v", [None])[0]

if video_id:
    base_embed_url = f"https://www.youtube.com/embed/{video_id}"

    # Add start time to embed if timestamp is selected
    if st.session_state.selected_timestamp:
        try:
            h, m, s = map(int, st.session_state.selected_timestamp.split(":"))
        except ValueError:
            h, m = map(int, st.session_state.selected_timestamp.split(":"))
            s = 0
        start_time = h * 3600 + m * 60 + s
        embed_url_with_time = f"{base_embed_url}?start={start_time}&autoplay=1"
    else:
        embed_url_with_time = base_embed_url

    st.subheader("📺 Video Preview")
    components.iframe(embed_url_with_time, height=400, width=700)

# -------- Timestamp Buttons --------
if st.session_state.last_results:
    st.subheader("🕒 Timestamps")
    for ts in st.session_state.last_results:
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            st.markdown(f"**{ts}**")
        with col2:
            if st.button(f"▶️ Jump to {ts}", key=f"jump_{ts}"):
                st.session_state.selected_timestamp = ts
                st.rerun()

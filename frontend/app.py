# app.py - Main Streamlit application for Documma
import streamlit as st
import requests
from PIL import Image
from pdf2image import convert_from_bytes
import io
import os
import base64
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="BaCot", page_icon="🤖", layout="wide")
st.title("📄 BaCot - Babble ChatBot")

st.markdown("""
<style>
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
        border-radius: 10px;
    }
    
    /* Message bubbles */
    .assistant-message {
        background-color: #777; /* Light grey for assistant */
        color: white;
        padding: 15px;
        border-radius: 15px 15px 0 15px; /* Rounded corners, except bottom right */
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-width: 80%;
        float: left; /* Assistant messages on the left */
        clear: both;
    }

    .user-message {
        background-color: #007bff; /* Blue for user */
        color: white;
        padding: 15px;
        border-radius: 15px 15px 15px 0; /* Rounded corners, except bottom left */
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-width: 80%;
        float: right; /* User messages on the right */
        clear: both;
    }
    
    .system-message {
        background-color: #e3f2fd; /* Light blue for system messages */
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: left;
        max-width: 40%;
        margin-left: 0%;
        font-style: italic;
        color: #1c1c1c;
    }
    
    /* Webcam button styling */
    .webcam-btn {
        background-color: #4CAF50 !important;
        color: white !important;
        border-radius: 5px;
        padding: 10px 24px;
        width: 100%;
        margin-top: 10px;
    }
    
    /* Clear floats */
    .message-container::after {
        content: "";
        clear: both;
        display: table;
    }
        /* Webcam preview styling */
    .webcam-preview {
        border-radius: 10px;
        overflow: hidden;
        margin: 20px 0;
    }
    
    /* Capture button styling */
    .capture-btn {
        background-color: #4CAF50 !important;
        color: white !important;
        border-radius: 5px;
        padding: 12px 28px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .capture-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
</style>
""", unsafe_allow_html=True)

def display_message(role, content, file_name=None): 
    css_class = "assistant-message" if role == "assistant" else "system-message"
    st.markdown(f'<div class="{css_class}">{content}</div>', unsafe_allow_html=True)
    st.markdown('<div class="message-container"></div>', unsafe_allow_html=True) 

def display_chat_message(role, content):
    if role == "user":
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    elif role == "assistant":
        st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)
    else: 
        st.markdown(f'<div class="system-message" style="text-align: center; margin: 10px auto;">{content}</div>', unsafe_allow_html=True)
    st.markdown('<div class="message-container"></div>', unsafe_allow_html=True)
    
def display_pdf(uploaded_file):
    # Read file as bytes from the UploadedFile object
    bytes_data = uploaded_file.getvalue() 
    # Convert to Base64
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    # Embed PDF in HTML
    pdf_display_html = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="70%" height="400px" type="application/pdf" style="border: none;"></iframe>'
    # Display file using st.markdown
    st.markdown(pdf_display_html, unsafe_allow_html=True)


def handle_webcam_capture(camera_photo):
    try:
        display_message("system", "📸 Webcam capture received")
        
        img_bytes = camera_photo.getvalue()
        files = {"file": ("webcam_capture.jpg", img_bytes, "image/jpeg")}
        
        with st.spinner("Analyzing document..."):
            resp = requests.post(f"{API_URL}/post-capture-image", files=files)
            resp.raise_for_status()
            data = resp.json()

        # Updated to handle translated_text and new snippet logic from /capture-image
        translated_text = data.get("translated_text", "No translated text available.")
        snippet = data.get("text_snippet", "No snippet available.") # This snippet is now from translated_text
        image_path = data.get("image_path") # Explicitly get image_path
        
        display_message("assistant", f"✅ Image captured, processed, and translated!")
        if translated_text and translated_text != "No translated text available.":
            # Display the full translated text in an expander or text area for better readability
            with st.expander("📜 View Full Translated Text", expanded=True):
                st.text_area("", translated_text, height=350, disabled=False)
            display_message("assistant", f"📝 Translated Text Snippet:\n{snippet}") # Display snippet as well for quick overview
        else:
            display_message("assistant", "ℹ️ No text was detected or translated from the image.")
        # Store in session state
        webcam_entry = {
            "name": "webcam_capture.jpg",
            "text_snippet": snippet, 
            "translated_text": translated_text, 
            "image_path": image_path, 
            "type": "webcam"
        }
        
        st.session_state.processed_files.append(webcam_entry)
        st.session_state.current_file = webcam_entry

        
    except Exception as e:
        display_message("assistant", f"❌ Error processing capture: {str(e)}")
        st.error(f"Webcam processing failed: {e}")
        
def process_uploaded_file(uploaded_file):
    try:
        display_message("system", f"📤 Received document: {uploaded_file.name}")
        
        file_entry = None
        endpoint_url = ""
        files_payload = {}

        if uploaded_file.type == "application/pdf":
            endpoint_url = f"{API_URL}/post-pdf-direct"
            files_payload = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            
            with st.spinner("Processing PDF directly..."):
                resp = requests.post(endpoint_url, files=files_payload)
                resp.raise_for_status()
                data = resp.json()
            
            snippet = data.get("text_snippet", "No snippet available.")
            page_count = data.get("page_count", 0)
            display_message("assistant", f"✅ PDF processed directly! Pages: {page_count}. Snippet below. Content embedded.")
            
            file_entry = {
                "name": uploaded_file.name,
                "type": "pdf", 
                "text_snippet": snippet,
                "page_count": page_count,
                "original_file_object": uploaded_file 
            }

        elif uploaded_file.type.startswith("image"):
            endpoint_url = f"{API_URL}/post-image"
        
            # Send original file without conversion
            uploaded_file.seek(0)  
            files_payload = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

            with st.spinner("Analyzing image..."):
                resp = requests.post(endpoint_url, files=files_payload)
                resp.raise_for_status()
                data = resp.json()

            snippet = data.get("text_snippet", "No snippet available.")
            display_message("assistant", f"✅ Document processed and content embedded!\n\n📝 Text Snippet:\n{snippet}")
            
            # Store in session state
            file_entry = {
                "name": uploaded_file.name, 
                "text_snippet": snippet, 
                "image": data.get("image_path"),
                "type": "image" 
            }
            
        if "processed_files" not in st.session_state:
            st.session_state.processed_files = []
        st.session_state.processed_files.append(file_entry)
        st.session_state.current_file = file_entry
        st.session_state.chat_ready = True
        
    except Exception as e:
        display_message("assistant", f"❌ Error processing document: {str(e)}")
        st.error(f"Failed to process {uploaded_file.name}") 

def handle_audio_processing(uploaded_audio_file_param, current_api_url, display_message_fn):
    display_message_fn("system", f"🎤 Audio file received: {uploaded_audio_file_param.name}")

    # Create file identifier for tracking
    file_id = f"{uploaded_audio_file_param.name}_{uploaded_audio_file_param.size}_{uploaded_audio_file_param.type}"
    
    files = {"file": (uploaded_audio_file_param.name, uploaded_audio_file_param.getvalue(), uploaded_audio_file_param.type)}

    try:
        with st.spinner("Transcribing and summarizing audio... This may take a moment."):
            resp = requests.post(f"{current_api_url}/post-audio", files=files)
            resp.raise_for_status() 
            data = resp.json()

        summary = data.get('summary', 'No summary received.')
        
        # Create audio entry with proper structure
        audio_summary = {
            "name": uploaded_audio_file_param.name,
            "summary": summary, 
            "type": "audio",
            "preview_snippet": summary[:750] + "..." if len(summary) > 750 else summary
        }
        
        # Update session state
        st.session_state.current_file = audio_summary
        st.session_state.current_transcript = summary
        
        if "processed_files" not in st.session_state:
            st.session_state.processed_audio_files = []
        st.session_state.processed_audio_files.append(audio_summary)

        display_message_fn("assistant", f"✅ Audio processed successfully! Summary received.")
        
        if summary and summary != 'No summary received.':
            with st.expander("📜 View Summary", expanded=True): 
                st.text_area("", summary, height=500, disabled=False)
        else:
            display_message_fn("assistant", "ℹ️ No summary was generated for the audio.")


    except requests.exceptions.RequestException as e:
        error_message_detail = f"❌ Error connecting to API: {str(e)}"
        if e.response is not None:
            try:
                server_error_detail = e.response.json().get("detail", e.response.text)
                error_message_detail += f"\nServer says: {server_error_detail}"
            except ValueError:
                error_message_detail += f"\nServer response: {e.response.text}"
        display_message_fn("assistant", error_message_detail)
        st.error(error_message_detail)
        st.session_state.chat_ready = False
        
        # Remove from processed files if processing failed
        file_id = f"{uploaded_audio_file_param.name}_{uploaded_audio_file_param.size}_{uploaded_audio_file_param.type}"
        st.session_state.processed_audio_files.discard(file_id)
        
    except Exception as e:
        error_message_detail = f"❌ Error processing audio: {str(e)}"
        display_message_fn("assistant", error_message_detail)
        st.error(error_message_detail)
        st.session_state.chat_ready = False
        
        # Remove from processed files if processing failed
        file_id = f"{uploaded_audio_file_param.name}_{uploaded_audio_file_param.size}_{uploaded_audio_file_param.type}"
        st.session_state.processed_audio_files.discard(file_id)

# Initialize session state variables if not already present
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "processed_audio_files" not in st.session_state:
    st.session_state.processed_audio_files = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_ready" not in st.session_state: # To enable chat interface
    st.session_state.chat_ready = False
if "current_transcript" not in st.session_state: # To store transcript from audio
    st.session_state.current_transcript = None


# Sidebar controls
with st.sidebar:
    st.header("⚙️ Control Panel")
    mode = st.radio("Input Method:", ["Upload File", "Webcam Capture", "Audio"]) # Added "Audio"
    
    st.markdown("---")
    st.header("Document Preview")
    if "current_file" in st.session_state and st.session_state.current_file:
        current_file = st.session_state.current_file
        st.write(f"**Name:** {current_file['name']}")
        file_type = current_file.get("type")

        if file_type == "pdf":
            st.write(f"**Type:** PDF Document")
            pdf_to_display = current_file.get("original_file_object")
            if pdf_to_display:
                # Ensure the UploadedFile object's internal pointer is at the beginning
                pdf_to_display.seek(0) 
                display_pdf(pdf_to_display)
                
        elif file_type == "audio":
            st.write(f"**Type:** Audio")
            # Audio files use 'summary' to store the full transcript
            if "summary" in current_file and current_file["summary"]:
                 st.text_area("Summary Preview", current_file["summary"][:300] + "...", height=100, disabled=True)
                 st.download_button(
                    label="Download sumary",
                    data=current_file["summary"], # Full transcript
                    file_name=f"{os.path.splitext(current_file['name'])[0]}_summary.txt",
                    mime="text/plain"
                )
                 
        elif file_type == "webcam": # New Webcam Specific Logic
            st.write(f"**Type:** Webcam Capture")
            if "imaage_path" in current_file and current_file["imaage_path"]:
                try:
                    st.image(Image.open(current_file["imaage_path"]), caption=current_file["name"])
                except Exception as e:
                    st.warning(f"Webcam image preview unavailable: {e}")
            elif "text_snippet" in current_file: # Fallback to snippet if full translation somehow missing
                st.text_area("Text Snippet", current_file["text_snippet"], height=100, disabled=True)
        # For images (processed by /post-image) and webcam captures
        elif "image" in current_file and current_file["image"]: 
            st.write(f"**Type:** Image/PDF") 
            try:
                st.image(Image.open(current_file["image"]), caption=current_file["name"])
                if "text_snippet" in current_file:
                    st.text_area("Text Snippet", current_file["text_snippet"], height=100, disabled=True)
                    st.download_button(
                        label="Download Text Snippet",
                        data=current_file["text_snippet"],
                        file_name=f"{os.path.splitext(current_file['name'])[0]}_snippet.txt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.warning(f"Preview unavailable: {e}")
        else:
            st.info("No preview available for this file type or file is corrupted.")
    else:
        st.info("Select an input method and process a file to begin chatting.")
    
    if st.button("🧹 Clear Conversation"):
        st.session_state.processed_files = [] 
        st.session_state.processed_audio_files = set()
        st.session_state.messages = [] 
        st.session_state.pop("current_file", None)
        st.session_state.pop("current_transcript", None) 
        st.session_state.chat_ready = False 
        st.rerun()

# Main content area
with st.container():
    # Input section based on mode
    if mode == "Upload File":
        uploaded_files = st.file_uploader(
            "Drag & drop files or click to browse",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files: # Variable name updated
            for uploaded_file in uploaded_files: 
                processed_file_names = [f['name'] for f in st.session_state.processed_files]
                if uploaded_file.name not in processed_file_names:
                    process_uploaded_file(uploaded_file) 
    
    elif mode == "Webcam Capture":
        # Webcam mode
        st.markdown("### Live Webcam Preview")
        camera_photo_ui = st.camera_input(
            "Look at the camera and click the button below to capture",
            key="webcam_capture",
            help="Position your document in the frame and click the capture button"
        )
        if camera_photo_ui:
            # st.image(camera_photo_ui, caption="Captured Image", use_column_width=True)
            if st.button("📸 Analyze Now", key="capture_btn", use_container_width=True):
                if camera_photo_ui:
                    handle_webcam_capture(camera_photo_ui) # Parameter name updated
                else:
                    st.error("Please allow webcam access first")
    
    elif mode == "Audio":
        st.markdown("### Upload Audio File")
        uploaded_audio_file_from_ui = st.file_uploader(
            "Upload an audio file for transcription and Q&A",
            type=['wav', 'mp3', 'm4a', 'ogg', 'flac'],
            key="audio_uploader"
        )

        if uploaded_audio_file_from_ui:
            # Call the refactored function using global API_URL and display_message
            handle_audio_processing(uploaded_audio_file_from_ui, API_URL, display_message)

    # Chat interface - appears if chat is ready (a document has been processed)
    if st.session_state.get('chat_ready', False):
        st.markdown("---")
        st.subheader("💬 Chat with your Document")

        # Display chat messages
        if not st.session_state.messages:
             st.session_state.messages.append({"role": "assistant", "content": "Hi there! Ask me anything about the processed content."})

        for msg in st.session_state.messages:
            display_chat_message(msg["role"], msg["content"])

        # Chat input
        user_query = st.chat_input("Ask a question...", key="chat_input")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})

            try:
                with st.spinner("Thinking..."):
                    chat_payload = {"query": user_query}
                    resp = requests.post(f"{API_URL}/chat", json=chat_payload)
                    resp.raise_for_status()
                    chat_data = resp.json()

                assistant_response = chat_data.get("answer", "Sorry, I couldn't get a response.")
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})

            except requests.exceptions.RequestException as e:
                error_msg = f"Sorry, I couldn't connect to the chat service. {str(e)}"
                if e.response is not None:
                    try:
                        error_detail = e.response.json().get("detail", e.response.text)
                        error_msg += f"\nServer says: {error_detail}"
                    except ValueError:
                         error_msg += f"\nServer response: {e.response.text}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"An error occurred: {str(e)}"})

            st.rerun() # Rerun to update chat display with new messages
    elif not st.session_state.get('current_file') and not mode : 
        st.info("Select an input method and process a file to begin chatting.")

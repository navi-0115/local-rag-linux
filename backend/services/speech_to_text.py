import whisper
import os # Added import
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OllamaEmbeddings
# from langchain.llms import Ollama

# Define a persistent path for the FAISS index
FAISS_INDEX_PATH = "services/faiss_index"



def transcribe_audio(audio_path):
    
    model=whisper.load_model("medium")

    # Transcribe the audio file
    result = model.transcribe(audio_path)
    print(f'Transcribed Text:\n{result["text"]}')
    return result["text"]
    
def embed_transcription(transcription):
    
    # Initialize the Ollama embeddings model
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Split the transcription into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(transcription)

    if os.path.exists(FAISS_INDEX_PATH):
        # Load the existing FAISS index
        vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        # Add new texts to the loaded index
        vector_store.add_texts(texts)
        print(f"FAISS index loaded from {FAISS_INDEX_PATH} and updated.")
    else:
        # Create a new FAISS index from the texts
        vector_store = FAISS.from_texts(texts, embeddings)
        print(f"New FAISS index created at {FAISS_INDEX_PATH}.")

    # Save the (new or updated) index to disk
    vector_store.save_local(FAISS_INDEX_PATH)
    print(f"FAISS index saved to {FAISS_INDEX_PATH}.")

    return vector_store
    


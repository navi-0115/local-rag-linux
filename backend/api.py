import os # Moved to top
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from services.ocr_module import extract_text
from services.preprocess import preprocess_image, light_preprocess_image
from services.llm_module import translate_context, summarize_context

# Imports for speech-to-text and chat functionalities
# import os
import tempfile
import io
from fastapi import Body, HTTPException # Added Body
from fastapi.responses import HTMLResponse

from services.speech_to_text import transcribe_audio, embed_transcription
from services.llm_module import summarize_context, translate_context
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS
from pypdf import PdfReader 
from langchain.llms import Ollama
# RecursiveCharacterTextSplitter is used within embed_transcription

# Define the path to the FAISS index (relative to this api.py file)
FAISS_INDEX_PATH = "services/faiss_index"

# Initialize Ollama components
embeddings = OllamaEmbeddings(model="nomic-embed-text")
llm = Ollama(model="gemma3:4b") 

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/post-image", status_code=200)
async def post_file_ocr(file: UploadFile = File(...)):
    # Get valid file extension
    suffix = os.path.splitext(file.filename)[-1].lower()
    if suffix not in ['.jpg', '.jpeg', '.png']:
        suffix = '.jpg'
    
    # Create temp file with valid extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_image:
        content = await file.read()
        temporary_image.write(content)
        temp_path = temporary_image.name
    # Preprocessing
    try:
        preprocessed_file = light_preprocess_image(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")
    
    # OCR processing
    try:
        extracted_text = extract_text(preprocessed_file)
        if not extracted_text.strip():
            print("OCR resulted in empty text. Skipping embedding.")
        else:
            print(f"OCR successful. Length: {len(extracted_text)}. Embedding extracted text...")
            embed_transcription(extracted_text)
            print(f"Embedding of extracted image/PDF text successful. FAISS index updated/created at {FAISS_INDEX_PATH}")

    except Exception as e:
        print(f"Error during OCR or Embedding for image/PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR or Embedding failed: {str(e)}")
    
    snippet_max_length = 250
    if not extracted_text or not extracted_text.strip():
        text_snippet = "No text extracted from document."
    else:
        text_snippet = extracted_text[:snippet_max_length] + "..." if len(extracted_text) > snippet_max_length else extracted_text

    return JSONResponse(
        status_code=200,
        content={
            "message": "Uploaded file processed successfully and content embedded.",
            "image_path": preprocessed_file, 
            "text_snippet": text_snippet
        }
    )
    

@app.post("/post-capture-image", status_code=200)
async def post_capture_image(file: UploadFile = File(...)):
    # Get valid file extension
    suffix = os.path.splitext(file.filename)[-1].lower()
    if suffix not in ['.jpg', '.jpeg', '.png']:
        suffix = '.jpg'
    
    # Create temp file with valid extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_image:
        content = await file.read()
        temporary_image.write(content)
        temp_path = temporary_image.name

    # Preprocessing
    try:
        preprocessed_file = light_preprocess_image(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")
    
    # OCR processing
    try:
        extracted_text = extract_text(preprocessed_file)
        if not extracted_text.strip():
            print("OCR resulted in empty text. Skipping embedding.")
        else:
            print(f"OCR successful. Length: {len(extracted_text)}. Embedding extracted text...")

    except Exception as e:
        # This will catch errors from extract_text or embed_transcription
        print(f"Error during OCR or Embedding for image/PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR or Embedding failed: {str(e)}")
    
    # Translate the extracted text
    translated_text = translate_context(extracted_text)
    print(f"Translation attempted. Original length: {len(extracted_text)}, Translated length: {len(translated_text)}")
    print(f"Translated text: {translated_text}") 
    
    # Generate text snippet
    snippet_max_length = 250
    if not translated_text.strip() or translated_text == "No text detected in image.": # Check if translate_text modified the "empty" message
        text_snippet = "No text detected or translated from image."
    else:
        text_snippet = translated_text[:snippet_max_length] + "..." if len(translated_text) > snippet_max_length else translated_text
    
    # No longer saving summary to a file or generating full summary here.
    # That functionality is now implicitly handled by RAG/chat.

    return JSONResponse(
        status_code=200,
        content={
            "message": "Captured image processed and translated successfully.",
            "image_path": preprocessed_file,
            "translated_text": translated_text,
            "text_snippet": text_snippet
        }
    )
    
@app.post("/post-pdf-direct", status_code=200)
async def post_pdf_direct(file: UploadFile = File(...)):
    try:
        pdf_content_bytes = await file.read()
        pdf_file = io.BytesIO(pdf_content_bytes)
        
        reader = PdfReader(pdf_file)
        num_pages = len(reader.pages)
        full_extracted_text = ""
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            full_extracted_text += page.extract_text() or ""

        if not full_extracted_text.strip():
            return JSONResponse(
                status_code=400, 
                content={"message": "No text could be extracted from the PDF."}
            )

        # Embed the full extracted text
        print(f"PDF text extraction successful. Length: {len(full_extracted_text)}. Embedding extracted text...")
        embed_transcription(full_extracted_text) 
        print("Embedding of extracted PDF text successful.")

        # Generate snippet
        snippet_max_length = 250
        text_snippet = full_extracted_text[:snippet_max_length]
        if len(full_extracted_text) > snippet_max_length:
            text_snippet += "..."
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "PDF processed successfully, text extracted and embedded.",
                "text_snippet": text_snippet,
                "page_count": num_pages
            }
        )
    except Exception as e:
        print(f"Error processing PDF directly: {str(e)}") # Log the error
        # Consider more specific error handling for pypdf exceptions if needed
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        await file.close()


# Endpoint to process audio: transcribe and embed
@app.post("/post-audio", status_code=200)
async def process_audio_endpoint(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        if not suffix: 
            suffix = '.mp3'

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_audio_file:
            content = await file.read()
            temporary_audio_file.write(content)
            temp_audio_path = temporary_audio_file.name

        print(f"Temporary audio file saved at: {temp_audio_path}")

        # 1. Transcribe audio
        transcript = transcribe_audio(temp_audio_path)
        print(f"Transcription successful. Length: {len(transcript)}")

        # 2. Summarize transcription
        summary = summarize_context(transcript)
        print(f"Summarization of transcript successful.")

        return JSONResponse(
            status_code=200,
            content={
                "message": "Audio processed and summarized successfully.", 
                "summary": summary
            }
        )
    except Exception as e:
        print(f"Error in /post-audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    finally:
        # Clean up the temporary audio file
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            print(f"Temporary audio file {temp_audio_path} deleted.")

# Endpoint for chat using the FAISS index
@app.post("/chat", status_code=200)
async def chat_endpoint(payload: dict = Body(...)):
    try:
        query = payload.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty.")

        # Check if FAISS index exists
        if not os.path.exists(FAISS_INDEX_PATH) or not os.path.isdir(FAISS_INDEX_PATH):
            return JSONResponse(
                status_code=404,
                content={"message": "FAISS index not found. Please upload and process the content first."}
            )

        # Load the FAISS index
        try:
            vector_store = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"FAISS index loaded successfully from {FAISS_INDEX_PATH}")
        except Exception as e:
            print(f"Error loading FAISS index: {str(e)}")
            # Attempt to provide more specific feedback if it's a common issue
            if "No such file or directory" in str(e) and "index.faiss" in str(e):
                 error_detail = "FAISS index files (e.g., index.faiss, index.pkl) not found. Ensure uploaded file was processed."
            else:
                error_detail = f"Could not load FAISS index: {str(e)}"
            raise HTTPException(status_code=500, detail=error_detail)


        # Perform similarity search
        docs = vector_store.similarity_search(query, k=3) # Retrieve top 3 relevant chunks
        print(f"Similarity search found {len(docs)} documents.")

        if not docs:
            return JSONResponse(
                status_code=200, # Or 404 if preferred when no context found
                content={"answer": "No relevant information found in the audio context to answer your query."}
            )

        # Construct context for the LLM
        context = "\n".join([doc.page_content for doc in docs])

        # Construct prompt for LLM
        prompt_template = f"You are an assistant for question-answering tasks. Use the following pieces of retrieved context \n\n---\n{context}\n to answer the question. If you don't know the answer, say that you don't know. DON'T MAKE UP ANYTHING. Answer the question informatively, but based on the above context---\n\nUser Query: {query}\n\n"


        # Invoke the LLM
        response = llm.invoke(prompt_template)
        print(f"LLM response received: {response}")

        return JSONResponse(
            status_code=200,
            content={"answer": response}
        )
    except HTTPException as e:
        # Re-raise HTTPExceptions to let FastAPI handle them
        raise e
    except Exception as e:
        print(f"Error in /chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}")

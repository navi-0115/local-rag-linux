# === llm_module ===
import requests
from langdetect import detect
import json

def query_llm(prompt):
    llm_api_url = os.getenv("LLM_API_URL", "http://localhost:11434")
    
    response = requests.post(
        f"{llm_api_url}/api/generate",
        json={
            "model": "gemma3:4b",
            "prompt": prompt,
            "stream": False,
        }
    )
    try:
        response.raise_for_status()
        response_data = response.json()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"LLM API error: {e.response.text}") from e
    except json.JSONDecodeError:
        raise RuntimeError("Invalid JSON response from LLM API")
    
    if "response" not in response_data:
        raise RuntimeError(f"Unexpected LLM response format: {response_data}")
    
    return response_data["response"]

def translate_context(context: str) -> str:
    try:
        prompt = f"""You are an assistant for translation tasks. 
        Use the following pieces of retrieved context \n\n---\n{context}\n to translate it in english. 
        IF ITS IN CHINESE, TRANSLATE IN ENGLISH. DO NOT GIVE CHINESE RESULTS. DON'T HALLUCINATE AND DON'T MAKE UP ANYTHING."""
        return query_llm(prompt)
    except Exception as e:
        raise RuntimeError(f"Translation failed: {str(e)}") from e

def summarize_context(context: str) -> str:
    try:
        prompt = f"""You are an assistant for summarization tasks. 
        Use the following pieces of retrieved context \n\n---\n{context}\n to summarize it in english. 
        DON'T HALLUCINATE AND DON'T MAKE UP ANYTHING. summarize informatively based on the above context"""
        return query_llm(prompt)
    except Exception as e:
        raise RuntimeError(f"Summarization failed: {str(e)}") from e
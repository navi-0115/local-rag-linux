# === ocr_module ===
from paddleocr import PaddleOCR
import os

def extract_text(image_path: str, text_save_path: str = None, lang='ch') -> str:
    ocr = PaddleOCR(use_angle_cls=True, lang=lang)
    result = ocr.ocr(image_path, cls=True)

    extracted_text = ""
    
    if not result:
        return "No text detected"
        
    try:
        for line in result:
            if line:  # Check for empty lines
                for word_info in line:
                    if word_info and len(word_info) >= 2:
                        text_entry = word_info[1]
                        if text_entry and len(text_entry) >= 1:
                            extracted_text += text_entry[0] + "\n"
    except Exception as e:
        raise RuntimeError(f"Text extraction failed: {str(e)}")

    # Optional text saving
    if text_save_path:
        os.makedirs(os.path.dirname(text_save_path), exist_ok=True)
        with open(text_save_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

    return extracted_text
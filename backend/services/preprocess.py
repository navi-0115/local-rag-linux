# === preprocess ===
import cv2
import numpy as np
import os
import threading


def preprocess_image(image_path: str) -> str:
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found or cannot be opened: {image_path}")
    
    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, h=20, templateWindowSize=8, searchWindowSize=21)
    # Blur
    blurred = cv2.GaussianBlur(denoised, (7, 7), 0)
    # Gamma correction
    gamma = 1.5
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
    gamma_corrected = cv2.LUT(blurred, table)
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gamma_corrected, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 19, 19
    )
    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    close_morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    dilation = cv2.dilate(close_morph, kernel_small, iterations=2)

    # Save processed
    base, ext = os.path.splitext(image_path)
    out_path = f"{base}_preprocessed.jpg" 
    success = cv2.imwrite(out_path, dilation)
    if not success:
        raise IOError(f"Failed to write preprocessed image to: {out_path}")
    return out_path

def light_preprocess_image(image_path: str) -> str:
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found or cannot be opened: {image_path}")
    
    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, h=20, templateWindowSize=8, searchWindowSize=21)
    # Gamma correction
    gamma = 1.5
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
    gamma_corrected = cv2.LUT(denoised, table)
    
    # Save processed
    base, ext = os.path.splitext(image_path)
    out_path = f"{base}_preprocessed.jpg" 
    success = cv2.imwrite(out_path, gamma_corrected)
    if not success:
        raise IOError(f"Failed to write preprocessed image to: {out_path}")
    return out_path




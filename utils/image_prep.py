import cv2
import numpy as np
from PIL import Image

def preprocess_for_ocr(pil_image):
    img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    img_cv = cv2.resize(img_cv, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    bg = cv2.GaussianBlur(gray, (55,55), 0)
    norm = cv2.divide(gray, bg, scale=255)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl1 = clahe.apply(norm)
    blur = cv2.GaussianBlur(cl1, (3, 3), 0)
    h, w = blur.shape
    left_block = blur[:, :int(w * 0.62)]
    t, _ = cv2.threshold(left_block, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, thresh = cv2.threshold(blur, t, 255, cv2.THRESH_BINARY)
    kernel = np.ones((2,2), np.uint8)
    thickened = cv2.erode(thresh, kernel, iterations=1)
    return Image.fromarray(thickened)

def preprocess_nik(pil_image):
    img = np.array(pil_image)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    # enlarge A LOT
    gray = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    variants = []
    # Variant 1 : Otsu
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(Image.fromarray(otsu))
    # Variant 2 : Adaptive
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
    variants.append(Image.fromarray(adaptive))
    # Variant 3 : Inverted
    _, inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    variants.append(Image.fromarray(inv))

    return variants
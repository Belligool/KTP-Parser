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

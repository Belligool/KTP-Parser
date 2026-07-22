import cv2
import numpy as np
from PIL import Image

def preprocess_for_ocr(pil_image):
    img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    img_cv = cv2.resize(img_cv, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (1, 1), 0)
    adjusted = cv2.convertScaleAbs(blur, alpha=1.5, beta=-20)
    _, thresh = cv2.threshold(adjusted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return Image.fromarray(thresh)
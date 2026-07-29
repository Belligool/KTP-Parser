import cv2
import numpy as np
from PIL import Image
import pytesseract

def classify_digit(pil_img):
    img = np.array(pil_img)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    gray = cv2.resize(gray, (96, 96), interpolation=cv2.INTER_CUBIC)
    kernel = np.array([
        [-1, -1, -1],
        [-1, 9, -1],
        [-1, -1, -1]
    ])
    sharp = cv2.filter2D(gray, -1, kernel)
    _, thresh = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(Image.fromarray(thresh), lang='eng', config='--psm 10 -c tessedit_char_whitelist=0123456789')
    text = ''.join(c for c in text if c.isdigit())
    if text:
        return text[0]
    return ''
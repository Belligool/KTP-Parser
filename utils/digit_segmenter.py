import cv2
import numpy as np
from PIL import Image

def segment_digits(pil_img):
    img = np.array(pil_img)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    digits = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area < 80:
            continue
        if w > h * 1.3:
            continue
        if h < 18:
            continue
        roi = thresh[y:y+h, x:x+w]
        roi = cv2.copyMakeBorder(roi, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=0)
        roi = cv2.resize(roi, (64, 64), interpolation=cv2.INTER_CUBIC)
        digits.append((x, Image.fromarray(255 - roi)))
    digits.sort(key=lambda x: x[0])
    return [d for _, d in digits]
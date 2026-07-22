import pytesseract
import fitz
import io
from PIL import Image
from utils.image_prep import preprocess_for_ocr

class OCREngine:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def extract(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"ERROR reading {pdf_path}. Details: {e}")
            return ""

        raw_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            clean_img = preprocess_for_ocr(img)
            page_text = pytesseract.image_to_string(clean_img, lang='ind', config='--psm 6')
            raw_text += page_text + "\n"
            
        return raw_text
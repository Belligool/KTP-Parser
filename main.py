import os
import pytesseract
import fitz
import io
from PIL import Image
from core.extractor import KTPExtractor
from utils.image_prep import preprocess_for_ocr

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def process_pdf(pdf_path, extractor):
    print(f"\n--- Scanning: {os.path.basename(pdf_path)} ---")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"ERROR reading {pdf_path}. Details: {e}")
        return

    raw_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        zoom = 2
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        clean_img = preprocess_for_ocr(img)
        page_text = pytesseract.image_to_string(clean_img, lang='ind')
        raw_text += page_text + "\n"
    parsed_data = extractor.extract_data(raw_text)
    
    for key, value in parsed_data.items():
        print(f"{key}: {value}")

def main():
    target_dir = 'tests/sample_pdfs/'
    extractor = KTPExtractor()
    
    if not os.path.exists(target_dir):
        print(f"Directory {target_dir} not found.")
        return
        
    for filename in os.listdir(target_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(target_dir, filename)
            process_pdf(pdf_path, extractor)

if __name__ == "__main__":
    main()
import os
import pytesseract
import fitz
import io
import csv
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

    return extractor.extract_data(raw_text)

def main():
    target_dir = 'tests/sample_pdfs/'
    extractor = KTPExtractor()
    
    if not os.path.exists(target_dir):
        print(f"Directory {target_dir} not found.")
        return
    
    all_ktp_records = []

    for filename in os.listdir(target_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(target_dir, filename)
            data = process_pdf(pdf_path, extractor)
            if data:
                data['Source File'] = filename
                all_ktp_records.append(data)
    if all_ktp_records:
        output_dir = 'tests/results/'
        os.makedirs(output_dir, exist_ok=True)
        csv_filename = os.path.join(output_dir, "ktp_export_results.csv")
        headers = ["Source File", "NIK", "Nama", "Tempat/Tgl Lahir", "Status Pernikahan"]
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_ktp_records)
        print(f"Exported {len(all_ktp_records)} KTP records to {csv_filename}")
    else:
        print("\nNo KTP data was extracted.")

if __name__ == "__main__":
    main()
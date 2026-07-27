import pytesseract
import fitz
import io
import os
import re
import numpy as np
from PIL import Image
from utils.image_prep import preprocess_for_ocr

class OCREngine:
    def __init__(self, confidence_threshold=60, merge_gap_ratio=0.25, merge_confidence_ceiling=90):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        # Words tesseract reports below this confidence (0-100) get flagged
        # for manual review instead of silently passed through.
        self.confidence_threshold = confidence_threshold
        # Tesseract's confidence score reflects certainty about character
        # shapes, not whether it inserted a space correctly, so a silently
        # merged word (e.g. "SUESTORM" from "SUE STORM") can still score high
        # confidence. As a second, independent check, we look for an unusually
        # wide gap of blank pixels *inside* a single word's own bounding box,
        # relative to that word's own height.
        self.merge_gap_ratio = merge_gap_ratio
        # Some label fonts on these cards (e.g. "NIK") have naturally wide,
        # uniform letter spacing and can trip the gap check even when
        # correctly read. Only trust the gap signal when tesseract's own
        # confidence for that word isn't already very high.
        self.merge_confidence_ceiling = merge_confidence_ceiling

    def _max_gap_ratio(self, arr, left, top, width, height):
        if width <= 0 or height <= 0:
            return 0
        crop = arr[top:top + height, left:left + width]
        mask = crop < 128
        col_has_text = mask.any(axis=0)
        max_gap = 0
        gap_len = 0
        for has_text in col_has_text:
            if not has_text:
                gap_len += 1
                max_gap = max(max_gap, gap_len)
            else:
                gap_len = 0
        return max_gap / height

    def _extract_nik_candidate(self, clean_img, data):
        n = len(data['text'])
        for i in range(n):
            word = data['text'][i].strip().upper().rstrip(':;-. ')
            if word != 'NIK':
                continue
            label_right = data['left'][i] + data['width'][i]
            top, height = data['top'][i], data['height'][i]
            img_w, img_h = clean_img.size
            pad = int(height * 0.3)
            crop = clean_img.crop((
                label_right, max(0, top - pad),
                img_w, min(img_h, top + height + pad)
            ))
            crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
            text = pytesseract.image_to_string(
                crop, lang='eng',
                config='--psm 7 -c tessedit_char_whitelist=0123456789'
            )
            digits = re.sub(r'\D', '', text)
            return digits or None
        return None

    def extract(self, pdf_path):
        """Returns (raw_text, flagged_words, nik_candidate).
        flagged_words is a list of raw OCR tokens that are either below
        self.confidence_threshold or show signs of a silently-merged space.
        nik_candidate is a best-effort digit-only re-read of the NIK field
        (see _extract_nik_candidate), or None if the label wasn't found."""
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"ERROR reading {pdf_path}. Details: {e}")
            return "", [], None
 
        raw_text = ""
        flagged_words = []
        nik_candidate = None
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            clean_img = preprocess_for_ocr(img)
            debug_dir = 'tests/results/debug_images/'
            os.makedirs(debug_dir, exist_ok=True)
            base_name = os.path.basename(pdf_path).replace('.pdf', f'_page_{page_num}.png')
            debug_path = os.path.join(debug_dir, base_name)
            clean_img.save(debug_path)
            page_text = pytesseract.image_to_string(clean_img, lang='ind', config='--psm 6')
            raw_text += page_text + "\n"
            data = pytesseract.image_to_data(
                clean_img, lang='ind', config='--psm 6',
                output_type=pytesseract.Output.DICT
            )
            arr = np.array(clean_img.convert('L'))
            n = len(data['text'])
            for i in range(n):
                word = data['text'][i].strip()
                if not word:
                    continue
                low_conf = False
                conf = -1
                try:
                    conf = float(data['conf'][i])
                    low_conf = 0 <= conf < self.confidence_threshold
                except (ValueError, TypeError):
                    pass
                gap_ratio = self._max_gap_ratio(
                    arr, data['left'][i], data['top'][i],
                    data['width'][i], data['height'][i]
                )
                merged = (gap_ratio > self.merge_gap_ratio
                          and 0 <= conf < self.merge_confidence_ceiling)
                if low_conf or merged:
                    flagged_words.append(word)
 
            if nik_candidate is None:
                nik_candidate = self._extract_nik_candidate(clean_img, data)
 
        return raw_text, flagged_words, nik_candidate

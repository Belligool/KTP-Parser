import pytesseract
import fitz
import io
import os
import re
import numpy as np
from PIL import Image
from utils.image_prep import *
from utils.digit_segmenter import segment_digits

class OCREngine:
    def __init__(self, confidence_threshold=60, merge_gap_ratio=0.25, merge_confidence_ceiling=90):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' #replace this with your tesseract folder
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

    def _extract_nik_candidate(self, original_img, data):
        n = len(data["text"])
        best_candidate = None
        best_score = -999
        configs = [
            "--psm 7 -c tessedit_char_whitelist=0123456789",
            "--psm 8 -c tessedit_char_whitelist=0123456789",
            "--psm 13 -c tessedit_char_whitelist=0123456789",
        ]
        for i in range(n):
            word = data["text"][i].strip().upper()
            normalized = (
                word.replace("1", "I")
                    .replace("L", "I")
                    .replace("|", "I")
                    .replace(":", "")
                    .replace(".", "")
            )
            if normalized != "NIK":
                continue
            left = data["left"][i]
            top = data["top"][i]
            width = data["width"][i]
            height = data["height"][i]
            img_w, img_h = original_img.size
            x1 = left + width + int(height * 1.0)
            x2 = min(img_w, x1 + int(img_w * 0.45))
            y1 = max(0, top - int(height * 0.5))
            y2 = min(img_h, top + int(height * 1.5))
            crop = original_img.crop((x1, y1, x2, y2))
            digit_images = segment_digits(crop)
            if len(digit_images) >= 14:
                nik = ""
                for digit in digit_images:
                    nik += self._ocr_single_digit(digit)
                if len(nik) == 16:
                    return nik
            for variant in preprocess_nik(crop):
                for cfg in configs:
                    text = pytesseract.image_to_string(variant, lang="eng", config=cfg)
                    digits = re.sub(r"\D", "", text)
                    score = 0
                    score -= abs(16 - len(digits)) * 20
                    if len(digits) == 16:
                        score += 100
                    if score > best_score:
                        best_score = score
                        best_candidate = digits
            return best_candidate

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
            gray_original = img.convert("L")
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
                nik_candidate = self._extract_nik_candidate(gray_original, data)
 
        return raw_text, flagged_words, nik_candidate

    def _ocr_single_digit(self, img):
        text = pytesseract.image_to_string(img, lang="eng", config="--psm 10 -c tessedit_char_whitelist=0123456789")
        text = re.sub(r"\D", "", text)
        if text:
            return text[0]
        return ""
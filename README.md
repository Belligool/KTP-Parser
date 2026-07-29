# KTP Parser

A lightweight OCR-based parser for Indonesian KTP (Kartu Tanda Penduduk) that extracts a small set of important fields from scanned or photographed identity cards.

## Features

- Extracts:
  - NIK
  - Nama
  - Tempat / Tanggal Lahir
  - Status Pernikahan
- Batch processes PDF files
- Exports results to Excel
- Automatic OCR preprocessing
- Confidence-based review flagging
- OCR post-processing and validation
- Saves preprocessed debug images for troubleshooting

---

## Project Structure

```
KTP Parser/
│
├── core/
│   ├── extractor.py
│   ├── ocr_engine.py
│   └── validators.py
│
├── utils/
│   ├── image_prep.py
│   └── regex_utils.py
│
├── tests/
│   ├── sample_pdfs/
│   └── results/
│       └── debug_images/
│
├── main.py
└── README.md
```
**IMPORTANT!** Make sure to create the tests folder.
---

## Requirements

- Python 3.10+
- Tesseract OCR
- OpenCV
- Pillow
- PyMuPDF
- NumPy
- OpenPyXL

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Tesseract separately and update the path inside:

```
core/ocr_engine.py
```

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## Usage

Place all KTP PDF files inside:

```
tests/sample_pdfs/
```

Run:

```bash
python main.py
```

Results will be generated in:

```
tests/results/
```

including:

- `ktp_export_results.xlsx`
- preprocessed debug images
- optional raw OCR text

---

## Output

| Field | Description |
|--------|-------------|
| Source File | Input PDF |
| NIK | Indonesian National ID Number |
| Nama | Full Name |
| Tempat/Tgl Lahir | Place and Date of Birth |
| Status Pernikahan | Marital Status |
| Review Needed | Fields that may require manual verification |

---

## Current Limitations

Older KTP cards using machine-readable OCR fonts may still produce occasional NIK recognition errors.
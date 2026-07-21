import re

# NIK remains strictly 16 digits
NIK_REGEX = re.compile(r'\b(\d{16})\b')

# Allow common OCR typos for "Nama" (Narna, Neme, Hama)
NAMA_REGEX = re.compile(r'(?:Nama|Narna|Name|Nema|Hama)\s*[:;]?\s*([A-Z\s\.\,]+)', re.IGNORECASE)

# Allow common OCR typos for "Lahir" (Tahir, Lshir)
TTL_REGEX = re.compile(r'(?:Lahir|Tahir|Lshir|Lahr)\s*[:;]?\s*([A-Za-z\s\.\,]+,\s*\d{2}-\d{2}-\d{4})', re.IGNORECASE)

# Strict legal dictionary
STATUS_REGEX = re.compile(r'(BELUM KAWIN|KAWIN|CERAI HIDUP|CERAI MATI)', re.IGNORECASE)
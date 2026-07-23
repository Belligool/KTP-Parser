import re

# NIK remains strictly 16 digits
NIK_REGEX = re.compile(r'\b(\d{16})\b')

# Allow common OCR typos for "Nama" (Narna, Neme, Hama)
NAMA_REGEX = re.compile(r'(?i:Nama|Narna|Name|Nema|Hama|Harna|Hame|Hema|Mama|Marna|Mame|Mema|Noma|Namo|Naama|Namaa|Nma|Naina|Naoa|Naua|Narna|Narne|Narno|Narn|Narnr)\s*[:;]?\s*[^A-Za-z]{0,3}\s*([A-Z]{2,}(?:[\s\.,]+[A-Z]{2,})*)')

# Allow common OCR typos for "Lahir" (Tahir, Lshir)
TTL_REGEX = re.compile(r'(?i:Lahir|Tahir|Lshir|Lahr|Lahir|Lahir:|Lahir.|Lahir,|Lah1r|Lahlr|Lahirr|Lahirh|Lahiri|Lahirl|LahirI|LahirT|Laher|Lehir|Lohir|Lahirn|Lahirm|Labir|Lakir|Lakir|Sahir|Jahir|Iahir)\s*[:;]?\s*([A-Za-z\s\.\,]+,\s*\d{2}-\d{2}-\d{4})')

# Strict legal dictionary
STATUS_REGEX = re.compile(r'\b(BELUM KAWIN|KAWIN|CERAI HIDUP|CERAI MATI|NOT MARRIED|MARRIED|DIVORCE|BELUM NIKAH)\b', re.IGNORECASE)
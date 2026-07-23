import re
from utils.regex_utils import *
from core.validators import KTPValidator

class KTPExtractor:
    def __init__(self):
        self.validator = KTPValidator()

    def extract_data(self, raw_text):
        # Keep lines for Name fallback, but also create a flattened block of text
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        joined_text = " ".join(lines)
        
        ktp_data = {
            "NIK": "",
            "Nama": "",
            "Tempat/Tgl Lahir": "",
            "Status Pernikahan": ""
        }
        
        # 1. PATTERN HUNT: NIK (Look for 16 digits anywhere in the document)
        nik_match = NIK_REGEX.search(joined_text)
        if nik_match:
            ktp_data["NIK"] = nik_match.group(1)
        else:
            fallback_matches = re.findall(r'\b([A-Za-z0-9]{16})\b', joined_text)
            for match in fallback_matches:
                cleaned = self.validator.clean_nik(match)
                if cleaned:
                    ktp_data["NIK"] = cleaned
                    break
                    
        # 2. PATTERN HUNT: TTL (Look for the undeniable City, DD-MM-YYYY format anywhere)
        # We limit the city search to ~30 chars behind the comma to prevent grabbing the whole document
        ttl_match = re.search(r'([A-Za-z\s\-]{3,30})\s*,\s*([\dOBISZ]{2}-[\dOBISZ]{2}-[\dOBISZ]{4})', joined_text)
        if ttl_match:
            city_raw = ttl_match.group(1)
            # Strip out any trailing OCR labels that might have bled into the city name
            clean_city = re.sub(r'(?i)(Tempat|Tgl|Lahir|Lahe|Jenis|Kelamin|Alamat|Nama|NIK)', '', city_raw).strip()
            # Grab just the final word(s) before the comma
            city = " ".join(clean_city.split()[-2:]) 
            ktp_data["Tempat/Tgl Lahir"] = f"{city.upper()}, {ttl_match.group(2)}"
            
        # 3. PATTERN HUNT: Status (Look for exact legal keywords like MARRIED or KAWIN anywhere)
        status_match = STATUS_REGEX.search(joined_text)
        if status_match:
            ktp_data["Status Pernikahan"] = status_match.group(1).upper().strip()
            
        # 4. HYBRID HUNT: Nama
        for i, line in enumerate(lines):
            if ktp_data["Nama"]:
                break
            nama_match = NAMA_REGEX.search(line)
            if nama_match:
                raw_nama = nama_match.group(1).replace("TEMPAT", "").strip()
                ktp_data["Nama"] = self.validator.clean_name(raw_nama)
                break
            if re.match(r'^(Nama|Narna|Name|Nema)\s*[:;]?$', line, re.IGNORECASE):
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j]
                    clean_chars = [c for c in next_line if c.isalpha()]
                    if clean_chars and sum(1 for c in clean_chars if c.isupper()) / len(clean_chars) > 0.6:
                        blocklist = r'\b(TEMPAT|JENIS|GOL|ALAMAT|RT|RW|MALE|FEMALE|BLOOD)\b'
                        if not re.search(blocklist, next_line, re.IGNORECASE):
                            clean_line = re.sub(r'^.*?[:;]\s*', '', next_line)
                            ktp_data["Nama"] = self.validator.clean_name(clean_line.replace("TEMPAT", "").strip())
                            break
                            
        return ktp_data
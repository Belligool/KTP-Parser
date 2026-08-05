import re
from utils.regex_utils import *
from core.validators import KTPValidator

class KTPExtractor:
    def __init__(self):
        self.validator = KTPValidator()

    def extract_data(self, raw_text, low_confidence_words=None, nik_candidate=None):
        # Keep lines for Name fallback, but also create a flattened block of text
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        joined_text = " ".join(lines)
        normalized_low_conf = set()
        for w in (low_confidence_words or []):
            cleaned = re.sub(r'[^A-Za-z0-9]', '', w).upper()
            if cleaned:
                normalized_low_conf.add(cleaned)

        ktp_data = {
            "NIK": "",
            "Nama": "",
            "Tempat/Tgl Lahir": "",
            "Status Pernikahan": "",
            "Review Needed": ""
        }
        
        # 1. PATTERN HUNT: NIK (Look for 16 digits anywhere in the document)
        nik_from_fallback = False
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
            if not ktp_data["NIK"]:
                if nik_candidate:
                    ktp_data["NIK"] = nik_candidate
                    nik_from_fallback = True
                else:
                    near_nik = re.search(
                        r'NIK\D{0,5}(\d{14,18})', joined_text, re.IGNORECASE
                    )
                    if near_nik:
                        ktp_data["NIK"] = near_nik.group(1)
                        nik_from_fallback = True
        '''
        NIK must always be exactly 16 digits. If what we extracted isn't,
        don't try to algorithmically guess which digit is wrong, flag it
        for a human to check against the original card instead. A NIK
        sourced from the fallback paths is also always flagged, even when
        it lands on exactly 16 digits, since testing showed the crop-based
        ensemble can produce a plausible-length but wrong value there.
        '''
        nik_needs_review = bool(ktp_data["NIK"]) and (
            len(ktp_data["NIK"]) != 16 or nik_from_fallback
        )
                    
        # 2. PATTERN HUNT: TTL (Look for the undeniable City, DD-MM-YYYY format anywhere)
        ttl_match = re.search(
            r'([A-Za-z\s\-]{3,30})\s*,\s*'
            r'([\dOBISZ]{2})[\s\-]*([\dOBISZ]{2})[\s\-]*([\dOBISZ]{4})',
            joined_text
        )
        if ttl_match:
            city_raw = ttl_match.group(1)
            # Strip out any trailing OCR labels that might have bled into the city name
            clean_city = re.sub(r'(?i)(Tempat|Tgl|Lahir|Lahe|Jenis|Kelamin|Alamat|Nama|NIK)', '', city_raw).strip()
            # Grab just the final word(s) before the comma
            city = " ".join(clean_city.split()[-2:]) 
            day, month, year = ttl_match.group(2), ttl_match.group(3), ttl_match.group(4)
            ktp_data["Tempat/Tgl Lahir"] = f"{city.upper()}, {day}-{month}-{year}"
            try:
                if not (1 <= int(day) <= 31 and 1 <= int(month) <= 12):
                    ttl_needs_review = True
                else:
                    ttl_needs_review = False
            except ValueError:
                ttl_needs_review = True
        else:
            ttl_needs_review = False
            
        # 3. PATTERN HUNT: Status
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

        if ktp_data["Nama"] and normalized_low_conf:
            words = ktp_data["Nama"].split()
            while len(words) > 1:
                last_clean = re.sub(r'[^A-Za-z0-9]', '', words[-1]).upper()
                if last_clean and last_clean in normalized_low_conf:
                    words.pop()
                else:
                    break
            ktp_data["Nama"] = " ".join(words)

        ''' 
        Residual safety net: even after trimming, a name this long is rare 
        enough to warrant a human glance rather than being trusted blindly.
        '''
        nama_word_count = len(ktp_data["Nama"].split()) if ktp_data["Nama"] else 0
        nama_needs_review = nama_word_count > 6

        # 5. QA FLAG
        flagged_fields = []
        if normalized_low_conf:
            for field_name in ("Nama", "Tempat/Tgl Lahir", "Status Pernikahan"):
                value = ktp_data[field_name]
                if not value:
                    continue
                for token in re.split(r'[\s,]+', value):
                    cleaned_token = re.sub(r'[^A-Za-z0-9]', '', token).upper()
                    if cleaned_token and cleaned_token in normalized_low_conf:
                        flagged_fields.append(field_name)
                        break
        if nik_needs_review and "NIK" not in flagged_fields:
            flagged_fields.append("NIK")
        if ttl_needs_review and "Tempat/Tgl Lahir" not in flagged_fields:
            flagged_fields.append("Tempat/Tgl Lahir")
        if nama_needs_review and "Nama" not in flagged_fields:
            flagged_fields.append("Nama")
        ktp_data["Review Needed"] = ", ".join(flagged_fields)

        return ktp_data
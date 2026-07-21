from utils.regex_utils import *
from core.validators import KTPValidator

class KTPExtractor:
    def __init__(self):
        self.validator = KTPValidator()

    def extract_data(self, raw_text):
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        ktp_data = {
            "NIK": "",
            "Nama": "",
            "Tempat/Tgl Lahir": "",
            "Status Pernikahan": ""
        }
        
        for line in lines:
            # NIK
            if not ktp_data["NIK"]:
                nik_match = NIK_REGEX.search(line)
                if nik_match:
                    ktp_data["NIK"] = nik_match.group(1)
                else:
                    fallback_match = re.search(r'\b([A-Za-z0-9]{16})\b', line)
                    if fallback_match:
                        cleaned = self.validator.clean_nik(fallback_match.group(1))
                        if cleaned:
                            ktp_data["NIK"] = cleaned
            # Nama
            if not ktp_data["Nama"]:
                nama_match = NAMA_REGEX.search(line)
                if nama_match:
                    ktp_data["Nama"] = nama_match.group(1).replace("TEMPAT", "").strip()
                elif ktp_data["NIK"] and not ktp_data["Tempat/Tgl Lahir"]:
                    if line.isupper() and not any(char.isdigit() for char in line):
                        if not re.search(r'\b(ALAMAT|RT|RW|KEL|DESA|PROVINSI)\b', line, re.IGNORECASE):
                            clean_line = re.sub(r'^.*?[:;]\s*', '', line)
                            ktp_data["Nama"] = self.validator.clean_name(clean_line.replace("TEMPAT", "").strip())
                    
            # TTL
            if not ktp_data["Tempat/Tgl Lahir"]:
                ttl_match = TTL_REGEX.search(line)
                if ttl_match:
                    ktp_data["Tempat/Tgl Lahir"] = ttl_match.group(1).strip()
                    
            # Status Nikah
            if not ktp_data["Status Pernikahan"]:
                loose_status_match = re.search(r'kawinan\s*[:;]?\s*(.*)', line, re.IGNORECASE)
                if loose_status_match:
                    ktp_data["Status Pernikahan"] = self.validator.clean_status(loose_status_match.group(1))
        
        return ktp_data

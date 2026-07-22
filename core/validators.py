import difflib

class KTPValidator:
    def __init__(self):
        self.valid_statuses = ["BELUM KAWIN", "KAWIN", "CERAI HIDUP", "CERAI MATI"]
        self.nik_replacements = {
            'O': '0', 'o': '0', 'D': '0', 'Q': '0',
            'I': '1', 'l': '1', 'i': '1', '|': '1', ']': '1', '[': '1',
            'Z': '2', 'z': '2',
            'S': '5', 's': '5',
            'G': '6',
            'B': '8',
            'A': '4'
        }
    
    def clean_status(self, raw_status):
        if not raw_status:
            return ""
        raw_upper = raw_status.upper().strip()
        matches = difflib.get_close_matches(raw_upper, self.valid_statuses, n=1, cutoff=0.6)
        if matches:
            return matches[0]
        return raw_upper

    def clean_nik(self, raw_nik):
        if not raw_nik:
            return ""
        cleaned = "".join([self.nik_replacements.get(c, c) for c in raw_nik])
        cleaned = "".join([c for c in cleaned if c.isdigit()])
        if len(cleaned) == 16:
            return cleaned
        return ""

    def clean_name(self, raw_name):
        if not raw_name:
            return ""
        text_replacements = {
            '0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B',
        }
        
        cleaned = "".join([text_replacements.get(c, c) for c in raw_name.upper()])
        cleaned = "".join([c for c in cleaned if c.isalpha() or c in " .,'-"])
        return cleaned.strip()
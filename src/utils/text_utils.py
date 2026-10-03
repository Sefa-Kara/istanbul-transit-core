import re
from typing import Optional

MOJIBAKE_MAP = {
    'Ä°': 'İ', 'Ã–': 'Ö', 'Ãœ': 'Ü', 'Ã‡': 'Ç', 'Åž': 'Ş', 'Äž': 'Ğ',
    'Ä±': 'ı', 'Ã¶': 'ö', 'Ã¼': 'ü', 'Ã§': 'ç', 'ÅŸ': 'ş', 'ÄŸ': 'ğ',
    'Ã°': 'İ', 'ð': 'İ', 'Ã*': 'Ç', 'Â ': 'Ğ', 'Â': '',
    'KAÂ ITHANE': 'KAĞITHANE', 'KAÂITHANE': 'KAĞITHANE',
    'EMÃ°NÃ–NÃœ': 'EMİNÖNÜ', 'MECÃ°DÃ°YEKÃ–Y': 'MECİDİYEKÖY',
    'TAKSÃ°M': 'TAKSİM', 'Å\x9e': 'Ş', 'Ä\x9e': 'Ğ', 'Ä\xb0': 'İ',
    'Ã§': 'ç', 'Ã¶': 'ö', 'Ã¼': 'ü', 'Ä±': 'ı', 'ÅŸ': 'ş', 'ÄŸ': 'ğ',
    'Å': 'Ş', 'Ä': 'Ğ', 'Ä°': 'İ', 'Ã‡': 'Ç', 'Ã': 'Ö', 'Ã': 'Ü'
}

def repair_turkish_mojibake(text: Optional[str]) -> str:
    """
    Repairs corrupted multi-byte UTF-8 strings mistakenly interpreted
    as Windows-1252 / ISO-8859-1 or split into ASCII control characters.
    Handles Istanbul GTFS edge cases like 'KAÂ ITHANE', '46Ã*', 'GÃœLBAÄž'.
    """
    if not text:
        return ""
    s = str(text)
    
    # Quick check for potential corruption marks
    if not any(c in s for c in ("Ã", "Å", "Ä", "â", "Â", "ð", "\u00c2", "\u00c3", "\u00c4", "\u00c5", "Ã*")):
        return s.strip()
        
    try:
        candidate = s.encode("windows-1252").decode("utf-8")
        s = candidate
    except Exception:
        pass

    for bad, good in MOJIBAKE_MAP.items():
        if bad in s:
            s = s.replace(bad, good)
            
    s = s.replace("\u00a0", " ").replace("Â", "")
    return re.sub(r"\s+", " ", s).strip()

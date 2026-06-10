import re

FILLER_PATTERN = re.compile(
    r"(?:,\s*)?\b(uh+|um+|erm+|hmm+|you know|i mean|like,|sort of,|kind of,)\b[,.]?\s*",
    re.IGNORECASE,
)

NOISE_TRANSCRIPTS = {
    "thank you.",
    "thanks for watching.",
    "you",
    ".",
    "",
}

TIME_PATTERN = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", re.IGNORECASE)

ABBREVIATIONS = {
    "ETA": "पहुंचने का अनुमानित समय",
    "ASAP": "जल्द से जल्द",
    "FYI": "आपकी जानकारी के लिए",
}


def remove_fillers(text: str) -> str:
    cleaned = FILLER_PATTERN.sub(" ", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.?!])", r"\1", cleaned)
    return cleaned.strip().lstrip(",.").strip()


def is_meaningful(text: str) -> bool:
    normalized = text.strip().lower()
    if normalized in NOISE_TRANSCRIPTS:
        return False
    return len(normalized) >= 2


def localize_times(hindi_text: str) -> str:
    def replace(match: re.Match) -> str:
        hour = int(match.group(1))
        minutes = match.group(2)
        meridiem = match.group(3).lower()
        if meridiem == "am":
            period = "सुबह" if hour < 12 else "दोपहर"
        else:
            period = "दोपहर" if hour in (12, 1, 2, 3) else "शाम" if hour <= 7 else "रात"
        time_str = f"{hour}:{minutes}" if minutes else str(hour)
        return f"{period} {time_str} बजे"

    return TIME_PATTERN.sub(replace, hindi_text)

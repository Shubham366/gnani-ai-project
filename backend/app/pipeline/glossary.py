import re

KEEP_IN_ENGLISH = [
    "Google Meet",
    "Google Calendar",
    "Asterisk",
    "Zoom",
    "Slack",
    "Microsoft Teams",
    "WhatsApp",
    "API",
    "OTP",
    "Wi-Fi",
    "GitHub",
    "Gnani",
]

ASR_HINT = ", ".join(KEEP_IN_ENGLISH)


def protect(text: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}
    protected = text
    for i, term in enumerate(KEEP_IN_ENGLISH):
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(protected):
            token = f"XQZ{i}XQZ"
            placeholders[token] = term
            protected = pattern.sub(token, protected)
    return protected, placeholders


def restore(text: str, placeholders: dict[str, str]) -> str:
    restored = text
    for token, term in placeholders.items():
        restored = re.sub(token, term, restored, flags=re.IGNORECASE)
    return restored

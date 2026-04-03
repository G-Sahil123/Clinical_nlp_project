import re
import os

def load_notes(patient_dir):
    notes = []
    files = sorted(os.listdir(patient_dir))

    for file in files:
        if file.endswith(".md"):
            path = os.path.join(patient_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            note_id = file.replace(".md", "")
            note_date = extract_note_date(text)
            text = add_line_numbers(text)
            notes.append((note_id, note_date, text))

    return notes


DATE_PATTERNS = [
    # "from MM/DD/YYYY to MM/DD/YYYY" → use first date
    r'from\s+(\d{1,2}/\d{1,2}/\d{2,4})',
    # "on MM/DD/YYYY"
    r'on\s+(\d{1,2}/\d{1,2}/\d{2,4})',
    # "for ... on MM/DD/YYYY"
    r'(\d{1,2}/\d{1,2}/\d{2,4})',
]

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def extract_note_date(text: str) -> str:
    lines = text.splitlines()[:10]

    # Patterns ordered by specificity — first match wins
    encounter_patterns = [
        r'from\s+(\d{1,2}/\d{1,2}/\d{2,4})',
        r'(?:presented|admitted|treated|follow.?up)\s+(?:\S+\s+){0,3}on\s+(\d{1,2}/\d{1,2}/\d{2,4})',
        r'on\s+(\d{1,2}/\d{1,2}/\d{2,4})',
    ]

    for line in lines:
        # Skip lines that mention date of birth — they contain the patient's DOB
        if 'born' in line.lower():
            continue

        for pattern in encounter_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                parts = match.group(1).split("/")
                if len(parts) == 3:
                    month = int(parts[0])
                    day = int(parts[1])
                    year  = int(parts[2])
                    if year < 100:
                        year += 2000
                    if 1 <= month <= 12:
                        return f"{day} {MONTH_NAMES[month]} {year}"
                elif len(parts) == 2:
                    month = int(parts[0])
                    year = int(parts[1])
                    if year < 100:
                        year += 2000
                    return f"{MONTH_NAMES[month]} {year}"
    return None 

def add_line_numbers(text):
    return "\n".join([f"{i+1}: {line}" for i, line in enumerate(text.split("\n"))])
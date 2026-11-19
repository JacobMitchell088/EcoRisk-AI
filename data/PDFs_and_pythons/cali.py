import fitz
import pandas as pd
import re

PDF_FILE = "California_plants.pdf"
OUTPUT_FILE = "california_plants.csv"

# Status codes we want
STATUS_CODES = {
    "SE": "Endangered",
    "FE": "Endangered",
    "ST": "Threatened",
    "FT": "Threatened"
}

# Scientific name pattern
SCIENTIFIC_PATTERN = re.compile(
    r"^[A-Z][a-z-]+(?: [a-z-]+)+(?: (?:pop\.|DPS|ESU).*)?$"
)

records = []

doc = fitz.open(PDF_FILE)

for page_number in range(len(doc)):
    text = doc[page_number].get_text("text")
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip headings and non-species text
        if (
            line in ["Taxon", "Common Name", "State Status",
                     "Federal Status", "Notes"]
            or "State and Federally Listed" in line
            or line in ["Invertebrates", "Fishes", "Amphibians",
                        "Reptiles", "Birds", "Mammals"]
        ):
            i += 1
            continue

        # Detect likely scientific name
        if SCIENTIFIC_PATTERN.match(line):

            scientific_name = line
            common_name_parts = []
            statuses = []

            j = i + 1

            # Read until another scientific name or section heading
            while j < len(lines):
                current = lines[j]

                if SCIENTIFIC_PATTERN.match(current):
                    break

                # Find status codes
                found_statuses = re.findall(
                    r"\b(?:SE|ST|FE|FT)\b",
                    current
                )

                if found_statuses:
                    statuses.extend(found_statuses)

                # Stop after collecting a status and date
                if statuses and re.search(r"\b\d{8}\b", current):
                    break

                # Avoid collecting headings
                if current not in [
                    "Taxon", "Common Name", "State Status",
                    "Federal Status", "Notes"
                ]:
                    common_name_parts.append(current)

                j += 1

            # Only keep endangered/threatened records
            if statuses:
                normalized_statuses = [
                    STATUS_CODES[status]
                    for status in statuses
                    if status in STATUS_CODES
                ]

                if normalized_statuses:
                    # Use the first status found
                    final_status = normalized_statuses[0]

                    # Remove dates and excess text from common name
                    common_name = " ".join(common_name_parts)
                    common_name = re.sub(
                        r"\b\d{8}\b", "", common_name
                    ).strip()

                    records.append({
                        "Common Name": common_name,
                        "Scientific Name": scientific_name,
                        "Status": final_status,
                        "Original Status": ", ".join(
                            sorted(set(statuses))
                        ),
                        "State": "California"
                    })

            i = j
        else:
            i += 1


df = pd.DataFrame(records)

if not df.empty:
    df = df.drop_duplicates(
        subset=[
            "Scientific Name",
            "Common Name",
            "Status"
        ]
    )

df.to_csv(OUTPUT_FILE, index=False)

print(f"Pages scanned: {len(doc)}")
print(f"Records collected: {len(df)}")
print(f"CSV saved as: {OUTPUT_FILE}")
import fitz
import pandas as pd
import re

PDF_FILE = "FloridaThreatEnd.pdf"
OUTPUT_FILE = "florida_species.csv"

doc = fitz.open(PDF_FILE)
rows = []

for page in doc:
    words = page.get_text("words")

    # Group words by their vertical position
    lines = {}

    for word in words:
        x0, y0, x1, y1, text = word[:5]
        key = round(y0, 1)

        if key not in lines:
            lines[key] = []

        lines[key].append((x0, text))

    current_common = []
    current_scientific = []

    for key in sorted(lines):
        words_on_line = sorted(lines[key])
        
        common = []
        scientific = []
        status = None

        for x, text in words_on_line:
            if x < 200:
                common.append(text)

            elif 200 <= x < 440:
                scientific.append(text)

            elif x >= 440:
                match = re.match(r"^(FE|FT\(S/A\)|FT|ST|FXN)", text)

                if match:
                    status = match.group(1)

        # Accumulate wrapped names
        if common:
            current_common.extend(common)

        if scientific:
            current_scientific.extend(scientific)

        # Finish record when status is found
        if status:
            common_name = " ".join(current_common).strip()
            scientific_name = " ".join(current_scientific).strip()

            if common_name and scientific_name:
                if status == "FE":
                    normalized_status = "Endangered"
                else:
                    normalized_status = "Threatened"

                rows.append({
                    "Common Name": common_name,
                    "Scientific Name": scientific_name,
                    "Status": normalized_status,
                    "Original Status": status,
                    "State": "Florida"
                })

            current_common = []
            current_scientific = []

df = pd.DataFrame(rows)
df = df.drop_duplicates()

df.to_csv(OUTPUT_FILE, index=False)

print(f"Saved {len(df)} species to {OUTPUT_FILE}")

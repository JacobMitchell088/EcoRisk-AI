import fitz
import pandas as pd
import re

PDF_FILE = "GeorgiaThreatEnd.pdf"
OUTPUT_FILE = "georgia_species.csv"

doc = fitz.open(PDF_FILE)
rows = []

for page in doc:
    text = page.get_text("text")

    for line in text.splitlines():
        match = re.search(
            r"\)\s+([A-Za-z][^:]+):\s+(.+?)\s+\((endangered|threatened|rare|unusual)\)",
            line,
            re.IGNORECASE
        )

        if match:
            scientific_name = match.group(1).strip()
            common_name = match.group(2).strip()
            original_status = match.group(3).capitalize()

            # Only keep endangered and threatened
            if original_status in ["Endangered", "Threatened"]:
                rows.append({
                    "Common Name": common_name,
                    "Scientific Name": scientific_name,
                    "Status": original_status,
                    "Original Status": original_status,
                    "State": "Georgia"
                })

df = pd.DataFrame(rows)

df.to_csv(OUTPUT_FILE, index=False)

print(f"Saved {len(df)} species to {OUTPUT_FILE}")
import fitz  # PyMuPDF
import pandas as pd
import re

PDF_FILE = "arkansasEndThreat.pdf"
OUTPUT_FILE = "arkansas_species.csv"

# Status conversion
def normalize_status(federal, state):
    federal = str(federal).strip().upper()
    state = str(state).strip().upper()

    if federal in ["LE", "SE"] or state == "SE":
        return "Endangered"

    if federal in ["LT", "ST"] or state == "ST":
        return "Threatened"

    return None


# Open PDF
doc = fitz.open(PDF_FILE)

records = []
current_county = "Unknown"
in_species_section = False

# Scrape from page 115 through the END of the PDF
for page_number in range(114, len(doc)):
    page = doc[page_number]
    text = page.get_text("text")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect county headings
        if "County" in line and len(line) < 60:
            current_county = line.replace("County", "").strip()

        # Detect vascular plant section
        if "Plants-Vascular" in line:
            in_species_section = True
            i += 1
            continue

        # Stop collecting when another major section begins
        if (
            "Animals-Invertebrates" in line
            or "Animals-Vertebrates" in line
        ):
            in_species_section = False

        # Look for a possible scientific name
        if re.match(
            r"^[A-Z][a-z]+ [a-z-]+", line
        ):
            scientific_name = line

            # Ensure enough lines remain for a complete record
            if i + 5 < len(lines):
                common_name = lines[i + 1]
                federal_status = lines[i + 2]
                state_status = lines[i + 3]
                global_rank = lines[i + 4]
                state_rank = lines[i + 5]

                status = normalize_status(
                    federal_status,
                    state_status
                )

                if status is not None:
                    records.append({
                        "County": current_county,
                        "Scientific Name": scientific_name,
                        "Common Name": common_name,
                        "Federal Status": federal_status,
                        "State Status": state_status,
                        "Status": status,
                        "Global Rank": global_rank,
                        "State Rank": state_rank
                    })

                i += 6
                continue

        i += 1


# Create DataFrame
df = pd.DataFrame(records)

# Remove duplicates
if not df.empty:
    df = df.drop_duplicates(
        subset=["Scientific Name", "County", "Status"]
    )

# Save CSV
df.to_csv(OUTPUT_FILE, index=False)

print(f"Finished scraping {len(doc)} PDF pages.")
print(f"Records collected: {len(df)}")
print(f"CSV saved as: {OUTPUT_FILE}")
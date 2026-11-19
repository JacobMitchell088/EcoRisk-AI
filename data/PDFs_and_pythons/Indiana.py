import pdfplumber
import pandas as pd
import re

import pdfplumber




def scrape_indiana_animal(PDF_FILE, OUTPUT_FILE):

    records = []
    status = None
    in_animals = False

    with pdfplumber.open(PDF_FILE) as pdf:

        for page in pdf.pages:
            text = page.extract_text() or ""

            for line in text.splitlines():
                line = line.strip()

                # Remove spaces only for checking section headings
                check = line.replace(" ", "")

                # Start of animals
                if check == "III.ANIMALS":
                    in_animals = True
                    continue

                # Plants start here
                if check == "IV.VASCULARPLANTS":
                    in_animals = False
                    status = None
                    continue

                if not in_animals:
                    continue

                # Endangered
                match = re.match(r'^\d+\.(Endangered)', check, re.IGNORECASE)

                if match:
                    status = "Endangered"
                    continue

                # Threatened
                match = re.match(r'^\d+\.(Threatened)', check, re.IGNORECASE)

                if match:
                    status = "Threatened"
                    continue

                # These sections should NOT be included
                if re.match(
                    r'^\d+\.(SpecialConcern|Extirpated|Rare)',
                    check,
                    re.IGNORECASE
                ):
                    status = None
                    continue

                # Species format:
                # Myotisgrisescens,"graymyotis"
                match = re.match(
                    r'^([^,]+),\s*"([^"]+)"$',
                    line
                )

                if match and status:

                    scientific_name = match.group(1).strip()
                    common_name = match.group(2).strip()

                    records.append({
                        "Common Name": common_name,
                        "Scientific Name": scientific_name,
                        "Status": status,
                        "Original Status": status,
                        "State": "Indiana"
                    })

    df = pd.DataFrame(records)

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved: {OUTPUT_FILE}")
    print(f"Records: {len(df)}")

    return df





# import pdfplumber
# import pandas as pd
# import re

PDF_FILE = "Indiana_plants.pdf"
OUTPUT_FILE = "indiana_plants.csv"

rows = []

# Recognized status codes
FEDERAL_CODES = {"E", "T", "C", "PE", "PT"}
STATE_CODES = {"SE", "ST", "SR", "SX"}

with pdfplumber.open(PDF_FILE) as pdf:

    for page in pdf.pages:
        text = page.extract_text()

        if not text:
            continue

        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            # Skip headers and empty lines
            if (
                not line
                or "Species Name" in line
                or "Common Name" in line
                or line.startswith("DNR")
                or line.startswith("Page ")
            ):
                continue

            # Find the GRANK and SRANK fields
            rank_match = re.search(
                r"\b(G[A-Z0-9?]+)\s+(S[A-Z0-9?]+)\b",
                line
            )

            if not rank_match:
                continue

            grank = rank_match.group(1)
            srank = rank_match.group(2)

            before_ranks = line[:rank_match.start()].strip()
            after_ranks = line[rank_match.end():].strip()

            # Scientific names generally begin with:
            # Genus species, with an optional subspecies
            scientific_match = re.match(
                r"^([A-Z][a-z-]+\s+[a-z][a-z-]+(?:\s+[a-z][a-z-]+)?)\s+(.+)$",
                before_ranks
            )

            if not scientific_match:
                continue

            scientific_name = scientific_match.group(1)
            common_name = scientific_match.group(2).strip()

            # Identify federal and state status codes
            status_codes = after_ranks.split()

            federal_status = ""
            state_status = ""

            for code in status_codes:
                code = code.upper().strip(" ,.;")

                if code in FEDERAL_CODES:
                    federal_status = code

                elif code in STATE_CODES:
                    state_status = code

            rows.append({
                "Species Name": scientific_name,
                "Common Name": common_name,
                "GRANK": grank,
                "SRANK": srank,
                "FEDERAL": federal_status,
                "STATE": state_status
            })

# Create DataFrame
df = pd.DataFrame(rows)

# Remove duplicate records
df = df.drop_duplicates()

# Save CSV
df.to_csv(OUTPUT_FILE, index=False)

print(f"CSV created: {OUTPUT_FILE}")
print(f"Total records: {len(df)}")


#scrape_indiana_animal("Indiana_animals.pdf", "data/Indiana_anim.csv" ) # create list through this

#scrape_indiana_plant("Indiana_plants.pdf","data/Indiana_plan.csv")

import pdfplumber
import pandas as pd
from pathlib import Path

PDF = Path("virginia.pdf")
OUTPUT = "virginia_threatened_endangered.csv"

if not PDF.exists():
    raise FileNotFoundError(f"Could not find PDF: {PDF.resolve()}")

records = []

with pdfplumber.open(PDF) as pdf:
    # The threatened/endangered species table is on pages 1–5.
    for page_number, page in enumerate(pdf.pages[:5], start=1):
        words = page.extract_words()

        # Find each State Endangered (SE) or State Threatened (ST) entry.
        for status_word in words:
            if not (
                440 <= status_word["x0"] < 490
                and status_word["text"] in {"SE", "ST"}
            ):
                continue

            y = status_word["top"]

            # Collect words on the same printed row.
            row_words = [
                word for word in words
                if abs(word["top"] - y) < 2.5
            ]

            row_words.sort(key=lambda word: word["x0"])

            common_name = " ".join(
                word["text"]
                for word in row_words
                if word["x0"] < 200
            )

            scientific_name = " ".join(
                word["text"]
                for word in row_words
                if 200 <= word["x0"] < 390
            )

            # Repair names that wrap onto a second line in this PDF.
            if page_number == 2 and common_name == "Rattlesnake)":
                common_name = (
                    "Canebrake Rattlesnake "
                    "(Coastal Plain population of Timber Rattlesnake)"
                )
                scientific_name = "Crotalus horridus"

            elif page_number == 3 and common_name.startswith(
                "Monkeyface (pearlymussel)"
            ):
                common_name = (
                    "Appalachian Rockshell "
                    "(=Appalachian Monkeyface (pearlymussel))"
                )
                scientific_name = "Theliderma sparsa"

            elif page_number == 3 and common_name == "Monkeyface)":
                common_name = "Cumberland Rockshell (=Cumberland Monkeyface)"
                scientific_name = "Theliderma intermedia"

            elif page_number == 4 and common_name == "name) Springsnail":
                common_name = "Morrison's (=Virginia; =no common name) Springsnail"
                scientific_name = "Fontigens morrisoni"

            # Keep only rows where both names were extracted.
            if common_name and scientific_name:
                records.append({
                    "name": common_name,
                    "scientific_name": scientific_name,
                    "status": (
                        "Endangered"
                        if status_word["text"] == "SE"
                        else "Threatened"
                    ),
                    "state": "Virginia"
                })

df = pd.DataFrame(records)
df = df.drop_duplicates()

df.to_csv(OUTPUT, index=False)

print(f"Extracted {len(df)} species entries.")
print(df["status"].value_counts())
print(f"Saved to: {OUTPUT}")
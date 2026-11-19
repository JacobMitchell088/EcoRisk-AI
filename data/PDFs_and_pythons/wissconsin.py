import pdfplumber
import pandas as pd
import re


def scrape_wisconsin_species(pdf_file, output_file):

    species = []

    current_status = None

    # These are section/category headings, not species
    categories = {
        "MAMMALS",
        "BIRDS",
        "FISHES",
        "AMPHIBIANS",
        "REPTILES",
        "MUSSELS",
        "SNAILS",
        "INSECTS",
        "PLANTS",
        "PLANTS cont."
    }

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            i = 0

            while i < len(lines):

                line = lines[i].strip()

                # ----------------------------------------
                # Find status
                # ----------------------------------------

                if line == "ENDANGERED":
                    current_status = "Endangered"
                    i += 1
                    continue

                if line == "THREATENED":
                    current_status = "Threatened"
                    i += 1
                    continue

                # ----------------------------------------
                # Ignore irrelevant lines
                # ----------------------------------------

                if current_status is None:
                    i += 1
                    continue

                if line in categories:
                    i += 1
                    continue

                if line.startswith("Wisconsin's Endangered"):
                    i += 1
                    continue

                if line.startswith("("):
                    # This is potentially a species,
                    # so don't skip it.
                    pass

                # Ignore footnotes
                if line.startswith("**"):
                    i += 1
                    continue

                if line.startswith("*"):
                    i += 1
                    continue

                # ----------------------------------------
                # Remove listing-date code
                # ----------------------------------------

                clean_line = re.sub(
                    r"^\([A-L]\)\s*",
                    "",
                    line
                ).strip()

                # ----------------------------------------
                # Try to identify scientific name
                #
                # Scientific names normally begin with
                # a capitalized genus followed by lowercase
                # species name.
                # ----------------------------------------

                match = re.search(
                    r"\b([A-Z][a-z]+)\s+([a-z]+(?:\s+[a-z]+)*)$",
                    clean_line
                )

                if match:

                    scientific_name = match.group(0)

                    common_name = clean_line[
                        :match.start()
                    ].strip()

                    # Make sure we actually have both
                    if common_name and scientific_name:

                        species.append({
                            "Common Name": common_name,
                            "Scientific Name": scientific_name,
                            "Status": current_status,
                            "Original Status": current_status,
                            "State": "Wisconsin"
                        })

                i += 1

    # ----------------------------------------
    # Create dataframe
    # ----------------------------------------

    df = pd.DataFrame(species)

    # Remove exact duplicates
    df = df.drop_duplicates()

    # Save
    df.to_csv(output_file, index=False)

    print(f"Saved {len(df)} species")
    print(f"File: {output_file}")

    return df


wisconsin = scrape_wisconsin_species(
    pdf_file="ER0001.pdf",
    output_file="data/wisconsin.csv"
)


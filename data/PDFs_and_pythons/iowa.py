import pdfplumber
import pandas as pd
import re


def scrape_iowa_species(pdf_file, output_file):

    species = []

    current_status = None

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                line = line.strip()

                # Detect which section we're in
                if "Endangered animal species:" in line:
                    current_status = "Endangered"
                    continue

                if "Threatened animal species:" in line:
                    current_status = "Threatened"
                    continue

                # Ignore everything until we reach one of the sections
                if current_status is None:
                    continue

                # Skip headers and animal group names
                if line in [
                    "Common Name Scientific Name",
                    "Mammals",
                    "Birds",
                    "Fish",
                    "Reptiles",
                    "Amphibians",
                    "Bumble Bees",
                    "Butterflies",
                    "Damselflies and Dragonflies",
                    "Land Snails",
                    "Fresh Water Mussels"
                ]:
                    continue

                # Stop if we've reached something that isn't a species
                if line.startswith("77.2("):
                    continue

                if line.startswith("[ARC"):
                    continue

                # Split common name from scientific name
                match = re.match(
                    r"^(.+?)\s+([A-Z][a-z]+(?:\s+[a-z]+)+(?:\s+[a-z]+)?)$",
                    line
                )

                if match:

                    common_name = match.group(1).strip()
                    scientific_name = match.group(2).strip()

                    species.append({
                        "Common Name": common_name,
                        "Scientific Name": scientific_name,
                        "Status": current_status,
                        "Original Status": current_status,
                        "State": "Iowa"
                    })

    # Create dataframe
    df = pd.DataFrame(species)

    # Remove duplicates
    df = df.drop_duplicates()

    # Save
    df.to_csv(output_file, index=False)

    print(f"Saved {len(df)} species to {output_file}")

    return df



def scrape_iowa_plant(pdf_file, output_file):

    species = []

    current_status = None

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                line = line.strip()

                # Detect which section we're in
                if "Endangered plant species:" in line:
                    current_status = "Endangered"
                    continue

                if "Threatened plant species:" in line:
                    current_status = "Threatened"
                    continue

                # Ignore everything until we reach one of the sections
                if current_status is None:
                    continue

                # Skip plants group names
                if line in [
                    "Common Name Scientific Name",
                    "Mammals",
                    "Birds",
                    "Fish",
                    "Reptiles",
                    "Amphibians",
                    "Bumble Bees",
                    "Butterflies",
                    "Damselflies and Dragonflies",
                    "Land Snails",
                    "Fresh Water Mussels"
                ]:
                    continue

                # Stop if we've reached something that isn't a species
                if line.startswith("77.2("):
                    continue

                if line.startswith("[ARC"):
                    continue

                # Split common name from scientific name
                match = re.match(
                    r"^(.+?)\s+([A-Z][a-z]+(?:\s+[a-z]+)+(?:\s+[a-z]+)?)$",
                    line
                )

                if match:

                    common_name = match.group(1).strip()
                    scientific_name = match.group(2).strip()

                    species.append({
                        "Common Name": common_name,
                        "Scientific Name": scientific_name,
                        "Status": current_status,
                        "Original Status": current_status,
                        "State": "Iowa"
                    })

    # Create dataframe
    df = pd.DataFrame(species)

    # Remove duplicates
    df = df.drop_duplicates()

    # Save
    df.to_csv(output_file, index=False)

    print(f"Saved {len(df)} species to {output_file}")

    return df


scrape_iowa_species("Iowa_Animals.pdf", "data/Iowa_anim.csv" ) # create list through this
scrape_iowa_plant("Iowa_plants.pdf", "data/Iowa_plns.csv")
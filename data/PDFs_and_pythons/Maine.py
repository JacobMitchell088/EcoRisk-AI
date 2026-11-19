
import fitz
import pandas as pd
import re

# Open the downloaded PDF
pdf = fitz.open("Maine_ThreatEnd.pdf")

species = []

# Page 1 = Endangered, Page 2 = Threatened
pages = {
    0: "Endangered",
    1: "Threatened"
}

# Match a scientific name inside parentheses
scientific_pattern = re.compile(
    r"\(([A-Z][a-z]+(?:\s+[a-z][a-z.-]+){1,3})\)"
)

for page_num, status in pages.items():
    page = pdf[page_num]

    for line in page.get_text().splitlines():
        line = line.strip()

        # Find the scientific name
        match = scientific_pattern.search(line)

        if match:
            scientific_name = match.group(1)

            # The common name comes before the parentheses
            common_name = line[:match.start()].strip()

            # Remove any trailing punctuation
            common_name = common_name.rstrip(" :")

            # Skip lines that are not species entries
            if not common_name:
                continue

            species.append({
                "Common Name": common_name,
                "Scientific Name": scientific_name,
                "Status": status,
                "Original Status": status,
                "State": "Maine"
            })

# Create the DataFrame
df = pd.DataFrame(species)

# Remove duplicate records, if any
df = df.drop_duplicates(
    subset=["Scientific Name", "Original Status"]
)

# Save to CSV
df.to_csv("maine_species.csv", index=False)

print("Total species:", len(df))
print(df.head(10))
print("Saved to maine_species.csv")

pdf.close()
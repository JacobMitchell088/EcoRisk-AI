
import fitz
import pandas as pd
import re

filename = "NewHampshire.pdf"
pdf = fitz.open(filename)

results = []

# The species lists are on the first page
page = pdf[0]
words = page.get_text("words")

# Group words by their vertical position
rows = {}

for word in words:
    x, y, x1, y1, text = word[:5]
    y_key = round(y)

    if y_key not in rows:
        rows[y_key] = []

    rows[y_key].append((x, text))

for y, row_words in sorted(rows.items()):

    row_words.sort(key=lambda item: item[0])

    # Reconstruct the text on this line
    line = " ".join(text for x, text in row_words).strip()

    # Skip lines that do not look like species entries
    if "," not in line:
        continue

    # Split common name and scientific name
    parts = line.split(",", 1)

    common_name = parts[0].strip()
    scientific_name = parts[1].strip()

    # Remove federal-status footnote markers
    scientific_name = re.sub(r"\*+", "", scientific_name).strip()

    # Remove any leftover text after the scientific name
    if not re.fullmatch(
        r"[A-Z][a-z]+(?:\s+[a-z][a-z-]*)+",
        scientific_name
    ):
        continue

    # The endangered lists appear above the threatened lists
    if y < 550:
        status = "Endangered"
    else:
        status = "Threatened"

    results.append({
        "Common Name": common_name,
        "Scientific Name": scientific_name,
        "Status": status,
        "Original Status": status,
        "State": "New Hampshire"
    })

pdf.close()

# Create and save the CSV
df = pd.DataFrame(results)
df = df.drop_duplicates()

df.to_csv("new_hampshire_species.csv", index=False)

print("Species found:", len(df))
print("Saved to new_hampshire_species.csv")
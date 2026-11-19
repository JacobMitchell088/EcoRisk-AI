import fitz
import pandas as pd

pdf_path = "ms-listed-species-2018.pdf"

doc = fitz.open(pdf_path)

species = []

for page in doc:

    words = page.get_text("words")

    # Group words by their line
    lines = {}

    for word in words:
        x0, y0, x1, y1, text = word[:5]

        y = round(y0)

        if y not in lines:
            lines[y] = []

        lines[y].append(word)

    for y in sorted(lines):

        line = sorted(lines[y], key=lambda w: w[0])

        # Need enough words to potentially be a species
        if len(line) < 5:
            continue

        # Get the words based on the PDF columns
        scientific = [
            w[4] for w in line
            if 90 <= w[0] < 235
        ]

        common = [
            w[4] for w in line
            if 235 <= w[0] < 410
        ]

        ranks = [
            w[4] for w in line
            if 405 <= w[0] < 450
        ]

        state_ranks = [
            w[4] for w in line
            if 450 <= w[0] < 490
        ]

        federal = [
            w[4] for w in line
            if 490 <= w[0] < 530
        ]

        state = [
            w[4] for w in line
            if 530 <= w[0] < 570
        ]

        # Make sure this is actually a species row
        if not scientific or not common or not ranks:
            continue

        global_rank = ranks[0]

        # Global ranks start with G
        if not global_rank.startswith("G"):
            continue

        scientific_name = " ".join(scientific)
        common_name = " ".join(common)

        federal_status = " ".join(federal)
        state_status = " ".join(state)

        # We only want Mississippi state endangered/threatened
        if state_status == "LE":
            status = "Endangered"

        elif state_status == "LT":
            status = "Threatened"

        else:
            continue

        species.append({
            "Common Name": common_name,
            "Scientific Name": scientific_name,
            "State": "Mississippi",
            "Status": status,
            "Federal Status": federal_status
        })


# Create dataframe
df = pd.DataFrame(species)

# Remove duplicates
df = df.drop_duplicates()

# Save CSV
df.to_csv(
    "mississippi_endangered_threatened.csv",
    index=False
)

print(df.to_string(index=False))

print()
print("Found", len(df), "species.")
print("Saved to mississippi_endangered_threatened.csv")
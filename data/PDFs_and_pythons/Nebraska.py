
import fitz
import pandas as pd
import re

filename = "Nebraska.pdf"
pdf = fitz.open(filename)

results = []

for page_num, page in enumerate(pdf):

    # Skip the appendix, which is the last page
    if page_num == 31:
        continue

    words = page.get_text("words")
    rows = {}

    # Group words by their vertical position
    for word in words:
        x, y, x1, y1, text = word[:5]
        y_key = round(y)

        if y_key not in rows:
            rows[y_key] = []

        rows[y_key].append((x, text))

    # Process each row
    for y, row_words in rows.items():
        row_words.sort(key=lambda item: item[0])

        scientific = " ".join(
            text for x, text in row_words if x < 150
        ).strip()

        common = " ".join(
            text for x, text in row_words if 175 <= x < 300
        ).strip()

        # Read only the State Status column
        state_status = next(
            (
                text for x, text in row_words
                if 440 <= x < 480 and text in ["E", "T"]
            ),
            ""
        )

        # Keep only endangered or threatened species
        if (
            scientific
            and common
            and state_status in ["E", "T"]
            and re.search(r"[a-z]", scientific)
        ):
            results.append({
                "Common Name": common,
                "Scientific Name": scientific,
                "Status": (
                    "Endangered"
                    if state_status == "E"
                    else "Threatened"
                ),
                "Original Status": state_status,
                "State": "Nebraska"
            })

pdf.close()

# Create the CSV
df = pd.DataFrame(results)
df = df.drop_duplicates()

df.to_csv("nebraska_species.csv", index=False)

print("Species found:", len(df))
print("Saved to nebraska_species.csv")
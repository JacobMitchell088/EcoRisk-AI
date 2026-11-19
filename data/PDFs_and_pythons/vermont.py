
import fitz
import pandas as pd
import re
from collections import defaultdict

def extract_rows(filename, kind):
    pdf = fitz.open(filename)
    species = []

    for page in pdf:
        rows = defaultdict(list)

        for word in page.get_text("words"):
            x0, y0, x1, y1, text = word[:5]

            # Skip page headings and introductory paragraphs.
            if y0 < 265:
                continue

            rows[round(y0)].append((x0, text))

        current = None

        for y in sorted(rows):
            items = sorted(rows[y])
            sci_words = []
            common_words = []
            statuses = []

            for x, word in items:
                if kind == "animal":
                    if 40 <= x < 220:
                        common_words.append(word)
                    elif 220 <= x < 420:
                        sci_words.append(word)
                    elif 420 <= x < 480:
                        if re.fullmatch(r"[ET]\*?", word):
                            statuses.append((x, word))
                else:
                    if 40 <= x < 255:
                        sci_words.append(word)
                    elif 255 <= x < 460:
                        common_words.append(word)
                    elif 460 <= x < 550:
                        if re.fullmatch(r"[ET]", word):
                            statuses.append((x, word))

            sci = " ".join(sci_words).strip()
            common = " ".join(common_words).strip()

            # Join a wrapped scientific name to the previous row.
            if kind == "plant" and sci and not common:
                if current and sci[0].islower():
                    current["Scientific Name"] += " " + sci
                continue

            if not sci or not common:
                continue

            # Only accept plausible scientific-name rows.
            if not re.match(r"^[A-Z][a-zA-Z-]+", sci):
                continue

            # Ignore category headings and other non-species rows.
            if sci.lower() in {
                "scientific name", "english name",
                "vascular plants", "bryophytes"
            }:
                continue

            # State status is in the first status column for these
            # layouts; verify against the PDF before finalizing.
            original_status = statuses[0][1] if statuses else ""

            current = {
                "Common Name": common,
                "Scientific Name": sci,
                "Original Status": original_status
            }
            species.append(current)

    pdf.close()
    return species


def normalize_status(status):
    status = str(status).strip().upper()

    if status.startswith("E"):
        return "Endangered"
    if status.startswith("T"):
        return "Threatened"
    return None


animals = extract_rows("Vermont_Animal.pdf", "animal")
plants = extract_rows("Vermont_Plants.pdf", "plant")

df = pd.DataFrame(animals + plants)

df["Status"] = df["Original Status"].apply(normalize_status)
df["State"] = "Vermont"

df = df[
    ["Common Name", "Scientific Name", "Status",
     "Original Status", "State"]
]

# Remove empty rows and duplicate records.
df = df.dropna(subset=["Common Name", "Scientific Name"])
df = df[
    df["Common Name"].str.strip().ne("") &
    df["Scientific Name"].str.strip().ne("") &
    df["Status"].notna()
]
df = df.drop_duplicates(
    subset=["Common Name", "Scientific Name", "State"]
)

df.to_csv("vermont_species.csv", index=False)

print(df.head(15).to_string(index=False))
print("\nTotal species:", len(df))
print("\nStatus counts:")
print(df["Status"].value_counts())

import collections
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "arquivo" / "originais" / "FEZ_Carta_e_Manifesto_Original.pdf"

with pdfplumber.open(SOURCE) as pdf:
    for page_index in [1, 5, 6]:
        page = pdf.pages[page_index]
        print(f"\n=== PAGE {page_index + 1} ===")
        lines = collections.defaultdict(list)
        for char in page.chars:
            if char.get("text", "").strip() or char.get("text") == " ":
                lines[round(char["top"], 1)].append(char)
        for top, chars in sorted(lines.items()):
            chars = sorted(chars, key=lambda item: item["x0"])
            text = "".join(char["text"] for char in chars)
            nonspace = [char for char in chars if char["text"].strip()]
            sizes = collections.Counter(round(char["size"], 1) for char in nonspace)
            fonts = collections.Counter(char["fontname"] for char in nonspace)
            x0 = min(char["x0"] for char in chars)
            size = sizes.most_common(1)[0][0] if sizes else 0
            font = fonts.most_common(1)[0][0] if fonts else ""
            print(f"{top:6.1f} x={x0:5.1f} sz={size:4} font={font} | {text[:150]}")

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / "work" / "render_separate"

for section in ("carta", "manifesto"):
    pages = sorted((ROOT / section).glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1]))
    out = ROOT / f"{section}_sheets"
    out.mkdir(exist_ok=True)
    for sheet_number, start in enumerate(range(0, len(pages), 4), 1):
        sheet = Image.new("RGB", (1414, 2000), "#d8d8d8")
        draw = ImageDraw.Draw(sheet)
        for slot, path in enumerate(pages[start:start + 4]):
            page = Image.open(path).convert("RGB")
            page.thumbnail((690, 970), Image.Resampling.LANCZOS)
            x = 12 + (slot % 2) * 707
            y = 18 + (slot // 2) * 990
            sheet.paste(page, (x, y))
            draw.text((x + 8, y + 8), f"p.{start + slot + 1}", fill="#777777")
        sheet.save(out / f"sheet-{sheet_number:02d}.png", optimize=True)

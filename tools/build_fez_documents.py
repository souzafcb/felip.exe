from __future__ import annotations

import collections
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "documentos" / "docx"
SOURCE_CADERNO = ROOT / "arquivo" / "originais" / "FEZ_Caderno_de_Letras_Original.pdf"
SOURCE_MANIFESTO = ROOT / "arquivo" / "originais" / "FEZ_Carta_e_Manifesto_Original.pdf"

OUT_CADERNO = OUTPUT / "FEZ_Caderno_de_Letras_Versao_Diagramada.docx"
OUT_MANIFESTO = OUTPUT / "FEZ_Carta_e_Manifesto_Versao_Diagramada.docx"
OUT_CARTA_SOLO = OUTPUT / "FEZ_Carta_ao_Emicida_Versao_Diagramada.docx"
OUT_MANIFESTO_SOLO = OUTPUT / "FEZ_Manifesto_Criar_no_Caldo_do_Mundo_Versao_Diagramada.docx"

MONO = "Cascadia Mono"
SERIF = "Noto Serif"
SANS = "Noto Sans"
BLACK = "111111"
GRAY = "646464"
LIGHT = "E7E7E7"
PALE = "F4F4F4"


@dataclass
class PdfLine:
    text: str
    top: float
    x0: float
    size: float
    font: str
    page: int


def set_run_font(run, name: str, size: float | None = None, color: str | None = None):
    run.font.name = name
    if size is not None:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rfonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{key}"), name)


def set_style_font(style, name: str, size: float, color: str = BLACK, bold: bool | None = None, italic: bool | None = None):
    style.font.name = name
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{key}"), name)


def clear_style_borders(style):
    ppr = style.element.get_or_add_pPr()
    border = ppr.find(qn("w:pBdr"))
    if border is not None:
        ppr.remove(border)


def set_cellless_shading(paragraph, fill: str):
    ppr = paragraph._p.get_or_add_pPr()
    shd = ppr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        ppr.append(shd)
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")


def set_left_border(paragraph, color: str = "B8B8B8", size: int = 12, space: int = 8):
    ppr = paragraph._p.get_or_add_pPr()
    pbdr = ppr.find(qn("w:pBdr"))
    if pbdr is None:
        pbdr = OxmlElement("w:pBdr")
        ppr.append(pbdr)
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), str(size))
    left.set(qn("w:space"), str(space))
    left.set(qn("w:color"), color)
    pbdr.append(left)


def add_page_field(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("FEZ_  /  ")
    set_run_font(run, MONO, 7.5, GRAY)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    rfonts.set(qn("w:ascii"), MONO)
    rfonts.set(qn("w:hAnsi"), MONO)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "15")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), GRAY)
    rpr.extend([rfonts, sz, color])
    r.append(rpr)
    r.extend([fld_begin, instr, fld_sep, txt, fld_end])
    paragraph._p.append(r)


def configure_document(doc: Document, running_title: str):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.9)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.35)
    section.right_margin = Cm(2.35)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.8)
    section.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    set_style_font(normal, SERIF, 10.5)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.18
    normal.paragraph_format.widow_control = True

    title = doc.styles["Title"]
    set_style_font(title, MONO, 28, BLACK, bold=True)
    clear_style_borders(title)
    title.paragraph_format.space_after = Pt(6)
    title.paragraph_format.keep_with_next = True

    h1 = doc.styles["Heading 1"]
    set_style_font(h1, MONO, 17, BLACK, bold=True)
    clear_style_borders(h1)
    h1.paragraph_format.space_before = Pt(18)
    h1.paragraph_format.space_after = Pt(8)
    h1.paragraph_format.keep_with_next = True
    h1.paragraph_format.widow_control = True

    h2 = doc.styles["Heading 2"]
    set_style_font(h2, MONO, 12.5, BLACK, bold=True)
    clear_style_borders(h2)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    h2.paragraph_format.keep_with_next = True

    styles = doc.styles
    if "FEZ Mono" not in styles:
        mono = styles.add_style("FEZ Mono", WD_STYLE_TYPE.PARAGRAPH)
        set_style_font(mono, MONO, 8.5, GRAY)
        mono.paragraph_format.space_before = Pt(4)
        mono.paragraph_format.space_after = Pt(4)
        mono.paragraph_format.line_spacing = 1.08
        mono.paragraph_format.keep_together = True
    if "FEZ Quote" not in styles:
        quote = styles.add_style("FEZ Quote", WD_STYLE_TYPE.PARAGRAPH)
        set_style_font(quote, SERIF, 10.3, BLACK, italic=True)
        quote.paragraph_format.left_indent = Cm(0.75)
        quote.paragraph_format.right_indent = Cm(0.65)
        quote.paragraph_format.space_before = Pt(7)
        quote.paragraph_format.space_after = Pt(7)
        quote.paragraph_format.line_spacing = 1.15
        quote.paragraph_format.keep_together = True
    if "FEZ Meta" not in styles:
        meta = styles.add_style("FEZ Meta", WD_STYLE_TYPE.PARAGRAPH)
        set_style_font(meta, MONO, 7.8, GRAY)
        meta.paragraph_format.space_after = Pt(10)
        meta.paragraph_format.keep_with_next = True

    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    hp.paragraph_format.space_after = Pt(0)
    hr = hp.add_run(f"FEZ_  /  {running_title.upper()}")
    set_run_font(hr, MONO, 7.2, GRAY)
    footer = section.footer
    fp = footer.paragraphs[0]
    add_page_field(fp)

    doc.core_properties.author = "Felipe Brito — FEZ"
    doc.core_properties.keywords = "FEZ, rap, poesia, ancestralidade, tecnologia"


def cover(doc: Document, label: str, subtitle: str):
    for _ in range(6):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(8)
    mark = doc.add_paragraph()
    mark.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = mark.add_run("FEZ_")
    set_run_font(r, MONO, 38, BLACK)
    r.bold = True
    mark.paragraph_format.space_after = Pt(18)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(label.upper())
    set_run_font(r, MONO, 11, GRAY)
    p.paragraph_format.space_after = Pt(5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(subtitle)
    set_run_font(r, SERIF, 11.5, BLACK)
    r.italic = True
    p.paragraph_format.space_after = Pt(22)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Felipe Brito — FEZ")
    set_run_font(r, SANS, 9.5, BLACK)
    r.bold = True
    p.paragraph_format.space_after = Pt(5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("rap  /  poesia  /  ancestralidade  /  tecnologia")
    set_run_font(r, MONO, 7.8, GRAY)


def extract_lines(source: Path, page_numbers: list[int]) -> dict[int, list[PdfLine]]:
    result: dict[int, list[PdfLine]] = {}
    with pdfplumber.open(source) as pdf:
        for page_number in page_numbers:
            page = pdf.pages[page_number - 1]
            grouped: dict[float, list[dict]] = collections.defaultdict(list)
            for char in page.chars:
                text = char.get("text", "")
                if text.strip() or text == " ":
                    grouped[round(char["top"], 1)].append(char)
            page_lines = []
            for top, chars in sorted(grouped.items()):
                chars.sort(key=lambda item: item["x0"])
                if top > 728:
                    continue
                text = unicodedata.normalize("NFC", "".join(char["text"] for char in chars)).strip()
                if not text or re.fullmatch(r"FEZ\s*\|\s*\d+", text):
                    continue
                nonspace = [char for char in chars if char["text"].strip()]
                sizes = collections.Counter(round(char["size"], 1) for char in nonspace)
                fonts = collections.Counter(char["fontname"] for char in nonspace)
                page_lines.append(PdfLine(
                    text=text,
                    top=top,
                    x0=min(char["x0"] for char in chars),
                    size=sizes.most_common(1)[0][0] if sizes else 10.5,
                    font=fonts.most_common(1)[0][0] if fonts else "",
                    page=page_number,
                ))
            result[page_number] = page_lines
    return result


def append_text(base: str, addition: str) -> str:
    if not base:
        return addition
    if base.endswith("-"):
        return base + addition
    return base + " " + addition


def classify_manifesto(line: PdfLine) -> str:
    if line.size >= 21:
        return "title"
    if line.size >= 13:
        return "heading"
    if line.size <= 9.2:
        return "code"
    if "Italic" in line.font:
        return "quote"
    if "Bold" in line.font and len(line.text) < 140:
        return "bold"
    return "body"


def structured_items(lines_by_page: dict[int, list[PdfLine]], skip_texts: set[str] | None = None):
    skip_texts = skip_texts or set()
    items = []
    last_line = None
    for page_no in sorted(lines_by_page):
        for line in lines_by_page[page_no]:
            if line.text in skip_texts:
                continue
            kind = classify_manifesto(line)
            if kind == "title":
                continue
            new_item = True
            if items:
                prev = items[-1]
                same_page = last_line and last_line.page == line.page
                gap = line.top - last_line.top if same_page else None
                if kind == prev["kind"]:
                    if kind == "body" and same_page and gap <= 18.2:
                        new_item = False
                    elif kind == "body" and not same_page and not re.search(r"[.!?…:]$", prev["text"]):
                        new_item = False
                    elif kind in {"quote", "code"} and same_page and gap <= 18.5:
                        new_item = False
            if new_item:
                items.append({"kind": kind, "text": line.text})
            else:
                if kind in {"quote", "code"}:
                    items[-1]["text"] += "\n" + line.text
                else:
                    items[-1]["text"] = append_text(items[-1]["text"], line.text)
            last_line = line
    return items


def add_multiline_paragraph(doc: Document, text: str, style: str | None = None, font: str | None = None, size: float | None = None, color: str | None = None):
    paragraph = doc.add_paragraph(style=style)
    parts = text.split("\n")
    for idx, part in enumerate(parts):
        if idx:
            paragraph.add_run().add_break()
        run = paragraph.add_run(part)
        if font:
            set_run_font(run, font, size, color)
    return paragraph


def add_editorial_item(doc: Document, item):
    kind, text = item["kind"], item["text"]
    if kind == "heading":
        clean = text.replace("◈", "").strip()
        if not re.search(r"[A-Za-zÀ-ÿ0-9]", clean):
            return None
        p = doc.add_paragraph(clean, style="Heading 1" if re.match(r"^\d+\.", clean) or clean.startswith("Prelúdio") else "Heading 2")
        tag = doc.add_paragraph(style="FEZ Meta")
        r = tag.add_run(f"// {re.sub(r'[^a-z0-9]+', '_', clean.lower()).strip('_')[:62]}")
        set_run_font(r, MONO, 7.2, GRAY)
        return p
    if kind == "code":
        p = add_multiline_paragraph(doc, text, style="FEZ Mono", font=MONO, size=8.4, color=BLACK)
        p.paragraph_format.left_indent = Cm(0.45)
        p.paragraph_format.right_indent = Cm(0.25)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(8)
        set_cellless_shading(p, PALE)
        set_left_border(p, "B0B0B0", 10, 6)
        return p
    if kind == "quote":
        p = add_multiline_paragraph(doc, text, style="FEZ Quote")
        set_left_border(p, "777777", 12, 8)
        return p
    if kind == "bold":
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(7)
        p.paragraph_format.keep_together = True
        r = p.add_run(text)
        set_run_font(r, SERIF, 10.5, BLACK)
        r.bold = True
        return p
    p = doc.add_paragraph(text)
    p.paragraph_format.keep_together = len(text) < 430
    return p


YORUBA_TRACK = """[INSTRUMENTAL INTRO – slow build, ritual atmosphere, minimal percussion, hand drums, shakers, deep reverb]
[Spoken call-and-response – MC cypher style, ritual tone]

Obatalá Aláàse, Bàbá òníwa pẹ̀lẹ́...

Yô… (Rua)
YÔ (Rua)
Yo (Rubá)

Io, Io, Io, Io rua, rua, rua
Yo que chama na batalha vira Io que abre a rua
Iorubá no som que soa mão levanta, corpo escuta

[Beat starts assembling – kick enters, MPC-style swing, dusty boom bap]

[VERSE 1 – walking boom bap, grounded flow]

a mão levanta e diz YÔ… Yô, Yô, ruuá
É rap preto e poesia da levada da batida
a mão pra cima yÔ yô Yô ru bá
Ritmo é partida e chegada
boom bap caminhada
dizer não e sim copada, sincopada
passo e despasso
corpo aprende no compasso

Beat marca caminhada
ponto pede respirada
rima fria sente nada
gira quem te vê parada
griô, sabedoria da história contada

[DRUM BRAKE – sudden stop, breath, ritual pause]

[INSTRUMENTAL BRIDGE – Afro-Brazilian percussion focus, trance-like]
[Call-and-response vocal textures, no full lyrics]

Io… Rua… Io… Rua…

[CHORUS / REFRAIN – chant-like, collective, ritual]

Obatalá Aláàse, Bàbá òníwa pẹ̀lẹ́
Ẹ jẹ́ kí o sọ mi di ẹni pẹ̀lẹ́
ẹni tó mọ ìwà rere

Fún mi ní àlàáfíà
ìmọ̀ràn rere
àti ìtọ́sọ́nà ní ọjọ́ mi

a mão levanta e diz YÔ… Yô, Yô, ruuá
É rap preto e poesia da levada da batida
a mão pra cima yÔ yô Yô ru bá
Ritmo é partida e chegada
boom bap caminhada
dizer não e sim copada, sincopada
passo e despasso

[VERSE 2 – griot storytelling, beat slightly stripped]

Griô é vivo, é RAPer
ponto é beat, marca a levada
o flow é santo
desde África até cada quebrada

Da roda ao asfalto
do terreiro ao concreto
som não pede licença
ele atravessa o tempo

Yo vira Io na boca
quando o corpo tá desperto
não é sample, é semente
é fundamento direto

[OUTRO – instrumental dissolve, ritual closing]
[Hand drums fade, reverb tails, ambient space]

àlàáfíà…
ìmọ̀ràn rere…
sónà ní ọjọ́ mi…"""


TRACKS = [
    ("TEMPODER", 3, 5),
    ("PANOS BRANCOS, PELES FRIAS", 6, 7),
    ("BOA TARDE MAJESTADE", 8, 9),
    ("O RAMO DA BENCIDEIRA", 10, 10),
    ("AQUI DE CIMA", 11, 12),
    ("A COBRAR", 13, 16),
    ("MOSTRE", 17, 19),
    ("POR UM TRIZ", 20, 21),
    ("ALQUIMISTA GRIOT", 22, 23),
    ("LAGRIMÁ — NANÃ", 24, 25),
    ("YÔ / IO / RUA / IORUBÁ", 26, 27),
    ("DELEITE", 28, 30),
    ("REMAR MARÉ", 31, 31),
]


def extract_track_lines(title: str, start: int, end: int):
    pages = extract_lines(SOURCE_CADERNO, list(range(start, end + 1)))
    result = []
    for page_no in range(start, end + 1):
        prev_top = None
        for line in pages[page_no]:
            if page_no == start and (line.size >= 16.5 or line.text == "FEZ — 2024"):
                continue
            gap = line.top - prev_top if prev_top is not None else 0
            result.append((line.text, gap > 20.0))
            prev_top = line.top
    return result


def add_track(doc: Document, title: str, number: int, source_lines):
    doc.add_page_break()
    p = doc.add_paragraph(style="FEZ Meta")
    r = p.add_run(f"TRACK_{number:02d}  /  LETRA  /  FEZ")
    set_run_font(r, MONO, 7.8, GRAY)
    p.paragraph_format.space_after = Pt(7)

    p = doc.add_paragraph(style="Title")
    r = p.add_run(title)
    set_run_font(r, MONO, 24, BLACK)
    r.bold = True
    p.paragraph_format.space_after = Pt(5)

    slug = re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()).strip("_")
    p = doc.add_paragraph(style="FEZ Meta")
    r = p.add_run(f"> abrir_arquivo --faixa {number:02d} --id {slug}")
    set_run_font(r, MONO, 7.2, GRAY)
    p.paragraph_format.space_after = Pt(14)

    if title == "YÔ / IO / RUA / IORUBÁ":
        prepared = []
        previous_blank = False
        for raw in YORUBA_TRACK.splitlines():
            if raw.strip():
                prepared.append((raw.strip(), previous_blank))
                previous_blank = False
            else:
                previous_blank = True
        source_lines = prepared

    compact = {
        "MOSTRE": (10.15, 1.04, 1.0),
        "POR UM TRIZ": (9.75, 1.02, 0.7),
        "ALQUIMISTA GRIOT": (9.7, 1.02, 0.7),
    }.get(title)
    for text, before_gap in source_lines:
        instruction = text.startswith("[") and text.endswith("]")
        p = doc.add_paragraph(style="FEZ Mono" if instruction else None)
        p.paragraph_format.space_before = Pt(7 if before_gap else 0)
        body_size, body_spacing, body_after = compact or (10.5, 1.12, 1.8)
        p.paragraph_format.space_after = Pt(2.4 if instruction and compact else (3.2 if instruction else body_after))
        p.paragraph_format.line_spacing = 1.04 if instruction and compact else (1.08 if instruction else body_spacing)
        p.paragraph_format.widow_control = True
        p.paragraph_format.keep_together = True
        if instruction:
            p.paragraph_format.keep_with_next = True
            r = p.add_run(text)
            set_run_font(r, MONO, 8.1, GRAY)
        else:
            r = p.add_run(text)
            set_run_font(r, SERIF, body_size, BLACK)


def build_caderno():
    doc = Document()
    configure_document(doc, "Caderno de letras")
    doc.core_properties.title = "FEZ Caderno de letras"
    cover(doc, "Caderno de letras", "Letras / ritmo / palavra")
    doc.add_page_break()

    p = doc.add_paragraph("NOTA DE EDIÇÃO", style="Heading 1")
    p.paragraph_format.space_before = Pt(50)
    p = doc.add_paragraph(style="FEZ Mono")
    r = p.add_run("// corpus_integral  /  versão diagramada")
    set_run_font(r, MONO, 8, GRAY)
    p.paragraph_format.space_after = Pt(16)
    p = doc.add_paragraph(
        "Letras reunidas a partir do corpus disponível. Mantidas integralmente conforme as versões recuperadas, sem completar por inferência trechos ausentes."
    )
    p.paragraph_format.left_indent = Cm(0.7)
    p.paragraph_format.right_indent = Cm(1.4)
    p.paragraph_format.space_after = Pt(0)
    set_left_border(p, "888888", 12, 10)

    for idx, (title, start, end) in enumerate(TRACKS, 1):
        add_track(doc, title, idx, extract_track_lines(title, start, end))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_CADERNO)


def build_manifesto():
    doc = Document()
    configure_document(doc, "Carta e manifesto")
    doc.core_properties.title = "FEZ Carta de apresentação e manifesto"
    cover(doc, "Carta de apresentação + manifesto", "Palavra / processo / criação")
    doc.add_page_break()

    # Letter pages: extract and rebuild the original editorial paragraphs.
    letter_lines = extract_lines(SOURCE_MANIFESTO, [2, 3, 4, 5])
    letter_items = structured_items(letter_lines, {"CARTA DE APRESENTAÇÃO"})
    title = doc.add_paragraph("CARTA DE APRESENTAÇÃO", style="Title")
    title.paragraph_format.space_after = Pt(4)
    meta = doc.add_paragraph(style="FEZ Meta")
    r = meta.add_run("> destinatário  /  Emicida")
    set_run_font(r, MONO, 7.6, GRAY)
    meta.paragraph_format.space_after = Pt(16)
    for item in letter_items:
        if item["text"] == "Ao Emicida,":
            p = doc.add_paragraph()
            r = p.add_run(item["text"])
            set_run_font(r, SERIF, 10.5, BLACK)
            r.bold = True
            p.paragraph_format.space_after = Pt(10)
            continue
        add_editorial_item(doc, item)

    doc.add_page_break()
    # Manifesto title page.
    for _ in range(5):
        doc.add_paragraph()
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("CRIAR NO CALDO\nDO MUNDO")
    set_run_font(r, MONO, 25, BLACK)
    r.bold = True
    p.paragraph_format.space_after = Pt(16)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('def ensaio_filosófico(): return "arte + tecnologia + dissolução_do_eu"')
    set_run_font(r, MONO, 8.2, GRAY)
    p.paragraph_format.space_after = Pt(24)
    for line in ["Felipe Brito (FEZ)", "AlquimiXGriot · RAPP RAPP", "Rhythm-Al-Prompt & Poetry · 2025"]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        set_run_font(r, SERIF if "Felipe" in line else MONO, 9.2, BLACK if "Felipe" in line else GRAY)
        p.paragraph_format.space_after = Pt(4)

    doc.add_page_break()
    manifesto_lines = extract_lines(SOURCE_MANIFESTO, list(range(6, 15)))
    skip = {
        "CRIAR NO CALDO DO MUNDO",
        'def ensaio_filosófico(): return "arte + tecnologia + dissolução_do_eu"',
        "Felipe Brito (FEZ)",
        "AlquimiXGriot · RAPP RAPP",
        "Rhythm-Al-Prompt & Poetry · 2025",
    }
    for item in structured_items(manifesto_lines, skip):
        add_editorial_item(doc, item)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_MANIFESTO)


def add_letter_content(doc: Document):
    letter_lines = extract_lines(SOURCE_MANIFESTO, [2, 3, 4, 5])
    letter_items = structured_items(letter_lines, {"CARTA DE APRESENTAÇÃO"})
    title = doc.add_paragraph("CARTA DE APRESENTAÇÃO", style="Title")
    title.paragraph_format.space_after = Pt(4)
    meta = doc.add_paragraph(style="FEZ Meta")
    r = meta.add_run("> destinatário  /  Emicida")
    set_run_font(r, MONO, 7.6, GRAY)
    meta.paragraph_format.space_after = Pt(16)
    for item in letter_items:
        if item["text"] == "Ao Emicida,":
            p = doc.add_paragraph()
            r = p.add_run(item["text"])
            set_run_font(r, SERIF, 10.5, BLACK)
            r.bold = True
            p.paragraph_format.space_after = Pt(10)
        else:
            add_editorial_item(doc, item)


def add_manifesto_content(doc: Document):
    manifesto_lines = extract_lines(SOURCE_MANIFESTO, list(range(6, 15)))
    skip = {
        "CRIAR NO CALDO DO MUNDO",
        'def ensaio_filosófico(): return "arte + tecnologia + dissolução_do_eu"',
        "Felipe Brito (FEZ)",
        "AlquimiXGriot · RAPP RAPP",
        "Rhythm-Al-Prompt & Poetry · 2025",
    }
    for item in structured_items(manifesto_lines, skip):
        add_editorial_item(doc, item)


def manifesto_cover(doc: Document):
    for _ in range(5):
        doc.add_paragraph()
    mark = doc.add_paragraph()
    mark.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = mark.add_run("FEZ_")
    set_run_font(r, MONO, 16, GRAY)
    r.bold = True
    mark.paragraph_format.space_after = Pt(30)
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("CRIAR NO CALDO\nDO MUNDO")
    set_run_font(r, MONO, 25, BLACK)
    r.bold = True
    p.paragraph_format.space_after = Pt(16)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('def ensaio_filosófico(): return "arte + tecnologia + dissolução_do_eu"')
    set_run_font(r, MONO, 8.2, GRAY)
    p.paragraph_format.space_after = Pt(24)
    for line in ["Felipe Brito (FEZ)", "AlquimiXGriot · RAPP RAPP", "Rhythm-Al-Prompt & Poetry · 2025"]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        set_run_font(r, SERIF if "Felipe" in line else MONO, 9.2, BLACK if "Felipe" in line else GRAY)
        p.paragraph_format.space_after = Pt(4)


def build_carta_solo():
    doc = Document()
    configure_document(doc, "Carta ao Emicida")
    doc.core_properties.title = "FEZ Carta ao Emicida"
    cover(doc, "Carta ao Emicida", "Palavra / processo / criação")
    doc.add_page_break()
    add_letter_content(doc)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_CARTA_SOLO)


def build_manifesto_solo():
    doc = Document()
    configure_document(doc, "Criar no Caldo do Mundo")
    doc.core_properties.title = "FEZ Manifesto Criar no Caldo do Mundo"
    manifesto_cover(doc)
    doc.add_page_break()
    add_manifesto_content(doc)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_MANIFESTO_SOLO)


if __name__ == "__main__":
    build_caderno()
    build_carta_solo()
    build_manifesto_solo()
    print(OUT_CADERNO)
    print(OUT_CARTA_SOLO)
    print(OUT_MANIFESTO_SOLO)

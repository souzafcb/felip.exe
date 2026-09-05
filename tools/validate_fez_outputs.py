import re
import unicodedata
from pathlib import Path

import pdfplumber
from docx import Document
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "documentos"

PAIRS = [
    (
        ROOT / "arquivo" / "originais" / "FEZ_Caderno_de_Letras_Original.pdf",
        OUTPUT / "pdf" / "FEZ_Caderno_de_Letras_Versao_Diagramada.pdf",
        OUTPUT / "docx" / "FEZ_Caderno_de_Letras_Versao_Diagramada.docx",
        {26, 27},
    ),
    (
        ROOT / "arquivo" / "originais" / "FEZ_Carta_e_Manifesto_Original.pdf",
        OUTPUT / "pdf" / "FEZ_Carta_ao_Emicida_Versao_Diagramada.pdf",
        OUTPUT / "docx" / "FEZ_Carta_ao_Emicida_Versao_Diagramada.docx",
        set(range(1, 2)) | set(range(6, 15)),
    ),
    (
        ROOT / "arquivo" / "originais" / "FEZ_Carta_e_Manifesto_Original.pdf",
        OUTPUT / "pdf" / "FEZ_Manifesto_Criar_no_Caldo_do_Mundo_Versao_Diagramada.pdf",
        OUTPUT / "docx" / "FEZ_Manifesto_Criar_no_Caldo_do_Mundo_Versao_Diagramada.docx",
        set(range(1, 6)),
    ),
]


def compact(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(char for char in value if char.isalnum())


def source_lines(path: Path, ignored_pages: set[int]):
    collected = []
    with pdfplumber.open(path) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            if page_no in ignored_pages:
                continue
            for line in (page.extract_text() or "").splitlines():
                clean = line.strip()
                if not clean or re.fullmatch(r"FEZ\s*\|\s*\d+", clean):
                    continue
                if compact(clean):
                    collected.append((page_no, clean))
    return collected


for source, rendered_pdf, docx, ignored in PAIRS:
    reader = PdfReader(rendered_pdf)
    output_text = "\n".join((page.extract_text() or "") for page in reader.pages)
    compact_output = compact(output_text)
    missing = []
    for page_no, line in source_lines(source, ignored):
        token = compact(line)
        if len(token) >= 8 and token not in compact_output:
            missing.append((page_no, line))
    reopened = Document(docx)
    assert reopened.paragraphs
    assert ":chatgpt-content-reference" not in output_text
    assert "filecite" not in output_text.casefold()
    print(f"{rendered_pdf.name}: pages={len(reader.pages)} bytes={rendered_pdf.stat().st_size} missing_source_lines={len(missing)}")
    for item in missing[:12]:
        print("  MISSING", item)

caderno_text = "\n".join((p.extract_text() or "") for p in PdfReader(PAIRS[0][1]).pages)
carta_text = "\n".join((p.extract_text() or "") for p in PdfReader(PAIRS[1][1]).pages)
manifesto_text = "\n".join((p.extract_text() or "") for p in PdfReader(PAIRS[2][1]).pages)

titles = [
    "TEMPODER", "PANOS BRANCOS, PELES FRIAS", "BOA TARDE MAJESTADE", "O RAMO DA BENCIDEIRA",
    "AQUI DE CIMA", "A COBRAR", "MOSTRE", "POR UM TRIZ", "ALQUIMISTA GRIOT", "LAGRIMÁ — NANÃ",
    "YÔ / IO / RUA / IORUBÁ", "DELEITE", "REMAR MARÉ",
]
for title in titles:
    assert title in caderno_text, title
assert "Foi através do RAP que conheci" in carta_text
caderno_docx_text = "\n".join(p.text for p in Document(PAIRS[0][2]).paragraphs)
assert "Ẹ jẹ́ kí o sọ mi di ẹni pẹ̀lẹ́" in caderno_docx_text
assert "CRIAR NO CALDO" in manifesto_text
print("KEY_CHECKS=PASS")

"""Synthetic documents for the file-reading checks (#129), built with the standard library only.

Each document carries an Arabic sentence and a SYNTH-* marker; the mock LLM logs the markers it finds in a request,
so a check can prove that the file's text reached the model without the mock logging any content.
"""

from __future__ import annotations

import io
import zipfile


def _zip(parts: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in parts.items():
            z.writestr(name, text)
    return buf.getvalue()


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def docx(paragraphs: list[str]) -> bytes:
    """A minimal WordprocessingML document (what mammoth, LibreChat's .docx parser, reads)."""
    body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{_esc(p)}</w:t></w:r></w:p>" for p in paragraphs)
    return _zip({
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/'
            'content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
            'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/'
            'document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+'
            'xml"/></Types>'),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/'
            '2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="word/document.xml"/></Relationships>'),
        "word/document.xml": (
            '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
            f'wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>'),
    })


def xlsx(rows: list[list[str]]) -> bytes:
    """A minimal SpreadsheetML workbook with inline strings (what SheetJS, LibreChat's Excel parser, reads)."""
    def cell(r: int, c: int, value: str) -> str:
        return f'<c r="{chr(65 + c)}{r}" t="inlineStr"><is><t>{_esc(value)}</t></is></c>'
    data = "".join(f'<row r="{r}">' + "".join(cell(r, c, v) for c, v in enumerate(row)) + "</row>"
                   for r, row in enumerate(rows, start=1))
    ns = "http://schemas.openxmlformats.org"
    return _zip({
        "[Content_Types].xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="{ns}/package/2006/content-types">'
            f'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'),
        "_rels/.rels": (
            f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>'),
        "xl/workbook.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{ns}/spreadsheetml/2006/main" '
            f'xmlns:r="{ns}/officeDocument/2006/relationships"><sheets><sheet name="بيانات" sheetId="1" r:id="rId1"/>'
            '</sheets></workbook>'),
        "xl/_rels/workbook.xml.rels": (
            f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/></Relationships>'),
        "xl/worksheets/sheet1.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{ns}/spreadsheetml/2006/main">'
            f"<sheetData>{data}</sheetData></worksheet>"),
    })


def pdf(lines: list[str]) -> bytes:
    """A one-page PDF whose text layer is Unicode: each character is drawn as a 2-byte CID equal to its code point
    (Identity-H) and a ToUnicode CMap maps it back, so a text extractor (pdf.js in LibreChat) reads the Arabic
    exactly. No font is embedded: the page is for extraction, not for display."""
    chars = sorted({ch for line in lines for ch in line})
    cmap = ("/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CMapName /EFAIW-UCS def "
            "/CMapType 2 def 1 begincodespacerange <0000> <FFFF> endcodespacerange "
            f"{len(chars)} beginbfchar " + " ".join(f"<{ord(c):04X}> <{ord(c):04X}>" for c in chars) +
            " endbfchar endcmap CMapName currentdict /CMap defineresource pop end end")
    text_ops = "".join(f"BT /F1 14 Tf 50 {780 - 24 * i} Td <{''.join(f'{ord(c):04X}' for c in line)}> Tj ET\n"
                       for i, line in enumerate(lines))
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> "
        "/Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type0 /BaseFont /EFAIWSynthetic /Encoding /Identity-H "
        "/DescendantFonts [6 0 R] /ToUnicode 7 0 R >>",
        f"<< /Length {len(text_ops.encode('latin-1'))} >>\nstream\n{text_ops}endstream",
        "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /EFAIWSynthetic /CIDSystemInfo << /Registry (Adobe) "
        "/Ordering (Identity) /Supplement 0 >> /FontDescriptor 8 0 R /DW 600 >>",
        f"<< /Length {len(cmap)} >>\nstream\n{cmap}\nendstream",
        "<< /Type /FontDescriptor /FontName /EFAIWSynthetic /Flags 4 /FontBBox [0 -200 1000 900] /ItalicAngle 0 "
        "/Ascent 900 /Descent -200 /CapHeight 700 /StemV 80 >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.7\n")
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{n} 0 obj\n{body}\nendobj\n".encode("latin-1"))
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def image_only_pdf() -> bytes:
    """A PDF page with no text layer (what a scan looks like to a parser without OCR)."""
    return pdf([" "])

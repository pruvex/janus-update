from pathlib import Path

import fitz

OUTPUT_DIR = Path("C:/Users/pruve/Documents/diamond_test_pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONTS = ["helv", "times-roman", "courier"]

PDF_DEFINITIONS = [
    {
        "name": "simple_paragraph.pdf",
        "pages": [
            {
                "width": 595.2,
                "height": 841.8,
                "spans": [
                    (72, 72, "Das ist ein einfacher Absatz mit einer klaren Aussage.", "helv", 12),
                    (72, 96, "Hier ist eine zweizeilige Aussage mit einem Faktenfehler: 110,4 Mio Einwohner.", "helv", 12),
                ],
            }
        ],
    },
    {
        "name": "multi_column.pdf",
        "pages": [
            {
                "width": 595.2,
                "height": 841.8,
                "spans": [
                    (72, 72, "Spalte A: Lorem ipsum dolor sit amet, consectetur adipiscing elit.", "helv", 11),
                    (320, 72, "Spalte B: Faktencheck: Die Hauptstadt ist Berlin.", "times-roman", 11),
                    (72, 144, "Spalte A: Zusätzliche Information zur Spalte A.", "helv", 11),
                    (320, 144, "Spalte B: Noch mehr Fakten, z. B. 84 Millionen Einwohner.", "times-roman", 11),
                ],
            }
        ],
    },
    {
        "name": "table_layout.pdf",
        "pages": [
            {
                "width": 595.2,
                "height": 841.8,
                "spans": [
                    (72, 72, "Tabelle: Land | Einwohner | Fläche", "courier", 10),
                    (72, 96, "Ägypten | 110,4 Mio | 1.010.000 km²", "courier", 10),
                    (72, 120, "Korrektur: Ägypten hat 116,5 Mio Einwohner.", "courier", 10),
                    (72, 144, "Quellen: Weltbank 2024 (Faktenfehler).", "courier", 10),
                ],
            }
        ],
    },
    {
        "name": "mixed_font_block.pdf",
        "pages": [
            {
                "width": 595.2,
                "height": 841.8,
                "spans": [
                    (72, 72, "Überschrift in Bold (durch Font).", "times-bold", 14),
                    (72, 110, "Darunter normaler Text, ", "helv", 11),
                    (72, 130, "mit einer eingebauten Fußnote: (1) 2019; (2) 2023.", "helv", 9),
                    (72, 190, "Fehlerhafte Passage: Die Fläche von Deutschland beträgt 357.000 km².", "times-italic", 11),
                ],
            }
        ],
    },
    {
        "name": "column_footer.pdf",
        "pages": [
            {
                "width": 595.2,
                "height": 841.8,
                "spans": [
                    (72, 72, "Haupttext mit Fußzeile und Kopfzeile in kleinem Font.", "helv", 12),
                    (72, 740, "Seitenzahl 1", "helv", 10),
                    (72, 760, "Kopfzeile: Zusammenfassung (falsch) - Bevölkerung 83 Mio.", "helv", 10),
                ],
            }
        ],
    },
]


def write_pdf(definition: dict) -> None:
    doc = fitz.open()
    for page_def in definition["pages"]:
        page = doc.new_page(width=page_def["width"], height=page_def["height"])
        for x, y, text, font, size in page_def["spans"]:
            page.insert_text((x, y), text, fontsize=size, fontname=font)
    doc.save(OUTPUT_DIR / definition["name"])
    doc.close()


def main() -> None:
    for definition in PDF_DEFINITIONS:
        write_pdf(definition)
    print("Diamond-standard test PDFs written to", OUTPUT_DIR)


if __name__ == "__main__":
    main()

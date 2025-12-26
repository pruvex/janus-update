# backend/tools/pdf_generator.py

import logging
import os
from typing import Optional

from fpdf import FPDF
from pydantic import BaseModel, Field

from backend.utils.paths import resource_path

logger = logging.getLogger("janus_backend")

FONT_PATH = resource_path("backend/assets/fonts/DejaVuSans.ttf")


def get_known_locations():
    home = os.path.expanduser("~")
    return {
        "desktop": os.path.join(home, "Desktop"),
        "documents": os.path.join(home, "Documents"),
        "downloads": os.path.join(home, "Downloads"),
    }


class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}", 0, 0, "C")

    def add_markdown_text(self, markdown_text: str, font_size: int):
        lines = markdown_text.split("\n")
        self.set_font("DejaVu", "", font_size)

        for line in lines:
            line = line.strip()

            if line.startswith("# "):
                self.set_font("DejaVu", "B", font_size * 1.5)
                self.multi_cell(0, 10, line[2:].strip(), 0, "L")
                self.ln(2)
            elif line.startswith("## "):
                self.set_font("DejaVu", "B", font_size * 1.3)
                self.multi_cell(0, 9, line[3:].strip(), 0, "L")
                self.ln(1)
            elif line.startswith("### "):
                self.set_font("DejaVu", "B", font_size * 1.1)
                self.multi_cell(0, 8, line[4:].strip(), 0, "L")
                self.ln(1)
            elif line.strip().startswith(("* ", "- ")):
                self.set_font("DejaVu", "", font_size)
                self.cell(5)
                self.multi_cell(0, 5, f"• {line.strip()[2:]}")
                self.ln(1)
            elif line:
                self.set_font("DejaVu", "", font_size)
                self.multi_cell(0, 5, line)
                self.ln(2)
            else:
                self.ln(5)
        # Setzt die Schriftart am Ende wieder auf den Normalzustand zurück
        self.set_font("DejaVu", "", font_size)


# WICHTIG: Die Signatur der Hauptfunktion wird um die neuen Parameter erweitert.
def create_pdf_from_markdown(
    content: str,
    filename: str,
    location: str = "Documents",
    image_path: Optional[str] = None,
    font_size: int = 12,
    image_width: int = 40,
    last_image_path: Optional[str] = None,
) -> str:
    """
    Kombiniert vorhandenen Text und optional das ZULETZT im Chatverlauf erstellte Bild zu einer PDF-Datei.
    """
    # Logik-Update: Wenn kein expliziter Bildpfad angegeben ist, aber ein letztes Bild existiert
    if not image_path and last_image_path and os.path.exists(last_image_path):
        # Einfache Heuristik: Wenn der User explizit nach "PDF mit Bild" fragt oder wir Kontext haben, nutzen wir es.
        # Da create_pdf oft explizit ist, nutzen wir es als Fallback.
        image_path = last_image_path
    try:
        logger.info("PDF-Erstellung gestartet mit folgenden Parametern:")
        logger.info(f"  - Dateiname: {filename}")
        logger.info(f"  - Speicherort: {location}")
        logger.info(f"  - Schriftgröße: {font_size}pt")
        logger.info(f"  - Bildpfad: {image_path}")
        logger.info(f"  - Bildbreite: {image_width}mm")

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        valid_filename = "".join(
            c for c in filename if c.isalnum() or c in (" ", ".", "_")
        ).rstrip()
        known_locations = get_known_locations()
        output_dir = known_locations.get(location.lower(), known_locations["documents"])
        janus_output_dir = os.path.join(output_dir, "JanusPDFs")
        os.makedirs(janus_output_dir, exist_ok=True)
        output_path = os.path.join(janus_output_dir, valid_filename)

        logger.info(f"Speichere PDF unter: {output_path}")

        pdf = PDF()
        pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
        pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)
        pdf.add_font("DejaVu", "I", FONT_PATH, uni=True)
        pdf.add_page()

        if image_path and os.path.exists(image_path):
            logger.info(f"Füge Bild hinzu: {image_path}")

            page_width = pdf.w - 2 * pdf.l_margin
            effective_width = image_width if image_width > 0 else page_width
            if effective_width > page_width:
                effective_width = page_width

            pdf.image(image_path, x=10, y=None, w=effective_width)
            pdf.ln(10)

        pdf.add_markdown_text(content, font_size)
        pdf.output(output_path)

        success_message = f"PDF '{valid_filename}' wurde erfolgreich auf deinem '{location}' im Ordner 'JanusPDFs' gespeichert."
        logger.info(success_message)
        return success_message

    except Exception as e:
        error_message = f"Fehler beim Erstellen der PDF mit fpdf2: {e}"
        logger.error(error_message, exc_info=True)
        return error_message


# --- Schema Definition ---
class CleanCreatePdfArgs(BaseModel):
    content: str = Field(
        ..., description="Der vollständige Textinhalt für die PDF (Markdown erlaubt)."
    )
    filename: str = Field(
        ...,
        description="Der Dateiname. WICHTIG: Der Parameter MUSS zwingend 'filename' heißen (NICHT 'file_name'). Endung muss .pdf sein.",
    )
    location: str = Field(
        "Desktop", description="Speicherort: 'Desktop', 'Documents' oder 'Downloads'."
    )

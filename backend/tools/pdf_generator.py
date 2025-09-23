# backend/tools/pdf_generator.py

import logging
import os
from typing import Optional
from fpdf import FPDF
from backend.utils.paths import resource_path

logger = logging.getLogger('janus_backend')

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
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 10, f'Seite {self.page_no()}', 0, 0, 'C')

    def add_markdown_text(self, markdown_text):
        # ... (Diese Funktion bleibt unverändert)
        lines = markdown_text.split('\n')
        for line in lines:
            if line.startswith('# '): self.set_font('DejaVu', 'B', 16); self.cell(0, 10, line[2:].strip(), 0, 1, 'L')
            elif line.startswith('## '): self.set_font('DejaVu', 'B', 14); self.cell(0, 10, line[3:].strip(), 0, 1, 'L')
            elif line.startswith('### '): self.set_font('DejaVu', 'B', 12); self.cell(0, 10, line[4:].strip(), 0, 1, 'L')
            elif line.strip().startswith(('* ', '- ')): self.set_font('DejaVu', '', 11); self.cell(5); self.cell(0, 5, f"• {line.strip()[2:]}", 0, 1)
            else: self.set_font('DejaVu', '', 11); self.multi_cell(0, 5, line)
            self.ln(2)

# WICHTIG: Die Signatur der Funktion ändert sich!
def create_pdf_from_markdown(content: str, filename: str, location: str = "Documents", image_path: Optional[str] = None) -> str:
    """
    Erstellt eine PDF mit Text und optional einem Bild.
    """
    try:
        # ... (Logik für Dateinamen und Speicherort bleibt gleich)
        if not filename.lower().endswith('.pdf'): filename += '.pdf'
        valid_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()
        known_locations = get_known_locations()
        output_dir = known_locations.get(location.lower(), known_locations["documents"])
        janus_output_dir = os.path.join(output_dir, "JanusPDFs")
        os.makedirs(janus_output_dir, exist_ok=True)
        output_path = os.path.join(janus_output_dir, valid_filename)

        logger.info(f"Erstelle PDF: {output_path} mit fpdf2.")

        pdf = PDF()
        pdf.add_font('DejaVu', '', FONT_PATH, uni=True)
        pdf.add_font('DejaVu', 'B', FONT_PATH, uni=True)
        pdf.add_font('DejaVu', 'I', FONT_PATH, uni=True)
        pdf.add_page()
        
        # NEUE LOGIK: Bild einfügen, falls ein Pfad übergeben wurde
        if image_path and os.path.exists(image_path):
            logger.info(f"Füge Bild hinzu: {image_path}")
            # Füge das Bild ein und passe die Breite an die Seite an
            # A4-Breite ist 210mm, mit Rändern (10mm links/rechts) bleiben 190mm
            pdf.image(image_path, x=10, y=None, w=190)
            pdf.ln(10) # Abstand nach dem Bild

        pdf.add_markdown_text(content)
        pdf.output(output_path)
        
        success_message = f"PDF '{valid_filename}' wurde erfolgreich auf deinem '{location}' im Ordner 'JanusPDFs' gespeichert."
        logger.info(success_message)
        return success_message

    except Exception as e:
        error_message = f"Fehler beim Erstellen der PDF mit fpdf2: {e}"
        logger.error(error_message, exc_info=True)
        return error_message

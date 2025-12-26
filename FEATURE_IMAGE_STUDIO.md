# Feature Plan: Image Studio

Dies ist ein detaillierter Plan zur Implementierung eines professionellen Bilderstellungs-Workflows ("Image Studio") in der Anwendung.

### Detaillierter Schritt-für-Schritt-Implementierungsplan (Version 2)

#### Phase 1: Backend-Erweiterung (Das Fundament)

Das Backend muss Kosteninformationen bereitstellen und die neuen Parameter verarbeiten können.

*   **Schritt 1.1: Datenbank-Modell für Bilder erstellen**
    *   Tabelle `generated_images` mit Spalten: `id` (PK), `user_id`, `prompt` (TEXT), `style_preset` (VARCHAR), `provider` (VARCHAR), `model` (VARCHAR), `parameters` (JSON), `image_url` (VARCHAR), `is_uploaded` (BOOLEAN), `created_at`.

*   **Schritt 1.2: API-Endpunkte anpassen/entwickeln**
    1.  **`POST /api/images/generate`**:
        *   **Request Body:** `{ "prompt": "...", "provider": "openai", "model": "dall-e-3", "parameters": {"quality": "hd", "resolution": "1024x1024"}, "style_preset": "photorealistic" }`
        *   **Logik:** Nimmt die strukturierte Anfrage entgegen, ruft den korrekten Service auf, speichert das Bild und legt den DB-Eintrag an. Gibt die `image_url` zurück.
    2.  **`POST /api/images/upload`**: Für den Upload von Nutzerbildern.
    3.  **`GET /api/images`**: Zum Abrufen der Bilder für die Galerien (`?type=generated` oder `?type=uploaded`).
    4.  **NEU - `GET /api/images/pricing`**:
        *   **Logik:** Dieser Endpunkt liefert eine JSON-Struktur mit den Preisinformationen für alle unterstützten Modelle und deren Optionen. Diese Logik kann im `cost_calculator.py` Service implementiert werden.
        *   **Beispiel-Antwort:**
            ```json
            {
              "openai": {
                "dall-e-3": {
                  "hd": {
                    "1024x1024": 0.080,
                    "1024x1792": 0.120
                  },
                  "standard": {
                    "1024x1024": 0.040,
                    "1024x1792": 0.080
                  }
                },
                "dall-e-2": {
                  "standard": {
                    "1024x1024": 0.020
                  }
                }
              },
              "google": {
                "imagen-3": { ... }
              }
            }
            ```

#### Phase 2: Frontend-Integration (Das Grundgerüst)

*   **Schritt 2.1: Sidebar-Button erstellen**
    *   Eintrag "Bilderstellung" in der Sidebar, der ein Modal öffnet.

*   **Schritt 2.2: Das Haupt-Modal `ImageStudioModal.js` erstellen**
    *   Großes Modal mit 2-spaltigem Layout (links: Kontrollen, rechts: Vorschau/Galerie).

#### Phase 3: Frontend - Das Kontrollpanel (Dynamische Kommandozentrale)

*   **Schritt 3.1: Dynamische Eingabefelder implementieren**
    1.  **Provider-Auswahl:** Ein `<Select>`-Dropdown zur Auswahl des Anbieters (z.B. "OpenAI", "Google").
    2.  **Modell-Auswahl:** Ein zweites `<Select>`, dessen Optionen dynamisch geladen werden, basierend auf dem gewählten Provider.
    3.  **Parameter-Auswahl:** Weitere, ebenfalls dynamische, Steuerelemente, die nur erscheinen, wenn sie für das gewählte Modell relevant sind (z.B. `<Select>` für "Qualität" (`hd`/`sd`) und "Auflösung" bei DALL-E 3).
    4.  **Prompt-Eingabe:** Ein großes `<Input.TextArea>`.

*   **Schritt 3.2: Stil-Voreinstellungen (`StylePresets.js`)**
    *   Grid aus klickbaren Karten zur Auswahl eines visuellen Stils.

*   **Schritt 3.3: Upload-Funktion und Galerie (`UploadGallery.js`)**
    *   Upload-Button und Galerie für hochgeladene Bilder.

*   **Schritt 3.4: Kostenanzeige und "Generieren"-Button**
    1.  **Kostenanzeige:** Ein Textfeld oder eine kleine `<Alert>`-Box, die die Kosten anzeigt: "Geschätzte Kosten / Bild: **$0.080**". Dieser Wert wird bei jeder Änderung der Parameter neu berechnet.
    2.  **Generieren-Button:** Ein prominenter `<Button type="primary">`.

#### Phase 4: Frontend - Vorschau, Galerie und State Management

*   **Schritt 4.1: Großes Vorschaubild (`LatestImagePreview.js`)**
    *   Prominente Anzeige des zuletzt generierten Bildes.

*   **Schritt 4.2: Ergebnisgalerie (`GeneratedGallery.js`)**
    *   Grid-Ansicht aller bisher generierten Bilder unterhalb der Hauptvorschau.

*   **Schritt 4.3: Erweitertes State Management**
    *   `pricingData`: Speichert die Preis-Struktur von `GET /api/images/pricing`.
    *   `selectedProvider`: Der aktuell gewählte Anbieter.
    *   `selectedModel`: Das aktuell gewählte Modell.
    *   `modelParameters`: Ein Objekt, das die dynamischen Parameter speichert, z.B. `{ quality: 'hd', resolution: '1024x1024' }`.
    *   `estimatedCost`: Wird aus den obigen States und `pricingData` berechnet.
    *   Die `onChange`-Handler der Dropdowns müssen kaskadierende Updates auslösen (Provider-Änderung setzt Modell und Parameter zurück, etc.).

*   **Schritt 4.4: API-Anbindung**
    *   Das Frontend ruft beim Mounten des Modals einmalig den `GET /api/images/pricing` Endpunkt auf, um die Kostenkalkulation zu ermöglichen.

Zusammenfassung: Sicherheitskonzept zur Verschlüsselung der Chat-Datenbank
1. Das Kernproblem
Unsere SQLite-Datenbank (chat_history.db), die alle Chat-Nachrichten und Verläufe enthält, liegt unverschlüsselt auf dem Server. Im Falle eines unautorisierten Serverzugriffs oder eines Backup-Diebstahls sind alle privaten Konversationen der Nutzer im Klartext lesbar. Dies stellt ein hohes Sicherheits- und Datenschutzrisiko dar.
2. Die vorgeschlagene Lösung: Transparente Anwendungs-Verschlüsselung
Wir implementieren eine Verschlüsselung auf Anwendungsebene ("Application-Level Encryption"). Das bedeutet:
Der Server verschlüsselt: Unsere FastAPI-Anwendung ver- und entschlüsselt die Daten im laufenden Betrieb.
Die Datenbank speichert nur Müll: In der SQLite-Datei auf der Festplatte werden ausschließlich verschlüsselte, unlesbare Daten (BLOBs) gespeichert.
Transparent & wartbar: Für den Rest des Codes bleibt die Logik unverändert. Die Entwickler arbeiten weiterhin mit normalen Strings, die Verschlüsselung geschieht automatisch im Hintergrund.
3. Technische Umsetzung im Detail
Technologie: Wir nutzen die Python-Standardbibliothek cryptography (spezifisch Fernet), die auf dem robusten und schnellen AES-Algorithmus im GCM-Modus basiert.
Mechanismus: Wir erstellen einen benutzerdefinierten SQLAlchemy TypeDecorator namens EncryptedString. Dieser Typ wird in unseren Datenbank-Models anstelle von String oder Text für sensible Felder verwendet.
Beim Speichern: Der TypeDecorator fängt den Klartext ab und verschlüsselt ihn, bevor er an die Datenbank gesendet wird.
Beim Laden: Er fängt die verschlüsselten Daten aus der Datenbank ab und entschlüsselt sie, bevor sie an die Anwendung zurückgegeben werden.
Schlüsselverwaltung: Der geheime Verschlüsselungsschlüssel (ENCRYPTION_KEY) wird niemals im Code gespeichert. Er wird sicher als Umgebungsvariable (z.B. in einer .env-Datei) auf dem Server hinterlegt und nur zur Laufzeit geladen.
Strategische Verschlüsselung:
chat_history.db: Felder wie content und memory_context werden mit EncryptedString verschlüsselt. Metadaten wie timestamp oder role bleiben unverschlüsselt, um schnelles Sortieren und Filtern zu ermöglichen.
costs.db: Numerische Felder (total_cost, tokens) bleiben unverschlüsselt, um mathematische Aggregationen (z.B. SUM()) per SQL zu erlauben. Nur potenziell sensible Identifier (z.B. user_identifier) werden verschlüsselt.
4. Auswirkungen und Konsequenzen
Performance (Latenz): Die Latenz ist nicht merkbar. Die AES-Verschlüsselung eines Text-Snippets dauert auf modernen CPUs nur wenige Mikrosekunden. Dies ist vernachlässigbar im Vergleich zu den Netzwerk- und Verarbeitungszeiten von Datenbankabfragen oder OpenAI-API-Aufrufen (mehrere hundert Millisekunden bis Sekunden).
Sicherheit: Ziel erreicht. Die gestohlene Datenbankdatei ist ohne den passenden ENCRYPTION_KEY wertlos. Das Risiko eines Massen-Datenlecks der Chat-Inhalte wird massiv reduziert.
Funktionalität (Trade-off): Eine direkte Volltextsuche per SQL auf verschlüsselten Feldern (SELECT ... WHERE content LIKE '%hallo%') ist nicht mehr möglich. Suchfunktionen müssten entweder im Client (nach Laden der Daten) oder über separate, spezialisierte Suchindizes realisiert werden.
5. Notwendige nächste Schritte
Einen sicheren ENCRYPTION_KEY generieren und in der Server-Umgebung hinterlegen.
Den EncryptedString TypeDecorator implementieren.
Die SQLAlchemy-Models (ChatMessage, etc.) anpassen, um den neuen Typen zu verwenden.
Ein einmaliges Migrations-Skript schreiben und ausführen, um alle bereits existierenden Klartext-Daten in der Datenbank zu verschlüsseln.
# Janus Projekt 0.4.17-beta.19
**Released:** 2026-05-08 20:02

### Fixed
- **Task 030:** Video-Liste Chat-Wechsel Persistenz-Fix. Video-Details (Titel, Kanal, Views, Upload-Datum) werden jetzt korrekt nach einem Chat-Wechsel beibehalten. Sender-Bedingung erweitert auf "bot" || "model", appendVideoReopenLink Parameter videoListMetadata hinzugefügt, wireVideoReopenLink übergibt videoListMetadata an appendVideoReopenLink, appendMessage generiert Markdown mit Header (wie SSE-Stream) beim Chat-Reload. Backend-Logging hinzugefügt zur Verfolgung von video_list_metadata. max_results=3 → max_results=payload.max_results in video_tools.py.
## 📦 Installation
Download the installer from the GitHub releases page.

## 🐛 Known Issues
None reported for this release.

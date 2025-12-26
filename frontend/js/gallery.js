document.addEventListener("DOMContentLoaded", () => {
  const galleryView = document.getElementById("gallery-view");
  const galleryWindow = document.getElementById("gallery-window");
  const showGalleryCheckbox = document.getElementById("show-gallery");
  const closeGalleryBtn = document.getElementById("close-gallery-btn");
  const galleryContent = document.getElementById("gallery-content");

  async function loadImages() {
    try {
      const response = await fetch("/api/images");

      // NEU: Prüfen, ob die Antwort wirklich JSON ist
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        // Wir lesen die Antwort als Text, um den Fehler besser zu verstehen
        const responseText = await response.text();
        throw new TypeError(
          `Falscher Antworttyp vom Server erhalten. Erwartet: JSON, Bekommen: HTML/Text. Antwort: ${responseText.substring(0, 100)}...`
        );
      }

      if (!response.ok) {
        throw new Error(`HTTP-Fehler! Status: ${response.status}`);
      }

      const data = await response.json();

      galleryContent.innerHTML = ""; // Leere die Galerie vor dem Neu-Laden
      if (data.images && data.images.length > 0) {
        data.images.forEach((imageUrl) => {
          const img = document.createElement("img");
          img.src = imageUrl;
          img.alt = "Generiertes Bild";
          img.addEventListener("click", () => {
            window.open(imageUrl, "_blank");
          });
          galleryContent.appendChild(img);
        });
      } else {
        galleryContent.innerHTML = '<p style="color: #ccc;">Noch keine Bilder erstellt.</p>';
      }
    } catch (error) {
      console.error("Fehler beim Laden der Bilder:", error);
      galleryContent.innerHTML =
        '<p style="color: #f88;">Bilder konnten nicht geladen werden. Prüfen Sie die Entwicklerkonsole für Details.</p>';
    }
  }

  function showGallery() {
    galleryView.style.display = "flex";
    loadImages();
  }

  function hideGallery() {
    galleryView.style.display = "none";
  }

  showGalleryCheckbox.addEventListener("change", () => {
    if (showGalleryCheckbox.checked) {
      showGallery();
    } else {
      hideGallery();
    }
  });

  closeGalleryBtn.addEventListener("click", () => {
    showGalleryCheckbox.checked = false;
    hideGallery();
  });

  // --- Drag & Drop Funktionalität ---
  let isDragging = false;
  let offsetX, offsetY;

  const header = document.getElementById("gallery-header");

  header.addEventListener("mousedown", (e) => {
    isDragging = true;
    offsetX = e.clientX - galleryWindow.offsetLeft;
    offsetY = e.clientY - galleryWindow.offsetTop;

    // Verhindert Textauswahl beim Ziehen
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    let newX = e.clientX - offsetX;
    let newY = e.clientY - offsetY;

    // Begrenze die Bewegung auf den sichtbaren Bereich
    const maxX = window.innerWidth - galleryWindow.offsetWidth;
    const maxY = window.innerHeight - galleryWindow.offsetHeight;

    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));

    galleryWindow.style.left = `${newX}px`;
    galleryWindow.style.top = `${newY}px`;
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
  });

  // --- Resize Funktionalität (vereinfacht) ---
  // Für eine vollwertige Resize-Funktion wird oft eine Bibliothek wie jQuery UI
  // oder Interact.js verwendet. Dies ist eine einfache Implementierung.
  // Hier fügen wir nur einen Resize-Handle hinzu.
  const resizeHandle = document.createElement("div");
  resizeHandle.style.width = "15px";
  resizeHandle.style.height = "15px";
  resizeHandle.style.position = "absolute";
  resizeHandle.style.right = "0";
  resizeHandle.style.bottom = "0";
  resizeHandle.style.cursor = "se-resize";
  galleryWindow.appendChild(resizeHandle);

  let isResizing = false;

  resizeHandle.addEventListener("mousedown", function (e) {
    isResizing = true;
    // Verhindert, dass das Dragging des Fensters ausgelöst wird
    e.stopPropagation();
    e.preventDefault();
  });

  document.addEventListener("mousemove", function (e) {
    if (!isResizing) return;

    const newWidth = e.clientX - galleryWindow.offsetLeft;
    const newHeight = e.clientY - galleryWindow.offsetTop;

    galleryWindow.style.width = `${Math.max(300, newWidth)}px`; // Mindestbreite
    galleryWindow.style.height = `${Math.max(200, newHeight)}px`; // Mindesthöhe
  });

  document.addEventListener("mouseup", function () {
    isResizing = false;
  });
});

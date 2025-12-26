document.addEventListener("contextmenu", async (event) => {
  // Check if the right-clicked element is an input or textarea
  const target = event.target;
  if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") {
    event.preventDefault(); // Prevent the default browser context menu

    // Remove any existing custom context menu
    const existingMenu = document.getElementById("custom-input-context-menu");
    if (existingMenu) {
      existingMenu.remove();
    }

    // Create the custom context menu
    const menu = document.createElement("div");
    menu.id = "custom-input-context-menu";
    menu.style.position = "fixed";
    menu.style.top = `${event.clientY}px`;
    menu.style.left = `${event.clientX}px`;
    menu.style.backgroundColor = "#333";
    menu.style.border = "1px solid #555";
    menu.style.borderRadius = "4px";
    menu.style.zIndex = "10000";
    menu.style.boxShadow = "0 2px 5px rgba(0,0,0,0.2)";
    menu.style.padding = "5px 0";
    menu.style.minWidth = "120px";

    // Add "Paste" option
    const pasteItem = document.createElement("div");
    pasteItem.classList.add("context-menu-item");
    pasteItem.textContent = "Einfügen";
    pasteItem.style.padding = "8px 15px";
    pasteItem.style.cursor = "pointer";
    pasteItem.style.color = "#eee";
    pasteItem.style.fontSize = "14px";

    pasteItem.addEventListener("mouseenter", () => {
      pasteItem.style.backgroundColor = "#555";
    });
    pasteItem.addEventListener("mouseleave", () => {
      pasteItem.style.backgroundColor = "#333";
    });

    pasteItem.addEventListener("click", async () => {
      try {
        const text = await navigator.clipboard.readText();
        // Insert text at the current cursor position
        const start = target.selectionStart;
        const end = target.selectionEnd;
        target.value = target.value.substring(0, start) + text + target.value.substring(end);
        target.selectionStart = target.selectionEnd = start + text.length;
        target.focus();
      } catch (err) {
        console.error("Failed to read clipboard contents: ", err);
        // Optionally, show a user-friendly error message
      }
      menu.remove(); // Hide menu after action
    });
    menu.appendChild(pasteItem);

    document.body.appendChild(menu);

    // Hide menu when clicking outside
    const clickOutsideHandler = (e) => {
      if (!menu.contains(e.target) && e.target !== target) {
        menu.remove();
        document.removeEventListener("click", clickOutsideHandler);
        document.removeEventListener("contextmenu", clickOutsideHandler); // Also hide if another right-click occurs
      }
    };
    document.addEventListener("click", clickOutsideHandler);
    document.addEventListener("contextmenu", clickOutsideHandler);
  }
});

// Optional: Hide menu if user scrolls or resizes window
window.addEventListener("scroll", () => {
  const existingMenu = document.getElementById("custom-input-context-menu");
  if (existingMenu) existingMenu.remove();
});
window.addEventListener("resize", () => {
  const existingMenu = document.getElementById("custom-input-context-menu");
  if (existingMenu) existingMenu.remove();
});

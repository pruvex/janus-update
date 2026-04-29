// frontend/js/cost-visualizer.js
import { API_BASE_URL } from "./config.js";

document.addEventListener("DOMContentLoaded", () => {
  const costDashboardElement = document.getElementById("cost-dashboard");

  const refreshCostButton = document.getElementById("refresh-cost-button");
  const costSummaryWidget = document.getElementById("cost-summary-widget"); // NEW

  if (refreshCostButton) {
    refreshCostButton.addEventListener("click", fetchCostData);
  }

  // NEW: Event listener for the cost summary widget
  if (costSummaryWidget) {
    costSummaryWidget.addEventListener("click", showDeepDiveModal);
  }

  const costDeepDiveModal = document.getElementById("cost-deep-dive-modal");
  const closeButton = document.querySelector("#cost-deep-dive-modal .close-button");
  const deepDiveContent = document.getElementById("deep-dive-content");

  let currentSortMode = "model"; // "model" or "cost"

  async function showDeepDiveModal() {
    costDeepDiveModal.style.display = "flex";
    deepDiveContent.innerHTML = "Lade detaillierte Kosten...";

    // Snapshot live metadata BEFORE async fetch (it won't change during await)
    const liveMeta = window.lastMetadata || null;

    let summaryData = [];
    let totalCost = 0;
    let dbOk = false;

    try {
      const [summaryResponse, dashboardResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/costs/summary-by-model`),
        fetch(`${API_BASE_URL}/api/costs/dashboard`),
      ]);

      if (summaryResponse.ok && dashboardResponse.ok) {
        summaryData = await summaryResponse.json();
        const dashboardData = await dashboardResponse.json();
        totalCost = dashboardData.current_month_cost;
        dbOk = true;
        console.log("[COST-VIS] summaryData from API:", JSON.stringify(summaryData));
        console.log("[COST-VIS] dashboardData:", JSON.stringify(dashboardData));
      } else {
        console.warn("[COST-VIS] API error:", summaryResponse.status, dashboardResponse.status);
      }
    } catch (error) {
      console.error("Error fetching deep dive cost data:", error);
    }

    // Render the modal with current sort mode
    renderDeepDiveContent(summaryData, totalCost, dbOk, liveMeta);
  }

  function renderDeepDiveContent(summaryData, totalCost, dbOk, liveMeta) {
    // --- BUILD HTML ---
    const buttonText = currentSortMode === "cost" ? "Nach Modellen sortieren" : "Nach Kosten sortieren";
    let html = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin: 0;">Kostenübersicht nach Modell (Dieser Monat)</h3>
        <button id="toggle-sort-btn" style="padding: 0.5rem 1rem; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem; white-space: nowrap;">
          ${buttonText}
        </button>
      </div>
    `;

    const hasDbData = dbOk && summaryData.length > 0;
    const hasLiveData = liveMeta && liveMeta.cost > 0;

    if (!hasDbData && !hasLiveData) {
      html += "<p>Keine Kosteninformationen für den aktuellen Monat verfügbar.</p>";
    } else {
      html += `
        <table id="cost-details-table">
          <thead>
            <tr>
              <th>Modell</th>
              <th>Details / Tokens</th>
              <th>Gesamtkosten (€)</th>
            </tr>
          </thead>
          <tbody>`;

      // LIVE ROW FIRST — from window.lastMetadata
      if (hasLiveData) {
        const liveCostFmt = liveMeta.cost.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + " €";
        html += `
            <tr class="live-cost-row" data-live-row="true" style="background: rgba(0,255,100,0.15);">
              <td><strong>🟢 Aktuelle Session (Live)</strong></td>
              <td>Eingabe: ${liveMeta.inputTokens}, Ausgabe: ${liveMeta.outputTokens}</td>
              <td><strong>${liveCostFmt}</strong></td>
            </tr>`;
        // Live row is visual feedback only — DB total is the single source of truth
      }

      // Sort based on current mode
      let sortedData = [...summaryData]; // Create a copy to avoid mutating original
      
      if (currentSortMode === "cost") {
        // Sort by total_cost descending (highest first)
        sortedData.sort((a, b) => (b.total_cost || 0) - (a.total_cost || 0));
      } else {
        // Custom sort: GPT models (nano → mini → base → 5.5 → pro), then Gemini (flash → pro)
        sortedData.sort((a, b) => {
          const modelA = (a.model || "").toLowerCase();
          const modelB = (b.model || "").toLowerCase();
          
          const isGptA = modelA.includes("gpt");
          const isGptB = modelB.includes("gpt");
          const isGeminiA = modelA.includes("gemini");
          const isGeminiB = modelB.includes("gemini");
          
          // GPT models come first
          if (isGptA && !isGptB) return -1;
          if (!isGptA && isGptB) return 1;
          
          // Within GPT: nano → mini → base → 5.5 → pro
          if (isGptA && isGptB) {
            const gptOrder = ["nano", "mini", "base", "5.5", "pro"];
            let orderA = 999, orderB = 999;
            for (let i = 0; i < gptOrder.length; i++) {
              if (modelA.includes(gptOrder[i])) orderA = i;
              if (modelB.includes(gptOrder[i])) orderB = i;
            }
            if (orderA !== orderB) return orderA - orderB;
            // Fallback: alphabetical
            return modelA.localeCompare(modelB);
          }
          
          // Within Gemini: flash → pro
          if (isGeminiA && isGeminiB) {
            const geminiOrder = ["flash", "pro"];
            let orderA = 999, orderB = 999;
            for (let i = 0; i < geminiOrder.length; i++) {
              if (modelA.includes(geminiOrder[i])) orderA = i;
              if (modelB.includes(geminiOrder[i])) orderB = i;
            }
            if (orderA !== orderB) return orderA - orderB;
            return modelA.localeCompare(modelB);
          }
          
          // Gemini comes after GPT
          if (isGeminiA && !isGeminiB) return 1;
          if (!isGeminiA && isGeminiB) return -1;
          
          // Default: alphabetical
          return modelA.localeCompare(modelB);
        });
      }

      // DB ROWS
      sortedData.forEach((item) => {
        // Special handling for Web Search entry
        if (item.model === "__WEB_SEARCHES__") {
          const searchCount = item.search_count || 0;
          const searchCost = item.search_cost || 0;
          html += `
            <tr class="web-search-row" style="background: rgba(100,149,237,0.15);">
              <td><strong>🔍 Web-Recherchen</strong></td>
              <td>${searchCount} Treffer | 0,01€ pro Suche</td>
              <td><strong>${searchCost.toFixed(4)} €</strong></td>
            </tr>`;
          return; // Skip normal processing
        }

        let detailText = "";
        if (item.total_input_tokens > 0 || item.total_output_tokens > 0) {
          detailText = `Eingabe: ${item.total_input_tokens}, Ausgabe: ${item.total_output_tokens}`;
        } else if (item.image_count > 0) {
          detailText = `Bilder: ${item.image_count}`;
        } else if (item.context_breakdown && item.context_breakdown.length > 0) {
          detailText = `Kontexte: ${item.context_breakdown.length}`;
        }

        // Janus Caching Savings
        const costSaved = item.total_cost_saved || 0;
        const totalCostWithSavings = (item.total_cost || 0) + costSaved;
        const efficiencyPct = totalCostWithSavings > 0
          ? Math.round((costSaved / totalCostWithSavings) * 100)
          : 0;
        
        if (costSaved > 0) {
          detailText += `<br><span style="color: #4caf50; font-size: 0.9em;">(Janus Caching: -${costSaved.toFixed(4)} € | ${efficiencyPct}% gespart)</span>`;
        }

        html += `
            <tr>
              <td>${item.model === 'gpt-4o-mini' ? 'gpt-4o-mini (gpt Sprachausgabe)' : item.model}</td>
              <td>${detailText}</td>
              <td>${item.total_cost.toFixed(4)}</td>
            </tr>`;
        if (item.image_details && item.image_details.length > 0) {
          item.image_details.forEach(detail => {
            html += `
              <tr class="image-detail-row">
                <td></td>
                <td class="image-detail-text">Qualität: ${detail.quality}, Größe: ${detail.size}</td>
                <td>${detail.cost.toFixed(4)}</td>
              </tr>`;
          });
        }
        // Only expand context breakdown if there are multiple contexts or non-default context
        const hasMultipleContexts = item.context_breakdown && item.context_breakdown.length > 1;
        const hasMeaningfulContext = item.context_breakdown && item.context_breakdown.length === 1
          && item.context_breakdown[0].context !== "conversation";
        if (hasMultipleContexts || hasMeaningfulContext) {
          item.context_breakdown.forEach(detail => {
            const detailParts = [];
            if (detail.input_tokens > 0 || detail.output_tokens > 0) {
              detailParts.push(`Eingabe: ${detail.input_tokens}, Ausgabe: ${detail.output_tokens}`);
            }
            if (detail.count > 0) {
              detailParts.push(`Anfragen: ${detail.count}`);
            }
            html += `
              <tr class="image-detail-row">
                <td></td>
                <td class="image-detail-text">${detail.context}: ${detailParts.join(" | ")}</td>
                <td>${detail.cost.toFixed(4)}</td>
              </tr>`;
          });
        }
      });

      // Calculate total savings across all models
      const totalSaved = summaryData.reduce((sum, item) => sum + (item.total_cost_saved || 0), 0);
      const totalSpent = summaryData.reduce((sum, item) => sum + (item.total_cost || 0), 0);
      const totalEffPct = (totalSpent + totalSaved) > 0
        ? Math.round((totalSaved / (totalSpent + totalSaved)) * 100)
        : 0;

      html += `
          </tbody>
          <tfoot>
            <tr>
              <td colspan="2"><strong>Gesamt</strong></td>
              <td><strong>${totalCost.toFixed(4)} €</strong></td>
            </tr>`;
      
      if (totalSaved > 0) {
        html += `
            <tr style="background: rgba(76, 175, 80, 0.1);">
              <td colspan="2"><strong>💚 Gesamtersparnis (Janus Caching)</strong></td>
              <td><strong style="color: #4caf50;">-${totalSaved.toFixed(4)} € (${totalEffPct}%)</strong></td>
            </tr>`;
      }
      
      html += `
          </tfoot>`;
      html += "</table>";
    }

    html += `
      <div class="budget-setter">
        <label for="budget-input">Monatsbudget festlegen (€):</label>
        <input type="number" id="budget-input" step="0.01">
        <button id="save-budget-btn">Speichern</button>
      </div>`;
    deepDiveContent.innerHTML = html;

    // Add event listener for sort toggle button
    const toggleBtn = document.getElementById("toggle-sort-btn");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", (e) => {
        e.preventDefault();
        currentSortMode = currentSortMode === "model" ? "cost" : "model";
        console.log("[COST-VIS] Sort mode toggled to:", currentSortMode);
        renderDeepDiveContent(summaryData, totalCost, dbOk, liveMeta);
      });
    }
  }

  function hideDeepDiveModal() {
    costDeepDiveModal.style.display = "none";
  }

  // Close the modal when the close button is clicked
  if (closeButton) {
    closeButton.addEventListener("click", hideDeepDiveModal);
  }

  // Close the modal when clicking outside of the modal content
  window.addEventListener("click", (event) => {
    if (event.target === costDeepDiveModal) {
      hideDeepDiveModal();
    }
  });

  window.fetchCostData = async function () {
    const currentMonthCostElement = document.getElementById("current-month-cost");
    const monthlyBudgetElement = document.getElementById("monthly-budget");
    const budgetProgressFill = document.getElementById("budget-progress-fill");
    const costSummaryWidgetEl = document.getElementById("cost-summary-widget");

    try {
      // Fetch dashboard data
      const dashboardResponse = await fetch(`${API_BASE_URL}/api/costs/dashboard`);
      const dashboardData = await dashboardResponse.json();

      const dbTotal = dashboardData.current_month_cost;

      // Math.max guard: never display less than the live metadata value
      const liveMeta = window.lastMetadata;
      const liveCostFloor = (liveMeta && typeof liveMeta.cost === "number" && liveMeta.cost > 0) ? liveMeta.cost : 0;
      const effectiveTotal = Math.max(dbTotal, liveCostFloor);
      const monthlyBudget = Number(dashboardData.monthly_budget) || 0;

      // Guard: only update sidebar if effective value is strictly greater than currently displayed
      if (currentMonthCostElement) {
        const currentText = currentMonthCostElement.textContent || "";
        const currentMatch = currentText.match(/([\d.,]+)\s*€/);
        const currentShown = currentMatch ? parseFloat(currentMatch[1].replace(",", ".")) : 0;
        if (effectiveTotal > currentShown) {
          currentMonthCostElement.textContent = `Aktueller Monat: ${effectiveTotal.toFixed(2)} €`;
          console.log(`[COST-VIS] Sidebar updated: ${currentShown} → ${effectiveTotal} (db=${dbTotal}, live=${liveCostFloor})`);
        } else {
          console.log(`[COST-VIS] Sidebar skip: effective ${effectiveTotal} <= shown ${currentShown}`);
        }
      }
      if (monthlyBudgetElement) {
        monthlyBudgetElement.textContent = `Budget: ${effectiveTotal.toFixed(2)} € / ${monthlyBudget.toFixed(2)} €`;
        if (effectiveTotal > monthlyBudget) {
          monthlyBudgetElement.classList.add("budget-exceeded");
        } else {
          monthlyBudgetElement.classList.remove("budget-exceeded");
        }
      }

      if (budgetProgressFill && monthlyBudget > 0) {
        const pct = Math.min(100, (effectiveTotal / monthlyBudget) * 100);
        budgetProgressFill.style.width = `${pct}%`;
      } else if (budgetProgressFill) {
        budgetProgressFill.style.width = "0%";
      }

      if (costSummaryWidgetEl) {
        if (effectiveTotal > monthlyBudget) {
          costSummaryWidgetEl.classList.add("budget-exceeded");
        } else {
          costSummaryWidgetEl.classList.remove("budget-exceeded");
        }
      }

      // Existing cost dashboard update (if still needed, otherwise remove)
    } catch (error) {
      console.error("Error fetching cost data:", error);
      if (currentMonthCostElement)
        currentMonthCostElement.textContent = "Fehler beim Laden der Kosten.";
      if (monthlyBudgetElement) monthlyBudgetElement.textContent = "";
      if (budgetProgressFill) budgetProgressFill.style.width = "0%";
      if (costSummaryWidgetEl) costSummaryWidgetEl.classList.remove("budget-exceeded");

      if (costDashboardElement) costDashboardElement.innerHTML = "";
    }
  };

  // Listen for cost update events (e.g., after video analysis)
  window.addEventListener("janus:cost-update", (e) => {
    console.log("[COST-VIS] janus:cost-update received, triggering fetchCostData");
    window.fetchCostData();
  });

  // Listen for live SSE metadata and inject into modal + sidebar
  window.addEventListener("janus:metadata", (e) => {
    const { cost, usage } = e.detail;
    const totalCost = cost?.total_cost ?? cost?.total ?? cost?.cost_usd ?? 0;
    const inputTokens = usage?.input_tokens ?? usage?.prompt_tokens ?? 0;
    const outputTokens = usage?.output_tokens ?? usage?.completion_tokens ?? 0;
    const costFormatted = totalCost.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + " €";

    console.log("[COST-VIS] janus:metadata received, cost:", costFormatted);

    // Update sidebar immediately
    const currentMonthCostElement = document.getElementById("current-month-cost");
    if (currentMonthCostElement) {
      currentMonthCostElement.textContent = `Letzte Anfrage: ${costFormatted}`;
    }

    // If modal is open, inject live row
    if (costDeepDiveModal && costDeepDiveModal.style.display !== "none") {
      const tbody = document.querySelector("#cost-details-table tbody");
      if (tbody) {
        const liveRow = document.createElement("tr");
        liveRow.style.background = "rgba(0,255,100,0.15)";
        liveRow.innerHTML = `
          <td><strong>Aktuelle Session (Live)</strong></td>
          <td>Eingabe: ${inputTokens}, Ausgabe: ${outputTokens}</td>
          <td><strong>${costFormatted}</strong></td>
        `;
        // Remove previous live row if exists
        const prev = tbody.querySelector("tr[data-live-row]");
        if (prev) prev.remove();
        liveRow.setAttribute("data-live-row", "true");
        tbody.insertBefore(liveRow, tbody.firstChild);
      }
    }
  });

  // Initial fetch with delay to allow backend to start
  setTimeout(window.fetchCostData, 2000);
});

document.addEventListener("click", async (event) => {
  if (event.target && event.target.id === "save-budget-btn") {
    const budgetInput = document.getElementById("budget-input");
    const newBudget = parseFloat(budgetInput.value);
    if (!isNaN(newBudget)) {
      await fetch(`${API_BASE_URL}/api/budget`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ budget: newBudget }),
      });
      // Aktualisiere die Anzeige nach dem Speichern
      window.fetchCostData();
    }
  }
});

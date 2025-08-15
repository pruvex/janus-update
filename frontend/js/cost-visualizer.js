// frontend/js/cost-visualizer.js

document.addEventListener('DOMContentLoaded', () => {
    const costDashboardElement = document.getElementById('cost-dashboard');
    
    const refreshCostButton = document.getElementById('refresh-cost-button');
    const costSummaryWidget = document.getElementById('cost-summary-widget'); // NEW

    if (refreshCostButton) {
        refreshCostButton.addEventListener('click', fetchCostData);
    }

    // NEW: Event listener for the cost summary widget
    if (costSummaryWidget) {
        costSummaryWidget.addEventListener('click', showDeepDiveModal);
    }

    const costDeepDiveModal = document.getElementById('cost-deep-dive-modal');
    const closeButton = document.querySelector('#cost-deep-dive-modal .close-button');
    const deepDiveContent = document.getElementById('deep-dive-content');

    async function showDeepDiveModal() {
        costDeepDiveModal.style.display = 'flex'; // Use flex to center content
        deepDiveContent.innerHTML = 'Lade detaillierte Kosten...'; // Loading message

        try {
            // Fetch both summary and dashboard data in parallel
            const [summaryResponse, dashboardResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/api/costs/summary-by-model`),
                fetch(`${API_BASE_URL}/api/costs/dashboard`)
            ]);

            if (!summaryResponse.ok) {
                throw new Error(`HTTP error! status: ${summaryResponse.status}`);
            }
            if (!dashboardResponse.ok) {
                throw new Error(`HTTP error! status: ${dashboardResponse.status}`);
            }

            const summaryData = await summaryResponse.json();
            const dashboardData = await dashboardResponse.json();
            const totalCost = dashboardData.current_month_cost;

            let html = '<h3>Kostenübersicht nach Modell (Dieser Monat)</h3>';
            if (summaryData.length === 0) {
                html += '<p>Keine Kosteninformationen für den aktuellen Monat verfügbar.</p>';
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
                summaryData.forEach(item => {
                  let detailText = '';
                  if (item.total_input_tokens > 0 || item.total_output_tokens > 0) {
                    detailText = `Eingabe: ${item.total_input_tokens}, Ausgabe: ${item.total_output_tokens}`;
                  } else if (item.image_count > 0) {
                    detailText = `Bilder: ${item.image_count}`;
                  }
                  
                  html += `
                    <tr>
                      <td>${item.model}</td>
                      <td>${detailText}</td>
                      <td>${item.total_cost.toFixed(4)}</td>
                    </tr>
                  `;
                });
                html += `
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colspan="2"><strong>Gesamt</strong></td>
                        <td><strong>${totalCost.toFixed(4)} €</strong></td>
                      </tr>
                    </tfoot>
                `;
                html += `</table>`;
            }
            html += `
                <div class="budget-setter">
                  <label for="budget-input">Monatsbudget festlegen (€):</label>
                  <input type="number" id="budget-input" step="0.01">
                  <button id="save-budget-btn">Speichern</button>
                </div>
            `;
            deepDiveContent.innerHTML = html;

        } catch (error) {
            console.error('Error fetching deep dive cost data:', error);
            deepDiveContent.innerHTML = '<p>Fehler beim Laden der detaillierten Kosten.</p>';
        }
    }

    function hideDeepDiveModal() {
        costDeepDiveModal.style.display = 'none';
    }

    // Close the modal when the close button is clicked
    if (closeButton) {
        closeButton.addEventListener('click', hideDeepDiveModal);
    }

    // Close the modal when clicking outside of the modal content
    window.addEventListener('click', (event) => {
        if (event.target === costDeepDiveModal) {
            hideDeepDiveModal();
        }
    });

    window.fetchCostData = async function() {
        const currentMonthCostElement = document.getElementById('current-month-cost');
        const monthlyBudgetElement = document.getElementById('monthly-budget');

        try {
            // Fetch dashboard data
            const dashboardResponse = await fetch(`${API_BASE_URL}/api/costs/dashboard`);
            const dashboardData = await dashboardResponse.json();
            
            // Update new summary widget
            if (currentMonthCostElement) {
                currentMonthCostElement.textContent = `Aktueller Monat: ${dashboardData.current_month_cost.toFixed(2)} €`;
            }
            if (monthlyBudgetElement) {
                monthlyBudgetElement.textContent = `Budget: ${dashboardData.current_month_cost.toFixed(2)} € / ${dashboardData.monthly_budget.toFixed(2)} €`;
                if (dashboardData.current_month_cost > dashboardData.monthly_budget) {
                    monthlyBudgetElement.classList.add('budget-exceeded');
                } else {
                    monthlyBudgetElement.classList.remove('budget-exceeded');
                }
            }

            // Existing cost dashboard update (if still needed, otherwise remove)
            

            

        } catch (error) {
            console.error('Error fetching cost data:', error);
            if (currentMonthCostElement) currentMonthCostElement.textContent = 'Fehler beim Laden der Kosten.';
            if (monthlyBudgetElement) monthlyBudgetElement.textContent = '';
            
            if (costDetailsElement) costDetailsElement.innerHTML = '';
        }
    }

    // Initial fetch
    window.fetchCostData();
});

document.addEventListener('click', async (event) => {
  if (event.target && event.target.id === 'save-budget-btn') {
    const budgetInput = document.getElementById('budget-input');
    const newBudget = parseFloat(budgetInput.value);
    if (!isNaN(newBudget)) {
      await fetch(`${API_BASE_URL}/api/budget`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ budget: newBudget })
      });
      // Aktualisiere die Anzeige nach dem Speichern
      window.fetchCostData(); 
    }
  }
});
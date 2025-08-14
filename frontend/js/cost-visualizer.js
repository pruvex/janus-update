// frontend/js/cost-visualizer.js

document.addEventListener('DOMContentLoaded', () => {
    const costDashboardElement = document.getElementById('cost-dashboard');
    const costDetailsElement = document.getElementById('cost-details');
    const refreshCostButton = document.getElementById('refresh-cost-button');

    if (refreshCostButton) {
        refreshCostButton.addEventListener('click', fetchCostData);
    }

    async function fetchCostData() {
        try {
            // Fetch dashboard data
            const dashboardResponse = await fetch(`${API_BASE_URL}/api/costs/dashboard`);
            const dashboardData = await dashboardResponse.json();
            
            if (costDashboardElement) {
                costDashboardElement.innerHTML = `
                    <h3>Kostenübersicht</h3>
                    <p>Aktueller Monat: ${dashboardData.current_month_cost.toFixed(2)} €</p>
                    <p>Budget: ${dashboardData.monthly_budget.toFixed(2)} €</p>
                `;
            }

            // Fetch details data
            const detailsResponse = await fetch(`${API_BASE_URL}/api/costs/details`);
            const detailsData = await detailsResponse.json();

            if (costDetailsElement) {
                let detailsHtml = '<h3>Kosten-Details</h3>';
                if (detailsData.length > 0) {
                    detailsHtml += '<ul>';
                    detailsData.forEach(detail => {
                        detailsHtml += `
                            <li>
                                <strong>${new Date(detail.date).toLocaleDateString()}</strong> - 
                                ${detail.model}: ${detail.total_cost.toFixed(4)} €
                                ${detail.input_tokens ? `(In: ${detail.input_tokens})` : ''}
                                ${detail.output_tokens ? `(Out: ${detail.output_tokens})` : ''}
                                ${detail.image_quality ? `(Qualität: ${detail.image_quality})` : ''}
                            </li>
                        `;
                    });
                    detailsHtml += '</ul>';
                } else {
                    detailsHtml += '<p>Keine detaillierten Kosten verfügbar.</p>';
                }
                costDetailsElement.innerHTML = detailsHtml;
            }

        } catch (error) {
            console.error('Error fetching cost data:', error);
            if (costDashboardElement) costDashboardElement.innerHTML = '<p>Fehler beim Laden der Kosten.</p>';
            if (costDetailsElement) costDetailsElement.innerHTML = '';
        }
    }

    // Initial fetch
    fetchCostData();
});
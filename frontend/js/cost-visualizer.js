import { API_BASE_URL } from "./config.js";

document.addEventListener("DOMContentLoaded", () => {
  const costDashboardElement = document.getElementById("cost-dashboard");
  const refreshCostButton = document.getElementById("refresh-cost-button");
  const costSummaryWidget = document.getElementById("cost-summary-widget");
  const costDeepDiveModal = document.getElementById("cost-deep-dive-modal");
  const closeButton = document.querySelector("#cost-deep-dive-modal .close-button");
  const deepDiveContent = document.getElementById("deep-dive-content");

  const deepDiveState = {
    data: null,
    dashboard: null,
    selectedGroupKey: null,
    selectedRequestId: null,
    anomalyFilter: "all",
    liveMeta: window.lastMetadata || null,
  };

  if (refreshCostButton) {
    refreshCostButton.addEventListener("click", fetchCostData);
  }

  if (costSummaryWidget) {
    costSummaryWidget.addEventListener("click", showDeepDiveModal);
  }

  async function showDeepDiveModal() {
    if (!costDeepDiveModal || !deepDiveContent) {
      return;
    }

    costDeepDiveModal.style.display = "flex";
    deepDiveContent.innerHTML = '<div class="deep-dive-loading">Lade Kosten-DeepDive...</div>';
    deepDiveState.liveMeta = window.lastMetadata || null;

    try {
      const [deepDiveResponse, dashboardResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/costs/deep-dive`),
        fetch(`${API_BASE_URL}/api/costs/dashboard`),
      ]);

      if (!deepDiveResponse.ok || !dashboardResponse.ok) {
        throw new Error(`DeepDive API error: ${deepDiveResponse.status}/${dashboardResponse.status}`);
      }

      deepDiveState.data = await deepDiveResponse.json();
      deepDiveState.dashboard = await dashboardResponse.json();
      selectDefaultDeepDiveState();
      renderDeepDiveContent();
    } catch (error) {
      console.error("Error fetching deep dive cost data:", error);
      deepDiveState.data = null;
      deepDiveState.dashboard = null;
      deepDiveContent.innerHTML =
        '<div class="deep-dive-empty-state">Die DeepDive-Daten konnten gerade nicht geladen werden.</div>';
    }
  }

  function selectDefaultDeepDiveState() {
    const filteredGroups = getFilteredGroups();
    if (!filteredGroups.length) {
      deepDiveState.selectedGroupKey = null;
      deepDiveState.selectedRequestId = null;
      return;
    }

    const currentGroup = filteredGroups.find((group) => group.group_key === deepDiveState.selectedGroupKey);
    const selectedGroup = currentGroup || filteredGroups[0];
    deepDiveState.selectedGroupKey = selectedGroup.group_key;

    const requests = selectedGroup.requests || [];
    const currentRequest = requests.find((request) => request.request_id === deepDiveState.selectedRequestId);
    deepDiveState.selectedRequestId = (currentRequest || requests[0] || {}).request_id || null;
  }

  function renderDeepDiveContent() {
    if (!deepDiveContent) {
      return;
    }

    const data = deepDiveState.data;
    const dashboard = deepDiveState.dashboard;
    if (!data || !dashboard) {
      deepDiveContent.innerHTML =
        '<div class="deep-dive-empty-state">Keine DeepDive-Daten fuer den aktuellen Monat verfuegbar.</div>';
      return;
    }

    const filteredGroups = getFilteredGroups();
    const selectedGroup = filteredGroups.find((group) => group.group_key === deepDiveState.selectedGroupKey) || null;
    const selectedRequest = selectedGroup
      ? (selectedGroup.requests || []).find((request) => request.request_id === deepDiveState.selectedRequestId) || null
      : null;

    const summary = data.summary || {};
    const crossProviderSummary = data.cross_provider_summary || {};
    const anomalies = Array.isArray(data.anomaly_overview) ? data.anomaly_overview : [];
    const hasGroups = filteredGroups.length > 0;
    const monthlyBudget = Number(dashboard.monthly_budget) || 0;
    const currentMonthCost = Number(dashboard.current_month_cost) || 0;

    deepDiveContent.innerHTML = `
      <div class="deep-dive-shell">
        <div class="deep-dive-topbar">
          <div>
            <div class="deep-dive-kicker">Kosten DeepDive</div>
            <h3 class="deep-dive-title">Cross-Provider zuerst, Gemini-Forensik darunter</h3>
            <p class="deep-dive-subtitle">
              Zeitraum ${escapeHtml(formatPeriodLabel(data.period))} | Provider ${escapeHtml(
                String(data.provider_scope || "cross_provider").toUpperCase(),
              )}
            </p>
          </div>
          <div class="deep-dive-budget-box">
            <div class="deep-dive-budget-label">Monatsbudget</div>
            <div class="deep-dive-budget-value">${formatCurrency(currentMonthCost)} / ${formatCurrency(monthlyBudget)}</div>
            <div class="deep-dive-budget-note">
              ${
                monthlyBudget > 0 && currentMonthCost > monthlyBudget
                  ? "Budget ueberschritten"
                  : "Budget-Tracking aktiv"
              }
            </div>
          </div>
        </div>

        ${renderLiveSnapshot(deepDiveState.liveMeta)}
        ${renderCrossProviderOverview(crossProviderSummary)}
        ${renderSummaryCards(summary, data.historical_reconciliation || {})}
        ${renderAnomalyOverview(anomalies)}

        <div class="deep-dive-layout">
          <section class="deep-dive-panel deep-dive-groups-panel">
            <div class="deep-dive-panel-header">
              <h4>Kostenbloecke</h4>
              <span>${filteredGroups.length} Gruppen</span>
            </div>
            ${
              hasGroups
                ? renderGroupList(filteredGroups, deepDiveState.selectedGroupKey)
                : '<div class="deep-dive-empty-state deep-dive-panel-empty">Keine Gruppen fuer den aktuellen Filter.</div>'
            }
          </section>

          <section class="deep-dive-panel deep-dive-requests-panel">
            <div class="deep-dive-panel-header">
              <h4>Requests</h4>
              <span>${selectedGroup ? selectedGroup.request_count : 0} Eintraege</span>
            </div>
            ${
              selectedGroup
                ? renderRequestList(selectedGroup, deepDiveState.selectedRequestId)
                : '<div class="deep-dive-empty-state deep-dive-panel-empty">Waehle links einen Kostenblock.</div>'
            }
          </section>

          <section class="deep-dive-panel deep-dive-detail-panel">
            <div class="deep-dive-panel-header">
              <h4>Request-Details</h4>
              <span>${selectedRequest ? escapeHtml(selectedRequest.request_id) : "Keine Auswahl"}</span>
            </div>
            ${
              selectedRequest
                ? renderRequestDetail(selectedRequest, data.historical_reconciliation || {})
                : '<div class="deep-dive-empty-state deep-dive-panel-empty">Waehle einen Request, um Komponenten, Abweichungen und Token zu sehen.</div>'
            }
          </section>
        </div>

        <div class="budget-setter deep-dive-budget-setter">
          <label for="budget-input">Monatsbudget festlegen (EUR)</label>
          <div class="deep-dive-budget-actions">
            <input type="number" id="budget-input" step="0.01" value="${escapeAttribute(
              monthlyBudget > 0 ? monthlyBudget.toFixed(2) : "",
            )}">
            <button id="save-budget-btn">Speichern</button>
          </div>
        </div>
      </div>
    `;

    bindDeepDiveInteractions();
  }

  function bindDeepDiveInteractions() {
    document.querySelectorAll("[data-anomaly-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        deepDiveState.anomalyFilter = button.getAttribute("data-anomaly-filter") || "all";
        selectDefaultDeepDiveState();
        renderDeepDiveContent();
      });
    });

    document.querySelectorAll("[data-group-key]").forEach((button) => {
      button.addEventListener("click", () => {
        deepDiveState.selectedGroupKey = button.getAttribute("data-group-key");
        const group = getFilteredGroups().find((entry) => entry.group_key === deepDiveState.selectedGroupKey);
        deepDiveState.selectedRequestId = group?.requests?.[0]?.request_id || null;
        renderDeepDiveContent();
      });
    });

    document.querySelectorAll("[data-request-id]").forEach((button) => {
      button.addEventListener("click", () => {
        deepDiveState.selectedRequestId = button.getAttribute("data-request-id");
        renderDeepDiveContent();
      });
    });
  }

  function getFilteredGroups() {
    const groups = Array.isArray(deepDiveState.data?.groups) ? [...deepDiveState.data.groups] : [];
    if (deepDiveState.anomalyFilter === "all") {
      return groups;
    }

    return groups
      .map((group) => ({
        ...group,
        requests: (group.requests || []).filter((request) =>
          Array.isArray(request.anomaly_flags) && request.anomaly_flags.includes(deepDiveState.anomalyFilter),
        ),
      }))
      .filter((group) => (group.requests || []).length > 0)
      .map((group) => ({
        ...group,
        request_count: group.requests.length,
        total_cost: sumCosts(group.requests, "total_cost"),
        internal_attributed_total: sumCosts(group.requests, "internal_attributed_total"),
        unattributed_residual_total: sumCosts(group.requests, "unattributed_residual_total"),
      }));
  }

  function renderSummaryCards(summary, historicalReconciliation) {
    const statusBuckets = Array.isArray(summary.status_buckets) ? summary.status_buckets : [];
    return `
      <section class="deep-dive-forensic-heading">
        <div>
          <div class="deep-dive-kicker">Gemini Forensik</div>
          <h4>Attribution, Restposten und Billing-Abweichungen</h4>
        </div>
      </section>
      <section class="deep-dive-summary-grid">
        <article class="deep-dive-metric-card">
          <span class="deep-dive-metric-label">Intern attribuiert</span>
          <strong>${formatCurrency(summary.internal_attributed_total)}</strong>
          <small>${summary.request_count || 0} Requests</small>
        </article>
        <article class="deep-dive-metric-card deep-dive-metric-card--warning">
          <span class="deep-dive-metric-label">Restposten</span>
          <strong>${formatCurrency(summary.unattributed_residual_total)}</strong>
          <small>${historicalReconciliation.visible_residual_required ? "sichtbar verpflichtend" : "offene Attribution"}</small>
        </article>
        <article class="deep-dive-metric-card">
          <span class="deep-dive-metric-label">Externe Billing-Summe</span>
          <strong>${formatCurrency(summary.external_billing_total)}</strong>
          <small>${escapeHtml(formatBillingReferenceLabel(historicalReconciliation.billing_reference_source))}</small>
        </article>
        <article class="deep-dive-metric-card ${
          Math.abs(Number(summary.deviation_total) || 0) > 0 ? "deep-dive-metric-card--critical" : ""
        }">
          <span class="deep-dive-metric-label">Abweichung</span>
          <strong>${formatSignedCurrency(summary.deviation_total)}</strong>
          <small>${summary.group_count || 0} Gruppen</small>
        </article>
      </section>
      <section class="deep-dive-status-strip">
        ${statusBuckets
          .map(
            (bucket) => `
              <div class="deep-dive-status-pill">
                <span>${escapeHtml(bucket.status || "Unbekannt")}</span>
                <strong>${formatCurrency(bucket.total_cost)}</strong>
              </div>
            `,
          )
          .join("")}
      </section>
    `;
  }

  function renderCrossProviderOverview(crossProviderSummary) {
    const providerBreakdown = Array.isArray(crossProviderSummary.provider_breakdown)
      ? crossProviderSummary.provider_breakdown
      : [];
    const modelBreakdown = Array.isArray(crossProviderSummary.model_breakdown)
      ? crossProviderSummary.model_breakdown
      : [];
    const topModels = modelBreakdown.slice(0, 6);
    const totalCostSaved = Number(crossProviderSummary.total_cost_saved) || 0;
    const totalTokensSaved = Number(crossProviderSummary.total_tokens_saved) || 0;
    const totalCachedTokens = Number(crossProviderSummary.total_cached_tokens) || 0;

    return `
      <section class="deep-dive-provider-section">
        <div class="deep-dive-anomaly-header">
          <div>
            <div class="deep-dive-kicker">Cross-Provider</div>
            <h4>Gesamtsicht ueber Provider, Modelle und Savings</h4>
          </div>
          <div class="deep-dive-provider-summary-note">
            ${escapeHtml(formatProviderSummaryLine(crossProviderSummary))}
          </div>
        </div>

        <section class="deep-dive-summary-grid deep-dive-summary-grid--cross-provider">
          <article class="deep-dive-metric-card">
            <span class="deep-dive-metric-label">Gesamtkosten</span>
            <strong>${formatCurrency(crossProviderSummary.total_cost)}</strong>
            <small>${providerBreakdown.length || 0} Provider aktiv</small>
          </article>
          <article class="deep-dive-metric-card">
            <span class="deep-dive-metric-label">Modelle sichtbar</span>
            <strong>${Number(crossProviderSummary.model_count) || 0}</strong>
            <small>${modelBreakdown.length || 0} Modelle im DeepDive</small>
          </article>
          <article class="deep-dive-metric-card ${totalCachedTokens > 0 ? "" : "deep-dive-metric-card--muted"}">
            <span class="deep-dive-metric-label">Cache-Tokens</span>
            <strong>${formatNumber(totalCachedTokens)}</strong>
            <small>${totalCachedTokens > 0 ? "wieder sichtbar" : "keine Cache-Tokens erfasst"}</small>
          </article>
          <article class="deep-dive-metric-card ${totalCostSaved > 0 ? "" : "deep-dive-metric-card--muted"}">
            <span class="deep-dive-metric-label">Savings</span>
            <strong>${formatCurrency(totalCostSaved)}</strong>
            <small>${totalTokensSaved > 0 ? `${formatNumber(totalTokensSaved)} Tokens gespart` : "keine Savings erfasst"}</small>
          </article>
        </section>

        <div class="deep-dive-provider-grid">
          ${
            providerBreakdown.length
              ? providerBreakdown
                  .map(
                    (provider) => `
                      <article class="deep-dive-provider-card">
                        <div class="deep-dive-provider-topline">
                          <strong>${escapeHtml(formatProviderLabel(provider.provider))}</strong>
                          <span>${formatCurrency(provider.total_cost)}</span>
                        </div>
                        <div class="deep-dive-provider-meta">
                          <span>${escapeHtml(formatModelCountLabel(provider.models))}</span>
                          <span>${formatNumber(provider.total_cached_tokens || 0)} Cache-Tokens</span>
                          <span>${formatCurrency(provider.total_cost_saved || 0)} Savings</span>
                        </div>
                      </article>
                    `,
                  )
                  .join("")
              : '<div class="deep-dive-empty-state">Keine provideruebergreifenden Kosten fuer diesen Zeitraum verfuegbar.</div>'
          }
        </div>

        <section class="deep-dive-model-section">
          <div class="deep-dive-panel-header">
            <h4>Top-Modelle</h4>
            <span>${modelBreakdown.length || 0} Modelle</span>
          </div>
          ${
            topModels.length
              ? `
                <div class="deep-dive-model-list">
                  ${topModels
                    .map(
                      (item) => `
                        <article class="deep-dive-model-row">
                          <div class="deep-dive-model-main">
                            <strong>${escapeHtml(item.model || "Unbekanntes Modell")}</strong>
                            <span>${escapeHtml(formatProviderLabel(item.provider))}</span>
                          </div>
                          <div class="deep-dive-model-metrics">
                            <span>${formatCurrency(item.total_cost)}</span>
                            <span>${formatNumber(item.total_cached_tokens || 0)} Cache</span>
                            <span>${formatCurrency(item.total_cost_saved || 0)} Savings</span>
                          </div>
                        </article>
                      `,
                    )
                    .join("")}
                </div>
              `
              : '<div class="deep-dive-empty-state">Keine Modellsicht fuer diesen Zeitraum verfuegbar.</div>'
          }
        </section>
      </section>
    `;
  }

  function renderAnomalyOverview(anomalies) {
    if (!anomalies.length) {
      return `
        <section class="deep-dive-anomaly-section">
          <div class="deep-dive-anomaly-header">
            <h4>Auffaelligkeiten</h4>
            <div class="deep-dive-filter-row">
              <button class="deep-dive-filter-chip is-active" data-anomaly-filter="all">Alle</button>
            </div>
          </div>
          <div class="deep-dive-empty-state">Keine aktiven Auffaelligkeiten fuer diesen Zeitraum.</div>
        </section>
      `;
    }

    return `
      <section class="deep-dive-anomaly-section">
        <div class="deep-dive-anomaly-header">
          <h4>Auffaelligkeiten</h4>
          <div class="deep-dive-filter-row">
            ${renderFilterChip("all", "Alle")}
            ${anomalies.map((item) => renderFilterChip(item.type, item.label)).join("")}
          </div>
        </div>
        <div class="deep-dive-anomaly-grid">
          ${anomalies
            .map(
              (item) => `
                <article class="deep-dive-anomaly-card deep-dive-anomaly-card--${escapeAttribute(item.severity || "info")}">
                  <div class="deep-dive-anomaly-topline">
                    <span class="deep-dive-badge deep-dive-badge--${escapeAttribute(item.severity || "info")}">${escapeHtml(
                      item.label || item.type || "Anomalie",
                    )}</span>
                    <strong>${formatCurrency(item.cost)}</strong>
                  </div>
                  <p>${escapeHtml(item.message || "Keine Zusatzdetails vorhanden.")}</p>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `;
  }

  function renderFilterChip(value, label) {
    const isActive = deepDiveState.anomalyFilter === value;
    return `
      <button class="deep-dive-filter-chip ${isActive ? "is-active" : ""}" data-anomaly-filter="${escapeAttribute(
        value,
      )}">
        ${escapeHtml(label)}
      </button>
    `;
  }

  function renderGroupList(groups, selectedGroupKey) {
    return `
      <div class="deep-dive-group-list">
        ${groups
          .map((group) => {
            const isActive = group.group_key === selectedGroupKey;
            return `
              <button class="deep-dive-list-item ${isActive ? "is-active" : ""}" data-group-key="${escapeAttribute(
                group.group_key,
              )}">
                <div class="deep-dive-list-item-main">
                  <strong>${escapeHtml(group.group_label || group.group_key)}</strong>
                  <span>${escapeHtml(formatGroupMetaLine(group))}</span>
                </div>
                <div class="deep-dive-list-item-meta">
                  <span>${formatCurrency(group.total_cost)}</span>
                  ${
                    Number(group.unattributed_residual_total) > 0
                      ? `<span class="deep-dive-inline-flag">Rest ${formatCurrency(group.unattributed_residual_total)}</span>`
                      : ""
                  }
                </div>
              </button>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function renderRequestList(group, selectedRequestId) {
    const requests = Array.isArray(group.requests) ? group.requests : [];
    if (!requests.length) {
      return '<div class="deep-dive-empty-state deep-dive-panel-empty">Keine Requests in dieser Gruppe.</div>';
    }

    return `
      <div class="deep-dive-request-list">
        ${requests
          .map((request) => {
            const isActive = request.request_id === selectedRequestId;
            return `
              <button class="deep-dive-list-item ${isActive ? "is-active" : ""}" data-request-id="${escapeAttribute(
                request.request_id,
              )}">
                <div class="deep-dive-list-item-main">
                  <strong>${escapeHtml(request.request_label || request.request_id)}</strong>
                  <span>${escapeHtml(formatRequestMetaLine(request))}</span>
                </div>
                <div class="deep-dive-request-flags">
                  ${renderRequestFlagList(request)}
                </div>
                <div class="deep-dive-list-item-meta">
                  <span>${formatCurrency(request.total_cost)}</span>
                </div>
              </button>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function renderRequestDetail(request, historicalReconciliation) {
    const components = Array.isArray(request.components) ? request.components : [];
    const models = Array.isArray(request.models) ? request.models : [];

    return `
      <div class="deep-dive-request-detail">
        <div class="deep-dive-request-header">
          <div>
            <h5>${escapeHtml(request.request_label || request.request_id)}</h5>
            <p>${escapeHtml(formatRequestIdentity(request))}</p>
          </div>
          <div class="deep-dive-request-total">${formatCurrency(request.total_cost)}</div>
        </div>

        <div class="deep-dive-request-summary">
          <div>
            <span>Provider</span>
            <strong>${escapeHtml(formatProviderLabel(request.provider))}</strong>
          </div>
          <div>
            <span>Status</span>
            <strong>${escapeHtml(request.attribution_status || "unbekannt")}</strong>
          </div>
          <div>
            <span>Modelle</span>
            <strong>${escapeHtml(models.join(", ") || "n/a")}</strong>
          </div>
          <div>
            <span>Intern attribuiert</span>
            <strong>${formatCurrency(request.internal_attributed_total)}</strong>
          </div>
          <div>
            <span>Restposten</span>
            <strong>${formatCurrency(request.unattributed_residual_total)}</strong>
          </div>
          <div>
            <span>Cache-Tokens</span>
            <strong>${formatNumber(request.total_cached_tokens || 0)}</strong>
          </div>
          <div>
            <span>Savings</span>
            <strong>${formatCurrency(request.total_cost_saved)}</strong>
          </div>
        </div>

        ${
          request.anomaly_flags?.length
            ? `
              <div class="deep-dive-flag-row">
                ${request.anomaly_flags
                  .map((flag) => `<span class="deep-dive-badge deep-dive-badge--neutral">${escapeHtml(formatFlagLabel(flag))}</span>`)
                  .join("")}
                ${
                  historicalReconciliation.visible_residual_required && Number(request.unattributed_residual_total) > 0
                    ? '<span class="deep-dive-badge deep-dive-badge--warning">historischer Rest sichtbar</span>'
                    : ""
                }
              </div>
            `
            : ""
        }

        <div class="deep-dive-component-list">
          ${components
            .map(
              (component) => `
                <article class="deep-dive-component-card">
                  <div class="deep-dive-component-topline">
                    <div>
                      <strong>${escapeHtml(formatComponentLabel(component.component))}</strong>
                      <span>${escapeHtml(component.model || "unbekanntes Modell")}</span>
                    </div>
                    <div class="deep-dive-component-total">${formatCurrency(component.total_cost)}</div>
                  </div>
                  <div class="deep-dive-component-meta">
                    <span>${escapeHtml(component.status || "unbekannt")}</span>
                    <span>${escapeHtml(formatProviderLabel(component.provider))}</span>
                    <span>${escapeHtml(formatTokenLine(component))}</span>
                    <span>${escapeHtml(formatSavingsLine(component))}</span>
                    <span>${escapeHtml(formatTimestamp(component.timestamp))}</span>
                    ${
                      component.manual_override
                        ? '<span class="deep-dive-badge deep-dive-badge--info">manueller Override</span>'
                        : ""
                    }
                  </div>
                  ${renderComponentMetadata(component.metadata)}
                </article>
              `,
            )
            .join("")}
        </div>
      </div>
    `;
  }

  function renderComponentMetadata(metadata) {
    if (!metadata || typeof metadata !== "object" || !Object.keys(metadata).length) {
      return "";
    }

    const visibleEntries = Object.entries(metadata)
      .filter(([, value]) => value !== null && value !== undefined && value !== "")
      .slice(0, 6);

    if (!visibleEntries.length) {
      return "";
    }

    return `
      <dl class="deep-dive-component-metadata">
        ${visibleEntries
          .map(
            ([key, value]) => `
              <div>
                <dt>${escapeHtml(formatMetadataKey(key))}</dt>
                <dd>${escapeHtml(String(value))}</dd>
              </div>
            `,
          )
          .join("")}
      </dl>
    `;
  }

  function renderRequestFlagList(request) {
    const parts = [];
    if (Number(request.unattributed_residual_total) > 0) {
      parts.push('<span class="deep-dive-badge deep-dive-badge--warning">Attributionsluecke</span>');
    }
    if (Array.isArray(request.anomaly_flags) && request.anomaly_flags.includes("avoidable_pro")) {
      parts.push('<span class="deep-dive-badge deep-dive-badge--info">Vermeidbarer Pro</span>');
    }
    return parts.join("");
  }

  function renderLiveSnapshot(liveMeta) {
    if (!liveMeta || Number(liveMeta.cost) <= 0) {
      return "";
    }

    return `
      <section class="deep-dive-live-card">
        <div>
          <span class="deep-dive-kicker">Live-Signal</span>
          <strong>Letzte Anfrage</strong>
        </div>
        <div class="deep-dive-live-metrics">
          <span>${formatCurrency(liveMeta.cost)}</span>
          <span>In ${Number(liveMeta.inputTokens) || 0}</span>
          <span>Out ${Number(liveMeta.outputTokens) || 0}</span>
        </div>
      </section>
    `;
  }

  function hideDeepDiveModal() {
    if (costDeepDiveModal) {
      costDeepDiveModal.style.display = "none";
    }
  }

  if (closeButton) {
    closeButton.addEventListener("click", hideDeepDiveModal);
  }

  window.addEventListener("click", (event) => {
    if (event.target === costDeepDiveModal) {
      hideDeepDiveModal();
    }
  });

  async function fetchCostData() {
    const currentMonthCostElement = document.getElementById("current-month-cost");
    const monthlyBudgetElement = document.getElementById("monthly-budget");
    const budgetProgressFill = document.getElementById("budget-progress-fill");
    const costSummaryWidgetEl = document.getElementById("cost-summary-widget");

    try {
      const dashboardResponse = await fetch(`${API_BASE_URL}/api/costs/dashboard`);
      const dashboardData = await dashboardResponse.json();

      const dbTotal = Number(dashboardData.current_month_cost) || 0;
      const liveMeta = window.lastMetadata;
      const liveCostFloor =
        liveMeta && typeof liveMeta.cost === "number" && liveMeta.cost > 0 ? liveMeta.cost : 0;
      const effectiveTotal = Math.max(dbTotal, liveCostFloor);
      const monthlyBudget = Number(dashboardData.monthly_budget) || 0;

      if (currentMonthCostElement) {
        const currentText = currentMonthCostElement.textContent || "";
        const currentMatch = currentText.match(/([\d.,]+)\s*€/);
        const currentShown = currentMatch ? parseFloat(currentMatch[1].replace(",", ".")) : 0;
        if (effectiveTotal > currentShown) {
          currentMonthCostElement.textContent = `Aktueller Monat: ${effectiveTotal.toFixed(2)} €`;
        }
      }

      if (monthlyBudgetElement) {
        monthlyBudgetElement.textContent = `Budget: ${effectiveTotal.toFixed(2)} € / ${monthlyBudget.toFixed(2)} €`;
        monthlyBudgetElement.classList.toggle("budget-exceeded", monthlyBudget > 0 && effectiveTotal > monthlyBudget);
      }

      if (budgetProgressFill) {
        const pct = monthlyBudget > 0 ? Math.min(100, (effectiveTotal / monthlyBudget) * 100) : 0;
        budgetProgressFill.style.width = `${pct}%`;
      }

      if (costSummaryWidgetEl) {
        costSummaryWidgetEl.classList.toggle("budget-exceeded", monthlyBudget > 0 && effectiveTotal > monthlyBudget);
      }
    } catch (error) {
      console.error("Error fetching cost data:", error);
      if (currentMonthCostElement) {
        currentMonthCostElement.textContent = "Fehler beim Laden der Kosten.";
      }
      if (monthlyBudgetElement) {
        monthlyBudgetElement.textContent = "";
      }
      if (budgetProgressFill) {
        budgetProgressFill.style.width = "0%";
      }
      if (costSummaryWidgetEl) {
        costSummaryWidgetEl.classList.remove("budget-exceeded");
      }
      if (costDashboardElement) {
        costDashboardElement.innerHTML = "";
      }
    }
  }

  window.fetchCostData = fetchCostData;

  window.addEventListener("janus:cost-update", () => {
    window.fetchCostData();
  });

  window.addEventListener("janus:metadata", (event) => {
    const { cost, usage } = event.detail;
    const totalCost = Number(cost?.total_cost ?? cost?.total ?? cost?.cost_usd ?? 0);
    const inputTokens = Number(usage?.input_tokens ?? usage?.prompt_tokens ?? 0);
    const outputTokens = Number(usage?.output_tokens ?? usage?.completion_tokens ?? 0);

    deepDiveState.liveMeta = {
      cost: totalCost,
      inputTokens,
      outputTokens,
    };

    const currentMonthCostElement = document.getElementById("current-month-cost");
    if (currentMonthCostElement) {
      currentMonthCostElement.textContent = `Letzte Anfrage: ${formatCurrency(totalCost)}`;
    }

    if (costDeepDiveModal && costDeepDiveModal.style.display !== "none" && deepDiveState.data) {
      renderDeepDiveContent();
    }
  });

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
      window.fetchCostData();
    }
  }
});

function formatCurrency(value) {
  const amount = Number(value) || 0;
  return `${amount.toLocaleString("de-DE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  })} €`;
}

function formatSignedCurrency(value) {
  const amount = Number(value) || 0;
  const prefix = amount > 0 ? "+" : "";
  return `${prefix}${formatCurrency(amount)}`;
}

function formatPeriodLabel(period) {
  if (!period || !/^\d{4}-\d{2}$/.test(period)) {
    return "aktueller Monat";
  }

  const [year, month] = period.split("-").map(Number);
  const date = new Date(year, month - 1, 1);
  return date.toLocaleDateString("de-DE", { month: "long", year: "numeric" });
}

function formatBillingReferenceLabel(value) {
  if (value === "persisted_external_reference") {
    return "persistierte Billing-Referenz";
  }
  if (value === "persisted_gemini_cost_records_proxy") {
    return "persistierte Gemini-Kosten als Proxy";
  }
  return "Billing-Referenz";
}

function formatRequestMetaLine(request) {
  const parts = [];
  if (request.group_kind === "test_run") {
    parts.push("Testlauf");
  } else if (request.group_kind === "session") {
    parts.push("Session");
  } else if (request.group_kind === "provider") {
    parts.push("Provider-Block");
  } else {
    parts.push("Legacy");
  }
  if (request.provider) {
    parts.push(formatProviderLabel(request.provider));
  }
  if (request.timestamp) {
    parts.push(formatTimestamp(request.timestamp));
  }
  return parts.join(" | ");
}

function formatRequestIdentity(request) {
  const parts = [request.group_label || request.group_key || "Unbekannte Gruppe"];
  if (request.timestamp) {
    parts.push(formatTimestamp(request.timestamp));
  }
  return parts.join(" | ");
}

function formatTimestamp(value) {
  if (!value) {
    return "ohne Zeitstempel";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatFlagLabel(flag) {
  if (flag === "attribution_gap") {
    return "Attributionsluecke";
  }
  if (flag === "avoidable_pro") {
    return "Vermeidbarer Pro";
  }
  return flag;
}

function formatComponentLabel(value) {
  if (value === "grounding_websearch") {
    return "Grounding / Websearch";
  }
  if (value === "conversation") {
    return "Conversation";
  }
  return value || "Komponente";
}

function formatProviderLabel(value) {
  if (String(value || "").toLowerCase() === "openai") {
    return "GPT / OpenAI";
  }
  if (String(value || "").toLowerCase() === "gemini") {
    return "Gemini";
  }
  return value || "Unbekannter Provider";
}

function formatProviderSummaryLine(summary) {
  const providerCount = Number(summary.provider_count) || 0;
  const modelCount = Number(summary.model_count) || 0;
  return `${providerCount} Provider | ${modelCount} Modelle | ${formatCurrency(summary.total_cost)}`;
}

function formatModelCountLabel(models) {
  const count = Array.isArray(models) ? models.length : 0;
  return `${count} Modell${count === 1 ? "" : "e"}`;
}

function formatGroupMetaLine(group) {
  const providerLabel = Array.isArray(group.providers) && group.providers.length
    ? group.providers.map((provider) => formatProviderLabel(provider)).join(", ")
    : "ohne Provider";
  return `${group.request_count || 0} Requests | ${providerLabel}`;
}

function formatMetadataKey(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatTokenLine(component) {
  return `In ${Number(component.input_tokens) || 0} | Out ${Number(component.output_tokens) || 0} | Total ${
    Number(component.total_tokens) || 0
  }`;
}

function formatSavingsLine(component) {
  const costSaved = Number(component.cost_saved) || 0;
  const tokensSaved = Number(component.tokens_saved) || 0;
  if (costSaved <= 0 && tokensSaved <= 0) {
    return "keine Savings";
  }
  return `Savings ${formatCurrency(costSaved)} | ${formatNumber(tokensSaved)} Tokens`;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("de-DE");
}

function sumCosts(items, key) {
  return items.reduce((sum, item) => sum + (Number(item?.[key]) || 0), 0);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

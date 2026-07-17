import { test, expect } from '@playwright/test';

test('OpenRouter DeepDive preserves zero and renders missing telemetry as unavailable', async ({ page }) => {
  await page.route('**/api/costs/deep-dive', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        provider_scope: 'cross_provider',
        user_summary: {
          primary_message: 'Kosten verstehen und Optimierungspotenziale erkennen.',
        },
        cross_provider_summary: {
          total_cost: 0,
          provider_count: 0,
          model_count: 0,
          total_cached_tokens: 0,
          total_tokens_saved: 0,
          total_cost_saved: 0,
          provider_breakdown: [],
          model_breakdown: [],
        },
        openrouter_telemetry: [
          {
            turn_id: 'turn-1',
            provider: 'openrouter',
            model: 'vendor/model-2026-07-17',
            prompt_tokens: 0,
            completion_tokens: null,
            total_tokens: null,
            cached_tokens: 0,
            cache_write_tokens: null,
            reasoning_tokens: null,
            credits_cost: 0,
            upstream_inference_cost: 0.125,
          },
        ],
        summary: {
          request_count: 0,
          group_count: 0,
          internal_attributed_total: 0,
          unattributed_residual_total: 0,
          external_billing_total: 0,
          deviation_total: 0,
          truthfulness_status: 'complete',
          truthfulness_message: 'Belastbar.',
          status_buckets: [],
        },
        groups: [],
        truthfulness_hints: [],
        anomaly_overview: [],
        historical_reconciliation: {},
      }),
    });
  });
  await page.route('**/api/costs/dashboard', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ current_month_cost: 0, monthly_budget: 0 }),
    });
  });

  await page.goto('/');
  const privacy = page.locator('#beta-privacy-modal');
  if (await privacy.isVisible()) {
    await privacy.getByRole('checkbox').check();
    await privacy.getByRole('button', { name: 'Akzeptieren' }).click();
  }
  await page.waitForSelector('#cost-summary-widget', { timeout: 20000 });
  await page.evaluate(() => document.getElementById('cost-summary-widget')?.click());

  const section = page.locator('[data-openrouter-telemetry]');
  await expect(section).toBeVisible();
  await expect(section).toContainText('vendor/model-2026-07-17');
  await expect(section).toContainText('Eingabe: 0');
  await expect(section).toContainText('Ausgabe: nicht verfügbar');
  await expect(section).toContainText('Belastete OpenRouter-Credits: 0');
  await expect(section).toContainText('Upstream-Inferenzkosten: 0,125');
  await expect(section).toContainText('Keine Schätzung oder Währungsumrechnung');
  await expect(section).not.toContainText('€');
  await expect(section).not.toContainText('$');
});

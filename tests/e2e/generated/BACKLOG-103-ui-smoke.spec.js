import { test, expect } from '@playwright/test';

const deepDivePayload = {
  provider_scope: 'cross_provider',
  period: '2026-06',
  user_summary: {
    primary_message: 'Kosten verstehen und Optimierungspotenziale erkennen.',
    total_cost: 0.084,
    provider_count: 2,
    model_count: 3,
    total_cached_tokens: 250,
    total_tokens_saved: 250,
    total_cost_saved: 0.001,
    top_providers: ['gemini', 'openai'],
    top_models: ['gemini-3-pro-preview', 'gemini-3-flash-preview', 'gpt-5.4-nano'],
  },
  truthfulness_hints: [
    {
      type: 'billing_alignment_partial',
      severity: 'info',
      cost: 0.001,
      message: 'Die interne Kostensicht ist noch nicht vollstaendig mit der Billing-Referenz abgeglichen.',
    },
  ],
  cross_provider_summary: {
    total_cost: 0.084,
    provider_count: 2,
    model_count: 3,
    total_cached_tokens: 250,
    total_tokens_saved: 250,
    total_cost_saved: 0.001,
    provider_breakdown: [
      {
        provider: 'openai',
        total_cost: 0.004,
        total_cached_tokens: 250,
        total_tokens_saved: 250,
        total_cost_saved: 0.001,
        models: ['gpt-5.4-nano'],
      },
      {
        provider: 'gemini',
        total_cost: 0.08,
        total_cached_tokens: 0,
        total_tokens_saved: 0,
        total_cost_saved: 0,
        models: ['gemini-3-flash-preview', 'gemini-3-pro-preview'],
      },
    ],
    model_breakdown: [
      {
        provider: 'gemini',
        model: 'gemini-3-pro-preview',
        total_cost: 0.05,
        total_cached_tokens: 0,
        total_tokens_saved: 0,
        total_cost_saved: 0,
        component_breakdown: [{ component: 'conversation', count: 1, total_cost: 0.05 }],
      },
      {
        provider: 'gemini',
        model: 'gemini-3-flash-preview',
        total_cost: 0.03,
        total_cached_tokens: 0,
        total_tokens_saved: 0,
        total_cost_saved: 0,
        component_breakdown: [
          { component: 'conversation', count: 1, total_cost: 0.02 },
          { component: 'grounding_websearch', count: 1, total_cost: 0.01 },
        ],
      },
      {
        provider: 'openai',
        model: 'gpt-5.4-nano',
        total_cost: 0.004,
        total_cached_tokens: 250,
        total_tokens_saved: 250,
        total_cost_saved: 0.001,
        component_breakdown: [{ component: 'conversation', count: 1, total_cost: 0.004 }],
      },
    ],
  },
  anomaly_overview: [
    {
      type: 'avoidable_pro',
      severity: 'info',
      label: 'Vermeidbarer Pro-Verbrauch',
      cost: 0.05,
      message: 'Pro-Kosten ohne sichtbaren manuellen Override wurden erkannt.',
    },
  ],
  summary: {
    forensic_provider_scope: 'gemini',
    request_count: 3,
    group_count: 3,
    internal_attributed_total: 0.08,
    unattributed_residual_total: 0,
    external_billing_total: 0.08,
    deviation_total: 0,
    truthfulness_status: 'partial',
    truthfulness_message: 'Die interne Kostensicht ist noch nicht vollstaendig mit der Billing-Referenz abgeglichen.',
    status_buckets: [
      { status: 'intern attribuiert', total_cost: 0.08 },
      { status: 'nicht eindeutig attribuiert', total_cost: 0 },
      { status: 'externe Billing-Summe', total_cost: 0.08 },
    ],
  },
  historical_reconciliation: {
    mode: 'standard',
    visible_residual_required: false,
    billing_reference_source: 'persisted_gemini_cost_records_proxy',
  },
  groups: [
    {
      group_key: 'session:chat-88',
      group_kind: 'session',
      group_value: 'chat-88',
      group_label: 'Session chat-88',
      request_count: 1,
      total_cost: 0.03,
      total_cached_tokens: 0,
      total_tokens_saved: 0,
      total_cost_saved: 0,
      internal_attributed_total: 0.03,
      unattributed_residual_total: 0,
      providers: ['gemini'],
      models: ['gemini-3-flash-preview'],
      requests: [
        {
          request_id: 'req-100',
          request_label: 'req-100',
          group_key: 'session:chat-88',
          group_kind: 'session',
          group_label: 'Session chat-88',
          timestamp: '2026-06-04T12:00:00Z',
          provider: 'gemini',
          models: ['gemini-3-flash-preview'],
          total_cost: 0.03,
          total_cached_tokens: 0,
          total_tokens_saved: 0,
          total_cost_saved: 0,
          internal_attributed_total: 0.03,
          unattributed_residual_total: 0,
          attribution_status: 'intern attribuiert',
          manual_override: false,
          anomaly_flags: [],
          components: [
            {
              cost_id: 1,
              provider: 'gemini',
              component: 'conversation',
              status: 'intern attribuiert',
              model: 'gemini-3-flash-preview',
              context: 'conversation',
              timestamp: '2026-06-04T12:00:00Z',
              total_cost: 0.02,
              input_tokens: 900,
              output_tokens: 180,
              cached_tokens: 0,
              total_tokens: 1080,
              tokens_saved: 0,
              cost_saved: 0,
              manual_override: false,
              metadata: { request_kind: 'simple_tool_loop' },
            },
          ],
        },
      ],
    },
    {
      group_key: 'test_run:TEST-RUN-1',
      group_kind: 'test_run',
      group_value: 'TEST-RUN-1',
      group_label: 'Testlauf TEST-RUN-1',
      request_count: 1,
      total_cost: 0.05,
      total_cached_tokens: 0,
      total_tokens_saved: 0,
      total_cost_saved: 0,
      internal_attributed_total: 0.05,
      unattributed_residual_total: 0,
      providers: ['gemini'],
      models: ['gemini-3-pro-preview'],
      requests: [
        {
          request_id: 'req-200',
          request_label: 'req-200',
          group_key: 'test_run:TEST-RUN-1',
          group_kind: 'test_run',
          group_label: 'Testlauf TEST-RUN-1',
          timestamp: '2026-06-04T12:05:00Z',
          provider: 'gemini',
          models: ['gemini-3-pro-preview'],
          total_cost: 0.05,
          total_cached_tokens: 0,
          total_tokens_saved: 0,
          total_cost_saved: 0,
          internal_attributed_total: 0.05,
          unattributed_residual_total: 0,
          attribution_status: 'intern attribuiert',
          manual_override: false,
          anomaly_flags: ['avoidable_pro'],
          components: [
            {
              cost_id: 3,
              provider: 'gemini',
              component: 'conversation',
              status: 'intern attribuiert',
              model: 'gemini-3-pro-preview',
              context: 'conversation',
              timestamp: '2026-06-04T12:05:00Z',
              total_cost: 0.05,
              input_tokens: 1100,
              output_tokens: 220,
              cached_tokens: 0,
              total_tokens: 1320,
              tokens_saved: 0,
              cost_saved: 0,
              manual_override: false,
              metadata: { request_kind: 'engine_owned_tool_loop' },
            },
          ],
        },
      ],
    },
  ],
};

const dashboardPayload = {
  current_month_cost: 0.084,
  monthly_budget: 0.25,
};

test('BACKLOG-103 deep dive opens in a compact two-stage flow and reveals details on demand', async ({ page }) => {
  await page.route('**/api/costs/deep-dive', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(deepDivePayload),
    });
  });

  await page.route('**/api/costs/dashboard', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(dashboardPayload),
    });
  });

  await page.goto('/');
  const betaPrivacyModal = page.locator('#beta-privacy-modal');
  if (await betaPrivacyModal.isVisible()) {
    await page.getByRole('checkbox', {
      name: /Ich habe verstanden, welche Daten Janus in der Beta verarbeitet/i,
    }).check();
    await page.getByRole('button', { name: 'Akzeptieren' }).click();
    await expect(betaPrivacyModal).toBeHidden();
  }

  await page.waitForSelector('#cost-summary-widget', { timeout: 20000 });
  await page.evaluate(() => document.getElementById('cost-summary-widget')?.click());

  await expect(page.getByText('Kosten verstehen, Einsparungen sehen, Hinweise klar lesen')).toBeVisible();
  await expect(page.getByText('Kostenquellen zuerst, Requests nur bei Bedarf')).toBeVisible();
  await expect(page.getByText('Starte mit einer Kostenquelle, um einzelne Requests und Kostenbestandteile zu sehen.')).toBeVisible();
  await expect(page.getByText('Waehle zuerst eine Kostenquelle.')).toBeVisible();
  await expect(page.getByText('Waehle einen Request, um Modelle, Kostenbestandteile und Ersparnis zu sehen.')).toBeVisible();
  await expect(page.getByText('Kosten verstehen und Optimierungspotenziale erkennen.')).toBeVisible();
  const savingsCard = page.locator('.deep-dive-metric-card').filter({
    has: page.getByText('Ersparnis', { exact: true }),
  });
  await expect(savingsCard).toBeVisible();
  await expect(savingsCard).toContainText('Durch Janus-Caching gespart | 250 Tokens | 1% weniger Kosten als ohne Cache');
  const trustHintSection = page.locator('section').filter({
    has: page.getByRole('heading', { name: 'Hinweise zur Kostensicht' }),
  });
  await expect(page.getByRole('heading', { name: 'Hinweise zur Kostensicht' })).toBeVisible();
  await expect(trustHintSection.locator('.deep-dive-anomaly-card')).toHaveCount(1);

  await expect(page.getByRole('button', { name: /Session chat-88/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /Testlauf TEST-RUN-1/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /req-100/i })).toHaveCount(0);
  await expect(page.getByText('simple_tool_loop')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Kostenbestandteile' })).toHaveCount(0);

  await page.getByRole('button', { name: /Session chat-88/i }).click();
  await expect(page.getByText('Quelle gewaehlt. Jetzt kannst du darunter einzelne Requests oeffnen.')).toBeVisible();
  await expect(page.getByRole('button', { name: /req-100/i })).toBeVisible();
  await expect(page.getByText('Ablauf simple_tool_loop')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Kostenbestandteile' })).toHaveCount(0);

  await page.getByRole('button', { name: /req-100/i }).click();
  await expect(page.getByText('Kostenbild')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Kostenbestandteile' })).toBeVisible();
  await expect(page.getByText('Ablauf simple_tool_loop')).toBeVisible();
  await expect(page.getByText('gemini-3-flash-preview').first()).toBeVisible();
});

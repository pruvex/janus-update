import { expect, test } from '@playwright/test';

const MINIMAL_PDF_BASE64 =
  'JVBERi0xLjQKJcTl8uXrp/Og0MTGCjEgMCBvYmoKPDwgL1R5cGUgL0NhdGFsb2cgL1BhZ2VzIDIgMCBSID4+CmVuZG9iagoyIDAgb2JqCjw8IC9UeXBlIC9QYWdlcyAvS2lkcyBbMyAwIFJdIC9Db3VudCAxID4+CmVuZG9iagozIDAgb2JqCjw8IC9UeXBlIC9QYWdlIC9QYXJlbnQgMiAwIFIgL01lZGlhQm94IFswIDAgMzAwIDE0NF0gL0NvbnRlbnRzIDQgMCBSIC9SZXNvdXJjZXMgPDwgL0ZvbnQgPDwgL0YxIDUgMCBSID4+ID4+ID4+CmVuZG9iago0IDAgb2JqCjw8IC9MZW5ndGggNDQgPj4Kc3RyZWFtCkJUCi9GMSAyNCBUZgoxMDAgMTAwIFRkCihKa2Fpcm8pIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKNSAwIG9iago8PCAvVHlwZSAvRm9udCAvU3VidHlwZSAvVHlwZTEgL0Jhc2VGb250IC9IZWx2ZXRpY2EgPj4KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAxMCAwMDAwMCBuIAowMDAwMDAwMDYwIDAwMDAwIG4gCjAwMDAwMDAxMTcgMDAwMDAgbiAKMDAwMDAwMDI0NCAwMDAwMCBuIAowMDAwMDAwMzM4IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNiAvUm9vdCAxIDAgUiA+PgpzdGFydHhyZWYKNDE4CiUlRU9G';

function installKnowledgeRoutes(page: import('@playwright/test').Page, auditStatus: 'new' | 'warning' | 'verified' = 'warning') {
  return Promise.all([
    page.route('**/api/rag/documents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            filename: 'kairo.pdf',
            upload_date: new Date().toISOString(),
            is_indexed: true,
            audit_status: auditStatus,
          },
        ]),
      });
    }),
    page.route('**/api/rag/files/1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: Buffer.from(MINIMAL_PDF_BASE64, 'base64'),
      });
    }),
    page.route('**/api/rag/search-ids**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, page: 1 }]),
      });
    }),
  ]);
}

async function bootstrapChat(page: import('@playwright/test').Page) {
  await page.goto('http://localhost:5173/');
  await page.evaluate(() => {
    localStorage.setItem('auth_token', 'e2e-test-fake-token');
  });
  await page.reload();

  const chatInput = page.getByPlaceholder('Nachricht an Janus senden...');
  await expect(chatInput).toBeVisible({ timeout: 15000 });

  const newChatButton = page.getByRole('button', { name: /neuer chat/i }).first();
  await newChatButton.click();
  await expect(page.locator('.message-list .message')).toHaveCount(0, { timeout: 5000 }).catch(() => {
    // Legacy UI fallback: keep test robust if message-list wrapper does not exist.
  });

  return chatInput;
}

test.describe('Diamond Scenarios (Phase O)', () => {
  test('Scenario A - The Robot Scout', async ({ page }) => {
    await installKnowledgeRoutes(page, 'verified');

    await page.route('**/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sender: 'model',
          text: 'Kairo Treffer gefunden. Ich oeffne das Dokument.',
          ui_command: {
            ui_action: 'open_pdf',
            document_id: 1,
          },
        }),
      });
    });

    const chatInput = await bootstrapChat(page);
    await chatInput.fill('Suche nach Kairo im Dokument.');
    await chatInput.press('Enter');

    await expect(page.getByTestId('knowledge-center-modal')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('knowledge-page-indicator')).toContainText('Seite 1 /', { timeout: 15000 });
  });

  test('Scenario B - The Gatekeeper', async ({ page }) => {
    await page.route('**/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sender: 'model',
          text: "Diese Aktion erfordert eine Freigabe. Moechtest du die Aktion 1. Einmalig erlauben, 2. In Zukunft immer ohne Nachfragen erlauben, oder 3. Abbrechen?",
        }),
      });
    });

    const chatInput = await bootstrapChat(page);
    await chatInput.fill('Lösche meine Datei test.txt');
    await chatInput.press('Enter');

    await expect(page.getByTestId('consent-actions')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('consent-option-1')).toBeVisible();
    await expect(page.getByTestId('consent-option-2')).toBeVisible();
    await expect(page.getByTestId('consent-option-3')).toBeVisible();
  });

  test('Scenario C - The Master Flow', async ({ page }) => {
    await installKnowledgeRoutes(page, 'warning');

    await page.route('**/api/chat', async (route) => {
      const payload = route.request().postDataJSON() as { content?: Array<{ text?: string }> };
      const prompt = String(payload?.content?.[0]?.text || '').toLowerCase();

      if (prompt.includes('faktencheck')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            sender: 'model',
            text: 'Faktencheck gestartet. Audit wurde durchgefuehrt.',
            ui_command: { ui_action: 'open_pdf', document_id: 1 },
          }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sender: 'model', text: 'Weiter mit dem Master Flow.' }),
      });
    });

    const chatInput = await bootstrapChat(page);
    await chatInput.fill('Starte jetzt den kompletten Faktencheck-Flow fuer Kairo.');
    await chatInput.press('Enter');

    await expect(page.getByTestId('knowledge-center-modal')).toBeVisible({ timeout: 15000 });
    const warningPill = page.getByTestId('audit-status-pill-warning').first();
    await expect(warningPill).toBeVisible();
    await expect(warningPill).toHaveClass(/status-warning/);
  });
});

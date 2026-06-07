import { test, expect } from "@playwright/test";

const CONTACTS = [
  {
    id: 1501,
    name: "Clara Kontakt",
    contact_type: "private_person",
    category: "Privat",
    email: "clara@example.com",
    phone: "555-01501",
    address: "Musterstrasse 15, Berlin",
    website: "",
    preferences: ["espresso"],
    dislikes: ["laute Orte"],
    personal_details: ["spricht Franzoesisch"],
    notes: "Bestaetigter direkter Kontext",
    proposal_status: "pending",
    proposal_source_context: "direct_context",
    proposal_last_outcome: "suggested_from_memory",
    memory_sync_status: "ready",
    created_at: "2026-06-07T00:00:00Z",
  },
  {
    id: 1502,
    name: "Praxis Klarblick",
    contact_type: "organization",
    category: "Business",
    email: "",
    phone: "030-111111",
    address: "Altadresse 1, Berlin",
    website: "https://klarblick.example",
    preferences: [],
    dislikes: [],
    personal_details: [],
    notes: "Oeffentliche Organisation",
    proposal_status: "pending",
    proposal_source_context: "web_enrichment",
    proposal_last_outcome: "conflict_requires_confirmation",
    memory_sync_status: "unlinked",
    created_at: "2026-06-07T00:00:00Z",
  },
];

async function installApiMocks(page) {
  await page.addInitScript(() => {
    localStorage.setItem("auth_token", "spec15-ui-evidence-token");
    localStorage.setItem(
      "janus_beta_privacy_ack_v1",
      JSON.stringify({
        accepted: true,
        noticeVersion: "2026-05-21.1",
        acceptedAt: "2026-06-07T00:00:00.000Z",
        storage: "localStorage",
      })
    );
    window.electron = {
      getApiKey: async () => "spec15-ui-evidence-key",
      getAppVersion: async () => "0.4.17-beta.spec15",
    };
  });

  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    if (path.includes("sentry") || url.hostname.includes("sentry")) {
      return route.fulfill({ status: 204, body: "" });
    }

    if (path === "/api/auth/token") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ access_token: "spec15-ui-evidence-token", token_type: "bearer" }),
      });
    }

    if (path === "/api/users/me") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          username: "Spec15 Tester",
          suggestion_mode: 1,
          dark_mode_enabled: false,
        }),
      });
    }

    if (path === "/api/models/catalog") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          "gpt-5.4-mini": {
            id: "gpt-5.4-mini",
            provider: "openai",
            display_name: "GPT 5.4 Mini",
            capabilities: ["chat"],
          },
        }),
      });
    }

    if (path.startsWith("/api/models/selection")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ openai: ["gpt-5.4-mini"], gemini: [] }),
      });
    }

    if (path === "/api/last-used-model") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ provider: "openai", model: "gpt-5.4-mini" }),
      });
    }

    if (path === "/api/projects" || path === "/api/chats") {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    }

    if (path === "/api/contacts") {
      if (request.method() === "GET") {
        return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(CONTACTS) });
      }
      if (request.method() === "POST") {
        const payload = JSON.parse(request.postData() || "{}");
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ id: 1600, created_at: "2026-06-07T00:00:00Z", ...payload }),
        });
      }
    }

    const contactMatch = path.match(/^\/api\/contacts\/(\d+)$/);
    if (contactMatch) {
      const contact = CONTACTS.find((item) => item.id === Number(contactMatch[1])) || CONTACTS[0];
      if (request.method() === "GET") {
        return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(contact) });
      }
      if (request.method() === "PUT") {
        const payload = JSON.parse(request.postData() || "{}");
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ...contact, ...payload }),
        });
      }
    }

    if (
      path.startsWith("/api/keys") ||
      path.startsWith("/api/workspaces") ||
      path.startsWith("/api/memory") ||
      path.startsWith("/api/local-image-gen") ||
      path.startsWith("/api/local-llm") ||
      path.startsWith("/api/personalities") ||
      path.startsWith("/api/rag") ||
      path.startsWith("/api/tts") ||
      path.startsWith("/api/styles") ||
      path.startsWith("/api/images") ||
      path.startsWith("/api/costs") ||
      path.startsWith("/api/budget")
    ) {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    }

    return route.continue();
  });
}

test("Spec 15 settings address book shows proposal, contact type, rich fields, and memory state", async ({ page }) => {
  test.setTimeout(60000);
  await installApiMocks(page);
  await page.goto("/");

  await page.evaluate(() => {
    document.querySelector("#chat-view").style.display = "none";
    document.querySelector("#settings-view").style.display = "flex";
    document.dispatchEvent(
      new CustomEvent("show-settings", { detail: { target: "address-book-section" } })
    );
    document.querySelector('.settings-nav-link[data-target="address-book-section"]')?.click();
  });

  const addressBook = page.locator("#address-book-section");
  await expect(addressBook).toBeVisible();
  const claraCard = addressBook.locator('.contact-card[data-id="1501"]');
  const praxisCard = addressBook.locator('.contact-card[data-id="1502"]');

  await expect(claraCard.getByText("Clara Kontakt")).toBeVisible();
  await expect(claraCard.getByText("Privatperson")).toBeVisible();
  await expect(claraCard.getByText("Offen")).toBeVisible();
  await expect(claraCard.getByText("Bereit")).toBeVisible();
  await expect(claraCard.getByText("espresso")).toBeVisible();
  await expect(claraCard.getByText("laute Orte")).toBeVisible();
  await expect(claraCard.getByText("spricht Franzoesisch")).toBeVisible();
  await expect(claraCard.getByText("suggested_from_memory")).toBeVisible();

  await expect(praxisCard.getByText("Praxis Klarblick")).toBeVisible();
  await expect(praxisCard.getByText("Organisation", { exact: true })).toBeVisible();
  await expect(praxisCard.getByText("conflict_requires_confirmation")).toBeVisible();

  await claraCard.locator(".edit-contact-btn").click();
  await expect(page.locator("#contact-modal")).toBeVisible();
  await expect(page.locator("#contact-type")).toHaveValue("private_person");
  await expect(page.locator("#contact-proposal-status")).toHaveValue("pending");
  await expect(page.locator("#contact-memory-sync-status")).toHaveValue("ready");
  await expect(page.locator("#contact-preferences")).toHaveValue(/espresso/);
  await expect(page.locator("#contact-dislikes")).toHaveValue(/laute Orte/);
  await expect(page.locator("#contact-personal-details")).toHaveValue(/spricht Franzoesisch/);
  await expect(page.locator("#contact-proposal-source-context")).toHaveValue("direct_context");
  await expect(page.locator("#contact-proposal-last-outcome")).toHaveValue("suggested_from_memory");
});

test("Spec 15 chat surface can render a confirmation-first contact proposal message", async ({ page }) => {
  await installApiMocks(page);
  await page.goto("/");

  await page.evaluate(() => {
    const messages = document.querySelector("#chat-messages-A");
    const wrapper = document.createElement("div");
    wrapper.className = "message bot-message";
    wrapper.innerHTML = `
      <div class="message-content">
        <p>Janus: Ich habe einen Kontaktvorschlag vorbereitet:</p>
        <ul>
          <li>Neuer Kontakt: Clara Kontakt (E-Mail: clara@example.com)</li>
          <li>Moeglichen Dublettenfall als Merge pruefen: Clara Kontakt (Telefon: 555-01501)</li>
        </ul>
        <p>Soll ich diese Kontaktvorschlaege anwenden? Antworte mit Ja zum Bestaetigen oder Nein zum Verwerfen.</p>
      </div>
    `;
    messages.appendChild(wrapper);
  });

  const chat = page.locator("#chat-messages-A");
  await expect(chat.getByText("Kontaktvorschlag vorbereitet")).toBeVisible();
  await expect(chat.getByText("Neuer Kontakt: Clara Kontakt")).toBeVisible();
  await expect(chat.getByText("Merge pruefen")).toBeVisible();
  await expect(chat.getByText("Ja zum Bestaetigen oder Nein zum Verwerfen")).toBeVisible();
});

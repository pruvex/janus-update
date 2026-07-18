/**
 * Shared model ordering for Settings checklists and chat model dropdowns.
 * Rule: group related families together, then cheap → expensive within a family.
 */

const OPENROUTER_FAMILY_LABELS = {
  anthropic: "Claude",
  "z-ai": "GLM",
  deepseek: "DeepSeek",
  qwen: "Qwen",
  moonshotai: "Kimi",
  "x-ai": "Grok",
  openai: "GPT",
};

const OPENROUTER_FAMILY_RANK = {
  anthropic: 10,
  "z-ai": 20,
  deepseek: 30,
  qwen: 40,
  moonshotai: 50,
  "x-ai": 60,
  openai: 70,
};

export function getModelFamilyLabel(familyKey) {
  const key = String(familyKey || "").trim().toLowerCase();
  if (Object.prototype.hasOwnProperty.call(OPENROUTER_FAMILY_LABELS, key)) {
    return OPENROUTER_FAMILY_LABELS[key];
  }
  if (!key || key === "other") return "Weitere";
  return key.charAt(0).toUpperCase() + key.slice(1);
}

/**
 * Group sorted models into family blocks (cheap → expensive within each).
 */
export function groupModelsByFamily(models) {
  const sorted = sortModelsByFamilyAndPrice(models);
  const groups = [];
  let current = null;
  for (const model of sorted) {
    const key = getModelFamilyKey(model);
    if (!current || current.key !== key) {
      current = {
        key,
        label: getModelFamilyLabel(key),
        models: [],
      };
      groups.push(current);
    }
    current.models.push(model);
  }
  return groups;
}

const OPENAI_MODEL_RANK = {
  "gpt-5.4-nano": 1,
  "gpt-5.4-mini": 2,
  "gpt-5.4": 3,
  "gpt-5.4-pro": 4,
  "gpt-5.5": 5,
  "gpt-5.5-pro": 6,
};

function modelId(model) {
  return String(model?.id || "").trim();
}

export function getModelFamilyKey(model) {
  const id = modelId(model).toLowerCase();
  if (!id) return "other";
  if (id.includes("/")) {
    return id.split("/", 1)[0] || "other";
  }
  // Native OpenAI / Gemini / Ollama ids: derive a coarse family from the prefix.
  if (id.startsWith("gpt-") || id.startsWith("o1") || id.startsWith("o3") || id.startsWith("o4")) {
    return "openai";
  }
  if (id.startsWith("gemini")) return "gemini";
  if (id.includes(":")) return "ollama";
  return id.split("-", 1)[0] || "other";
}

export function getModelSortPrice(model) {
  const input = Number(model?.cost_per_token_input);
  const output = Number(model?.cost_per_token_output);
  const inputOk = Number.isFinite(input) && input >= 0 ? input : null;
  const outputOk = Number.isFinite(output) && output >= 0 ? output : null;
  if (inputOk !== null) return inputOk;
  if (outputOk !== null) return outputOk;
  return Number.POSITIVE_INFINITY;
}

function familyRank(familyKey) {
  if (Object.prototype.hasOwnProperty.call(OPENROUTER_FAMILY_RANK, familyKey)) {
    return OPENROUTER_FAMILY_RANK[familyKey];
  }
  // Unknown families stay after known ones, still grouped alphabetically.
  return 500;
}

/**
 * Sort models: family groups first, then ascending price, then id.
 */
export function sortModelsByFamilyAndPrice(models) {
  if (!Array.isArray(models)) return models;
  return [...models].sort((a, b) => {
    const fa = getModelFamilyKey(a);
    const fb = getModelFamilyKey(b);
    const ra = familyRank(fa);
    const rb = familyRank(fb);
    if (ra !== rb) return ra - rb;
    if (fa !== fb) return fa.localeCompare(fb);

    const pa = getModelSortPrice(a);
    const pb = getModelSortPrice(b);
    if (pa !== pb) return pa - pb;

    return modelId(a).localeCompare(modelId(b));
  });
}

function geminiSidebarModelRank(model) {
  const id = modelId(model).toLowerCase();
  const typ = String(model?.type || "").toLowerCase();
  if (typ === "text" || !typ) {
    if (/flash/i.test(id)) return 100;
    if (/pro/i.test(id) && !/vision/i.test(id) && !/image/i.test(id)) return 101;
    return 150;
  }
  if (typ === "image") {
    if (/flash/i.test(id)) return 200;
    if (/pro/i.test(id)) return 201;
    return 250;
  }
  if (typ === "text_image") return 300;
  return 400;
}

/**
 * Provider-aware ordering used by chat dropdown + settings management.
 */
export function sortModelsForProvider(provider, models) {
  if (!Array.isArray(models)) return models;
  const p = String(provider || "").trim().toLowerCase();

  if (p === "openai") {
    return [...models].sort((a, b) => {
      const ra = OPENAI_MODEL_RANK[modelId(a)] || 999;
      const rb = OPENAI_MODEL_RANK[modelId(b)] || 999;
      if (ra !== rb) return ra - rb;
      return modelId(a).localeCompare(modelId(b));
    });
  }

  if (p === "gemini") {
    return [...models].sort((a, b) => {
      const ra = geminiSidebarModelRank(a);
      const rb = geminiSidebarModelRank(b);
      if (ra !== rb) return ra - rb;
      return modelId(a).localeCompare(modelId(b));
    });
  }

  // OpenRouter and any future multi-family providers: family groups, cheap → expensive.
  return sortModelsByFamilyAndPrice(models);
}

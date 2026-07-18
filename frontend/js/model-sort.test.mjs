import assert from "node:assert/strict";
import {
  getModelFamilyKey,
  getModelSortPrice,
  groupModelsByFamily,
  sortModelsByFamilyAndPrice,
  sortModelsForProvider,
} from "../../frontend/js/model-sort.js";

const models = [
  {
    id: "qwen/qwen3.7-plus",
    cost_per_token_input: 0.00000032,
    cost_per_token_output: 0.00000128,
  },
  {
    id: "qwen/qwen3.6-flash",
    cost_per_token_input: 0.0000001875,
    cost_per_token_output: 0.000001125,
  },
  {
    id: "qwen/qwen3.7-max",
    cost_per_token_input: 0.000001475,
    cost_per_token_output: 0.000004425,
  },
  {
    id: "moonshotai/kimi-k3",
    cost_per_token_input: 0.000003,
    cost_per_token_output: 0.000015,
  },
  {
    id: "anthropic/claude-sonnet-5",
    cost_per_token_input: 0.000002,
    cost_per_token_output: 0.00001,
  },
];

assert.equal(getModelFamilyKey(models[0]), "qwen");
assert.ok(getModelSortPrice(models[1]) < getModelSortPrice(models[0]));

const ordered = sortModelsForProvider("openrouter", models).map((m) => m.id);
assert.deepEqual(ordered, [
  "anthropic/claude-sonnet-5",
  "qwen/qwen3.6-flash",
  "qwen/qwen3.7-plus",
  "qwen/qwen3.7-max",
  "moonshotai/kimi-k3",
]);

const byPriceOnly = sortModelsByFamilyAndPrice([
  models[2],
  models[0],
  models[1],
]).map((m) => m.id);
assert.deepEqual(byPriceOnly, [
  "qwen/qwen3.6-flash",
  "qwen/qwen3.7-plus",
  "qwen/qwen3.7-max",
]);

const groups = groupModelsByFamily(models);
assert.deepEqual(
  groups.map((g) => ({ label: g.label, ids: g.models.map((m) => m.id) })),
  [
    { label: "Claude", ids: ["anthropic/claude-sonnet-5"] },
    {
      label: "Qwen",
      ids: ["qwen/qwen3.6-flash", "qwen/qwen3.7-plus", "qwen/qwen3.7-max"],
    },
    { label: "Kimi", ids: ["moonshotai/kimi-k3"] },
  ],
);

console.log("model-sort tests PASS");

# OpenRouter MCP Recommendation Template - 2026-07-04

Status: IMPLEMENTED / DEV INFRA ONLY / HUMAN-READABLE OPERATOR TEMPLATE

## Purpose

This template defines the first repeatable, human-readable output format for the optional OpenRouter MCP pre-run research helper.

It is meant for operator-facing recommendation display before a real OR candidate test.

It stays informational only.

## Use Moment

Use this template after the optional MCP research step has already completed and before a real OR candidate test is approved.

## Template

```text
MCP PRE-RUN RECOMMENDATION

Task Class:
Recommendation Time:
Live Data Freshness:
Internal Evidence Freshness:

Recommended Favorite:
- Model:
- Why it leads:
- Best fit task type:
- Main tradeoff:
- Suggested next action:

Alternatives:
1. Model:
   Why it stays viable:
   Best fit task type:
   Main tradeoff:
2. Model:
   Why it stays viable:
   Best fit task type:
   Main tradeoff:

Decision Notes:
- Price-performance signal:
- Benchmark/ranking signal:
- Internal evidence signal:
- Confidence level:

Approval Boundary:
- This is a recommendation only.
- Codex/operator approval is required before any real OR candidate test continues.
```

## Required Display Rules

- show one clear favorite first
- show 1 to 2 alternatives below the favorite
- keep language human-readable and quick to scan
- include one short reason why the favorite leads
- include one concrete next suggested action
- keep the whole output suitable for later storage and comparison

## Fill Rules

- `Task Class` should reflect the actual delegated work class, such as executor fleissarbeit, debug fleissarbeit, test-run support, or docs fleissarbeit
- `Live Data Freshness` should indicate whether the MCP market signals are fresh enough for the current decision
- `Internal Evidence Freshness` should indicate whether local OR evidence is recent, mixed, or stale
- `Why it leads` should stay short and decision-oriented
- `Suggested next action` should name a concrete operator step such as "use for next bounded OR candidate test"
- `Confidence level` should stay qualitative, not fake precision

## Boundary Rules

The template must not:

- claim automatic model selection
- imply auto-run authority
- imply final validation authority
- replace Codex review
- replace the normal OpenRouter runtime path
- hide contradictory signals when they exist

## Archival Rules

The filled template should be storable as a comparison artifact for later review.

That means:

- stable section order
- stable field names
- no dependency on transient chat wording
- enough context to compare one recommendation with later ones

## Example Shape

```text
MCP PRE-RUN RECOMMENDATION

Task Class: docs fleissarbeit
Recommendation Time: 2026-07-04 13:30 +02:00
Live Data Freshness: fresh
Internal Evidence Freshness: recent

Recommended Favorite:
- Model: openrouter/moonshotai/kimi-k2.5
- Why it leads: strongest current balance of reviewability and price-performance for this task class
- Best fit task type: docs fleissarbeit
- Main tradeoff: not the absolute cheapest option in every market state
- Suggested next action: use this model for the next bounded OR candidate test for docs fleissarbeit

Alternatives:
1. Model: openrouter/qwen/qwen3-coder-30b-a3b-instruct
   Why it stays viable: still competitive when low-cost pressure is higher and structure demands remain moderate
   Best fit task type: docs fleissarbeit
   Main tradeoff: weaker preferred-first signal than the favorite
2. Model: none
   Why it stays viable: no third candidate cleared the current shortlist threshold
   Best fit task type: n/a
   Main tradeoff: n/a

Decision Notes:
- Price-performance signal: favorable for the favorite
- Benchmark/ranking signal: supportive but not decisive alone
- Internal evidence signal: stronger than generic benchmark noise
- Confidence level: medium

Approval Boundary:
- This is a recommendation only.
- Codex/operator approval is required before any real OR candidate test continues.
```

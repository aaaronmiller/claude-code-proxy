---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, browser-extension, multi-model, aggregator, workflow, fan-out]
---

# F17: Web Browser Multi-Model Aggregator

> STATUS v1.1: MISSING (idea sketch only). Lowest priority; slot after the core lands (roadmap
> W12). In-scope per the no-silent-deferral rule.

Scope: a browser extension plus local site that broadcasts one query to multiple LLM web UIs,
scrapes each result, and sends them to an aggregator model for synthesis. Lowest maturity of all
modules (idea sketch), but in-scope per the "no silent deferral" rule. Distinct from the gateway:
it drives web UIs by DOM automation to avoid API cost, rather than calling APIs.

## Design

- Query distributor: one input fanned to several LLM site tabs (radio-selected targets),
  auto-submit. (`web browser plugin - multi model question distributor and aggregator.md:2`)
- Result scraper: click copy per tab, collect outputs via DOM automation. (`:2`)
- Aggregator step: send collected outputs to a known-good model (API, structured output) for
  synthesis; render in a companion local website. (`:2`)
- Workflow primitives: loop / branch / sequence / transform / judge, with per-step custom prompt
  injection. (`:4`)
- Composition model: LLM sites = atoms, joined into molecules then elements; non-LLM atoms
  possible. (`:4`)

## Hard requirements

- Result scraper and aggregator and local display are the three required pieces of the MVP.

## Status and open questions

- Earliest-stage idea: open questions on difficulty, whether it already exists, and
  differentiation vs n8n / Zapier / workflow builders. (`:7-21`)
- Sequencing: slot into Phase D or E; does not block the gateway core.

## Dependencies

- Can reuse the aggregator-model call path through the gateway (F01/F04). Otherwise independent.

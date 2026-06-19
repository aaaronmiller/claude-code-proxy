"""
Free-model ranking alignment tests.

Compares:
1. Deterministic programmatic ranking (free_model_rankings.py)
2. A stronger "deep-analysis" heuristic scorer
3. Optional LLM+search ranking (when API keys are configured)
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List

import pytest

from src.services.models.free_model_rankings import build_free_model_rankings
from src.services.models.model_ranker import rank_models_with_llm
from src.services.models.openrouter_fetcher import get_models, refresh_openrouter_models_sync


REPORT_PATH = Path("tests/integration/ranking_alignment_report.json")


def _deep_analysis_score(model: Dict) -> float:
    """
    Heavier coding-focused score used as a reference baseline.
    """
    model_id = (model.get("id") or "").lower()
    ctx = int(model.get("context_length", 0) or 0)
    out = int(model.get("max_completion_tokens", 0) or 0)
    tools = bool(model.get("supports_tools", False))
    reasoning = bool(model.get("supports_reasoning", False))
    structured = bool(model.get("supports_structured_output", False))
    created = int(model.get("created", 0) or 0)

    score = 0.0
    score += 30.0 if tools else 0.0
    score += 20.0 if reasoning else 0.0
    score += 8.0 if structured else 0.0

    # Context and output capacity.
    score += min(22.0, (ctx / 256_000.0) * 22.0)
    score += min(14.0, (out / 65_536.0) * 14.0)

    # Recency bonus (crude).
    if created > 0:
        # Epoch 2025-01-01 ~= 1735689600
        score += 6.0 if created >= 1735689600 else 2.0

    # Family priors from repeated coding benchmark trends.
    priors = {
        "qwen": 7.0,
        "deepseek": 7.0,
        "kimi": 6.0,
        "glm": 5.0,
        "llama": 3.5,
        "mistral": 3.0,
    }
    for token, bonus in priors.items():
        if token in model_id:
            score += bonus
            break

    return round(score, 3)


def _top_ids_from_programmatic(models: List[Dict], n: int = 10) -> List[str]:
    rankings = build_free_model_rankings(models=models)
    return [r.model_id for r in rankings[:n]]


def _top_ids_from_deep_analysis(models: List[Dict], n: int = 10) -> List[str]:
    free_models = [m for m in models if m.get("pricing", {}).get("is_free", False)]
    scored = sorted(
        free_models,
        key=lambda m: (_deep_analysis_score(m), int(m.get("context_length", 0) or 0)),
        reverse=True,
    )
    return [m.get("id", "") for m in scored[:n]]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def _write_report(payload: Dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_programmatic_ranking_matches_deep_analysis_baseline():
    if os.getenv("LIVE_OPENROUTER_MODELS", "false").lower() == "true":
        refresh_openrouter_models_sync(force=True, ttl_hours=0)

    models = get_models()
    if not models:
        pytest.skip("No cached OpenRouter models available for ranking alignment test")

    programmatic_top = _top_ids_from_programmatic(models, n=12)
    deep_top = _top_ids_from_deep_analysis(models, n=12)
    overlap = _jaccard(programmatic_top, deep_top)

    _write_report(
        {
            "programmatic_top": programmatic_top,
            "deep_analysis_top": deep_top,
            "jaccard_top12": overlap,
        }
    )

    # Target: substantial overlap with stronger baseline.
    assert overlap >= 0.35, (
        f"Ranking overlap too low ({overlap:.3f}). "
        f"See {REPORT_PATH} for mismatch details."
    )


@pytest.mark.skipif(
    os.getenv("RUN_LLM_RANKING_ALIGNMENT_TEST", "false").lower() != "true",
    reason="Set RUN_LLM_RANKING_ALIGNMENT_TEST=true to run live LLM ranking alignment",
)
def test_optional_llm_ranking_alignment():
    models = get_models()
    if not models:
        pytest.skip("No cached models available")

    free_models = [m for m in models if m.get("pricing", {}).get("is_free", False)]
    if len(free_models) < 6:
        pytest.skip("Not enough free models to evaluate")

    # Keep prompt size bounded for cost/stability.
    candidates = sorted(
        free_models,
        key=lambda m: (_deep_analysis_score(m), int(m.get("context_length", 0) or 0)),
        reverse=True,
    )[:20]

    llm_rankings = asyncio.run(rank_models_with_llm(candidates, use_web_search=bool(os.getenv("EXA_API_KEY"))))
    if not llm_rankings:
        pytest.skip("LLM ranking did not return results")

    llm_top = [r.model_id for r in llm_rankings[:10]]
    deep_top = [m.get("id", "") for m in candidates[:10]]
    overlap = _jaccard(llm_top, deep_top)

    _write_report(
        {
            "llm_top": llm_top,
            "deep_analysis_top_candidates": deep_top,
            "jaccard_top10_llm_vs_deep": overlap,
        }
    )

    assert overlap >= 0.25, (
        f"LLM ranking drift too large ({overlap:.3f}). "
        f"See {REPORT_PATH}."
    )

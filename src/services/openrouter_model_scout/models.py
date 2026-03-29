"""
Pydantic data models for OpenRouter Model Scout.
Defines Model, Leaderboard, Meta, and related schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


# === Nested Schemas ===

class IntelligenceMetrics(BaseModel):
    """Intelligence benchmark scores."""
    score: Optional[float] = Field(None, ge=0, le=100, description="Artificial Analysis Intelligence Index")
    percentile: Optional[float] = Field(None, ge=0, le=100, description="Percentile rank (0-100)")


class CodingMetrics(BaseModel):
    """Coding benchmark scores."""
    score: Optional[float] = Field(None, ge=0, le=100, description="Coding benchmark score")
    percentile: Optional[float] = Field(None, ge=0, le=100, description="Coding percentile (0-100)")


class AgenticMetrics(BaseModel):
    """Agentic benchmark scores."""
    score: Optional[float] = Field(None, ge=0, le=100, description="Agentic Index score")
    percentile: Optional[float] = Field(None, ge=0, le=100, description="Agentic percentile (0-100)")


class Pricing(BaseModel):
    """Pricing information per 1M tokens."""
    prompt: float = Field(..., ge=0, description="Input cost per 1M tokens ($)")
    completion: float = Field(..., ge=0, description="Output cost per 1M tokens ($)")
    cache_read: Optional[float] = Field(None, ge=0, description="Cache hit cost per 1M tokens ($)")
    cache_write: Optional[float] = Field(None, ge=0, description="Cache write cost per 1M tokens ($)")
    cache_creation: Optional[float] = Field(None, ge=0, description="Cache write cost (alternative API field name)")
    web_search: Optional[float] = Field(None, ge=0, description="Cost per 1K web search calls ($)")

    @model_validator(mode='after')
    def normalize_cache_fields(self) -> 'Pricing':
        """Normalize cache_creation to cache_write if present."""
        if self.cache_creation is not None and self.cache_write is None:
            self.cache_write = self.cache_creation
        return self


class Performance(BaseModel):
    """Performance metrics from provider."""
    throughput_tps: Optional[float] = Field(None, gt=0, description="Tokens per second")
    latency_seconds: Optional[float] = Field(None, gt=0, description="Time to first token")
    e2e_latency_seconds: Optional[float] = Field(None, gt=0, description="End-to-end generation latency")
    tool_error_rate: Optional[float] = Field(None, ge=0, le=100, description="Tool call failure percentage")
    uptime_percent: Optional[float] = Field(None, ge=0, le=100, description="Provider uptime percentage")


class Benchmarks(BaseModel):
    """Benchmark scores from Artificial Analysis."""
    intelligence: Optional[IntelligenceMetrics] = Field(None, description="Intelligence benchmark metrics")
    coding: Optional[CodingMetrics] = Field(None, description="Coding benchmark metrics")
    agentic: Optional[AgenticMetrics] = Field(None, description="Agentic benchmark metrics")

    # Detailed benchmarks (all optional, flat at this level)
    gpqa_diamond: Optional[float] = Field(None, ge=0, le=100)
    hle: Optional[float] = Field(None, ge=0, le=100)
    ifbench: Optional[float] = Field(None, ge=0, le=100)
    aa_lcr: Optional[float] = Field(None, ge=0, le=100)
    gdpval_aa: Optional[float] = Field(None, ge=0, le=100)
    critpt: Optional[float] = Field(None, ge=0, le=100)
    scicode: Optional[float] = Field(None, ge=0, le=100)
    terminal_bench: Optional[float] = Field(None, ge=0, le=100)
    omniscience_accuracy: Optional[float] = Field(None, ge=0, le=100)
    omniscience_hallucination: Optional[float] = Field(None, ge=0, le=100)

    @property
    def intelligence_score(self) -> Optional[float]:
        """Convenience accessor for intelligence score."""
        return self.intelligence.score if self.intelligence else None

    @property
    def intelligence_percentile(self) -> Optional[float]:
        """Convenience accessor for intelligence percentile."""
        return self.intelligence.percentile if self.intelligence else None

    @property
    def coding_score(self) -> Optional[float]:
        """Convenience accessor for coding score."""
        return self.coding.score if self.coding else None

    @property
    def coding_percentile(self) -> Optional[float]:
        """Convenience accessor for coding percentile."""
        return self.coding.percentile if self.coding else None

    @property
    def agentic_score(self) -> Optional[float]:
        """Convenience accessor for agentic score."""
        return self.agentic.score if self.agentic else None

    @property
    def agentic_percentile(self) -> Optional[float]:
        """Convenience accessor for agentic percentile."""
        return self.agentic.percentile if self.agentic else None


# === Core Entity ===

class Model(BaseModel):
    """AI model available through OpenRouter."""
    id: str = Field(..., description="Unique model identifier (format: 'provider/model-name')")
    name: str = Field(..., description="Display name")
    organization: Optional[str] = Field(None, description="Provider parsed from ID")
    description_short: Optional[str] = Field(None, description="First 2 sentences of overview")
    description_full: Optional[str] = Field(None, description="Full 'Overview' section text")
    release_date: Optional[str] = Field(None, description="Release date (ISO 8601)")
    parameter_size: Optional[str] = Field(None, description="Model size (e.g., 'Unknown', '70B')")

    # Context & Constraints
    context_length: int = Field(..., gt=0, description="Maximum context window size in tokens")
    max_output_tokens: Optional[int] = Field(None, gt=0, description="Maximum generation tokens")
    supports_vision: bool = Field(False, description="Image input capability")
    supports_tools: bool = Field(False, description="Function calling support")
    supports_caching: bool = Field(False, description="Prompt caching availability")
    quantization: Optional[str] = Field(None, description="Quantization level")

    # Nested objects
    pricing: Pricing = Field(..., description="Pricing information")
    performance: Optional[Performance] = Field(None, description="Performance metrics")
    benchmarks: Optional[Benchmarks] = Field(None, description="Benchmark scores")

    @model_validator(mode='after')
    def set_organization(self) -> 'Model':
        """Derive organization from model ID if not provided."""
        if self.organization is None and '/' in self.id:
            self.organization = self.id.split('/')[0]
        return self

    @property
    def is_free(self) -> bool:
        """Derived field: True if both prompt and completion are $0."""
        return (
            self.pricing.prompt == 0 and
            self.pricing.completion == 0
        )

    @property
    def value_score(self) -> float:
        """Derived field: intelligence score divided by prompt cost."""
        if self.benchmarks and self.benchmarks.intelligence_score is not None:
            cost = max(self.pricing.prompt, 0.000001)  # prevent division by zero
            return self.benchmarks.intelligence_score / cost
        return 0.0

    @property
    def effective_price_input(self) -> float:
        """Placeholder: would be computed as weighted average across providers."""
        # For now, just return the model's own pricing
        return self.pricing.prompt

    @property
    def effective_price_output(self) -> float:
        """Placeholder: would be computed as weighted average across providers."""
        return self.pricing.completion


# === Leaderboard Entries ===

class SmartestEntry(BaseModel):
    """Entry in the smartest models leaderboard."""
    id: str
    name: str
    intelligence_score: float = Field(..., ge=0, le=100)
    percentile: float = Field(..., ge=0, le=100)
    price_per_1m: float = Field(..., ge=0)


class CodingEntry(BaseModel):
    """Entry in the coding models leaderboard."""
    id: str
    name: str
    coding_score: float = Field(..., ge=0, le=100)
    agentic_score: float = Field(..., ge=0, le=100)
    price_per_1m: float = Field(..., ge=0)


class FreeEntry(BaseModel):
    """Entry in the free models leaderboard."""
    id: str
    name: str
    intelligence_score: float = Field(..., ge=0, le=100)
    context_length: int = Field(..., gt=0)
    throughput_tps: Optional[float] = Field(None, gt=0)


class ValueEntry(BaseModel):
    """Entry in the value models leaderboard."""
    id: str
    name: str
    value_score: float = Field(..., ge=0)
    price_per_1m: float = Field(..., ge=0)
    intelligence_percentile: float = Field(..., ge=0, le=100)


# === Leaderboard ===

class Leaderboard(BaseModel):
    """Top-5 lists generated from model database."""
    generated_at: str = Field(..., description="ISO 8601 timestamp when leaderboard was generated")
    smartest: List[SmartestEntry] = Field(default_factory=list, description="Top 5 by intelligence")
    coding: List[CodingEntry] = Field(default_factory=list, description="Top 5 by coding score")
    free: List[FreeEntry] = Field(default_factory=list, description="Top 5 free models")
    value: List[ValueEntry] = Field(default_factory=list, description="Top 5 value (intelligence/cost)")


# === Meta & Run History ===

class RunHistoryEntry(BaseModel):
    """Single run record in meta.json."""
    timestamp: str = Field(..., description="ISO 8601 timestamp when run started")
    mode: str = Field(..., description="Run mode: 'full', 'fast', 'force', etc.")
    api_sync_duration_seconds: float = Field(..., ge=0, description="Duration of API sync phase")
    scrape_duration_seconds: float = Field(..., ge=0, description="Duration of deep scrape phase")
    models_count: int = Field(..., ge=0, description="Number of models processed")
    token_usage: Dict[str, Any] = Field(..., description="Token counts and cost estimate")


class Meta(BaseModel):
    """Operational metadata."""
    last_run: str = Field(..., description="ISO 8601 timestamp of last successful run")
    last_deep_audit: str = Field(..., description="ISO 8601 timestamp of last deep scrape")
    run_history: List[RunHistoryEntry] = Field(default_factory=list, description="Historical run records")

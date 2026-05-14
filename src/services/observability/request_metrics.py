"""Per-attempt request telemetry with assignment and model dimensions.

Extends the existing src/services/usage/usage_tracker.py schema with:
- request_id (shared across cascade attempts)
- attempt_index (0=primary, 1+=fallback)
- resolved_assignment_id
- incoming_identifier
- resolved_model

Enables independent per-assignment and per-model success-rate queries (FR-031, FR-033, SC-009, SC-010).
Implementation lands in Phase 7 (tasks T072, T073).
"""

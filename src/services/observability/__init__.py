"""Configuration audit logging and per-assignment request telemetry.

- audit_log: append-only record of successful config writes (FR-030, logs/config-audit.log)
- request_metrics: per-attempt routing telemetry with assignment/model dimensions (FR-031, FR-033)

See specs/001-unified-config-system/data-model.md#auditlogentry and #requestmetric.
"""

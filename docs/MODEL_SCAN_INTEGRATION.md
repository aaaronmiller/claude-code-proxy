---
date: 2026-06-02 00:00:00 America/Los_Angeles
ver: 1.0.0
author: codex
model: gpt-5-codex
tags: [model-scan, routing, launcher, lanes, quota, reliability, observability]
---
# Model-Scan Integration

The proxy consumes model-scan through one credential-free contract:
`routing_snapshot.json`. Model-scan owns measurement and scoring; the proxy owns live routing,
credentials, cascades, sessions, and logging.

## Producer

Run model-scan independently:

```bash
cd /home/cheta/code/model-scan
model-scan --emit-snapshot
python3 gateway.py 7099
```

Default snapshot path:

```text
~/.config/model-scan/routing_snapshot.json
```

Gateway endpoints used by the proxy:

```text
GET  /routing-snapshot
POST /reliability
```

## Consumer

Enable the router in `config/proxy_chain.json`:

```json
"model_scan": {
  "enabled": true,
  "policy": "free",
  "snapshot_path": "~/.config/model-scan/routing_snapshot.json",
  "gateway_url": "http://127.0.0.1:7099/routing-snapshot",
  "cache_ttl_s": 300,
  "staleness_limit_s": 86400,
  "lanes": {
    "interactive": {"allow_paid": true},
    "standby": {"allow_paid": false}
  }
}
```

Reload without restarting:

```bash
curl -X POST http://127.0.0.1:8082/api/proxy/reload-models
```

Invalid, missing, or stale snapshots leave the current static routing in place.

## Profiles And Launcher

Profiles declare `slot_bindings` that map proxy assignments to model-scan roles:

```json
"slot_bindings": {
  "big": "R1_primary",
  "middle": "R8_web_extract",
  "small": "R8_web_extract"
}
```

`scripts/ccp-launch.sh` creates a temporary routing profile, runs a tool through `/p/{session}/v1`,
and deletes the profile on exit:

```bash
ccp codex --preset codex --role R1_primary
ccp hermes --preset hermes --provider openrouter
ccp errors --follow --provider openrouter
```

`scripts/install-aliases.sh` installs `ccp`, plus `ante` and `antigravity` aliases.

## Quota And Rotation

Quota samples normalize through `src/core/quota_sources.py` with precedence:

```text
tokscale > ccusage > model_scan_quota > billing > rate_limiter > usage_tracker
```

`src/core/rotation.py` handles free floor fallback, cooldown, drained-provider avoidance, and standby
lane protection. The `standby` lane never selects paid quota.

## Observability

Standard Python logs include `session=<profile-id>`. Structured errors append to:

```text
~/.ccp/errors.jsonl
```

Dashboard summary:

```bash
curl http://127.0.0.1:8082/api/model-scan/dashboard
```

That response includes active model-scan provenance, RTK compression stats, and recent unified errors.

Reliability feedback is aggregated from `usage_tracking.db` and posted to model-scan on an interval.
Model-scan persists it and degrades provider health in future snapshots when error or rate-limit
rates are high.

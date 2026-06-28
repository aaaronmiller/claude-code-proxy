# Activating the F18 quota-aware allocator

The allocator is built, integrated, and live-verified, but **off by default** (decision O8: off
until validated). Turning it on is a config-only change to `config/proxy_chain.json` — no code
change. While off, routing is unchanged.

## What it does when on

For each configured session profile + role it picks a model from the model-scan snapshot under the
live quota meters, using a **satisfice-then-maximize** rule:

- `value_sensitivity` high (maximize): take the highest-fitness affordable model.
- `value_sensitivity` low (satisfice): take the most abundant floor-clearing model, preserving
  scarce smart capacity for the maximizing roles.

Picks are written to the per-profile overlay the request path already reads (no registry writes).
Live verified end-to-end: maximizing Hermes primaries -> cerebras gpt-oss-120b; satisficing
pi-economy -> deepseek-v4-flash:free, under real Groq/Cerebras quota.

## How to turn it on

In `config/proxy_chain.json`, under `model_scan`, set `allocator_enabled: true` and add a
`session_profiles` map. It stays a safe no-op until BOTH are set.

```jsonc
"model_scan": {
  "enabled": true,
  "allocator_enabled": true,
  "snapshot_path": "~/.config/model-scan/routing_snapshot.json",
  "policy": "rotate",
  "quota_nominal_calls": 1000,
  "session_profiles": {
    "hermes-full": {
      "roles": {
        "primary":     {"floor": {"needs_tools": true, "min_value": "gpt-oss-120b"}, "value_sensitivity": 1.0, "importance": 1.0, "fallback_depth": 5},
        "delegation":  {"floor": {"needs_tools": true}, "value_sensitivity": 0.8, "importance": 0.9},
        "aux":         {"floor": {"min_value": "gpt-oss-120b"}, "value_sensitivity": 0.05, "count": 10},
        "vision":      {"floor": {"needs_vision": true}, "value_sensitivity": 0.5},
        "compression": {"floor": {"min_ctx": 200000}, "value_sensitivity": 0.3}
      }
    },
    "cc-standard": {
      "roles": {
        "big":    {"floor": {"min_value": "gpt-oss-120b"}, "value_sensitivity": 0.9, "importance": 0.8},
        "middle": {"floor": {"min_value": "gpt-oss-120b"}, "value_sensitivity": 0.4},
        "small":  {"floor": {"min_value": "gpt-oss-120b"}, "value_sensitivity": 0.1}
      }
    },
    "pi-premium": {
      "roles": {
        "primary":  {"floor": {"needs_tools": true}, "value_sensitivity": 0.9, "importance": 0.8},
        "toolcall": {"floor": {"needs_tools": true, "min_value": "gpt-oss-120b"}, "value_sensitivity": 0.4}
      }
    },
    "pi-economy": {
      "roles": {
        "primary":  {"floor": {"needs_tools": true, "min_value": "deepseek-v4-flash"}, "value_sensitivity": 0.1, "importance": 0.3},
        "toolcall": {"floor": {"needs_tools": true, "min_value": "gpt-oss-120b"}, "value_sensitivity": 0.1}
      }
    }
  }
}
```

Field meanings (per role):
- `floor.min_value`: a number OR a model NAME; a name resolves to that model's fitness in the
  snapshot (e.g. "gpt-oss-120b" gates at gpt-oss-120b's score). `needs_tools` / `needs_vision` /
  `min_ctx`: hard gates.
- `value_sensitivity`: 0 = satisfice (floor is enough), 1 = maximize (want the best).
- `importance`: priority when scarce capacity is contended (higher wins).
- `count`: expands one role into N (e.g. 10 aux roles aux-1..aux-10).

The snapshot slot a role draws from defaults to the role id; override with `allocator_slot_map`.

## Verify after enabling

Reload model-scan (`POST :8082/api/proxy/reload-models` or restart) and check the reload summary's
`allocator` report (profiles -> chosen model, tightest meters). With `allocator_enabled` off again,
behavior reverts immediately.

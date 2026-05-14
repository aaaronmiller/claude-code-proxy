# Quickstart — Unified Configuration & Multi-Surface Control System

**Feature**: 001-unified-config-system | **Phase**: 1 | **Audience**: proxy operators

Walkthrough covering each of the four user stories end-to-end. Run as a tutorial; each section is self-contained.

---

## Before you start

- Proxy is running (`proxies up`).
- Your shell has `$OPENROUTER_API_KEY` (or equivalent provider keys) exported.
- You are logged into the web UI as a user with the **admin** role (any authenticated user can *read* config; only admins can *write* — FR-026/FR-027).
- `git branch --show-current` returns `001-unified-config-system`.

---

## Story 1 — Route any model to any tier or slot from any surface

Goal: set `think` slot to `openai/o1-preview`, verify the change in the web UI, and confirm it is used on the next request.

**Via `.env`** (editor of choice):
```
ROUTER_THINK_MODEL=openai/o1-preview
ROUTER_THINK_PROVIDER=openai
ROUTER_THINK_API_KEY=${OPENAI_API_KEY}
```
Reload:
```
curl -X POST http://127.0.0.1:8082/api/config/reload -H "Authorization: Bearer $PROXY_ADMIN_TOKEN"
```

**Via CLI** (at startup or via `start_proxy.py` running in foreground — assignment writes flow into the CLI layer):
```
python start_proxy.py \
  --assign think model=openai/o1-preview provider=openai api_key='${OPENAI_API_KEY}'
```

**Via TUI**:
```
proxies chain   # opens the TUI
```
Navigate to Assignments → `think` → Enter. Edit `model`, `provider`, `api_key`. Save.

**Via web UI**:
Open `http://127.0.0.1:8082/web-ui/assignments`. Click the `think` row. Edit inline. Save.

**Verify propagation + provenance**:
```
curl http://127.0.0.1:8082/api/config/assignments.think.model
```
Response includes `{"value": "openai/o1-preview", "source_layer": "stored"}` (or whichever surface you used). This is SC-003 in action.

**Verify routing**: send a reasoning-heavy request through Claude Code; watch `/api/metrics/by-assignment` confirm the `think` slot served it.

---

## Story 2 — Reorder the proxy chain

Goal: change chain order from `[claude_code_proxy, headroom, rtk]` to `[rtk, headroom, claude_code_proxy]`, see it reflect everywhere.

**Via CLI**:
```
python start_proxy.py --chain-order rtk,headroom,claude_code_proxy
```

**Via TUI**: in `proxies chain`, navigate to Chain panel; up/down arrows move the selected entry. Ctrl-S saves.

**Via web UI**: drag-and-drop rows at `http://127.0.0.1:8082/web-ui/chain`.

**Via HTTP** (for scripting):
```
curl -X POST http://127.0.0.1:8082/api/chain/reorder \
  -H "Authorization: Bearer $PROXY_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order": ["rtk", "headroom", "claude_code_proxy"]}'
```

**Toggle an entry off without removing it**:
```
curl -X PATCH http://127.0.0.1:8082/api/chain/cliproxyapi \
  -H "Authorization: Bearer $PROXY_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

Check it appears disabled in TUI and web UI within 5 seconds (SC-008).

---

## Story 3 — Live-reload across surfaces without restart

Goal: prove that an edit from one surface reflects in others without restart, and that in-flight requests survive the change.

1. Open the web UI at `http://127.0.0.1:8082/web-ui/assignments` in one browser tab.
2. Open the TUI in another terminal: `proxies chain`.
3. Edit the `background` slot in the TUI. Save.
4. Watch the web UI: the new value appears within 2 seconds without reload (FR-022).
5. Start a long streaming request from Claude Code.
6. While it streams, edit the `big` tier model via web UI.
7. Watch the streaming request complete successfully against the *old* `big` model (FR-008, SC-006).
8. Start a new request — it uses the new model (SC-002).

**If the live-reload indicator goes amber** (web UI header badge), SSE disconnected. Reconnect is automatic with exponential backoff; click the refresh button in the header to force immediate reconnect.

---

## Story 4 — Debug with provenance

Goal: answer "where did this value come from?" for a specific field.

```
curl http://127.0.0.1:8082/api/config/assignments.big.model
```

Response:
```json
{
  "field_path": "assignments.big.model",
  "value": "nvidia/nemotron-70b-instruct",
  "raw_value": "nvidia/nemotron-70b-instruct",
  "source_layer": "cli"
}
```

The `source_layer` is the debugging unlock. If you expected `.env` to win but see `cli`, an overridden CLI flag is in play. If you see `default`, no layer configured the field.

In the web UI, every field displays a small badge showing its `source_layer`; click the badge for the raw value and the layer tooltip.

---

## Adding a new purpose slot (Hermes integration)

Goal: Hermes' `config.yaml` references a role `document_summarizer` that doesn't exist as a built-in slot. Make requests for this role route through the proxy.

1. Create the slot:
   ```
   curl -X POST http://127.0.0.1:8082/api/assignments \
     -H "Authorization: Bearer $PROXY_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "document_summarizer",
       "kind": "slot",
       "model": "anthropic/claude-haiku-4-5",
       "provider": "anthropic",
       "api_key": "${ANTHROPIC_API_KEY}",
       "enabled": true,
       "cascade": ["openai/gpt-4o-mini", "openrouter/nvidia/nemotron-70b-instruct"]
     }'
   ```
2. Map Hermes' incoming identifier to the slot:
   ```
   curl -X POST http://127.0.0.1:8082/api/identifier-mappings \
     -H "Authorization: Bearer $PROXY_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "incoming_identifier": "hermes.document_summarizer",
       "assignment_id": "document_summarizer",
       "enabled": true,
       "notes": "Routes Hermes summarizer role to Haiku with GPT/Nemotron fallbacks"
     }'
   ```
3. Send a request from Hermes. Confirm it routed through the new slot:
   ```
   curl "http://127.0.0.1:8082/api/metrics/by-assignment?since=$(date -u -d '1 hour ago' --iso-8601=seconds)"
   ```

The `document_summarizer` row shows attempts. If the primary model fails, cascade kicks in — the per-attempt `RequestMetric` rows let you see which fallback served the request (FR-033).

---

## Reverting

Revert an edit by removing the value from the winning layer — the next-highest layer's value (often the default) takes over.

Example: remove the CLI override by restarting without the flag. Remove a stored-layer value via the UI's "revert" action or:
```
curl -X PATCH http://127.0.0.1:8082/api/assignments/think \
  -H "Authorization: Bearer $PROXY_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": null}'
```
`null` signals "remove from stored layer"; the `.env` value (if any) becomes the resolved value. Check `/api/config/assignments.think.model` — `source_layer` should now be `dotenv`.

---

## Audit and analytics

- Successful writes: `GET /api/audit?principal=<you>&since=...` shows your recent edits.
- Rate pivots: `/api/metrics/by-assignment` and `/api/metrics/by-model` answer role-vs-model attribution questions (SC-009, SC-010).
- Disk locations: `logs/config-audit.log` (append-only); analytics in existing `usage_tracking.db`.

---

## Upgrading (auto-migration in action)

After a proxy upgrade, first start reads the existing `proxy_chain.json` and detects `schema_version=1`. The proxy:
1. Writes a backup: `proxy_chain.json.bak.YYYY-MM-DD-HHMMSS`.
2. Applies the migration chain (1 → 2 → ...).
3. Rewrites `proxy_chain.json` at the current version.
4. Writes a migration log: `config/migrations/2026-04-23-v1-to-v2.log`.
5. Starts normally.

If migration detects an unsafe transformation (FR-023c), startup halts with a message naming the problematic fields. Fix them in `proxy_chain.json`, restart.

---

## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| TUI shows old value after web-UI edit | SSE subscriber dropped | Check `/api/config/events` is reachable; restart TUI |
| Secret literal warning at startup | Someone committed an `api_key: "sk-..."` value | Replace with `"${VAR_NAME}"` reference |
| Request routed to wrong model | Check provenance: `GET /api/config/assignments.<tier>.model` | If `source_layer` surprises, an unexpected layer is winning |
| Deprecation warning summary on startup | Legacy env vars in use | Migrate to modern names per the summary; restart |

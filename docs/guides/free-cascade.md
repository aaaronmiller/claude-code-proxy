# Free Model Cascade + Selection History

This guide covers the new free-model workflow:
- Dynamic ranked free models (`stealth` vs `evergreen`)
- Model cascade fallback chains
- Model selection history

## TUI Workflow
Run:

```bash
python start_proxy.py --select-models
```

Inside the selector:
- `VIEW HISTORY`: shows recently selected models.
- `MANAGE FREE CASCADE`: builds or edits `BIG_CASCADE`, `MIDDLE_CASCADE`, `SMALL_CASCADE`.
- In model picker:
  - `a`: cycle `RECOMMENDED FREE` -> `RECOMMENDED` -> `ALL MODELS`
  - `h`: open selection history

## Web UI Workflow
In the **Models** tab:
- Enable `Model Cascade (Fallback)`
- Edit cascade chains per tier
- Use:
  - `Apply Free Cascade Template`
  - `Load Ranked Free Models`
  - `Load Selection History`

## Environment Variables
Existing cascade vars are used:

```env
MODEL_CASCADE=true
BIG_CASCADE=model-a,model-b,model-c
MIDDLE_CASCADE=model-d,model-e
SMALL_CASCADE=model-f,model-g
MODEL_CASCADE_DAILY_LIMIT=1000
```

## Runtime Behavior
- Streaming and non-streaming requests use cascade when enabled and tier-matched.
- Usage tracking logs UTC-day model request counts to help monitor limit pressure.
- Daily counters are UTC calendar-day based.
- Cascade events (retry/switch/success/exhausted) are emitted with reason codes.
- The Monitor tab shows cascade switches, success rate, and top fallback reasons.

## Forcing Cascade In Tests
- Set `MODEL_CASCADE_DAILY_LIMIT` to the provider/day threshold you want to enforce.
- Update `daily_model_stats.request_count` for the active UTC day and model in `usage_tracking.db`.
- When `request_count >= MODEL_CASCADE_DAILY_LIMIT`, the proxy preemptively skips that model and moves to the next cascade model.

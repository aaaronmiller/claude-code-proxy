# API Contract: Profiled Chat Completions

```
POST /p/{profile}/v1/chat/completions
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile` | string | Name of the profile to apply. Must be defined in `profiles/profiles.json`. |

### Request Body

Same shape as `POST /v1/chat/completions` (OpenAI-compatible).

### Response

Same shape as `POST /v1/chat/completions`.

### Errors

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Profile not defined in registry | `{"profile_requested": "<name>", "profiles_available": ["default", "pi", ...], "message": "Profile '<name>' is not defined. Edit profiles/profiles.json to add it."}` |

---

# API Contract: Profiled Messages (Anthropic)

```
POST /p/{profile}/v1/messages
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile` | string | Name of the profile to apply. Must be defined in `profiles/profiles.json`. |

### Request Body

Same shape as `POST /v1/messages` (Anthropic-compatible).

### Response

Same shape as `POST /v1/messages`.

### Errors

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Profile not defined in registry | Same structured error body as chat completions endpoint. |

---

# API Contract: Legacy Routes

```
POST /v1/chat/completions
POST /v1/messages
```

### Behavior

Identical to pre-existing behavior. Internally resolves the `default` profile. No reconfiguration required for existing clients.

# Text/Config File Audit: /home/cheta/code/claude-code-proxy/config/proxy_chain.json
**File Size:** 2212 bytes

## Content / Data Structure:
```text
{
  "entries": [
    {
      "id": "claude_code_proxy",
      "name": "Claude Code Proxy",
      "url": "http://127.0.0.1:8082/v1",
      "auth_key": "",
      "enabled": true,
      "order": 0,
      "service_cmd": "cd /home/cheta/code/claude-code-proxy && source .venv/bin/activate && LOG_LEVEL=info python start_proxy.py --skip-validation",
      "service_stop_cmd": "",
      "health_path": "/health",
      "port": 8082,
      "timeout": 90,
      "extra_headers": {},
      "type": "http",
      "model_prefixes": []
    },
    {
      "id": "headroom",
      "name": "Headroom Compression",
      "url": "http://127.0.0.1:8787/v1",
      "auth_key": "${OPENROUTER_API_KEY}",
      "enabled": true,
      "order": 1,
      "service_cmd": "headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry",
      "service_stop_cmd": "",
      "health_path": "/health",
      "port": 8787,
      "timeout": 90,
      "extra_headers": {},
      "type": "http",
      "model_prefixes": []
    },
    {
      "id": "rtk",
      "name": "RTK Terminal Compression",
      "url": "",
      "auth_key": "",
      "enabled": true,
      "order": 2,
      "service_cmd": "",
      "service_stop_cmd": "",
      "health_path": "/health",
      "port": 0,
      "timeout": 90,
      "extra_headers": {},
      "type": "cli_wrapper",
      "model_prefixes": []
    },
    {
      "id": "cliproxyapi",
      "name": "CLIProxyAPI (Antigravity)",
      "url": "http://127.0.0.1:8317/v1",
      "auth_key": "",
      "enabled": false,
      "order": 3,
      "service_cmd": "/home/cheta/code/cliproxyapi/cli-proxy-api-plus --config /home/cheta/code/cliproxyapi/config.yaml",
      "service_stop_cmd": "",
      "health_path": "/v1/models",
      "port": 8317,
      "timeout": 90,
      "extra_headers": {},
      "type": "http",
      "model_prefixes": []
    }
  ],
  "router": {
    "default": "",
    "background": "nvidia/nemotron-nano-9b-v2:free",
    "think": "",
    "long_context": "minimax/minimax-m2.5:free",
    "long_context_threshold": 60000,
    "web_search": "",
    "image": "qwen/qwen2.5-vl-72b-instruct",
    "custom_router_path": ""
  }
}
```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/data/model_usage.json
**File Size:** 8230 bytes

## Content / Data Structure:
```text
{
  "models": {
    "kwaipilot/kat-coder-pro:free": {
      "count": 1844,
      "last_used": "2025-11-16T06:46:46.030289",
      "first_used": "2025-11-16T00:59:54.796086"
    },
    "openai/gpt-5.1-codex": {
      "count": 724,
      "last_used": "2025-11-18T15:13:30.310808",
      "first_used": "2025-11-16T01:59:33.601547"
    },
    "minimax/minimax-m2": {
      "count": 1,
      "last_used": "2025-11-16T02:21:00.159430",
      "first_used": "2025-11-16T02:21:00.159424"
    },
    "openrouter/sherlock-dash-alpha": {
      "count": 498,
      "last_used": "2025-11-21T01:46:20.789551",
      "first_used": "2025-11-16T06:52:44.964381"
    },
    "openrouter/sherlock-think-alpha": {
      "count": 154,
      "last_used": "2025-11-21T01:46:20.794464",
      "first_used": "2025-11-16T23:36:18.596005"
    },
    "x-ai/grok-4.1-fast:free": {
      "count": 385,
      "last_used": "2025-12-20T19:36:23.614293",
      "first_used": "2025-11-21T01:50:55.211766"
    },
    "openai/gpt-4o": {
      "count": 67,
      "last_used": "2025-11-21T04:28:15.890059",
      "first_used": "2025-11-21T03:19:22.434574"
    },
    "openai/gpt-4o-mini": {
      "count": 53,
      "last_used": "2026-03-18T22:39:10.838991",
      "first_used": "2025-11-21T04:25:52.603387"
    },
    "claude-opus-4-5-thinking": {
      "count": 20,
      "last_used": "2025-12-20T19:38:40.251607",
      "first_used": "2025-12-20T19:37:56.213181"
    },
    "gemini-3-pro": {
      "count": 87,
      "last_used": "2026-02-11T16:06:09.605922",
      "first_used": "2025-12-20T19:39:11.394405"
    },
    "cgemini-3-pro": {
      "count": 7,
      "last_used": "2025-12-20T19:39:39.395961",
      "first_used": "2025-12-20T19:39:14.736082"
    },
    "o4-mini": {
      "count": 14,
      "last_used": "2026-01-05T17:14:20.358258",
      "first_used": "2025-12-20T20:13:07.456302"
    },
    "gpt-4": {
      "count": 14,
      "last_used": "2026-01-05T17:14:20.359077",
      "first_used": "2025-12-20T20:13:07.477877"
    },
    "gpt-4o": {
      "count": 26,
      "last_used": "2026-03-29T15:09:54.734140",
      "first_used": "2025-12-20T20:24:27.485645"
    },
    "gemini-3-flash": {
      "count": 1576,
      "last_used": "2026-04-08T00:10:40.101970",
      "first_used": "2025-12-20T23:06:35.745032"
    },
    "gemini-3-pro-preview": {
      "count": 586,
      "last_used": "2026-01-04T15:50:38.101253",
      "first_used": "2025-12-20T23:06:35.747146"
    },
    "gemini-claude-opus-4-5-thinking": {
      "count": 2048,
      "last_used": "2026-02-12T07:59:12.653534",
      "first_used": "2025-12-21T05:01:06.515376"
    },
    "gemini-claude-sonnet-4-5-thinking": {
      "count": 12,
      "last_used": "2025-12-24T20:41:22.447313",
      "first_used": "2025-12-24T20:40:40.708733"
    },
    "gemini-2.5-flash": {
      "count": 1,
      "last_used": "2025-12-29T20:23:25.546216",
      "first_used": "2025-12-29T20:23:25.546208"
    },
    "openrouter/oss-120": {
      "count": 8,
      "last_used": "2025-12-29T22:37:27.144447",
      "first_used": "2025-12-29T22:34:21.601750"
    },
    "gemini/gemini-2.0-flash-exp": {
      "count": 8,
      "last_used": "2025-12-29T22:37:27.198486",
      "first_used": "2025-12-29T22:34:21.665366"
    },
    "gpt-oss-120b-medium": {
      "count": 17,
      "last_used": "2025-12-29T22:45:35.384008",
      "first_used": "2025-12-29T22:41:15.011050"
    },
    "xiaomi/mimo-v2-flash:free": {
      "count": 1326,
      "last_used": "2026-01-06T00:24:39.919800",
      "first_used": "2025-12-31T11:12:19.142227"
    },
    "xiaomi/mimo-v2-flash": {
      "count": 10,
      "last_used": "2026-01-03T07:17:39.852276",
      "first_used": "2026-01-02T22:25:04.149431"
    },
    "moonshotai/kimi-k2": {
      "count": 4,
      "last_used": "2026-01-02T22:26:28.250878",
      "first_used": "2026-01-02T22:26:28.214776"
    },
    "google/gemini-3-flash-preview": {
      "count": 2,
      "last_used": "2026-01-03T03:02:32.566316",
      "first_used": "2026-01-03T03:02:29.494102"
    },
    "meta-llama/llama-3.1-8b-instruct:free": {
      "count": 2,
      "last_used": "2026-01-03T07:52:03.793870",
      "first_used": "2026-01-03T07:52:00.572722"
    },
    "moonshotai/kimi-k2:free": {
      "count": 2,
      "last_used": "2026-01-03T07:52:08.251348",
      "first_used": "2026-01-03T07:52:05.006641"
    },
    "google/gemini-2.0-flash-exp:free": {
      "count": 56,
      "last_used": "2026-01-05T23:52:58.600431",
      "first_used": "2026-01-05T18:00:59.491215"
    },
    "openrouter/pony-alpha": {
      "count": 106,
      "last_used": "2026-02-11T06:51:39.309057",
      "first_used": "2026-02-10T09:37:55.712439"
    },
    "openrouter/gpt-oss-120b-medium": {
      "count": 24,
      "last_used": "2026-02-11T05:11:10.040269",
      "first_used": "2026-02-10T10:01:33.551277"
    },
    "openai/gpt-oss-120b:free": {
      "count": 939,
      "last_used": "2026-04-03T11:42:16.066256",
      "first_used": "2026-02-11T01:10:27.695552"
    },
    "openai/gpt-oss-120b": {
      "count": 111,
      "last_used": "2026-02-12T07:59:03.468065",
      "first_used": "2026-02-11T05:12:27.807309"
    },
    "gemini-claude-opus-4.5-thinking": {
      "count": 6,
      "last_used": "2026-02-11T16:16:50.281237",
      "first_used": "2026-02-11T16:13:43.996565"
    },
    "gemini-claude-opus-4.6-thinking": {
      "count": 1,
      "last_used": "2026-02-11T16:19:03.030667",
      "first_used": "2026-02-11T16:19:03.030615"
    },
    "gemini-claude-opus-4-6-thinking": {
      "count": 436,
      "last_used": "2026-02-28T10:52:22.105315",
      "first_used": "2026-02-12T03:19:21.047718"
    },
    "stepfun/step-3.5-flash:free": {
      "count": 1788,
      "last_used": "2026-04-03T11:42:13.697772",
      "first_used": "2026-02-13T15:58:15.833897"
    },
    "arcee-ai/trinity-large-preview:free": {
      "count": 2540,
      "last_used": "2026-03-16T16:05:26.171739",
      "first_used": "2026-02-13T16:58:44.333828"
    },
    "gemini-3.1-pro": {
      "count": 42,
      "last_used": "2026-02-28T02:55:21.273308",
      "first_used": "2026-02-23T04:08:14.774181"
    },
    "gemini-3.1-pro-high": {
      "count": 183,
      "last_used": "2026-04-08T00:02:35.987466",
      "first_used": "2026-03-04T11:47:33.608534"
    },
    "gemini-pro-3.1-high": {
      "count": 2,
      "last_used": "2026-03-05T22:20:36.478109",
      "first_used": "2026-03-05T22:20:34.718653"
    },
    "openrouter/hunter-alpha": {
      "count": 92,
      "last_used": "2026-03-16T08:20:38.483945",
      "first_used": "2026-03-13T14:15:28.677676"
    },
    "minimax/minimax-m2.5:free": {
      "count": 190,
      "last_used": "2026-04-18T19:02:48.350164",
      "first_used": "2026-03-16T08:49:53.060309"
    },
    "minimax/minimax-m2.7": {
      "count": 315,
      "last_used": "2026-04-02T17:02:49.832717",
      "first_used": "2026-03-29T07:29:40.023196"
    },
    "nvidia/nemotron-3-super-120b-a12b": {
      "count": 648,
      "last_used": "2026-04-16T03:06:36.977325",
      "first_used": "2026-03-29T15:13:13.235253"
    },
    "minimax-m2.7": {
      "count": 1,
      "last_used": "2026-04-02T14:47:32.846105",
      "first_used": "2026-04-02T14:47:32.846088"
    },
    "minimmax-m2.7": {
      "count": 1,
      "last_used": "2026-04-02T14:47:51.057370",
      "first_used": "2026-04-02T14:47:51.057359"
    },
    "gemini-3.1-flash-lite": {
      "count": 9,
      "last_used": "2026-04-12T00:01:28.234266",
      "first_used": "2026-04-03T22:41:25.625794"
    },
    "nvidia/nemotron-3-super-120b-a12b:free": {
      "count": 80,
      "last_used": "2026-04-18T19:02:37.302214",
      "first_used": "2026-04-12T07:53:25.135509"
    },
    "=nvidia/nemotron-3-super-120b-a12:free": {
      "count": 6,
      "last_used": "2026-04-14T20:01:45.373358",
      "first_used": "2026-04-14T20:01:22.940355"
    },
    "nvidia/nemotron-nano-9b-v2": {
      "count": 4,
      "last_used": "2026-04-14T21:47:55.558029",
      "first_used": "2026-04-14T21:23:10.939173"
    },
    "openrouter/elephant-alpha": {
      "count": 186,
      "last_used": "2026-04-18T19:16:35.158109",
      "first_used": "2026-04-16T11:03:19.709883"
    }
  },
  "last_updated": "2026-04-18T19:16:35.158118"
}
```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/data/openrouter_models.json
**File Size:** 477899 bytes

## Content / Data Structure:
```text
{
  "fetched_at": "2026-04-18T03:12:33.620507",
  "source": "https://openrouter.ai/api/v1/models",
  "stats": {
    "total": 343,
    "free": 29,
    "reasoning": 167,
    "vision": 147,
    "tools": 249,
    "by_provider": {
      "anthropic": 14,
      "openrouter": 4,
      "z-ai": 13,
      "google": 31,
      "qwen": 47,
      "arcee-ai": 7,
      "x-ai": 10,
      "kwaipilot": 1,
      "rekaai": 2,
      "xiaomi": 3,
      "minimax": 8,
      "openai": 62,
      "mistralai": 25,
      "nvidia": 10,
      "bytedance-seed": 4,
      "inception": 1,
      "liquid": 3,
      "aion-labs": 4,
      "stepfun": 1,
      "moonshotai": 4,
      "upstage": 1,
      "writer": 1,
      "allenai": 2,
      "relace": 2,
      "nex-agi": 1,
      "essentialai": 1,
      "amazon": 5,
      "deepseek": 11,
      "prime-intellect": 1,
      "deepcogito": 1,
      "perplexity": 5,
      "ibm-granite": 1,
      "baidu": 5,
      "thedrummer": 4,
      "alibaba": 1,
      "nousresearch": 6,
      "ai21": 1,
      "bytedance": 1,
      "switchpoint": 1,
      "cognitivecomputations": 1,
      "tencent": 1,
      "tngtech": 1,
      "morph": 2,
      "meta-llama": 14,
      "alfredpros": 1,
      "cohere": 4,
      "microsoft": 2,
      "sao10k": 5,
      "anthracite-org": 1,
      "inflection": 2,
      "alpindale": 1,
      "mancer": 1,
      "undi95": 1,
      "gryphe": 1
    }
  },
  "models": [
    {
      "id": "ai21/jamba-large-1.7",
      "name": "AI21: Jamba Large 1.7",
      "provider": "ai21",
      "canonical_slug": "ai21/jamba-large-1.7",
      "hugging_face_id": "ai21labs/AI21-Jamba-Large-1.7",
      "description": "Jamba Large 1.7 is the latest model in the Jamba open family, offering improvements in grounding, instruction-following, and overall efficiency. Built on a hybrid SSM-Transformer architecture with a 256K context...",
      "context_length": 256000,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 8.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1754669020
    },
    {
      "id": "aion-labs/aion-1.0",
      "name": "AionLabs: Aion-1.0",
      "provider": "aion-labs",
      "canonical_slug": "aion-labs/aion-1.0",
      "hugging_face_id": "",
      "description": "Aion-1.0 is a multi-model system designed for high performance across various tasks, including reasoning and coding. It is built on DeepSeek-R1, augmented with additional models and techniques such as Tree...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 4.0,
        "output_per_million": 8.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "temperature",
        "top_p"
      ],
      "created": 1738697557
    },
    {
      "id": "aion-labs/aion-1.0-mini",
      "name": "AionLabs: Aion-1.0-Mini",
      "provider": "aion-labs",
      "canonical_slug": "aion-labs/aion-1.0-mini",
      "hugging_face_id": "FuseAI/FuseO1-DeepSeekR1-QwQ-SkyT1-32B-Preview",
      "description": "Aion-1.0-Mini 32B parameter model is a distilled version of the DeepSeek-R1 model, designed for strong performance in reasoning domains such as mathematics, coding, and logic. It is a modified variant...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.7,
        "output_per_million": 1.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "temperature",
        "top_p"
      ],
      "created": 1738697107
    },
    {
      "id": "aion-labs/aion-2.0",
      "name": "AionLabs: Aion-2.0",
      "provider": "aion-labs",
      "canonical_slug": "aion-labs/aion-2.0-20260223",
      "hugging_face_id": null,
      "description": "Aion-2.0 is a variant of DeepSeek V3.2 optimized for immersive roleplaying and storytelling. It is particularly strong at introducing tension, crises, and conflict into stories, making narratives feel more engaging....",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.8,
        "output_per_million": 1.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "temperature",
        "top_p"
      ],
      "created": 1771881306
    },
    {
      "id": "aion-labs/aion-rp-llama-3.1-8b",
      "name": "AionLabs: Aion-RP 1.0 (8B)",
      "provider": "aion-labs",
      "canonical_slug": "aion-labs/aion-rp-llama-3.1-8b",
      "hugging_face_id": "",
      "description": "Aion-RP-Llama-3.1-8B ranks the highest in the character evaluation portion of the RPBench-Auto benchmark, a roleplaying-specific variant of Arena-Hard-Auto, where LLMs evaluate each other’s responses. It is a fine-tuned base model...",
      "context_length": 32768,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.8,
        "output_per_million": 1.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "temperature",
        "top_p"
      ],
      "created": 1738696718
    },
    {
      "id": "alfredpros/codellama-7b-instruct-solidity",
      "name": "AlfredPros: CodeLLaMa 7B Instruct Solidity",
      "provider": "alfredpros",
      "canonical_slug": "alfredpros/codellama-7b-instruct-solidity",
      "hugging_face_id": "AlfredPros/CodeLlama-7b-Instruct-Solidity",
      "description": "A finetuned 7 billion parameters Code LLaMA - Instruct model to generate Solidity smart contract using 4-bit QLoRA finetuning provided by PEFT library.",
      "context_length": 4096,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.8,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1744641874
    },
    {
      "id": "alibaba/tongyi-deepresearch-30b-a3b",
      "name": "Tongyi DeepResearch 30B A3B",
      "provider": "alibaba",
      "canonical_slug": "alibaba/tongyi-deepresearch-30b-a3b",
      "hugging_face_id": "Alibaba-NLP/Tongyi-DeepResearch-30B-A3B",
      "description": "Tongyi DeepResearch is an agentic large language model developed by Tongyi Lab, with 30 billion total parameters activating only 3 billion per token. It's optimized for long-horizon, deep information-seeking tasks...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.09,
        "output_per_million": 0.45,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1758210804
    },
    {
      "id": "allenai/olmo-3-32b-think",
      "name": "AllenAI: Olmo 3 32B Think",
      "provider": "allenai",
      "canonical_slug": "allenai/olmo-3-32b-think-20251121",
      "hugging_face_id": "allenai/Olmo-3-32B-Think",
      "description": "Olmo 3 32B Think is a large-scale, 32-billion-parameter model purpose-built for deep reasoning, complex logic chains and advanced instruction-following scenarios. Its capacity enables strong performance on demanding evaluation tasks and...",
      "context_length": 65536,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1763758276
    },
    {
      "id": "allenai/olmo-3.1-32b-instruct",
      "name": "AllenAI: Olmo 3.1 32B Instruct",
      "provider": "allenai",
      "canonical_slug": "allenai/olmo-3.1-32b-instruct-20251215",
      "hugging_face_id": "allenai/Olmo-3.1-32B-Instruct",
      "description": "Olmo 3.1 32B Instruct is a large-scale, 32-billion-parameter instruction-tuned language model engineered for high-performance conversational AI, multi-turn dialogue, and practical instruction following. As part of the Olmo 3.1 family, this...",
      "context_length": 65536,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1767728554
    },
    {
      "id": "alpindale/goliath-120b",
      "name": "Goliath 120B",
      "provider": "alpindale",
      "canonical_slug": "alpindale/goliath-120b",
      "hugging_face_id": "alpindale/goliath-120b",
      "description": "A large LLM created by combining two fine-tuned Llama 70B models into one 120B model. Combines Xwin and Euryale. Credits to - [@chargoddard](https://huggingface.co/chargoddard) for developing the framework used to merge...",
      "context_length": 6144,
      "max_completion_tokens": 1024,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama2",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.75,
        "output_per_million": 7.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_a",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1699574400
    },
    {
      "id": "amazon/nova-2-lite-v1",
      "name": "Amazon: Nova 2 Lite",
      "provider": "amazon",
      "canonical_slug": "amazon/nova-2-lite-v1",
      "hugging_face_id": "",
      "description": "Nova 2 Lite is a fast, cost-effective reasoning model for everyday workloads that can process text, images, and videos to generate text. Nova 2 Lite demonstrates standout capabilities in processing...",
      "context_length": 1000000,
      "max_completion_tokens": 65535,
      "modality": "text+image+file+video->text",
      "input_modalities": [
        "text",
        "image",
        "video",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Nova",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 2.5,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1764696672
    },
    {
      "id": "amazon/nova-lite-v1",
      "name": "Amazon: Nova Lite 1.0",
      "provider": "amazon",
      "canonical_slug": "amazon/nova-lite-v1",
      "hugging_face_id": "",
      "description": "Amazon Nova Lite 1.0 is a very low-cost multimodal model from Amazon that focused on fast processing of image, video, and text inputs to generate text output. Amazon Nova Lite...",
      "context_length": 300000,
      "max_completion_tokens": 5120,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Nova",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.06,
        "output_per_million": 0.24,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1733437363
    },
    {
      "id": "amazon/nova-micro-v1",
      "name": "Amazon: Nova Micro 1.0",
      "provider": "amazon",
      "canonical_slug": "amazon/nova-micro-v1",
      "hugging_face_id": "",
      "description": "Amazon Nova Micro 1.0 is a text-only model that delivers the lowest latency responses in the Amazon Nova family of models at a very low cost. With a context length...",
      "context_length": 128000,
      "max_completion_tokens": 5120,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Nova",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.035,
        "output_per_million": 0.14,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1733437237
    },
    {
      "id": "amazon/nova-premier-v1",
      "name": "Amazon: Nova Premier 1.0",
      "provider": "amazon",
      "canonical_slug": "amazon/nova-premier-v1",
      "hugging_face_id": "",
      "description": "Amazon Nova Premier is the most capable of Amazon’s multimodal models for complex reasoning tasks and for use as the best teacher for distilling custom models.",
      "context_length": 1000000,
      "max_completion_tokens": 32000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Nova",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 12.5,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1761950332
    },
    {
      "id": "amazon/nova-pro-v1",
      "name": "Amazon: Nova Pro 1.0",
      "provider": "amazon",
      "canonical_slug": "amazon/nova-pro-v1",
      "hugging_face_id": "",
      "description": "Amazon Nova Pro 1.0 is a capable multimodal model from Amazon focused on providing a combination of accuracy, speed, and cost for a wide range of tasks. As of December...",
      "context_length": 300000,
      "max_completion_tokens": 5120,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Nova",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.8,
        "output_per_million": 3.2,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1733436303
    },
    {
      "id": "anthracite-org/magnum-v4-72b",
      "name": "Magnum v4 72B",
      "provider": "anthracite-org",
      "canonical_slug": "anthracite-org/magnum-v4-72b",
      "hugging_face_id": "anthracite-org/magnum-v4-72b",
      "description": "This is a series of models designed to replicate the prose quality of the Claude 3 models, specifically Sonnet(https://openrouter.ai/anthropic/claude-3.5-sonnet) and Opus(https://openrouter.ai/anthropic/claude-3-opus).\n\nThe model is fine-tuned on top of [Qwen2.5 72B](https://openrouter.ai/qwen/qwen-2.5-72b-instruct).",
      "context_length": 16384,
      "max_completion_tokens": 2048,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 5.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_a",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1729555200
    },
    {
      "id": "anthropic/claude-3-haiku",
      "name": "Anthropic: Claude 3 Haiku",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-3-haiku",
      "hugging_face_id": null,
      "description": "Claude 3 Haiku is Anthropic's fastest and most compact model for\nnear-instant responsiveness. Quick and accurate targeted performance.\n\nSee the launch announcement and benchmark results [here](https://www.anthropic.com/news/claude-3-haiku)\n\n#multimodal",
      "context_length": 200000,
      "max_completion_tokens": 4096,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 1.25,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1710288000
    },
    {
      "id": "anthropic/claude-3.5-haiku",
      "name": "Anthropic: Claude 3.5 Haiku",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-3-5-haiku",
      "hugging_face_id": null,
      "description": "Claude 3.5 Haiku features offers enhanced capabilities in speed, coding accuracy, and tool use. Engineered to excel in real-time applications, it delivers quick response times that are essential for dynamic...",
      "context_length": 200000,
      "max_completion_tokens": 8192,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.8,
        "output_per_million": 4.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1730678400
    },
    {
      "id": "anthropic/claude-3.7-sonnet",
      "name": "Anthropic: Claude 3.7 Sonnet",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-3-7-sonnet-20250219",
      "hugging_face_id": "",
      "description": "Claude 3.7 Sonnet is an advanced large language model with improved reasoning, coding, and problem-solving capabilities. It introduces a hybrid reasoning approach, allowing users to choose between rapid responses and...",
      "context_length": 200000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1740422110
    },
    {
      "id": "anthropic/claude-3.7-sonnet:thinking",
      "name": "Anthropic: Claude 3.7 Sonnet (thinking)",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-3-7-sonnet-20250219",
      "hugging_face_id": "",
      "description": "Claude 3.7 Sonnet is an advanced large language model with improved reasoning, coding, and problem-solving capabilities. It introduces a hybrid reasoning approach, allowing users to choose between rapid responses and...",
      "context_length": 200000,
      "max_completion_tokens": 64000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1740422110
    },
    {
      "id": "anthropic/claude-haiku-4.5",
      "name": "Anthropic: Claude Haiku 4.5",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.5-haiku-20251001",
      "hugging_face_id": "",
      "description": "Claude Haiku 4.5 is Anthropic’s fastest and most efficient model, delivering near-frontier intelligence at a fraction of the cost and latency of larger Claude models. Matching Claude Sonnet 4’s performance...",
      "context_length": 200000,
      "max_completion_tokens": 64000,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.0,
        "output_per_million": 5.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1760547638
    },
    {
      "id": "anthropic/claude-opus-4",
      "name": "Anthropic: Claude Opus 4",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4-opus-20250522",
      "hugging_face_id": "",
      "description": "Claude Opus 4 is benchmarked as the world’s best coding model, at time of release, bringing sustained performance on complex, long-running tasks and agent workflows. It sets new benchmarks in...",
      "context_length": 200000,
      "max_completion_tokens": 32000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 15.0,
        "output_per_million": 75.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1747931245
    },
    {
      "id": "anthropic/claude-opus-4.1",
      "name": "Anthropic: Claude Opus 4.1",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.1-opus-20250805",
      "hugging_face_id": "",
      "description": "Claude Opus 4.1 is an updated version of Anthropic’s flagship model, offering improved performance in coding, reasoning, and agentic tasks. It achieves 74.5% on SWE-bench Verified and shows notable gains...",
      "context_length": 200000,
      "max_completion_tokens": 32000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 15.0,
        "output_per_million": 75.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1754411591
    },
    {
      "id": "anthropic/claude-opus-4.5",
      "name": "Anthropic: Claude Opus 4.5",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.5-opus-20251124",
      "hugging_face_id": "",
      "description": "Claude Opus 4.5 is Anthropic’s frontier reasoning model optimized for complex software engineering, agentic workflows, and long-horizon computer use. It offers strong multimodal capabilities, competitive performance across real-world coding and...",
      "context_length": 200000,
      "max_completion_tokens": 64000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 5.0,
        "output_per_million": 25.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "verbosity"
      ],
      "created": 1764010580
    },
    {
      "id": "anthropic/claude-opus-4.6",
      "name": "Anthropic: Claude Opus 4.6",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.6-opus-20260205",
      "hugging_face_id": "",
      "description": "Opus 4.6 is Anthropic’s strongest model for coding and long-running professional tasks. It is built for agents that operate across entire workflows rather than single prompts, making it especially effective...",
      "context_length": 1000000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 5.0,
        "output_per_million": 25.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p",
        "verbosity"
      ],
      "created": 1770219050
    },
    {
      "id": "anthropic/claude-opus-4.6-fast",
      "name": "Anthropic: Claude Opus 4.6 (Fast)",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.6-opus-fast-20260407",
      "hugging_face_id": null,
      "description": "Fast-mode variant of [Opus 4.6](/anthropic/claude-opus-4.6) - identical capabilities with higher output speed at premium 6x pricing.\n\nLearn more in Anthropic's docs: https://platform.claude.com/docs/en/build-with-claude/fast-mode",
      "context_length": 1000000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 30.0,
        "output_per_million": 150.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p",
        "verbosity"
      ],
      "created": 1775592472
    },
    {
      "id": "anthropic/claude-opus-4.7",
      "name": "Anthropic: Claude Opus 4.7",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.7-opus-20260416",
      "hugging_face_id": null,
      "description": "Opus 4.7 is the next generation of Anthropic's Opus family, built for long-running, asynchronous agents. Building on the coding and agentic strengths of Opus 4.6, it delivers stronger performance on...",
      "context_length": 1000000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 5.0,
        "output_per_million": 25.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "tool_choice",
        "tools",
        "verbosity"
      ],
      "created": 1776351100
    },
    {
      "id": "anthropic/claude-sonnet-4",
      "name": "Anthropic: Claude Sonnet 4",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4-sonnet-20250522",
      "hugging_face_id": "",
      "description": "Claude Sonnet 4 significantly enhances the capabilities of its predecessor, Sonnet 3.7, excelling in both coding and reasoning tasks with improved precision and controllability. Achieving state-of-the-art performance on SWE-bench (72.7%),...",
      "context_length": 1000000,
      "max_completion_tokens": 64000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1747930371
    },
    {
      "id": "anthropic/claude-sonnet-4.5",
      "name": "Anthropic: Claude Sonnet 4.5",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.5-sonnet-20250929",
      "hugging_face_id": "",
      "description": "Claude Sonnet 4.5 is Anthropic’s most advanced Sonnet model to date, optimized for real-world agents and coding workflows. It delivers state-of-the-art performance on coding benchmarks such as SWE-bench Verified, with...",
      "context_length": 1000000,
      "max_completion_tokens": 64000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1759161676
    },
    {
      "id": "anthropic/claude-sonnet-4.6",
      "name": "Anthropic: Claude Sonnet 4.6",
      "provider": "anthropic",
      "canonical_slug": "anthropic/claude-4.6-sonnet-20260217",
      "hugging_face_id": "",
      "description": "Sonnet 4.6 is Anthropic's most capable Sonnet-class model yet, with frontier performance across coding, agents, and professional work. It excels at iterative development, complex codebase navigation, end-to-end project management with...",
      "context_length": 1000000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Claude",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p",
        "verbosity"
      ],
      "created": 1771342990
    },
    {
      "id": "arcee-ai/coder-large",
      "name": "Arcee AI: Coder Large",
      "provider": "arcee-ai",
      "canonical_slug": "arcee-ai/coder-large",
      "hugging_face_id": "",
      "description": "Coder‑Large is a 32 B‑parameter offspring of Qwen 2.5‑Instruct that has been further trained on permissively‑licensed GitHub, CodeSearchNet and synthetic bug‑fix corpora. It supports a 32k context window, enabling multi‑file...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.5,
        "output_per_million": 0.8,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1746478663
    },
    {
      "id": "arcee-ai/maestro-reasoning",
      "name": "Arcee AI: Maestro Reasoning",
      "provider": "arcee-ai",
      "canonical_slug": "arcee-ai/maestro-reasoning",
      "hugging_face_id": "",
      "description": "Maestro Reasoning is Arcee's flagship analysis model: a 32 B‑parameter derivative of Qwen 2.5‑32 B tuned with DPO and chain‑of‑thought RL for step‑by‑step logic. Compared to the earlier 7 B...",
      "context_length": 131072,
      "max_completion_tokens": 32000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.9,
        "output_per_million": 3.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1746481269
    },
    {
      "id": "arcee-ai/spotlight",
      "name": "Arcee AI: Spotlight",
      "provider": "arcee-ai",
      "canonical_slug": "arcee-ai/spotlight",
      "hugging_face_id": "",
      "description": "Spotlight is a 7‑billion‑parameter vision‑language model derived from Qwen 2.5‑VL and fine‑tuned by Arcee AI for tight image‑text grounding tasks. It offers a 32 k‑token context window, enabling rich multimodal...",
      "context_length": 131072,
      "max_completion_tokens": 65537,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.18,
        "output_per_million": 0.18,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1746481552
    },
    {
      "id": "arcee-ai/trinity-large-preview:free",
      "name": "Arcee AI: Trinity Large Preview (free)",
      "provider": "arcee-ai",
      "canonical_slug": "arcee-ai/trinity-large-preview",
      "hugging_face_id": "arcee-ai/Trinity-Large-Preview",
      "description": "Trinity-Large-Preview is a frontier-scale open-weight language model from Arcee, built as a 400B-parameter sparse Mixture-of-Experts with 13B active parameters per token using 4-of-256 expert routing. It excels in creative writing,...",
      "context_length": 131000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "structured_outputs",
        "temperature",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1769552670
    },
    {
      "id": "arcee-ai/trinity-large-thinking",
      "name": "Arcee AI: Trinity Large Thinking",
      "provider": "arcee-ai",
      "canonical_slug": "arcee-ai/trinity-large-thinking",
      "hugging_face_id": "arcee-ai/Trinity-Large-Thinking",
      "description": "Trinity Large Thinking is a powerful open source reasoning model from the team at Arcee AI. It shows strong performance in PinchBench, agentic workloads, and reasoning tasks. Launch video: https://youtu.be/Gc82AXLa0Rg?si=4RLn6WBz33qT--B7",
      "context_length": 262144,
      "max_completion_tokens": 262144,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.22,
        "output_per_million": 0.85,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1775058318
    },
    {
      "id": "arcee-ai/trinity-mini",
      "name": "Arcee AI: Trinity Mini",
      "provider": "arcee-ai",
      "canonical_slug": "arcee-ai/trinity-mini-20251201",
      "hugging_face_id": "arcee-ai/Trinity-Mini",
      "description": "Trinity Mini is a 26B-parameter (3B active) sparse mixture-of-experts language model featuring 128 experts with 8 active per token. Engineered for efficient reasoning over long contexts (131k) with robust function...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.045,
        "output_per_million": 0.15,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1764601720
    },
    {
      "id": "arcee-ai/virtuoso-large",
      "name": "Arcee AI: Virtuoso Large",
      "provider": "arcee-ai",
      "canonical_slug": "arcee-ai/virtuoso-large",
      "hugging_face_id": "",
      "description": "Virtuoso‑Large is Arcee's top‑tier general‑purpose LLM at 72 B parameters, tuned to tackle cross‑domain reasoning, creative writing and enterprise QA. Unlike many 70 B peers, it retains the 128 k...",
      "context_length": 131072,
      "max_completion_tokens": 64000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.75,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1746478885
    },
    {
      "id": "baidu/ernie-4.5-21b-a3b",
      "name": "Baidu: ERNIE 4.5 21B A3B",
      "provider": "baidu",
      "canonical_slug": "baidu/ernie-4.5-21b-a3b",
      "hugging_face_id": "baidu/ERNIE-4.5-21B-A3B-PT",
      "description": "A sophisticated text-based Mixture-of-Experts (MoE) model featuring 21B total parameters with 3B activated per token, delivering exceptional multimodal understanding and generation through heterogeneous MoE structures and modality-isolated routing. Supporting an...",
      "context_length": 120000,
      "max_completion_tokens": 8000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.07,
        "output_per_million": 0.28,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1755034167
    },
    {
      "id": "baidu/ernie-4.5-21b-a3b-thinking",
      "name": "Baidu: ERNIE 4.5 21B A3B Thinking",
      "provider": "baidu",
      "canonical_slug": "baidu/ernie-4.5-21b-a3b-thinking",
      "hugging_face_id": "baidu/ERNIE-4.5-21B-A3B-Thinking",
      "description": "ERNIE-4.5-21B-A3B-Thinking is Baidu's upgraded lightweight MoE model, refined to boost reasoning depth and quality for top-tier performance in logical puzzles, math, science, coding, text generation, and expert-level academic benchmarks.",
      "context_length": 131072,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.07,
        "output_per_million": 0.28,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1760048887
    },
    {
      "id": "baidu/ernie-4.5-300b-a47b",
      "name": "Baidu: ERNIE 4.5 300B A47B ",
      "provider": "baidu",
      "canonical_slug": "baidu/ernie-4.5-300b-a47b",
      "hugging_face_id": "baidu/ERNIE-4.5-300B-A47B-PT",
      "description": "ERNIE-4.5-300B-A47B is a 300B parameter Mixture-of-Experts (MoE) language model developed by Baidu as part of the ERNIE 4.5 series. It activates 47B parameters per token and supports text generation in...",
      "context_length": 123000,
      "max_completion_tokens": 12000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.28,
        "output_per_million": 1.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1751300139
    },
    {
      "id": "baidu/ernie-4.5-vl-28b-a3b",
      "name": "Baidu: ERNIE 4.5 VL 28B A3B",
      "provider": "baidu",
      "canonical_slug": "baidu/ernie-4.5-vl-28b-a3b",
      "hugging_face_id": "baidu/ERNIE-4.5-VL-28B-A3B-PT",
      "description": "A powerful multimodal Mixture-of-Experts chat model featuring 28B total parameters with 3B activated per token, delivering exceptional text and vision understanding through its innovative heterogeneous MoE structure with modality-isolated routing....",
      "context_length": 30000,
      "max_completion_tokens": 8000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.14,
        "output_per_million": 0.56,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1755032836
    },
    {
      "id": "baidu/ernie-4.5-vl-424b-a47b",
      "name": "Baidu: ERNIE 4.5 VL 424B A47B ",
      "provider": "baidu",
      "canonical_slug": "baidu/ernie-4.5-vl-424b-a47b",
      "hugging_face_id": "baidu/ERNIE-4.5-VL-424B-A47B-PT",
      "description": "ERNIE-4.5-VL-424B-A47B is a multimodal Mixture-of-Experts (MoE) model from Baidu’s ERNIE 4.5 series, featuring 424B total parameters with 47B active per token. It is trained jointly on text and image data...",
      "context_length": 123000,
      "max_completion_tokens": 16000,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.42,
        "output_per_million": 1.25,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1751300903
    },
    {
      "id": "bytedance/ui-tars-1.5-7b",
      "name": "ByteDance: UI-TARS 7B ",
      "provider": "bytedance",
      "canonical_slug": "bytedance/ui-tars-1.5-7b",
      "hugging_face_id": "ByteDance-Seed/UI-TARS-1.5-7B",
      "description": "UI-TARS-1.5 is a multimodal vision-language agent optimized for GUI-based environments, including desktop interfaces, web browsers, mobile systems, and games. Built by ByteDance, it builds upon the UI-TARS framework with reinforcement...",
      "context_length": 128000,
      "max_completion_tokens": 2048,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1753205056
    },
    {
      "id": "bytedance-seed/seed-1.6",
      "name": "ByteDance Seed: Seed 1.6",
      "provider": "bytedance-seed",
      "canonical_slug": "bytedance-seed/seed-1.6-20250625",
      "hugging_face_id": "",
      "description": "Seed 1.6 is a general-purpose model released by the ByteDance Seed team. It incorporates multimodal capabilities and adaptive deep thinking with a 256K context window.",
      "context_length": 262144,
      "max_completion_tokens": 32768,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1766504997
    },
    {
      "id": "bytedance-seed/seed-1.6-flash",
      "name": "ByteDance Seed: Seed 1.6 Flash",
      "provider": "bytedance-seed",
      "canonical_slug": "bytedance-seed/seed-1.6-flash-20250625",
      "hugging_face_id": "",
      "description": "Seed 1.6 Flash is an ultra-fast multimodal deep thinking model by ByteDance Seed, supporting both text and visual understanding. It features a 256k context window and can generate outputs of...",
      "context_length": 262144,
      "max_completion_tokens": 32768,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.075,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1766505011
    },
    {
      "id": "bytedance-seed/seed-2.0-lite",
      "name": "ByteDance Seed: Seed-2.0-Lite",
      "provider": "bytedance-seed",
      "canonical_slug": "bytedance-seed/seed-2.0-lite-20260309",
      "hugging_face_id": null,
      "description": "Seed-2.0-Lite is a versatile, cost‑efficient enterprise workhorse that delivers strong multimodal and agent capabilities while offering noticeably lower latency, making it a practical default choice for most production workloads across...",
      "context_length": 262144,
      "max_completion_tokens": 131072,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1773157231
    },
    {
      "id": "bytedance-seed/seed-2.0-mini",
      "name": "ByteDance Seed: Seed-2.0-Mini",
      "provider": "bytedance-seed",
      "canonical_slug": "bytedance-seed/seed-2.0-mini-20260224",
      "hugging_face_id": "",
      "description": "Seed-2.0-mini targets latency-sensitive, high-concurrency, and cost-sensitive scenarios, emphasizing fast response and flexible inference deployment. It delivers performance comparable to ByteDance-Seed-1.6, supports 256k context, four reasoning effort modes (minimal/low/medium/high), multimodal understanding,...",
      "context_length": 262144,
      "max_completion_tokens": 131072,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1772131107
    },
    {
      "id": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
      "name": "Venice: Uncensored (free)",
      "provider": "cognitivecomputations",
      "canonical_slug": "venice/uncensored",
      "hugging_face_id": "cognitivecomputations/Dolphin-Mistral-24B-Venice-Edition",
      "description": "Venice Uncensored Dolphin Mistral 24B Venice Edition is a fine-tuned variant of Mistral-Small-24B-Instruct-2501, developed by dphn.ai in collaboration with Venice.ai. This model is designed as an “uncensored” instruct-tuned LLM, preserving...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1752094966
    },
    {
      "id": "cohere/command-a",
      "name": "Cohere: Command A",
      "provider": "cohere",
      "canonical_slug": "cohere/command-a-03-2025",
      "hugging_face_id": "CohereForAI/c4ai-command-a-03-2025",
      "description": "Command A is an open-weights 111B parameter model with a 256k context window focused on delivering great performance across agentic, multilingual, and coding use cases. Compared to other leading proprietary...",
      "context_length": 256000,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1741894342
    },
    {
      "id": "cohere/command-r-08-2024",
      "name": "Cohere: Command R (08-2024)",
      "provider": "cohere",
      "canonical_slug": "cohere/command-r-08-2024",
      "hugging_face_id": null,
      "description": "command-r-08-2024 is an update of the [Command R](/models/cohere/command-r) with improved performance for multilingual retrieval-augmented generation (RAG) and tool use. More broadly, it is better at math, code and reasoning and...",
      "context_length": 128000,
      "max_completion_tokens": 4000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Cohere",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1724976000
    },
    {
      "id": "cohere/command-r-plus-08-2024",
      "name": "Cohere: Command R+ (08-2024)",
      "provider": "cohere",
      "canonical_slug": "cohere/command-r-plus-08-2024",
      "hugging_face_id": null,
      "description": "command-r-plus-08-2024 is an update of the [Command R+](/models/cohere/command-r-plus) with roughly 50% higher throughput and 25% lower latencies as compared to the previous Command R+ version, while keeping the hardware footprint...",
      "context_length": 128000,
      "max_completion_tokens": 4000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Cohere",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1724976000
    },
    {
      "id": "cohere/command-r7b-12-2024",
      "name": "Cohere: Command R7B (12-2024)",
      "provider": "cohere",
      "canonical_slug": "cohere/command-r7b-12-2024",
      "hugging_face_id": "",
      "description": "Command R7B (12-2024) is a small, fast update of the Command R+ model, delivered in December 2024. It excels at RAG, tool use, agents, and similar tasks requiring complex reasoning...",
      "context_length": 128000,
      "max_completion_tokens": 4000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Cohere",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0375,
        "output_per_million": 0.15,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1734158152
    },
    {
      "id": "deepcogito/cogito-v2.1-671b",
      "name": "Deep Cogito: Cogito v2.1 671B",
      "provider": "deepcogito",
      "canonical_slug": "deepcogito/cogito-v2.1-671b-20251118",
      "hugging_face_id": "",
      "description": "Cogito v2.1 671B MoE represents one of the strongest open models globally, matching performance of frontier closed and open models. This model is trained using self play with reinforcement learning...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 1.25,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1763071233
    },
    {
      "id": "deepseek/deepseek-chat",
      "name": "DeepSeek: DeepSeek V3",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-chat-v3",
      "hugging_face_id": "deepseek-ai/DeepSeek-V3",
      "description": "DeepSeek-V3 is the latest model from the DeepSeek team, building upon the instruction following and coding abilities of the previous versions. Pre-trained on nearly 15 trillion tokens, the reported evaluations...",
      "context_length": 163840,
      "max_completion_tokens": 163840,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.32,
        "output_per_million": 0.89,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1735241320
    },
    {
      "id": "deepseek/deepseek-chat-v3-0324",
      "name": "DeepSeek: DeepSeek V3 0324",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-chat-v3-0324",
      "hugging_face_id": "deepseek-ai/DeepSeek-V3-0324",
      "description": "DeepSeek V3, a 685B-parameter, mixture-of-experts model, is the latest iteration of the flagship chat model family from the DeepSeek team. It succeeds the [DeepSeek V3](/deepseek/deepseek-chat-v3) model and performs really well...",
      "context_length": 163840,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.77,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1742824755
    },
    {
      "id": "deepseek/deepseek-chat-v3.1",
      "name": "DeepSeek: DeepSeek V3.1",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-chat-v3.1",
      "hugging_face_id": "deepseek-ai/DeepSeek-V3.1",
      "description": "DeepSeek-V3.1 is a large hybrid reasoning model (671B parameters, 37B active) that supports both thinking and non-thinking modes via prompt templates. It extends the DeepSeek-V3 base with a two-phase long-context...",
      "context_length": 32768,
      "max_completion_tokens": 7168,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.75,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1755779628
    },
    {
      "id": "deepseek/deepseek-v3.1-terminus",
      "name": "DeepSeek: DeepSeek V3.1 Terminus",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-v3.1-terminus",
      "hugging_face_id": "deepseek-ai/DeepSeek-V3.1-Terminus",
      "description": "DeepSeek-V3.1 Terminus is an update to [DeepSeek V3.1](/deepseek/deepseek-chat-v3.1) that maintains the model's original capabilities while addressing issues reported by users, including language consistency and agent capabilities, further optimizing the model's...",
      "context_length": 163840,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.21,
        "output_per_million": 0.79,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1758548275
    },
    {
      "id": "deepseek/deepseek-v3.2",
      "name": "DeepSeek: DeepSeek V3.2",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-v3.2-20251201",
      "hugging_face_id": "deepseek-ai/DeepSeek-V3.2",
      "description": "DeepSeek-V3.2 is a large language model designed to harmonize high computational efficiency with strong reasoning and agentic tool-use performance. It introduces DeepSeek Sparse Attention (DSA), a fine-grained sparse attention mechanism...",
      "context_length": 163840,
      "max_completion_tokens": 163840,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.259,
        "output_per_million": 0.42,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1764594642
    },
    {
      "id": "deepseek/deepseek-v3.2-exp",
      "name": "DeepSeek: DeepSeek V3.2 Exp",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-v3.2-exp",
      "hugging_face_id": "deepseek-ai/DeepSeek-V3.2-Exp",
      "description": "DeepSeek-V3.2-Exp is an experimental large language model released by DeepSeek as an intermediate step between V3.1 and future architectures. It introduces DeepSeek Sparse Attention (DSA), a fine-grained sparse attention mechanism...",
      "context_length": 163840,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.27,
        "output_per_million": 0.41,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1759150481
    },
    {
      "id": "deepseek/deepseek-v3.2-speciale",
      "name": "DeepSeek: DeepSeek V3.2 Speciale",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-v3.2-speciale-20251201",
      "hugging_face_id": "deepseek-ai/DeepSeek-V3.2-Speciale",
      "description": "DeepSeek-V3.2-Speciale is a high-compute variant of DeepSeek-V3.2 optimized for maximum reasoning and agentic performance. It builds on DeepSeek Sparse Attention (DSA) for efficient long-context processing, then scales post-training reinforcement learning...",
      "context_length": 163840,
      "max_completion_tokens": 163840,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1764594837
    },
    {
      "id": "deepseek/deepseek-r1",
      "name": "DeepSeek: R1",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-r1",
      "hugging_face_id": "deepseek-ai/DeepSeek-R1",
      "description": "DeepSeek R1 is here: Performance on par with [OpenAI o1](/openai/o1), but open-sourced and with fully open reasoning tokens. It's 671B parameters in size, with 37B active in an inference pass....",
      "context_length": 64000,
      "max_completion_tokens": 16000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.7,
        "output_per_million": 2.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1737381095
    },
    {
      "id": "deepseek/deepseek-r1-0528",
      "name": "DeepSeek: R1 0528",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-r1-0528",
      "hugging_face_id": "deepseek-ai/DeepSeek-R1-0528",
      "description": "May 28th update to the [original DeepSeek R1](/deepseek/deepseek-r1) Performance on par with [OpenAI o1](/openai/o1), but open-sourced and with fully open reasoning tokens. It's 671B parameters in size, with 37B active...",
      "context_length": 163840,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.5,
        "output_per_million": 2.15,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1748455170
    },
    {
      "id": "deepseek/deepseek-r1-distill-llama-70b",
      "name": "DeepSeek: R1 Distill Llama 70B",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-r1-distill-llama-70b",
      "hugging_face_id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
      "description": "DeepSeek R1 Distill Llama 70B is a distilled large language model based on [Llama-3.3-70B-Instruct](/meta-llama/llama-3.3-70b-instruct), using outputs from [DeepSeek R1](/deepseek/deepseek-r1). The model combines advanced distillation techniques to achieve high performance across...",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.7,
        "output_per_million": 0.8,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1737663169
    },
    {
      "id": "deepseek/deepseek-r1-distill-qwen-32b",
      "name": "DeepSeek: R1 Distill Qwen 32B",
      "provider": "deepseek",
      "canonical_slug": "deepseek/deepseek-r1-distill-qwen-32b",
      "hugging_face_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
      "description": "DeepSeek R1 Distill Qwen 32B is a distilled large language model based on [Qwen 2.5 32B](https://huggingface.co/Qwen/Qwen2.5-32B), using outputs from [DeepSeek R1](/deepseek/deepseek-r1). It outperforms OpenAI's o1-mini across various benchmarks, achieving new...",
      "context_length": 32768,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.29,
        "output_per_million": 0.29,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "top_logprobs",
        "top_p"
      ],
      "created": 1738194830
    },
    {
      "id": "essentialai/rnj-1-instruct",
      "name": "EssentialAI: Rnj 1 Instruct",
      "provider": "essentialai",
      "canonical_slug": "essentialai/rnj-1-instruct",
      "hugging_face_id": "EssentialAI/rnj-1-instruct",
      "description": "Rnj-1 is an 8B-parameter, dense, open-weight model family developed by Essential AI and trained from scratch with a focus on programming, math, and scientific reasoning. The model demonstrates strong performance...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.15,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1765094847
    },
    {
      "id": "google/gemini-2.0-flash-001",
      "name": "Google: Gemini 2.0 Flash",
      "provider": "google",
      "canonical_slug": "google/gemini-2.0-flash-001",
      "hugging_face_id": "",
      "description": "Gemini Flash 2.0 offers a significantly faster time to first token (TTFT) compared to [Gemini Flash 1.5](/google/gemini-flash-1.5), while maintaining quality on par with larger models like [Gemini Pro 1.5](/google/gemini-pro-1.5). It...",
      "context_length": 1048576,
      "max_completion_tokens": 8192,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "file",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1738769413
    },
    {
      "id": "google/gemini-2.0-flash-lite-001",
      "name": "Google: Gemini 2.0 Flash Lite",
      "provider": "google",
      "canonical_slug": "google/gemini-2.0-flash-lite-001",
      "hugging_face_id": "",
      "description": "Gemini 2.0 Flash Lite offers a significantly faster time to first token (TTFT) compared to [Gemini Flash 1.5](/google/gemini-flash-1.5), while maintaining quality on par with larger models like [Gemini Pro 1.5](/google/gemini-pro-1.5),...",
      "context_length": 1048576,
      "max_completion_tokens": 8192,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "file",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.075,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1740506212
    },
    {
      "id": "google/gemini-2.5-flash",
      "name": "Google: Gemini 2.5 Flash",
      "provider": "google",
      "canonical_slug": "google/gemini-2.5-flash",
      "hugging_face_id": "",
      "description": "Gemini 2.5 Flash is Google's state-of-the-art workhorse model, specifically designed for advanced reasoning, coding, mathematics, and scientific tasks. It includes built-in \"thinking\" capabilities, enabling it to provide responses with greater...",
      "context_length": 1048576,
      "max_completion_tokens": 65535,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "file",
        "image",
        "text",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 2.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1750172488
    },
    {
      "id": "google/gemini-2.5-flash-lite",
      "name": "Google: Gemini 2.5 Flash Lite",
      "provider": "google",
      "canonical_slug": "google/gemini-2.5-flash-lite",
      "hugging_face_id": "",
      "description": "Gemini 2.5 Flash-Lite is a lightweight reasoning model in the Gemini 2.5 family, optimized for ultra-low latency and cost efficiency. It offers improved throughput, faster token generation, and better performance...",
      "context_length": 1048576,
      "max_completion_tokens": 65535,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "file",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1753200276
    },
    {
      "id": "google/gemini-2.5-flash-lite-preview-09-2025",
      "name": "Google: Gemini 2.5 Flash Lite Preview 09-2025",
      "provider": "google",
      "canonical_slug": "google/gemini-2.5-flash-lite-preview-09-2025",
      "hugging_face_id": "",
      "description": "Gemini 2.5 Flash-Lite is a lightweight reasoning model in the Gemini 2.5 family, optimized for ultra-low latency and cost efficiency. It offers improved throughput, faster token generation, and better performance...",
      "context_length": 1048576,
      "max_completion_tokens": 65535,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "file",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1758819686
    },
    {
      "id": "google/gemini-2.5-pro",
      "name": "Google: Gemini 2.5 Pro",
      "provider": "google",
      "canonical_slug": "google/gemini-2.5-pro",
      "hugging_face_id": "",
      "description": "Gemini 2.5 Pro is Google’s state-of-the-art AI model designed for advanced reasoning, coding, mathematics, and scientific tasks. It employs “thinking” capabilities, enabling it to reason through responses with enhanced accuracy...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "file",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1750169544
    },
    {
      "id": "google/gemini-2.5-pro-preview-05-06",
      "name": "Google: Gemini 2.5 Pro Preview 05-06",
      "provider": "google",
      "canonical_slug": "google/gemini-2.5-pro-preview-03-25",
      "hugging_face_id": "",
      "description": "Gemini 2.5 Pro is Google’s state-of-the-art AI model designed for advanced reasoning, coding, mathematics, and scientific tasks. It employs “thinking” capabilities, enabling it to reason through responses with enhanced accuracy...",
      "context_length": 1048576,
      "max_completion_tokens": 65535,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "file",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1746578513
    },
    {
      "id": "google/gemini-2.5-pro-preview",
      "name": "Google: Gemini 2.5 Pro Preview 06-05",
      "provider": "google",
      "canonical_slug": "google/gemini-2.5-pro-preview-06-05",
      "hugging_face_id": "",
      "description": "Gemini 2.5 Pro is Google’s state-of-the-art AI model designed for advanced reasoning, coding, mathematics, and scientific tasks. It employs “thinking” capabilities, enabling it to reason through responses with enhanced accuracy...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image+file+audio->text",
      "input_modalities": [
        "file",
        "image",
        "text",
        "audio"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1749137257
    },
    {
      "id": "google/gemini-3-flash-preview",
      "name": "Google: Gemini 3 Flash Preview",
      "provider": "google",
      "canonical_slug": "google/gemini-3-flash-preview-20251217",
      "hugging_face_id": "",
      "description": "Gemini 3 Flash Preview is a high speed, high value thinking model designed for agentic workflows, multi turn chat, and coding assistance. It delivers near Pro level reasoning and tool...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "file",
        "audio",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.5,
        "output_per_million": 3.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1765987078
    },
    {
      "id": "google/gemini-3.1-flash-lite-preview",
      "name": "Google: Gemini 3.1 Flash Lite Preview",
      "provider": "google",
      "canonical_slug": "google/gemini-3.1-flash-lite-preview-20260303",
      "hugging_face_id": "",
      "description": "Gemini 3.1 Flash Lite Preview is Google's high-efficiency model optimized for high-volume use cases. It outperforms Gemini 2.5 Flash Lite on overall quality and approaches Gemini 2.5 Flash performance across...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "image",
        "video",
        "file",
        "audio"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 1.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1772512673
    },
    {
      "id": "google/gemini-3.1-pro-preview",
      "name": "Google: Gemini 3.1 Pro Preview",
      "provider": "google",
      "canonical_slug": "google/gemini-3.1-pro-preview-20260219",
      "hugging_face_id": "",
      "description": "Gemini 3.1 Pro Preview is Google’s frontier reasoning model, delivering enhanced software engineering performance, improved agentic reliability, and more efficient token usage across complex workflows. Building on the multimodal foundation...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "audio",
        "file",
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 12.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1771509627
    },
    {
      "id": "google/gemini-3.1-pro-preview-customtools",
      "name": "Google: Gemini 3.1 Pro Preview Custom Tools",
      "provider": "google",
      "canonical_slug": "google/gemini-3.1-pro-preview-customtools-20260219",
      "hugging_face_id": null,
      "description": "Gemini 3.1 Pro Preview Custom Tools is a variant of Gemini 3.1 Pro that improves tool selection behavior by preventing overuse of a general bash tool when more efficient third-party...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image+file+audio+video->text",
      "input_modalities": [
        "text",
        "audio",
        "image",
        "video",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 12.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1772045923
    },
    {
      "id": "google/gemma-2-27b-it",
      "name": "Google: Gemma 2 27B",
      "provider": "google",
      "canonical_slug": "google/gemma-2-27b-it",
      "hugging_face_id": "google/gemma-2-27b-it",
      "description": "Gemma 2 27B by Google is an open model built from the same research and technology used to create the [Gemini models](/models?q=gemini). Gemma models are well-suited for a variety of...",
      "context_length": 8192,
      "max_completion_tokens": 2048,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.65,
        "output_per_million": 0.65,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "top_p"
      ],
      "created": 1720828800
    },
    {
      "id": "google/gemma-3-12b-it",
      "name": "Google: Gemma 3 12B",
      "provider": "google",
      "canonical_slug": "google/gemma-3-12b-it",
      "hugging_face_id": "google/gemma-3-12b-it",
      "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs. It handles context windows up to 128k tokens, understands over 140 languages, and offers improved math, reasoning, and chat capabilities,...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.04,
        "output_per_million": 0.13,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1741902625
    },
    {
      "id": "google/gemma-3-12b-it:free",
      "name": "Google: Gemma 3 12B (free)",
      "provider": "google",
      "canonical_slug": "google/gemma-3-12b-it",
      "hugging_face_id": "google/gemma-3-12b-it",
      "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs. It handles context windows up to 128k tokens, understands over 140 languages, and offers improved math, reasoning, and chat capabilities,...",
      "context_length": 32768,
      "max_completion_tokens": 8192,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "seed",
        "stop",
        "temperature",
        "top_p"
      ],
      "created": 1741902625
    },
    {
      "id": "google/gemma-3-27b-it",
      "name": "Google: Gemma 3 27B",
      "provider": "google",
      "canonical_slug": "google/gemma-3-27b-it",
      "hugging_face_id": "google/gemma-3-27b-it",
      "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs. It handles context windows up to 128k tokens, understands over 140 languages, and offers improved math, reasoning, and chat capabilities,...",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.08,
        "output_per_million": 0.16,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1741756359
    },
    {
      "id": "google/gemma-3-27b-it:free",
      "name": "Google: Gemma 3 27B (free)",
      "provider": "google",
      "canonical_slug": "google/gemma-3-27b-it",
      "hugging_face_id": "google/gemma-3-27b-it",
      "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs. It handles context windows up to 128k tokens, understands over 140 languages, and offers improved math, reasoning, and chat capabilities,...",
      "context_length": 131072,
      "max_completion_tokens": 8192,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_p"
      ],
      "created": 1741756359
    },
    {
      "id": "google/gemma-3-4b-it",
      "name": "Google: Gemma 3 4B",
      "provider": "google",
      "canonical_slug": "google/gemma-3-4b-it",
      "hugging_face_id": "google/gemma-3-4b-it",
      "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs. It handles context windows up to 128k tokens, understands over 140 languages, and offers improved math, reasoning, and chat capabilities,...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.04,
        "output_per_million": 0.08,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1741905510
    },
    {
      "id": "google/gemma-3-4b-it:free",
      "name": "Google: Gemma 3 4B (free)",
      "provider": "google",
      "canonical_slug": "google/gemma-3-4b-it",
      "hugging_face_id": "google/gemma-3-4b-it",
      "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs. It handles context windows up to 128k tokens, understands over 140 languages, and offers improved math, reasoning, and chat capabilities,...",
      "context_length": 32768,
      "max_completion_tokens": 8192,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_p"
      ],
      "created": 1741905510
    },
    {
      "id": "google/gemma-3n-e2b-it:free",
      "name": "Google: Gemma 3n 2B (free)",
      "provider": "google",
      "canonical_slug": "google/gemma-3n-e2b-it",
      "hugging_face_id": "google/gemma-3n-E2B-it",
      "description": "Gemma 3n E2B IT is a multimodal, instruction-tuned model developed by Google DeepMind, designed to operate efficiently at an effective parameter size of 2B while leveraging a 6B architecture. Based...",
      "context_length": 8192,
      "max_completion_tokens": 2048,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "temperature",
        "top_p"
      ],
      "created": 1752074904
    },
    {
      "id": "google/gemma-3n-e4b-it",
      "name": "Google: Gemma 3n 4B",
      "provider": "google",
      "canonical_slug": "google/gemma-3n-e4b-it",
      "hugging_face_id": "google/gemma-3n-E4B-it",
      "description": "Gemma 3n E4B-it is optimized for efficient execution on mobile and low-resource devices, such as phones, laptops, and tablets. It supports multimodal inputs—including text, visual data, and audio—enabling diverse tasks...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.06,
        "output_per_million": 0.12,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1747776824
    },
    {
      "id": "google/gemma-3n-e4b-it:free",
      "name": "Google: Gemma 3n 4B (free)",
      "provider": "google",
      "canonical_slug": "google/gemma-3n-e4b-it",
      "hugging_face_id": "google/gemma-3n-E4B-it",
      "description": "Gemma 3n E4B-it is optimized for efficient execution on mobile and low-resource devices, such as phones, laptops, and tablets. It supports multimodal inputs—including text, visual data, and audio—enabling diverse tasks...",
      "context_length": 8192,
      "max_completion_tokens": 2048,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "temperature",
        "top_p"
      ],
      "created": 1747776824
    },
    {
      "id": "google/gemma-4-26b-a4b-it",
      "name": "Google: Gemma 4 26B A4B ",
      "provider": "google",
      "canonical_slug": "google/gemma-4-26b-a4b-it-20260403",
      "hugging_face_id": "google/gemma-4-26B-A4B-it",
      "description": "Gemma 4 26B A4B IT is an instruction-tuned Mixture-of-Experts (MoE) model from Google DeepMind. Despite 25.2B total parameters, only 3.8B activate per token during inference — delivering near-31B quality at...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemma",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.08,
        "output_per_million": 0.35,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1775227989
    },
    {
      "id": "google/gemma-4-26b-a4b-it:free",
      "name": "Google: Gemma 4 26B A4B  (free)",
      "provider": "google",
      "canonical_slug": "google/gemma-4-26b-a4b-it-20260403",
      "hugging_face_id": "google/gemma-4-26B-A4B-it",
      "description": "Gemma 4 26B A4B IT is an instruction-tuned Mixture-of-Experts (MoE) model from Google DeepMind. Despite 25.2B total parameters, only 3.8B activate per token during inference — delivering near-31B quality at...",
      "context_length": 262144,
      "max_completion_tokens": 32768,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemma",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1775227989
    },
    {
      "id": "google/gemma-4-31b-it",
      "name": "Google: Gemma 4 31B",
      "provider": "google",
      "canonical_slug": "google/gemma-4-31b-it-20260402",
      "hugging_face_id": "google/gemma-4-31B-it",
      "description": "Gemma 4 31B Instruct is Google DeepMind's 30.7B dense multimodal model supporting text and image input with text output. Features a 256K token context window, configurable thinking/reasoning mode, native function...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemma",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.13,
        "output_per_million": 0.38,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1775148486
    },
    {
      "id": "google/gemma-4-31b-it:free",
      "name": "Google: Gemma 4 31B (free)",
      "provider": "google",
      "canonical_slug": "google/gemma-4-31b-it-20260402",
      "hugging_face_id": "google/gemma-4-31B-it",
      "description": "Gemma 4 31B Instruct is Google DeepMind's 30.7B dense multimodal model supporting text and image input with text output. Features a 256K token context window, configurable thinking/reasoning mode, native function...",
      "context_length": 262144,
      "max_completion_tokens": 32768,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Gemma",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1775148486
    },
    {
      "id": "google/lyria-3-clip-preview",
      "name": "Google: Lyria 3 Clip Preview",
      "provider": "google",
      "canonical_slug": "google/lyria-3-clip-preview-20260330",
      "hugging_face_id": null,
      "description": "30 second duration clips are priced at $0.04 per clip. Lyria 3 is Google's family of music generation models, available through the Gemini API. With Lyria 3, you can generate...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image->text+audio",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text",
        "audio"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "temperature",
        "top_p"
      ],
      "created": 1774907255
    },
    {
      "id": "google/lyria-3-pro-preview",
      "name": "Google: Lyria 3 Pro Preview",
      "provider": "google",
      "canonical_slug": "google/lyria-3-pro-preview-20260330",
      "hugging_face_id": null,
      "description": "Full-length songs are priced at $0.08 per song. Lyria 3 is Google's family of music generation models, available through the Gemini API. With Lyria 3, you can generate high-quality, 48kHz...",
      "context_length": 1048576,
      "max_completion_tokens": 65536,
      "modality": "text+image->text+audio",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text",
        "audio"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "temperature",
        "top_p"
      ],
      "created": 1774907286
    },
    {
      "id": "google/gemini-2.5-flash-image",
      "name": "Google: Nano Banana (Gemini 2.5 Flash Image)",
      "provider": "google",
      "canonical_slug": "google/gemini-2.5-flash-image",
      "hugging_face_id": "",
      "description": "Gemini 2.5 Flash Image, a.k.a. \"Nano Banana,\" is now generally available. It is a state of the art image generation model with contextual understanding. It is capable of image generation,...",
      "context_length": 32768,
      "max_completion_tokens": 32768,
      "modality": "text+image->text+image",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "image",
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 2.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_p"
      ],
      "created": 1759870431
    },
    {
      "id": "google/gemini-3.1-flash-image-preview",
      "name": "Google: Nano Banana 2 (Gemini 3.1 Flash Image Preview)",
      "provider": "google",
      "canonical_slug": "google/gemini-3.1-flash-image-preview-20260226",
      "hugging_face_id": "",
      "description": "Gemini 3.1 Flash Image Preview, a.k.a. \"Nano Banana 2,\" is Google’s latest state of the art image generation and editing model, delivering Pro-level visual quality at Flash speed. It combines...",
      "context_length": 65536,
      "max_completion_tokens": 65536,
      "modality": "text+image->text+image",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "image",
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.5,
        "output_per_million": 3.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_p"
      ],
      "created": 1772119558
    },
    {
      "id": "google/gemini-3-pro-image-preview",
      "name": "Google: Nano Banana Pro (Gemini 3 Pro Image Preview)",
      "provider": "google",
      "canonical_slug": "google/gemini-3-pro-image-preview-20251120",
      "hugging_face_id": "",
      "description": "Nano Banana Pro is Google’s most advanced image-generation and editing model, built on Gemini 3 Pro. It extends the original Nano Banana with significantly improved multimodal reasoning, real-world grounding, and...",
      "context_length": 65536,
      "max_completion_tokens": 32768,
      "modality": "text+image->text+image",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "image",
        "text"
      ],
      "tokenizer": "Gemini",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 12.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_p"
      ],
      "created": 1763653797
    },
    {
      "id": "gryphe/mythomax-l2-13b",
      "name": "MythoMax 13B",
      "provider": "gryphe",
      "canonical_slug": "gryphe/mythomax-l2-13b",
      "hugging_face_id": "Gryphe/MythoMax-L2-13b",
      "description": "One of the highest performing and most popular fine-tunes of Llama 2 13B, with rich descriptions and roleplay. #merge",
      "context_length": 4096,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama2",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.06,
        "output_per_million": 0.06,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_a",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1688256000
    },
    {
      "id": "ibm-granite/granite-4.0-h-micro",
      "name": "IBM: Granite 4.0 Micro",
      "provider": "ibm-granite",
      "canonical_slug": "ibm-granite/granite-4.0-h-micro",
      "hugging_face_id": "ibm-granite/granite-4.0-h-micro",
      "description": "Granite-4.0-H-Micro is a 3B parameter from the Granite 4 family of models. These models are the latest in a series of models released by IBM. They are fine-tuned for long...",
      "context_length": 131000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.017,
        "output_per_million": 0.11,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1760927695
    },
    {
      "id": "inception/mercury-2",
      "name": "Inception: Mercury 2",
      "provider": "inception",
      "canonical_slug": "inception/mercury-2-20260304",
      "hugging_face_id": null,
      "description": "Mercury 2 is an extremely fast reasoning LLM, and the first reasoning diffusion LLM (dLLM). Instead of generating tokens sequentially, Mercury 2 produces and refines multiple tokens in parallel, achieving...",
      "context_length": 128000,
      "max_completion_tokens": 50000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 0.75,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools"
      ],
      "created": 1772636275
    },
    {
      "id": "inflection/inflection-3-pi",
      "name": "Inflection: Inflection 3 Pi",
      "provider": "inflection",
      "canonical_slug": "inflection/inflection-3-pi",
      "hugging_face_id": null,
      "description": "Inflection 3 Pi powers Inflection's [Pi](https://pi.ai) chatbot, including backstory, emotional intelligence, productivity, and safety. It has access to recent news, and excels in scenarios like customer support and roleplay. Pi...",
      "context_length": 8000,
      "max_completion_tokens": 1024,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "top_p"
      ],
      "created": 1728604800
    },
    {
      "id": "inflection/inflection-3-productivity",
      "name": "Inflection: Inflection 3 Productivity",
      "provider": "inflection",
      "canonical_slug": "inflection/inflection-3-productivity",
      "hugging_face_id": null,
      "description": "Inflection 3 Productivity is optimized for following instructions. It is better for tasks requiring JSON output or precise adherence to provided guidelines. It has access to recent news. For emotional...",
      "context_length": 8000,
      "max_completion_tokens": 1024,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "top_p"
      ],
      "created": 1728604800
    },
    {
      "id": "kwaipilot/kat-coder-pro-v2",
      "name": "Kwaipilot: KAT-Coder-Pro V2",
      "provider": "kwaipilot",
      "canonical_slug": "kwaipilot/kat-coder-pro-v2-20260327",
      "hugging_face_id": "",
      "description": "KAT-Coder-Pro V2 is the latest high-performance model in KwaiKAT’s KAT-Coder series, designed for complex enterprise-grade software engineering and SaaS integration. It builds on the agentic coding strengths of earlier versions,...",
      "context_length": 256000,
      "max_completion_tokens": 80000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1774649310
    },
    {
      "id": "liquid/lfm-2-24b-a2b",
      "name": "LiquidAI: LFM2-24B-A2B",
      "provider": "liquid",
      "canonical_slug": "liquid/lfm-2-24b-a2b-20260224",
      "hugging_face_id": "LiquidAI/LFM2-24B-A2B",
      "description": "LFM2-24B-A2B is the largest model in the LFM2 family of hybrid architectures designed for efficient on-device deployment. Built as a 24B parameter Mixture-of-Experts model with only 2B active parameters per...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.03,
        "output_per_million": 0.12,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1772048711
    },
    {
      "id": "liquid/lfm-2.5-1.2b-instruct:free",
      "name": "LiquidAI: LFM2.5-1.2B-Instruct (free)",
      "provider": "liquid",
      "canonical_slug": "liquid/lfm-2.5-1.2b-instruct-20260120",
      "hugging_face_id": "LiquidAI/LFM2.5-1.2B-Instruct",
      "description": "LFM2.5-1.2B-Instruct is a compact, high-performance instruction-tuned model built for fast on-device AI. It delivers strong chat quality in a 1.2B parameter footprint, with efficient edge inference and broad runtime support.",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1768927521
    },
    {
      "id": "liquid/lfm-2.5-1.2b-thinking:free",
      "name": "LiquidAI: LFM2.5-1.2B-Thinking (free)",
      "provider": "liquid",
      "canonical_slug": "liquid/lfm-2.5-1.2b-thinking-20260120",
      "hugging_face_id": "LiquidAI/LFM2.5-1.2B-Thinking",
      "description": "LFM2.5-1.2B-Thinking is a lightweight reasoning-focused model optimized for agentic tasks, data extraction, and RAG—while still running comfortably on edge devices. It supports long context (up to 32K tokens) and is...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1768927527
    },
    {
      "id": "mancer/weaver",
      "name": "Mancer: Weaver (alpha)",
      "provider": "mancer",
      "canonical_slug": "mancer/weaver",
      "hugging_face_id": null,
      "description": "An attempt to recreate Claude-style verbosity, but don't expect the same level of coherence or memory. Meant for use in roleplay/narrative situations.",
      "context_length": 8000,
      "max_completion_tokens": 2000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama2",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.75,
        "output_per_million": 1.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_a",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1690934400
    },
    {
      "id": "meta-llama/llama-guard-3-8b",
      "name": "Llama Guard 3 8B",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-guard-3-8b",
      "hugging_face_id": "meta-llama/Llama-Guard-3-8B",
      "description": "Llama Guard 3 is a Llama-3.1-8B pretrained model, fine-tuned for content safety classification. Similar to previous versions, it can be used to classify content in both LLM inputs (prompt classification)...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.48,
        "output_per_million": 0.03,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1739401318
    },
    {
      "id": "meta-llama/llama-3-70b-instruct",
      "name": "Meta: Llama 3 70B Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3-70b-instruct",
      "hugging_face_id": "meta-llama/Meta-Llama-3-70B-Instruct",
      "description": "Meta's latest class of model (Llama 3) launched with a variety of sizes & flavors. This 70B instruct-tuned version was optimized for high quality dialogue usecases. It has demonstrated strong...",
      "context_length": 8192,
      "max_completion_tokens": 8000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.51,
        "output_per_million": 0.74,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1713398400
    },
    {
      "id": "meta-llama/llama-3-8b-instruct",
      "name": "Meta: Llama 3 8B Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3-8b-instruct",
      "hugging_face_id": "meta-llama/Meta-Llama-3-8B-Instruct",
      "description": "Meta's latest class of model (Llama 3) launched with a variety of sizes & flavors. This 8B instruct-tuned version was optimized for high quality dialogue usecases. It has demonstrated strong...",
      "context_length": 8192,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.03,
        "output_per_million": 0.04,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1713398400
    },
    {
      "id": "meta-llama/llama-3.1-70b-instruct",
      "name": "Meta: Llama 3.1 70B Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.1-70b-instruct",
      "hugging_face_id": "meta-llama/Meta-Llama-3.1-70B-Instruct",
      "description": "Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This 70B instruct-tuned version is optimized for high quality dialogue usecases. It has demonstrated strong...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1721692800
    },
    {
      "id": "meta-llama/llama-3.1-8b-instruct",
      "name": "Meta: Llama 3.1 8B Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.1-8b-instruct",
      "hugging_face_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
      "description": "Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This 8B instruct-tuned version is fast and efficient. It has demonstrated strong performance compared to...",
      "context_length": 16384,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.02,
        "output_per_million": 0.05,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1721692800
    },
    {
      "id": "meta-llama/llama-3.2-11b-vision-instruct",
      "name": "Meta: Llama 3.2 11B Vision Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.2-11b-vision-instruct",
      "hugging_face_id": "meta-llama/Llama-3.2-11B-Vision-Instruct",
      "description": "Llama 3.2 11B Vision is a multimodal model with 11 billion parameters, designed to handle tasks combining visual and textual data. It excels in tasks such as image captioning and...",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.245,
        "output_per_million": 0.245,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1727222400
    },
    {
      "id": "meta-llama/llama-3.2-1b-instruct",
      "name": "Meta: Llama 3.2 1B Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.2-1b-instruct",
      "hugging_face_id": "meta-llama/Llama-3.2-1B-Instruct",
      "description": "Llama 3.2 1B is a 1-billion-parameter language model focused on efficiently performing natural language tasks, such as summarization, dialogue, and multilingual text analysis. Its smaller size allows it to operate...",
      "context_length": 60000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.027,
        "output_per_million": 0.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1727222400
    },
    {
      "id": "meta-llama/llama-3.2-3b-instruct",
      "name": "Meta: Llama 3.2 3B Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.2-3b-instruct",
      "hugging_face_id": "meta-llama/Llama-3.2-3B-Instruct",
      "description": "Llama 3.2 3B is a 3-billion-parameter multilingual large language model, optimized for advanced natural language processing tasks like dialogue generation, reasoning, and summarization. Designed with the latest transformer architecture, it...",
      "context_length": 80000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.051,
        "output_per_million": 0.34,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1727222400
    },
    {
      "id": "meta-llama/llama-3.2-3b-instruct:free",
      "name": "Meta: Llama 3.2 3B Instruct (free)",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.2-3b-instruct",
      "hugging_face_id": "meta-llama/Llama-3.2-3B-Instruct",
      "description": "Llama 3.2 3B is a 3-billion-parameter multilingual large language model, optimized for advanced natural language processing tasks like dialogue generation, reasoning, and summarization. Designed with the latest transformer architecture, it...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1727222400
    },
    {
      "id": "meta-llama/llama-3.3-70b-instruct",
      "name": "Meta: Llama 3.3 70B Instruct",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.3-70b-instruct",
      "hugging_face_id": "meta-llama/Llama-3.3-70B-Instruct",
      "description": "The Meta Llama 3.3 multilingual large language model (LLM) is a pretrained and instruction tuned generative model in 70B (text in/text out). The Llama 3.3 instruction tuned text only model...",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.32,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1733506137
    },
    {
      "id": "meta-llama/llama-3.3-70b-instruct:free",
      "name": "Meta: Llama 3.3 70B Instruct (free)",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-3.3-70b-instruct",
      "hugging_face_id": "meta-llama/Llama-3.3-70B-Instruct",
      "description": "The Meta Llama 3.3 multilingual large language model (LLM) is a pretrained and instruction tuned generative model in 70B (text in/text out). The Llama 3.3 instruction tuned text only model...",
      "context_length": 65536,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1733506137
    },
    {
      "id": "meta-llama/llama-4-maverick",
      "name": "Meta: Llama 4 Maverick",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-4-maverick-17b-128e-instruct",
      "hugging_face_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
      "description": "Llama 4 Maverick 17B Instruct (128E) is a high-capacity multimodal language model from Meta, built on a mixture-of-experts (MoE) architecture with 128 experts and 17 billion active parameters per forward...",
      "context_length": 1048576,
      "max_completion_tokens": 16384,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama4",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1743881822
    },
    {
      "id": "meta-llama/llama-4-scout",
      "name": "Meta: Llama 4 Scout",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-4-scout-17b-16e-instruct",
      "hugging_face_id": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
      "description": "Llama 4 Scout 17B Instruct (16E) is a mixture-of-experts (MoE) language model developed by Meta, activating 17 billion parameters out of a total of 109B. It supports native multimodal input...",
      "context_length": 327680,
      "max_completion_tokens": 16384,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama4",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.08,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1743881519
    },
    {
      "id": "meta-llama/llama-guard-4-12b",
      "name": "Meta: Llama Guard 4 12B",
      "provider": "meta-llama",
      "canonical_slug": "meta-llama/llama-guard-4-12b",
      "hugging_face_id": "meta-llama/Llama-Guard-4-12B",
      "description": "Llama Guard 4 is a Llama 4 Scout-derived multimodal pretrained model, fine-tuned for content safety classification. Similar to previous versions, it can be used to classify content in both LLM...",
      "context_length": 163840,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.18,
        "output_per_million": 0.18,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1745975193
    },
    {
      "id": "microsoft/phi-4",
      "name": "Microsoft: Phi 4",
      "provider": "microsoft",
      "canonical_slug": "microsoft/phi-4",
      "hugging_face_id": "microsoft/phi-4",
      "description": "[Microsoft Research](/microsoft) Phi-4 is designed to perform well in complex reasoning tasks and can operate efficiently in situations with limited memory or where quick responses are needed. At 14 billion...",
      "context_length": 16384,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.065,
        "output_per_million": 0.14,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1736489872
    },
    {
      "id": "microsoft/wizardlm-2-8x22b",
      "name": "WizardLM-2 8x22B",
      "provider": "microsoft",
      "canonical_slug": "microsoft/wizardlm-2-8x22b",
      "hugging_face_id": "microsoft/WizardLM-2-8x22B",
      "description": "WizardLM-2 8x22B is Microsoft AI's most advanced Wizard model. It demonstrates highly competitive performance compared to leading proprietary models, and it consistently outperforms all existing state-of-the-art opensource models. It is...",
      "context_length": 65535,
      "max_completion_tokens": 8000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.62,
        "output_per_million": 0.62,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1713225600
    },
    {
      "id": "minimax/minimax-m1",
      "name": "MiniMax: MiniMax M1",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-m1",
      "hugging_face_id": "",
      "description": "MiniMax-M1 is a large-scale, open-weight reasoning model designed for extended context and high-efficiency inference. It leverages a hybrid Mixture-of-Experts (MoE) architecture paired with a custom \"lightning attention\" mechanism, allowing it...",
      "context_length": 1000000,
      "max_completion_tokens": 40000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 2.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1750200414
    },
    {
      "id": "minimax/minimax-m2",
      "name": "MiniMax: MiniMax M2",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-m2",
      "hugging_face_id": "MiniMaxAI/MiniMax-M2",
      "description": "MiniMax-M2 is a compact, high-efficiency large language model optimized for end-to-end coding and agentic workflows. With 10 billion activated parameters (230 billion total), it delivers near-frontier intelligence across general reasoning,...",
      "context_length": 196608,
      "max_completion_tokens": 196608,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.255,
        "output_per_million": 1.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1761252093
    },
    {
      "id": "minimax/minimax-m2-her",
      "name": "MiniMax: MiniMax M2-her",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-m2-her-20260123",
      "hugging_face_id": "",
      "description": "MiniMax M2-her is a dialogue-first large language model built for immersive roleplay, character-driven chat, and expressive multi-turn conversations. Designed to stay consistent in tone and personality, it supports rich message...",
      "context_length": 65536,
      "max_completion_tokens": 2048,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "temperature",
        "top_p"
      ],
      "created": 1769177239
    },
    {
      "id": "minimax/minimax-m2.1",
      "name": "MiniMax: MiniMax M2.1",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-m2.1",
      "hugging_face_id": "MiniMaxAI/MiniMax-M2.1",
      "description": "MiniMax-M2.1 is a lightweight, state-of-the-art large language model optimized for coding, agentic workflows, and modern application development. With only 10 billion activated parameters, it delivers a major jump in real-world...",
      "context_length": 196608,
      "max_completion_tokens": 196608,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.29,
        "output_per_million": 0.95,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1766454997
    },
    {
      "id": "minimax/minimax-m2.5",
      "name": "MiniMax: MiniMax M2.5",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-m2.5-20260211",
      "hugging_face_id": "MiniMaxAI/MiniMax-M2.5",
      "description": "MiniMax-M2.5 is a SOTA large language model designed for real-world productivity. Trained in a diverse range of complex real-world digital working environments, M2.5 builds upon the coding expertise of M2.1...",
      "context_length": 196608,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.118,
        "output_per_million": 0.99,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "parallel_tool_calls",
        "presence_penalty",
        "reasoning",
        "reasoning_effort",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1770908502
    },
    {
      "id": "minimax/minimax-m2.5:free",
      "name": "MiniMax: MiniMax M2.5 (free)",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-m2.5-20260211",
      "hugging_face_id": "MiniMaxAI/MiniMax-M2.5",
      "description": "MiniMax-M2.5 is a SOTA large language model designed for real-world productivity. Trained in a diverse range of complex real-world digital working environments, M2.5 builds upon the coding expertise of M2.1...",
      "context_length": 196608,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tools"
      ],
      "created": 1770908502
    },
    {
      "id": "minimax/minimax-m2.7",
      "name": "MiniMax: MiniMax M2.7",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-m2.7-20260318",
      "hugging_face_id": "MiniMaxAI/MiniMax-M2.7",
      "description": "MiniMax-M2.7 is a next-generation large language model designed for autonomous, real-world productivity and continuous improvement. Built to actively participate in its own evolution, M2.7 integrates advanced agentic capabilities through multi-agent...",
      "context_length": 196608,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1773836697
    },
    {
      "id": "minimax/minimax-01",
      "name": "MiniMax: MiniMax-01",
      "provider": "minimax",
      "canonical_slug": "minimax/minimax-01",
      "hugging_face_id": "MiniMaxAI/MiniMax-Text-01",
      "description": "MiniMax-01 is a combines MiniMax-Text-01 for text generation and MiniMax-VL-01 for image understanding. It has 456 billion parameters, with 45.9 billion parameters activated per inference, and can handle a context...",
      "context_length": 1000192,
      "max_completion_tokens": 1000192,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 1.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "temperature",
        "top_p"
      ],
      "created": 1736915462
    },
    {
      "id": "mistralai/mistral-large",
      "name": "Mistral Large",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-large",
      "hugging_face_id": null,
      "description": "This is Mistral AI's flagship model, Mistral Large 2 (version `mistral-large-2407`). It's a proprietary weights-available model and excels at reasoning, code, JSON, chat, and more. Read the launch announcement [here](https://mistral.ai/news/mistral-large-2407/)....",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1708905600
    },
    {
      "id": "mistralai/mistral-large-2407",
      "name": "Mistral Large 2407",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-large-2407",
      "hugging_face_id": "",
      "description": "This is Mistral AI's flagship model, Mistral Large 2 (version mistral-large-2407). It's a proprietary weights-available model and excels at reasoning, code, JSON, chat, and more. Read the launch announcement [here](https://mistral.ai/news/mistral-large-2407/)....",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1731978415
    },
    {
      "id": "mistralai/mistral-large-2411",
      "name": "Mistral Large 2411",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-large-2411",
      "hugging_face_id": "",
      "description": "Mistral Large 2 2411 is an update of [Mistral Large 2](/mistralai/mistral-large) released together with [Pixtral Large 2411](/mistralai/pixtral-large-2411) It provides a significant upgrade on the previous [Mistral Large 24.07](/mistralai/mistral-large-2407), with notable...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1731978685
    },
    {
      "id": "mistralai/codestral-2508",
      "name": "Mistral: Codestral 2508",
      "provider": "mistralai",
      "canonical_slug": "mistralai/codestral-2508",
      "hugging_face_id": "",
      "description": "Mistral's cutting-edge language model for coding released end of July 2025. Codestral specializes in low-latency, high-frequency tasks such as fill-in-the-middle (FIM), code correction and test generation.\n\n[Blog Post](https://mistral.ai/news/codestral-25-08)",
      "context_length": 256000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 0.9,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1754079630
    },
    {
      "id": "mistralai/devstral-2512",
      "name": "Mistral: Devstral 2 2512",
      "provider": "mistralai",
      "canonical_slug": "mistralai/devstral-2512",
      "hugging_face_id": "mistralai/Devstral-2-123B-Instruct-2512",
      "description": "Devstral 2 is a state-of-the-art open-source model by Mistral AI specializing in agentic coding. It is a 123B-parameter dense transformer model supporting a 256K context window. Devstral 2 supports exploring...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1765285419
    },
    {
      "id": "mistralai/devstral-medium",
      "name": "Mistral: Devstral Medium",
      "provider": "mistralai",
      "canonical_slug": "mistralai/devstral-medium-2507",
      "hugging_face_id": "",
      "description": "Devstral Medium is a high-performance code generation and agentic reasoning model developed jointly by Mistral AI and All Hands AI. Positioned as a step up from Devstral Small, it achieves...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1752161321
    },
    {
      "id": "mistralai/devstral-small",
      "name": "Mistral: Devstral Small 1.1",
      "provider": "mistralai",
      "canonical_slug": "mistralai/devstral-small-2507",
      "hugging_face_id": "mistralai/Devstral-Small-2507",
      "description": "Devstral Small 1.1 is a 24B parameter open-weight language model for software engineering agents, developed by Mistral AI in collaboration with All Hands AI. Finetuned from Mistral Small 3.1 and...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1752160751
    },
    {
      "id": "mistralai/ministral-14b-2512",
      "name": "Mistral: Ministral 3 14B 2512",
      "provider": "mistralai",
      "canonical_slug": "mistralai/ministral-14b-2512",
      "hugging_face_id": "mistralai/Ministral-3-14B-Instruct-2512",
      "description": "The largest model in the Ministral 3 family, Ministral 3 14B offers frontier capabilities and performance comparable to its larger Mistral Small 3.2 24B counterpart. A powerful and efficient language...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1764681735
    },
    {
      "id": "mistralai/ministral-3b-2512",
      "name": "Mistral: Ministral 3 3B 2512",
      "provider": "mistralai",
      "canonical_slug": "mistralai/ministral-3b-2512",
      "hugging_face_id": "mistralai/Ministral-3-3B-Instruct-2512",
      "description": "The smallest model in the Ministral 3 family, Ministral 3 3B is a powerful, efficient tiny language model with vision capabilities.",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1764681560
    },
    {
      "id": "mistralai/ministral-8b-2512",
      "name": "Mistral: Ministral 3 8B 2512",
      "provider": "mistralai",
      "canonical_slug": "mistralai/ministral-8b-2512",
      "hugging_face_id": "mistralai/Ministral-3-8B-Instruct-2512",
      "description": "A balanced model in the Ministral 3 family, Ministral 3 8B is a powerful, efficient tiny language model with vision capabilities.",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.15,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1764681654
    },
    {
      "id": "mistralai/mistral-7b-instruct-v0.1",
      "name": "Mistral: Mistral 7B Instruct v0.1",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-7b-instruct-v0.1",
      "hugging_face_id": "mistralai/Mistral-7B-Instruct-v0.1",
      "description": "A 7.3B parameter model that outperforms Llama 2 13B on all benchmarks, with optimizations for speed and context length.",
      "context_length": 2824,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.11,
        "output_per_million": 0.19,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1695859200
    },
    {
      "id": "mistralai/mistral-large-2512",
      "name": "Mistral: Mistral Large 3 2512",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-large-2512",
      "hugging_face_id": "",
      "description": "Mistral Large 3 2512 is Mistral’s most capable model to date, featuring a sparse mixture-of-experts architecture with 41B active parameters (675B total), and released under the Apache 2.0 license.",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.5,
        "output_per_million": 1.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1764624472
    },
    {
      "id": "mistralai/mistral-medium-3",
      "name": "Mistral: Mistral Medium 3",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-medium-3",
      "hugging_face_id": "",
      "description": "Mistral Medium 3 is a high-performance enterprise-grade language model designed to deliver frontier-level capabilities at significantly reduced operational cost. It balances state-of-the-art reasoning and multimodal performance with 8× lower cost...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1746627341
    },
    {
      "id": "mistralai/mistral-medium-3.1",
      "name": "Mistral: Mistral Medium 3.1",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-medium-3.1",
      "hugging_face_id": "",
      "description": "Mistral Medium 3.1 is an updated version of Mistral Medium 3, which is a high-performance enterprise-grade language model designed to deliver frontier-level capabilities at significantly reduced operational cost. It balances...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1755095639
    },
    {
      "id": "mistralai/mistral-nemo",
      "name": "Mistral: Mistral Nemo",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-nemo",
      "hugging_face_id": "mistralai/Mistral-Nemo-Instruct-2407",
      "description": "A 12B parameter model with a 128k token context length built by Mistral in collaboration with NVIDIA. The model is multilingual, supporting English, French, German, Spanish, Italian, Portuguese, Chinese, Japanese,...",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.02,
        "output_per_million": 0.04,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1721347200
    },
    {
      "id": "mistralai/mistral-small-24b-instruct-2501",
      "name": "Mistral: Mistral Small 3",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-small-24b-instruct-2501",
      "hugging_face_id": "mistralai/Mistral-Small-24B-Instruct-2501",
      "description": "Mistral Small 3 is a 24B-parameter language model optimized for low-latency performance across common AI tasks. Released under the Apache 2.0 license, it features both pre-trained and instruction-tuned versions designed...",
      "context_length": 32768,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.05,
        "output_per_million": 0.08,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1738255409
    },
    {
      "id": "mistralai/mistral-small-3.1-24b-instruct",
      "name": "Mistral: Mistral Small 3.1 24B",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-small-3.1-24b-instruct-2503",
      "hugging_face_id": "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
      "description": "Mistral Small 3.1 24B Instruct is an upgraded variant of Mistral Small 3 (2501), featuring 24 billion parameters with advanced multimodal capabilities. It provides state-of-the-art performance in text-based reasoning and...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.35,
        "output_per_million": 0.56,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1742238937
    },
    {
      "id": "mistralai/mistral-small-3.2-24b-instruct",
      "name": "Mistral: Mistral Small 3.2 24B",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-small-3.2-24b-instruct-2506",
      "hugging_face_id": "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
      "description": "Mistral-Small-3.2-24B-Instruct-2506 is an updated 24B parameter model from Mistral optimized for instruction following, repetition reduction, and improved function calling. Compared to the 3.1 release, version 3.2 significantly improves accuracy on...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.075,
        "output_per_million": 0.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1750443016
    },
    {
      "id": "mistralai/mistral-small-2603",
      "name": "Mistral: Mistral Small 4",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-small-2603",
      "hugging_face_id": "mistralai/Mistral-Small-4-119B-2603",
      "description": "Mistral Small 4 is the next major release in the Mistral Small family, unifying the capabilities of several flagship Mistral models into a single system. It combines strong reasoning from...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1773695685
    },
    {
      "id": "mistralai/mistral-small-creative",
      "name": "Mistral: Mistral Small Creative",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-small-creative-20251216",
      "hugging_face_id": null,
      "description": "Mistral Small Creative is an experimental small model designed for creative writing, narrative generation, roleplay and character-driven dialogue, general-purpose instruction following, and conversational agents.",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "tool_choice",
        "tools"
      ],
      "created": 1765908653
    },
    {
      "id": "mistralai/mixtral-8x22b-instruct",
      "name": "Mistral: Mixtral 8x22B Instruct",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mixtral-8x22b-instruct",
      "hugging_face_id": "mistralai/Mixtral-8x22B-Instruct-v0.1",
      "description": "Mistral's official instruct fine-tuned version of [Mixtral 8x22B](/models/mistralai/mixtral-8x22b). It uses 39B active parameters out of 141B, offering unparalleled cost efficiency for its size. Its strengths include: - strong math, coding,...",
      "context_length": 65536,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1713312000
    },
    {
      "id": "mistralai/mixtral-8x7b-instruct",
      "name": "Mistral: Mixtral 8x7B Instruct",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mixtral-8x7b-instruct",
      "hugging_face_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
      "description": "Mixtral 8x7B Instruct is a pretrained generative Sparse Mixture of Experts, by Mistral AI, for chat and instruction use. Incorporates 8 experts (feed-forward networks) for a total of 47 billion...",
      "context_length": 32768,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.54,
        "output_per_million": 0.54,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1702166400
    },
    {
      "id": "mistralai/pixtral-large-2411",
      "name": "Mistral: Pixtral Large 2411",
      "provider": "mistralai",
      "canonical_slug": "mistralai/pixtral-large-2411",
      "hugging_face_id": "",
      "description": "Pixtral Large is a 124B parameter, open-weight, multimodal model built on top of [Mistral Large 2](/mistralai/mistral-large-2411). The model is able to understand documents, charts and natural images. The model is...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1731977388
    },
    {
      "id": "mistralai/mistral-saba",
      "name": "Mistral: Saba",
      "provider": "mistralai",
      "canonical_slug": "mistralai/mistral-saba-2502",
      "hugging_face_id": "",
      "description": "Mistral Saba is a 24B-parameter language model specifically designed for the Middle East and South Asia, delivering accurate and contextually relevant responses while maintaining efficient performance. Trained on curated regional...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1739803239
    },
    {
      "id": "mistralai/voxtral-small-24b-2507",
      "name": "Mistral: Voxtral Small 24B 2507",
      "provider": "mistralai",
      "canonical_slug": "mistralai/voxtral-small-24b-2507",
      "hugging_face_id": "mistralai/Voxtral-Small-24B-2507",
      "description": "Voxtral Small is an enhancement of Mistral Small 3, incorporating state-of-the-art audio input capabilities while retaining best-in-class text performance. It excels at speech transcription, translation and audio understanding. Input audio...",
      "context_length": 32000,
      "max_completion_tokens": 0,
      "modality": "text+audio->text",
      "input_modalities": [
        "text",
        "audio"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": true,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1761835144
    },
    {
      "id": "moonshotai/kimi-k2",
      "name": "MoonshotAI: Kimi K2 0711",
      "provider": "moonshotai",
      "canonical_slug": "moonshotai/kimi-k2",
      "hugging_face_id": "moonshotai/Kimi-K2-Instruct",
      "description": "Kimi K2 Instruct is a large-scale Mixture-of-Experts (MoE) language model developed by Moonshot AI, featuring 1 trillion total parameters with 32 billion active per forward pass. It is optimized for...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.57,
        "output_per_million": 2.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1752263252
    },
    {
      "id": "moonshotai/kimi-k2-0905",
      "name": "MoonshotAI: Kimi K2 0905",
      "provider": "moonshotai",
      "canonical_slug": "moonshotai/kimi-k2-0905",
      "hugging_face_id": "moonshotai/Kimi-K2-Instruct-0905",
      "description": "Kimi K2 0905 is the September update of [Kimi K2 0711](moonshotai/kimi-k2). It is a large-scale Mixture-of-Experts (MoE) language model developed by Moonshot AI, featuring 1 trillion total parameters with 32...",
      "context_length": 262144,
      "max_completion_tokens": 262144,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1757021147
    },
    {
      "id": "moonshotai/kimi-k2-thinking",
      "name": "MoonshotAI: Kimi K2 Thinking",
      "provider": "moonshotai",
      "canonical_slug": "moonshotai/kimi-k2-thinking-20251106",
      "hugging_face_id": "moonshotai/Kimi-K2-Thinking",
      "description": "Kimi K2 Thinking is Moonshot AI’s most advanced open reasoning model to date, extending the K2 series into agentic, long-horizon reasoning. Built on the trillion-parameter Mixture-of-Experts (MoE) architecture introduced in...",
      "context_length": 262144,
      "max_completion_tokens": 262144,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.6,
        "output_per_million": 2.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1762440622
    },
    {
      "id": "moonshotai/kimi-k2.5",
      "name": "MoonshotAI: Kimi K2.5",
      "provider": "moonshotai",
      "canonical_slug": "moonshotai/kimi-k2.5-0127",
      "hugging_face_id": "moonshotai/Kimi-K2.5",
      "description": "Kimi K2.5 is Moonshot AI's native multimodal model, delivering state-of-the-art visual coding capability and a self-directed agent swarm paradigm. Built on Kimi K2 with continued pretraining over approximately 15T mixed...",
      "context_length": 256000,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "parallel_tool_calls",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1769487076
    },
    {
      "id": "morph/morph-v3-fast",
      "name": "Morph: Morph V3 Fast",
      "provider": "morph",
      "canonical_slug": "morph/morph-v3-fast",
      "hugging_face_id": "",
      "description": "Morph's fastest apply model for code edits. ~10,500 tokens/sec with 96% accuracy for rapid code transformations. The model requires the prompt to be in the following format: <instruction>{instruction}</instruction> <code>{initial_code}</code> <update>{edit_snippet}</update>...",
      "context_length": 81920,
      "max_completion_tokens": 38000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.8,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature"
      ],
      "created": 1751910002
    },
    {
      "id": "morph/morph-v3-large",
      "name": "Morph: Morph V3 Large",
      "provider": "morph",
      "canonical_slug": "morph/morph-v3-large",
      "hugging_face_id": "",
      "description": "Morph's high-accuracy apply model for complex code edits. ~4,500 tokens/sec with 98% accuracy for precise code transformations. The model requires the prompt to be in the following format: <instruction>{instruction}</instruction> <code>{initial_code}</code>...",
      "context_length": 262144,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.9,
        "output_per_million": 1.9,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature"
      ],
      "created": 1751910858
    },
    {
      "id": "nex-agi/deepseek-v3.1-nex-n1",
      "name": "Nex AGI: DeepSeek V3.1 Nex N1",
      "provider": "nex-agi",
      "canonical_slug": "nex-agi/deepseek-v3.1-nex-n1",
      "hugging_face_id": "nex-agi/DeepSeek-V3.1-Nex-N1",
      "description": "DeepSeek V3.1 Nex-N1 is the flagship release of the Nex-N1 series — a post-trained model designed to highlight agent autonomy, tool use, and real-world productivity. Nex-N1 demonstrates competitive performance across...",
      "context_length": 131072,
      "max_completion_tokens": 163840,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.135,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "response_format",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1765204393
    },
    {
      "id": "nousresearch/hermes-3-llama-3.1-405b",
      "name": "Nous: Hermes 3 405B Instruct",
      "provider": "nousresearch",
      "canonical_slug": "nousresearch/hermes-3-llama-3.1-405b",
      "hugging_face_id": "NousResearch/Hermes-3-Llama-3.1-405B",
      "description": "Hermes 3 is a generalist language model with many improvements over Hermes 2, including advanced agentic capabilities, much better roleplaying, reasoning, multi-turn conversation, long context coherence, and improvements across the...",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.0,
        "output_per_million": 1.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1723766400
    },
    {
      "id": "nousresearch/hermes-3-llama-3.1-405b:free",
      "name": "Nous: Hermes 3 405B Instruct (free)",
      "provider": "nousresearch",
      "canonical_slug": "nousresearch/hermes-3-llama-3.1-405b",
      "hugging_face_id": "NousResearch/Hermes-3-Llama-3.1-405B",
      "description": "Hermes 3 is a generalist language model with many improvements over Hermes 2, including advanced agentic capabilities, much better roleplaying, reasoning, multi-turn conversation, long context coherence, and improvements across the...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1723766400
    },
    {
      "id": "nousresearch/hermes-3-llama-3.1-70b",
      "name": "Nous: Hermes 3 70B Instruct",
      "provider": "nousresearch",
      "canonical_slug": "nousresearch/hermes-3-llama-3.1-70b",
      "hugging_face_id": "NousResearch/Hermes-3-Llama-3.1-70B",
      "description": "Hermes 3 is a generalist language model with many improvements over [Hermes 2](/models/nousresearch/nous-hermes-2-mistral-7b-dpo), including advanced agentic capabilities, much better roleplaying, reasoning, multi-turn conversation, long context coherence, and improvements across the...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1723939200
    },
    {
      "id": "nousresearch/hermes-4-405b",
      "name": "Nous: Hermes 4 405B",
      "provider": "nousresearch",
      "canonical_slug": "nousresearch/hermes-4-405b",
      "hugging_face_id": "NousResearch/Hermes-4-405B",
      "description": "Hermes 4 is a large-scale reasoning model built on Meta-Llama-3.1-405B and released by Nous Research. It introduces a hybrid reasoning mode, where the model can choose to deliberate internally with...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.0,
        "output_per_million": 3.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1756235463
    },
    {
      "id": "nousresearch/hermes-4-70b",
      "name": "Nous: Hermes 4 70B",
      "provider": "nousresearch",
      "canonical_slug": "nousresearch/hermes-4-70b",
      "hugging_face_id": "NousResearch/Hermes-4-70B",
      "description": "Hermes 4 70B is a hybrid reasoning model from Nous Research, built on Meta-Llama-3.1-70B. It introduces the same hybrid mode as the larger 405B release, allowing the model to either...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.13,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1756236182
    },
    {
      "id": "nousresearch/hermes-2-pro-llama-3-8b",
      "name": "NousResearch: Hermes 2 Pro - Llama-3 8B",
      "provider": "nousresearch",
      "canonical_slug": "nousresearch/hermes-2-pro-llama-3-8b",
      "hugging_face_id": "NousResearch/Hermes-2-Pro-Llama-3-8B",
      "description": "Hermes 2 Pro is an upgraded, retrained version of Nous Hermes 2, consisting of an updated and cleaned version of the OpenHermes 2.5 Dataset, as well as a newly introduced...",
      "context_length": 8192,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.14,
        "output_per_million": 0.14,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1716768000
    },
    {
      "id": "nvidia/llama-3.1-nemotron-70b-instruct",
      "name": "NVIDIA: Llama 3.1 Nemotron 70B Instruct",
      "provider": "nvidia",
      "canonical_slug": "nvidia/llama-3.1-nemotron-70b-instruct",
      "hugging_face_id": "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
      "description": "NVIDIA's Llama 3.1 Nemotron 70B is a language model designed for generating precise and useful responses. Leveraging [Llama 3.1 70B](/models/meta-llama/llama-3.1-70b-instruct) architecture and Reinforcement Learning from Human Feedback (RLHF), it excels...",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.2,
        "output_per_million": 1.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1728950400
    },
    {
      "id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
      "name": "NVIDIA: Llama 3.3 Nemotron Super 49B V1.5",
      "provider": "nvidia",
      "canonical_slug": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
      "hugging_face_id": "nvidia/Llama-3_3-Nemotron-Super-49B-v1_5",
      "description": "Llama-3.3-Nemotron-Super-49B-v1.5 is a 49B-parameter, English-centric reasoning/chat model derived from Meta’s Llama-3.3-70B-Instruct with a 128K context. It’s post-trained for agentic workflows (RAG, tool calling) via SFT across math, code, science, and...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1760101395
    },
    {
      "id": "nvidia/nemotron-3-nano-30b-a3b",
      "name": "NVIDIA: Nemotron 3 Nano 30B A3B",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-3-nano-30b-a3b",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
      "description": "NVIDIA Nemotron 3 Nano 30B A3B is a small language MoE model with highest compute efficiency and accuracy for developers to build specialized agentic AI systems. The model is fully...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.05,
        "output_per_million": 0.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1765731275
    },
    {
      "id": "nvidia/nemotron-3-nano-30b-a3b:free",
      "name": "NVIDIA: Nemotron 3 Nano 30B A3B (free)",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-3-nano-30b-a3b",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
      "description": "NVIDIA Nemotron 3 Nano 30B A3B is a small language MoE model with highest compute efficiency and accuracy for developers to build specialized agentic AI systems. The model is fully...",
      "context_length": 256000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1765731275
    },
    {
      "id": "nvidia/nemotron-3-super-120b-a12b",
      "name": "NVIDIA: Nemotron 3 Super",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-3-super-120b-a12b-20230311",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8",
      "description": "NVIDIA Nemotron 3 Super is a 120B-parameter open hybrid MoE model, activating just 12B parameters for maximum compute efficiency and accuracy in complex multi-agent applications. Built on a hybrid Mamba-Transformer...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.09,
        "output_per_million": 0.45,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1773245239
    },
    {
      "id": "nvidia/nemotron-3-super-120b-a12b:free",
      "name": "NVIDIA: Nemotron 3 Super (free)",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-3-super-120b-a12b-20230311",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8",
      "description": "NVIDIA Nemotron 3 Super is a 120B-parameter open hybrid MoE model, activating just 12B parameters for maximum compute efficiency and accuracy in complex multi-agent applications. Built on a hybrid Mamba-Transformer...",
      "context_length": 262144,
      "max_completion_tokens": 262144,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1773245239
    },
    {
      "id": "nvidia/nemotron-nano-12b-v2-vl",
      "name": "NVIDIA: Nemotron Nano 12B 2 VL",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-nano-12b-v2-vl",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16",
      "description": "NVIDIA Nemotron Nano 2 VL is a 12-billion-parameter open multimodal reasoning model designed for video understanding and document intelligence. It introduces a hybrid Transformer-Mamba architecture, combining transformer-level accuracy with Mamba’s...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1761675565
    },
    {
      "id": "nvidia/nemotron-nano-12b-v2-vl:free",
      "name": "NVIDIA: Nemotron Nano 12B 2 VL (free)",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-nano-12b-v2-vl",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16",
      "description": "NVIDIA Nemotron Nano 2 VL is a 12-billion-parameter open multimodal reasoning model designed for video understanding and document intelligence. It introduces a hybrid Transformer-Mamba architecture, combining transformer-level accuracy with Mamba’s...",
      "context_length": 128000,
      "max_completion_tokens": 128000,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1761675565
    },
    {
      "id": "nvidia/nemotron-nano-9b-v2",
      "name": "NVIDIA: Nemotron Nano 9B V2",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-nano-9b-v2",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
      "description": "NVIDIA-Nemotron-Nano-9B-v2 is a large language model (LLM) trained from scratch by NVIDIA, and designed as a unified model for both reasoning and non-reasoning tasks. It responds to user queries and...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.04,
        "output_per_million": 0.16,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1757106807
    },
    {
      "id": "nvidia/nemotron-nano-9b-v2:free",
      "name": "NVIDIA: Nemotron Nano 9B V2 (free)",
      "provider": "nvidia",
      "canonical_slug": "nvidia/nemotron-nano-9b-v2",
      "hugging_face_id": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
      "description": "NVIDIA-Nemotron-Nano-9B-v2 is a large language model (LLM) trained from scratch by NVIDIA, and designed as a unified model for both reasoning and non-reasoning tasks. It responds to user queries and...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1757106807
    },
    {
      "id": "openai/gpt-audio",
      "name": "OpenAI: GPT Audio",
      "provider": "openai",
      "canonical_slug": "openai/gpt-audio",
      "hugging_face_id": "",
      "description": "The gpt-audio model is OpenAI's first generally available audio model. The new snapshot features an upgraded decoder for more natural sounding voices and maintains better voice consistency. Audio is priced...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+audio->text+audio",
      "input_modalities": [
        "text",
        "audio"
      ],
      "output_modalities": [
        "text",
        "audio"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": true,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1768862569
    },
    {
      "id": "openai/gpt-audio-mini",
      "name": "OpenAI: GPT Audio Mini",
      "provider": "openai",
      "canonical_slug": "openai/gpt-audio-mini",
      "hugging_face_id": "",
      "description": "A cost-efficient version of GPT Audio. The new snapshot features an upgraded decoder for more natural sounding voices and maintains better voice consistency. Input is priced at $0.60 per million...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+audio->text+audio",
      "input_modalities": [
        "text",
        "audio"
      ],
      "output_modalities": [
        "text",
        "audio"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": true,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.6,
        "output_per_million": 2.4,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1768859419
    },
    {
      "id": "openai/gpt-3.5-turbo",
      "name": "OpenAI: GPT-3.5 Turbo",
      "provider": "openai",
      "canonical_slug": "openai/gpt-3.5-turbo",
      "hugging_face_id": null,
      "description": "GPT-3.5 Turbo is OpenAI's fastest model. It can understand and generate natural language or code, and is optimized for chat and traditional completion tasks.\n\nTraining data up to Sep 2021.",
      "context_length": 16385,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.5,
        "output_per_million": 1.5,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1685232000
    },
    {
      "id": "openai/gpt-3.5-turbo-0613",
      "name": "OpenAI: GPT-3.5 Turbo (older v0613)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-3.5-turbo-0613",
      "hugging_face_id": null,
      "description": "GPT-3.5 Turbo is OpenAI's fastest model. It can understand and generate natural language or code, and is optimized for chat and traditional completion tasks.\n\nTraining data up to Sep 2021.",
      "context_length": 4095,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.0,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1706140800
    },
    {
      "id": "openai/gpt-3.5-turbo-16k",
      "name": "OpenAI: GPT-3.5 Turbo 16k",
      "provider": "openai",
      "canonical_slug": "openai/gpt-3.5-turbo-16k",
      "hugging_face_id": null,
      "description": "This model offers four times the context length of gpt-3.5-turbo, allowing it to support approximately 20 pages of text in a single request at a higher cost. Training data: up...",
      "context_length": 16385,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 4.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1693180800
    },
    {
      "id": "openai/gpt-3.5-turbo-instruct",
      "name": "OpenAI: GPT-3.5 Turbo Instruct",
      "provider": "openai",
      "canonical_slug": "openai/gpt-3.5-turbo-instruct",
      "hugging_face_id": null,
      "description": "This model is a variant of GPT-3.5 Turbo tuned for instructional prompts and omitting chat-related optimizations. Training data: up to Sep 2021.",
      "context_length": 4095,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.5,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_logprobs",
        "top_p"
      ],
      "created": 1695859200
    },
    {
      "id": "openai/gpt-4",
      "name": "OpenAI: GPT-4",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4",
      "hugging_face_id": null,
      "description": "OpenAI's flagship model, GPT-4 is a large-scale multimodal language model capable of solving difficult problems with greater accuracy than previous models due to its broader general knowledge and advanced reasoning...",
      "context_length": 8191,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 30.0,
        "output_per_million": 60.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1685232000
    },
    {
      "id": "openai/gpt-4-0314",
      "name": "OpenAI: GPT-4 (older v0314)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4-0314",
      "hugging_face_id": null,
      "description": "GPT-4-0314 is the first version of GPT-4 released, with a context length of 8,192 tokens, and was supported until June 14. Training data: up to Sep 2021.",
      "context_length": 8191,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 30.0,
        "output_per_million": 60.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1685232000
    },
    {
      "id": "openai/gpt-4-turbo",
      "name": "OpenAI: GPT-4 Turbo",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4-turbo",
      "hugging_face_id": null,
      "description": "The latest GPT-4 Turbo model with vision capabilities. Vision requests can now use JSON mode and function calling.\n\nTraining data: up to December 2023.",
      "context_length": 128000,
      "max_completion_tokens": 4096,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 10.0,
        "output_per_million": 30.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1712620800
    },
    {
      "id": "openai/gpt-4-1106-preview",
      "name": "OpenAI: GPT-4 Turbo (older v1106)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4-1106-preview",
      "hugging_face_id": null,
      "description": "The latest GPT-4 Turbo model with vision capabilities. Vision requests can now use JSON mode and function calling.\n\nTraining data: up to April 2023.",
      "context_length": 128000,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 10.0,
        "output_per_million": 30.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1699228800
    },
    {
      "id": "openai/gpt-4-turbo-preview",
      "name": "OpenAI: GPT-4 Turbo Preview",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4-turbo-preview",
      "hugging_face_id": null,
      "description": "The preview GPT-4 model with improved instruction following, JSON mode, reproducible outputs, parallel function calling, and more. Training data: up to Dec 2023. **Note:** heavily rate limited by OpenAI while...",
      "context_length": 128000,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 10.0,
        "output_per_million": 30.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1706140800
    },
    {
      "id": "openai/gpt-4.1",
      "name": "OpenAI: GPT-4.1",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4.1-2025-04-14",
      "hugging_face_id": "",
      "description": "GPT-4.1 is a flagship large language model optimized for advanced instruction following, real-world software engineering, and long-context reasoning. It supports a 1 million token context window and outperforms GPT-4o and...",
      "context_length": 1047576,
      "max_completion_tokens": 0,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 8.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_completion_tokens",
        "max_tokens",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1744651385
    },
    {
      "id": "openai/gpt-4.1-mini",
      "name": "OpenAI: GPT-4.1 Mini",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4.1-mini-2025-04-14",
      "hugging_face_id": "",
      "description": "GPT-4.1 Mini is a mid-sized model delivering performance competitive with GPT-4o at substantially lower latency and cost. It retains a 1 million token context window and scores 45.1% on hard...",
      "context_length": 1047576,
      "max_completion_tokens": 32768,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 1.6,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_completion_tokens",
        "max_tokens",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1744651381
    },
    {
      "id": "openai/gpt-4.1-nano",
      "name": "OpenAI: GPT-4.1 Nano",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4.1-nano-2025-04-14",
      "hugging_face_id": "",
      "description": "For tasks that demand low latency, GPT‑4.1 nano is the fastest and cheapest model in the GPT-4.1 series. It delivers exceptional performance at a small size with its 1 million...",
      "context_length": 1047576,
      "max_completion_tokens": 32768,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_completion_tokens",
        "max_tokens",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1744651369
    },
    {
      "id": "openai/gpt-4o",
      "name": "OpenAI: GPT-4o",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o",
      "hugging_face_id": null,
      "description": "GPT-4o (\"o\" for \"omni\") is OpenAI's latest AI model, supporting both text and image inputs with text outputs. It maintains the intelligence level of [GPT-4 Turbo](/models/openai/gpt-4-turbo) while being twice as...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1715558400
    },
    {
      "id": "openai/gpt-4o-2024-05-13",
      "name": "OpenAI: GPT-4o (2024-05-13)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-2024-05-13",
      "hugging_face_id": null,
      "description": "GPT-4o (\"o\" for \"omni\") is OpenAI's latest AI model, supporting both text and image inputs with text outputs. It maintains the intelligence level of [GPT-4 Turbo](/models/openai/gpt-4-turbo) while being twice as...",
      "context_length": 128000,
      "max_completion_tokens": 4096,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 5.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1715558400
    },
    {
      "id": "openai/gpt-4o-2024-08-06",
      "name": "OpenAI: GPT-4o (2024-08-06)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-2024-08-06",
      "hugging_face_id": null,
      "description": "The 2024-08-06 version of GPT-4o offers improved performance in structured outputs, with the ability to supply a JSON schema in the respone_format. Read more [here](https://openai.com/index/introducing-structured-outputs-in-the-api/). GPT-4o (\"o\" for \"omni\") is...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1722902400
    },
    {
      "id": "openai/gpt-4o-2024-11-20",
      "name": "OpenAI: GPT-4o (2024-11-20)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-2024-11-20",
      "hugging_face_id": "",
      "description": "The 2024-11-20 version of GPT-4o offers a leveled-up creative writing ability with more natural, engaging, and tailored writing to improve relevance & readability. It’s also better at working with uploaded...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1732127594
    },
    {
      "id": "openai/gpt-4o:extended",
      "name": "OpenAI: GPT-4o (extended)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o",
      "hugging_face_id": null,
      "description": "GPT-4o (\"o\" for \"omni\") is OpenAI's latest AI model, supporting both text and image inputs with text outputs. It maintains the intelligence level of [GPT-4 Turbo](/models/openai/gpt-4-turbo) while being twice as...",
      "context_length": 128000,
      "max_completion_tokens": 64000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 6.0,
        "output_per_million": 18.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1715558400
    },
    {
      "id": "openai/gpt-4o-audio-preview",
      "name": "OpenAI: GPT-4o Audio",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-audio-preview",
      "hugging_face_id": "",
      "description": "The gpt-4o-audio-preview model adds support for audio inputs as prompts. This enhancement allows the model to detect nuances within audio recordings and add depth to generated user experiences. Audio outputs...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+audio->text+audio",
      "input_modalities": [
        "audio",
        "text"
      ],
      "output_modalities": [
        "text",
        "audio"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": true,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1755233061
    },
    {
      "id": "openai/gpt-4o-search-preview",
      "name": "OpenAI: GPT-4o Search Preview",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-search-preview-2025-03-11",
      "hugging_face_id": "",
      "description": "GPT-4o Search Previewis a specialized model for web search in Chat Completions. It is trained to understand and execute web search queries.",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "structured_outputs",
        "web_search_options"
      ],
      "created": 1741817949
    },
    {
      "id": "openai/gpt-4o-mini",
      "name": "OpenAI: GPT-4o-mini",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-mini",
      "hugging_face_id": null,
      "description": "GPT-4o mini is OpenAI's newest model after [GPT-4 Omni](/models/openai/gpt-4o), supporting both text and image inputs with text outputs. As their most advanced small model, it is many multiples more affordable...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1721260800
    },
    {
      "id": "openai/gpt-4o-mini-2024-07-18",
      "name": "OpenAI: GPT-4o-mini (2024-07-18)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-mini-2024-07-18",
      "hugging_face_id": null,
      "description": "GPT-4o mini is OpenAI's newest model after [GPT-4 Omni](/models/openai/gpt-4o), supporting both text and image inputs with text outputs. As their most advanced small model, it is many multiples more affordable...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1721260800
    },
    {
      "id": "openai/gpt-4o-mini-search-preview",
      "name": "OpenAI: GPT-4o-mini Search Preview",
      "provider": "openai",
      "canonical_slug": "openai/gpt-4o-mini-search-preview-2025-03-11",
      "hugging_face_id": "",
      "description": "GPT-4o mini Search Preview is a specialized model for web search in Chat Completions. It is trained to understand and execute web search queries.",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "structured_outputs",
        "web_search_options"
      ],
      "created": 1741818122
    },
    {
      "id": "openai/gpt-5",
      "name": "OpenAI: GPT-5",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-2025-08-07",
      "hugging_face_id": "",
      "description": "GPT-5 is OpenAI’s most advanced model, offering major improvements in reasoning, code quality, and user experience. It is optimized for complex tasks that require step-by-step reasoning, instruction following, and accuracy...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1754587413
    },
    {
      "id": "openai/gpt-5-chat",
      "name": "OpenAI: GPT-5 Chat",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-chat-2025-08-07",
      "hugging_face_id": "",
      "description": "GPT-5 Chat is designed for advanced, natural, multimodal, and context-aware conversations for enterprise applications.",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "seed",
        "structured_outputs"
      ],
      "created": 1754587837
    },
    {
      "id": "openai/gpt-5-codex",
      "name": "OpenAI: GPT-5 Codex",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-codex",
      "hugging_face_id": "",
      "description": "GPT-5-Codex is a specialized version of GPT-5 optimized for software engineering and coding workflows. It is designed for both interactive development sessions and long, independent execution of complex engineering tasks....",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1758643403
    },
    {
      "id": "openai/gpt-5-image",
      "name": "OpenAI: GPT-5 Image",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-image",
      "hugging_face_id": "",
      "description": "[GPT-5](https://openrouter.ai/openai/gpt-5) Image combines OpenAI's GPT-5 model with state-of-the-art image generation capabilities. It offers major improvements in reasoning, code quality, and user experience while incorporating GPT Image 1's superior instruction following,...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text+image",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "image",
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 10.0,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1760447986
    },
    {
      "id": "openai/gpt-5-image-mini",
      "name": "OpenAI: GPT-5 Image Mini",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-image-mini",
      "hugging_face_id": "",
      "description": "GPT-5 Image Mini combines OpenAI's advanced language capabilities, powered by [GPT-5 Mini](https://openrouter.ai/openai/gpt-5-mini), with GPT Image 1 Mini for efficient image generation. This natively multimodal model features superior instruction following, text...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text+image",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "image",
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1760624583
    },
    {
      "id": "openai/gpt-5-mini",
      "name": "OpenAI: GPT-5 Mini",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-mini-2025-08-07",
      "hugging_face_id": "",
      "description": "GPT-5 Mini is a compact version of GPT-5, designed to handle lighter-weight reasoning tasks. It provides the same instruction-following and safety-tuning benefits as GPT-5, but with reduced latency and cost....",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1754587407
    },
    {
      "id": "openai/gpt-5-nano",
      "name": "OpenAI: GPT-5 Nano",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-nano-2025-08-07",
      "hugging_face_id": "",
      "description": "GPT-5-Nano is the smallest and fastest variant in the GPT-5 system, optimized for developer tools, rapid interactions, and ultra-low latency environments. While limited in reasoning depth compared to its larger...",
      "context_length": 400000,
      "max_completion_tokens": 0,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.05,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1754587402
    },
    {
      "id": "openai/gpt-5-pro",
      "name": "OpenAI: GPT-5 Pro",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5-pro-2025-10-06",
      "hugging_face_id": "",
      "description": "GPT-5 Pro is OpenAI’s most advanced model, offering major improvements in reasoning, code quality, and user experience. It is optimized for complex tasks that require step-by-step reasoning, instruction following, and...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 15.0,
        "output_per_million": 120.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1759776663
    },
    {
      "id": "openai/gpt-5.1",
      "name": "OpenAI: GPT-5.1",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.1-20251113",
      "hugging_face_id": "",
      "description": "GPT-5.1 is the latest frontier-grade model in the GPT-5 series, offering stronger general-purpose reasoning, improved instruction adherence, and a more natural conversational style compared to GPT-5. It uses adaptive reasoning...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1763060305
    },
    {
      "id": "openai/gpt-5.1-chat",
      "name": "OpenAI: GPT-5.1 Chat",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.1-chat-20251113",
      "hugging_face_id": "",
      "description": "GPT-5.1 Chat (AKA Instant is the fast, lightweight member of the 5.1 family, optimized for low-latency chat while retaining strong general intelligence. It uses adaptive reasoning to selectively “think” on...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_completion_tokens",
        "max_tokens",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1763060302
    },
    {
      "id": "openai/gpt-5.1-codex",
      "name": "OpenAI: GPT-5.1-Codex",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.1-codex-20251113",
      "hugging_face_id": "",
      "description": "GPT-5.1-Codex is a specialized version of GPT-5.1 optimized for software engineering and coding workflows. It is designed for both interactive development sessions and long, independent execution of complex engineering tasks....",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1763060298
    },
    {
      "id": "openai/gpt-5.1-codex-max",
      "name": "OpenAI: GPT-5.1-Codex-Max",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.1-codex-max-20251204",
      "hugging_face_id": "",
      "description": "GPT-5.1-Codex-Max is OpenAI’s latest agentic coding model, designed for long-running, high-context software development tasks. It is based on an updated version of the 5.1 reasoning stack and trained on agentic...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.25,
        "output_per_million": 10.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1764878934
    },
    {
      "id": "openai/gpt-5.1-codex-mini",
      "name": "OpenAI: GPT-5.1-Codex-Mini",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.1-codex-mini-20251113",
      "hugging_face_id": "",
      "description": "GPT-5.1-Codex-Mini is a smaller and faster version of GPT-5.1-Codex",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1763057820
    },
    {
      "id": "openai/gpt-5.2",
      "name": "OpenAI: GPT-5.2",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.2-20251211",
      "hugging_face_id": "",
      "description": "GPT-5.2 is the latest frontier-grade model in the GPT-5 series, offering stronger agentic and long context perfomance compared to GPT-5.1. It uses adaptive reasoning to allocate computation dynamically, responding quickly...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.75,
        "output_per_million": 14.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1765389775
    },
    {
      "id": "openai/gpt-5.2-chat",
      "name": "OpenAI: GPT-5.2 Chat",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.2-chat-20251211",
      "hugging_face_id": "",
      "description": "GPT-5.2 Chat (AKA Instant) is the fast, lightweight member of the 5.2 family, optimized for low-latency chat while retaining strong general intelligence. It uses adaptive reasoning to selectively “think” on...",
      "context_length": 128000,
      "max_completion_tokens": 32000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.75,
        "output_per_million": 14.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_completion_tokens",
        "max_tokens",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1765389783
    },
    {
      "id": "openai/gpt-5.2-pro",
      "name": "OpenAI: GPT-5.2 Pro",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.2-pro-20251211",
      "hugging_face_id": "",
      "description": "GPT-5.2 Pro is OpenAI’s most advanced model, offering major improvements in agentic coding and long context performance over GPT-5 Pro. It is optimized for complex tasks that require step-by-step reasoning,...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 21.0,
        "output_per_million": 168.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1765389780
    },
    {
      "id": "openai/gpt-5.2-codex",
      "name": "OpenAI: GPT-5.2-Codex",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.2-codex-20260114",
      "hugging_face_id": "",
      "description": "GPT-5.2-Codex is an upgraded version of GPT-5.1-Codex optimized for software engineering and coding workflows. It is designed for both interactive development sessions and long, independent execution of complex engineering tasks....",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.75,
        "output_per_million": 14.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1768409315
    },
    {
      "id": "openai/gpt-5.3-chat",
      "name": "OpenAI: GPT-5.3 Chat",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.3-chat-20260303",
      "hugging_face_id": "",
      "description": "GPT-5.3 Chat is an update to ChatGPT's most-used model that makes everyday conversations smoother, more useful, and more directly helpful. It delivers more accurate answers with better contextualization and significantly...",
      "context_length": 128000,
      "max_completion_tokens": 16384,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.75,
        "output_per_million": 14.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_completion_tokens",
        "max_tokens",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1772564061
    },
    {
      "id": "openai/gpt-5.3-codex",
      "name": "OpenAI: GPT-5.3-Codex",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.3-codex-20260224",
      "hugging_face_id": "",
      "description": "GPT-5.3-Codex is OpenAI’s most advanced agentic coding model, combining the frontier software engineering performance of GPT-5.2-Codex with the broader reasoning and professional knowledge capabilities of GPT-5.2. It achieves state-of-the-art results...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.75,
        "output_per_million": 14.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1771959164
    },
    {
      "id": "openai/gpt-5.4",
      "name": "OpenAI: GPT-5.4",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.4-20260305",
      "hugging_face_id": "",
      "description": "GPT-5.4 is OpenAI’s latest frontier model, unifying the Codex and GPT lines into a single system. It features a 1M+ token context window (922K input, 128K output) with support for...",
      "context_length": 1050000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.5,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1772734352
    },
    {
      "id": "openai/gpt-5.4-mini",
      "name": "OpenAI: GPT-5.4 Mini",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.4-mini-20260317",
      "hugging_face_id": "",
      "description": "GPT-5.4 mini brings the core capabilities of GPT-5.4 to a faster, more efficient model optimized for high-throughput workloads. It supports text and image inputs with strong performance across reasoning, coding,...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.75,
        "output_per_million": 4.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1773748178
    },
    {
      "id": "openai/gpt-5.4-nano",
      "name": "OpenAI: GPT-5.4 Nano",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.4-nano-20260317",
      "hugging_face_id": "",
      "description": "GPT-5.4 nano is the most lightweight and cost-efficient variant of the GPT-5.4 family, optimized for speed-critical and high-volume tasks. It supports text and image inputs and is designed for low-latency...",
      "context_length": 400000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 1.25,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1773748187
    },
    {
      "id": "openai/gpt-5.4-pro",
      "name": "OpenAI: GPT-5.4 Pro",
      "provider": "openai",
      "canonical_slug": "openai/gpt-5.4-pro-20260305",
      "hugging_face_id": "",
      "description": "GPT-5.4 Pro is OpenAI's most advanced model, building on GPT-5.4's unified architecture with enhanced reasoning capabilities for complex, high-stakes tasks. It features a 1M+ token context window (922K input, 128K...",
      "context_length": 1050000,
      "max_completion_tokens": 128000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 30.0,
        "output_per_million": 180.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_completion_tokens",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1772734366
    },
    {
      "id": "openai/gpt-oss-120b",
      "name": "OpenAI: gpt-oss-120b",
      "provider": "openai",
      "canonical_slug": "openai/gpt-oss-120b",
      "hugging_face_id": "openai/gpt-oss-120b",
      "description": "gpt-oss-120b is an open-weight, 117B-parameter Mixture-of-Experts (MoE) language model from OpenAI designed for high-reasoning, agentic, and general-purpose production use cases. It activates 5.1B parameters per forward pass and is optimized...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.039,
        "output_per_million": 0.19,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1754414231
    },
    {
      "id": "openai/gpt-oss-120b:free",
      "name": "OpenAI: gpt-oss-120b (free)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-oss-120b",
      "hugging_face_id": "openai/gpt-oss-120b",
      "description": "gpt-oss-120b is an open-weight, 117B-parameter Mixture-of-Experts (MoE) language model from OpenAI designed for high-reasoning, agentic, and general-purpose production use cases. It activates 5.1B parameters per forward pass and is optimized...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools"
      ],
      "created": 1754414231
    },
    {
      "id": "openai/gpt-oss-20b",
      "name": "OpenAI: gpt-oss-20b",
      "provider": "openai",
      "canonical_slug": "openai/gpt-oss-20b",
      "hugging_face_id": "openai/gpt-oss-20b",
      "description": "gpt-oss-20b is an open-weight 21B parameter model released by OpenAI under the Apache 2.0 license. It uses a Mixture-of-Experts (MoE) architecture with 3.6B active parameters per forward pass, optimized for...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.03,
        "output_per_million": 0.14,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "reasoning_effort",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1754414229
    },
    {
      "id": "openai/gpt-oss-20b:free",
      "name": "OpenAI: gpt-oss-20b (free)",
      "provider": "openai",
      "canonical_slug": "openai/gpt-oss-20b",
      "hugging_face_id": "openai/gpt-oss-20b",
      "description": "gpt-oss-20b is an open-weight 21B parameter model released by OpenAI under the Apache 2.0 license. It uses a Mixture-of-Experts (MoE) architecture with 3.6B active parameters per forward pass, optimized for...",
      "context_length": 131072,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools"
      ],
      "created": 1754414229
    },
    {
      "id": "openai/gpt-oss-safeguard-20b",
      "name": "OpenAI: gpt-oss-safeguard-20b",
      "provider": "openai",
      "canonical_slug": "openai/gpt-oss-safeguard-20b",
      "hugging_face_id": "openai/gpt-oss-safeguard-20b",
      "description": "gpt-oss-safeguard-20b is a safety reasoning model from OpenAI built upon gpt-oss-20b. This open-weight, 21B-parameter Mixture-of-Experts (MoE) model offers lower latency for safety tasks like content classification, LLM filtering, and trust...",
      "context_length": 131072,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.075,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1761752836
    },
    {
      "id": "openai/o1",
      "name": "OpenAI: o1",
      "provider": "openai",
      "canonical_slug": "openai/o1-2024-12-17",
      "hugging_face_id": "",
      "description": "The latest and strongest model family from OpenAI, o1 is designed to spend more time thinking before responding. The o1 model series is trained with large-scale reinforcement learning to reason...",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 15.0,
        "output_per_million": 60.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1734459999
    },
    {
      "id": "openai/o1-pro",
      "name": "OpenAI: o1-pro",
      "provider": "openai",
      "canonical_slug": "openai/o1-pro",
      "hugging_face_id": "",
      "description": "The o1 series of models are trained with reinforcement learning to think before they answer and perform complex reasoning. The o1-pro model uses more compute to think harder and provide...",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 150.0,
        "output_per_million": 600.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs"
      ],
      "created": 1742423211
    },
    {
      "id": "openai/o3",
      "name": "OpenAI: o3",
      "provider": "openai",
      "canonical_slug": "openai/o3-2025-04-16",
      "hugging_face_id": "",
      "description": "o3 is a well-rounded and powerful model across domains. It sets a new standard for math, science, coding, and visual reasoning tasks. It also excels at technical writing and instruction-following....",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 8.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1744823457
    },
    {
      "id": "openai/o3-deep-research",
      "name": "OpenAI: o3 Deep Research",
      "provider": "openai",
      "canonical_slug": "openai/o3-deep-research-2025-06-26",
      "hugging_face_id": "",
      "description": "o3-deep-research is OpenAI's advanced model for deep research, designed to tackle complex, multi-step research tasks.\n\nNote: This model always uses the 'web_search' tool which adds additional cost.",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 10.0,
        "output_per_million": 40.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1760129661
    },
    {
      "id": "openai/o3-mini",
      "name": "OpenAI: o3 Mini",
      "provider": "openai",
      "canonical_slug": "openai/o3-mini-2025-01-31",
      "hugging_face_id": "",
      "description": "OpenAI o3-mini is a cost-efficient language model optimized for STEM reasoning tasks, particularly excelling in science, mathematics, and coding. This model supports the `reasoning_effort` parameter, which can be set to...",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+file->text",
      "input_modalities": [
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.1,
        "output_per_million": 4.4,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1738351721
    },
    {
      "id": "openai/o3-mini-high",
      "name": "OpenAI: o3 Mini High",
      "provider": "openai",
      "canonical_slug": "openai/o3-mini-high-2025-01-31",
      "hugging_face_id": "",
      "description": "OpenAI o3-mini-high is the same model as [o3-mini](/openai/o3-mini) with reasoning_effort set to high. o3-mini is a cost-efficient language model optimized for STEM reasoning tasks, particularly excelling in science, mathematics, and...",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+file->text",
      "input_modalities": [
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.1,
        "output_per_million": 4.4,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1739372611
    },
    {
      "id": "openai/o3-pro",
      "name": "OpenAI: o3 Pro",
      "provider": "openai",
      "canonical_slug": "openai/o3-pro-2025-06-10",
      "hugging_face_id": "",
      "description": "The o-series of models are trained with reinforcement learning to think before they answer and perform complex reasoning. The o3-pro model uses more compute to think harder and provide consistently...",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "file",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 20.0,
        "output_per_million": 80.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1749598352
    },
    {
      "id": "openai/o4-mini",
      "name": "OpenAI: o4 Mini",
      "provider": "openai",
      "canonical_slug": "openai/o4-mini-2025-04-16",
      "hugging_face_id": "",
      "description": "OpenAI o4-mini is a compact reasoning model in the o-series, optimized for fast, cost-efficient performance while retaining strong multimodal and agentic capabilities. It supports tool use and demonstrates competitive reasoning...",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.1,
        "output_per_million": 4.4,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1744820942
    },
    {
      "id": "openai/o4-mini-deep-research",
      "name": "OpenAI: o4 Mini Deep Research",
      "provider": "openai",
      "canonical_slug": "openai/o4-mini-deep-research-2025-06-26",
      "hugging_face_id": "",
      "description": "o4-mini-deep-research is OpenAI's faster, more affordable deep research model—ideal for tackling complex, multi-step research tasks.\n\nNote: This model always uses the 'web_search' tool which adds additional cost.",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "file",
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 8.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1760129642
    },
    {
      "id": "openai/o4-mini-high",
      "name": "OpenAI: o4 Mini High",
      "provider": "openai",
      "canonical_slug": "openai/o4-mini-high-2025-04-16",
      "hugging_face_id": "",
      "description": "OpenAI o4-mini-high is the same model as [o4-mini](/openai/o4-mini) with reasoning_effort set to high. OpenAI o4-mini is a compact reasoning model in the o-series, optimized for fast, cost-efficient performance while retaining...",
      "context_length": 200000,
      "max_completion_tokens": 100000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "GPT",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 1.1,
        "output_per_million": 4.4,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "tool_choice",
        "tools"
      ],
      "created": 1744824212
    },
    {
      "id": "openrouter/auto",
      "name": "Auto Router",
      "provider": "openrouter",
      "canonical_slug": "openrouter/auto",
      "hugging_face_id": null,
      "description": "Your prompt will be processed by a meta-model and routed to one of dozens of models (see below), optimizing for the best possible output. To see which model was used,...",
      "context_length": 2000000,
      "max_completion_tokens": 0,
      "modality": "text+image+file+audio+video->text+image",
      "input_modalities": [
        "text",
        "image",
        "audio",
        "file",
        "video"
      ],
      "output_modalities": [
        "text",
        "image"
      ],
      "tokenizer": "Router",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": -1000000.0,
        "output_per_million": -1000000.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p",
        "web_search_options"
      ],
      "created": 1699401600
    },
    {
      "id": "openrouter/bodybuilder",
      "name": "Body Builder (beta)",
      "provider": "openrouter",
      "canonical_slug": "openrouter/bodybuilder",
      "hugging_face_id": "",
      "description": "Transform your natural language requests into structured OpenRouter API request objects. Describe what you want to accomplish with AI models, and Body Builder will construct the appropriate API calls. Example:...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Router",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": -1000000.0,
        "output_per_million": -1000000.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [],
      "created": 1764903653
    },
    {
      "id": "openrouter/elephant-alpha",
      "name": "Elephant",
      "provider": "openrouter",
      "canonical_slug": "openrouter/elephant-alpha",
      "hugging_face_id": null,
      "description": "Elephant Alpha is a 100B-parameter text model focused on intelligence efficiency, delivering strong performance while minimizing token usage. It supports a 256K context window with up to 32K output tokens,...",
      "context_length": 262144,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "response_format",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1776052598
    },
    {
      "id": "openrouter/free",
      "name": "Free Models Router",
      "provider": "openrouter",
      "canonical_slug": "openrouter/free",
      "hugging_face_id": "",
      "description": "The simplest way to get free inference. openrouter/free is a router that selects free models at random from the models available on OpenRouter. The router smartly filters for models that...",
      "context_length": 200000,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Router",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1769917427
    },
    {
      "id": "perplexity/sonar",
      "name": "Perplexity: Sonar",
      "provider": "perplexity",
      "canonical_slug": "perplexity/sonar",
      "hugging_face_id": "",
      "description": "Sonar is lightweight, affordable, fast, and simple to use — now featuring citations and the ability to customize sources. It is designed for companies seeking to integrate lightweight question-and-answer features...",
      "context_length": 127072,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.0,
        "output_per_million": 1.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "temperature",
        "top_k",
        "top_p",
        "web_search_options"
      ],
      "created": 1738013808
    },
    {
      "id": "perplexity/sonar-deep-research",
      "name": "Perplexity: Sonar Deep Research",
      "provider": "perplexity",
      "canonical_slug": "perplexity/sonar-deep-research",
      "hugging_face_id": "",
      "description": "Sonar Deep Research is a research-focused model designed for multi-step retrieval, synthesis, and reasoning across complex topics. It autonomously searches, reads, and evaluates sources, refining its approach as it gathers...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 8.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "temperature",
        "top_k",
        "top_p",
        "web_search_options"
      ],
      "created": 1741311246
    },
    {
      "id": "perplexity/sonar-pro",
      "name": "Perplexity: Sonar Pro",
      "provider": "perplexity",
      "canonical_slug": "perplexity/sonar-pro",
      "hugging_face_id": "",
      "description": "Note: Sonar Pro pricing includes Perplexity search pricing. See [details here](https://docs.perplexity.ai/guides/pricing#detailed-pricing-breakdown-for-sonar-reasoning-pro-and-sonar-pro) For enterprises seeking more advanced capabilities, the Sonar Pro API can handle in-depth, multi-step queries with added extensibility, like...",
      "context_length": 200000,
      "max_completion_tokens": 8000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "temperature",
        "top_k",
        "top_p",
        "web_search_options"
      ],
      "created": 1741312423
    },
    {
      "id": "perplexity/sonar-pro-search",
      "name": "Perplexity: Sonar Pro Search",
      "provider": "perplexity",
      "canonical_slug": "perplexity/sonar-pro-search",
      "hugging_face_id": "",
      "description": "Exclusively available on the OpenRouter API, Sonar Pro's new Pro Search mode is Perplexity's most advanced agentic search system. It is designed for deeper reasoning and analysis. Pricing is based...",
      "context_length": 200000,
      "max_completion_tokens": 8000,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p",
        "web_search_options"
      ],
      "created": 1761854366
    },
    {
      "id": "perplexity/sonar-reasoning-pro",
      "name": "Perplexity: Sonar Reasoning Pro",
      "provider": "perplexity",
      "canonical_slug": "perplexity/sonar-reasoning-pro",
      "hugging_face_id": "",
      "description": "Note: Sonar Pro pricing includes Perplexity search pricing. See [details here](https://docs.perplexity.ai/guides/pricing#detailed-pricing-breakdown-for-sonar-reasoning-pro-and-sonar-pro) Sonar Reasoning Pro is a premier reasoning model powered by DeepSeek R1 with Chain of Thought (CoT). Designed for...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 8.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "temperature",
        "top_k",
        "top_p",
        "web_search_options"
      ],
      "created": 1741313308
    },
    {
      "id": "prime-intellect/intellect-3",
      "name": "Prime Intellect: INTELLECT-3",
      "provider": "prime-intellect",
      "canonical_slug": "prime-intellect/intellect-3-20251126",
      "hugging_face_id": "PrimeIntellect/INTELLECT-3-FP8",
      "description": "INTELLECT-3 is a 106B-parameter Mixture-of-Experts model (12B active) post-trained from GLM-4.5-Air-Base using supervised fine-tuning (SFT) followed by large-scale reinforcement learning (RL). It offers state-of-the-art performance for its size across math,...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 1.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1764212534
    },
    {
      "id": "qwen/qwen-2.5-72b-instruct",
      "name": "Qwen2.5 72B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-2.5-72b-instruct",
      "hugging_face_id": "Qwen/Qwen2.5-72B-Instruct",
      "description": "Qwen2.5 72B is the latest series of Qwen large language models. Qwen2.5 brings the following improvements upon Qwen2: - Significantly more knowledge and has greatly improved capabilities in coding and...",
      "context_length": 32768,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.12,
        "output_per_million": 0.39,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1726704000
    },
    {
      "id": "qwen/qwen-2.5-coder-32b-instruct",
      "name": "Qwen2.5 Coder 32B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-2.5-coder-32b-instruct",
      "hugging_face_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
      "description": "Qwen2.5-Coder is the latest series of Code-Specific Qwen large language models (formerly known as CodeQwen). Qwen2.5-Coder brings the following improvements upon CodeQwen1.5: - Significantly improvements in **code generation**, **code reasoning**...",
      "context_length": 32768,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.66,
        "output_per_million": 1.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1731368400
    },
    {
      "id": "qwen/qwq-32b",
      "name": "Qwen: QwQ 32B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwq-32b",
      "hugging_face_id": "Qwen/QwQ-32B",
      "description": "QwQ is the reasoning model of the Qwen series. Compared with conventional instruction-tuned models, QwQ, which is capable of thinking and reasoning, can achieve significantly enhanced performance in downstream tasks,...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.58,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "reasoning",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1741208814
    },
    {
      "id": "qwen/qwen-plus-2025-07-28",
      "name": "Qwen: Qwen Plus 0728",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-plus-2025-07-28",
      "hugging_face_id": "",
      "description": "Qwen Plus 0728, based on the Qwen3 foundation model, is a 1 million context hybrid reasoning model with a balanced performance, speed, and cost combination.",
      "context_length": 1000000,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.26,
        "output_per_million": 0.78,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1757347599
    },
    {
      "id": "qwen/qwen-plus-2025-07-28:thinking",
      "name": "Qwen: Qwen Plus 0728 (thinking)",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-plus-2025-07-28",
      "hugging_face_id": "",
      "description": "Qwen Plus 0728, based on the Qwen3 foundation model, is a 1 million context hybrid reasoning model with a balanced performance, speed, and cost combination.",
      "context_length": 1000000,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.26,
        "output_per_million": 0.78,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1757347599
    },
    {
      "id": "qwen/qwen-vl-max",
      "name": "Qwen: Qwen VL Max",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-vl-max-2025-01-25",
      "hugging_face_id": "",
      "description": "Qwen VL Max is a visual understanding model with 7500 tokens context length. It excels in delivering optimal performance for a broader spectrum of complex tasks.\n",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.52,
        "output_per_million": 2.08,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1738434304
    },
    {
      "id": "qwen/qwen-vl-plus",
      "name": "Qwen: Qwen VL Plus",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-vl-plus",
      "hugging_face_id": "",
      "description": "Qwen's Enhanced Large Visual Language Model. Significantly upgraded for detailed recognition capabilities and text recognition abilities, supporting ultra-high pixel resolutions up to millions of pixels and extreme aspect ratios for...",
      "context_length": 131072,
      "max_completion_tokens": 8192,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.1365,
        "output_per_million": 0.4095,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "top_p"
      ],
      "created": 1738731255
    },
    {
      "id": "qwen/qwen-max",
      "name": "Qwen: Qwen-Max ",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-max-2025-01-25",
      "hugging_face_id": "",
      "description": "Qwen-Max, based on Qwen2.5, provides the best inference performance among [Qwen models](/qwen), especially for complex multi-step tasks. It's a large-scale MoE model that has been pretrained on over 20 trillion...",
      "context_length": 32768,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.04,
        "output_per_million": 4.16,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1738402289
    },
    {
      "id": "qwen/qwen-plus",
      "name": "Qwen: Qwen-Plus",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-plus-2025-01-25",
      "hugging_face_id": "",
      "description": "Qwen-Plus, based on the Qwen2.5 foundation model, is a 131K context model with a balanced performance, speed, and cost combination.",
      "context_length": 1000000,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.26,
        "output_per_million": 0.78,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1738409840
    },
    {
      "id": "qwen/qwen-turbo",
      "name": "Qwen: Qwen-Turbo",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-turbo-2024-11-01",
      "hugging_face_id": "",
      "description": "Qwen-Turbo, based on Qwen2.5, is a 1M context model that provides fast speed and low cost, suitable for simple tasks.",
      "context_length": 131072,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0325,
        "output_per_million": 0.13,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1738410974
    },
    {
      "id": "qwen/qwen-2.5-7b-instruct",
      "name": "Qwen: Qwen2.5 7B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen-2.5-7b-instruct",
      "hugging_face_id": "Qwen/Qwen2.5-7B-Instruct",
      "description": "Qwen2.5 7B is the latest series of Qwen large language models. Qwen2.5 brings the following improvements upon Qwen2: - Significantly more knowledge and has greatly improved capabilities in coding and...",
      "context_length": 32768,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.04,
        "output_per_million": 0.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1729036800
    },
    {
      "id": "qwen/qwen2.5-vl-72b-instruct",
      "name": "Qwen: Qwen2.5 VL 72B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen2.5-vl-72b-instruct",
      "hugging_face_id": "Qwen/Qwen2.5-VL-72B-Instruct",
      "description": "Qwen2.5-VL is proficient in recognizing common objects such as flowers, birds, fish, and insects. It is also highly capable of analyzing texts, charts, icons, graphics, and layouts within images.",
      "context_length": 32000,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.25,
        "output_per_million": 0.75,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1738410311
    },
    {
      "id": "qwen/qwen3-14b",
      "name": "Qwen: Qwen3 14B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-14b-04-28",
      "hugging_face_id": "Qwen/Qwen3-14B",
      "description": "Qwen3-14B is a dense 14.8B parameter causal language model from the Qwen3 series, designed for both complex reasoning and efficient dialogue. It supports seamless switching between a \"thinking\" mode for...",
      "context_length": 40960,
      "max_completion_tokens": 40960,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.06,
        "output_per_million": 0.24,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1745876478
    },
    {
      "id": "qwen/qwen3-235b-a22b",
      "name": "Qwen: Qwen3 235B A22B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-235b-a22b-04-28",
      "hugging_face_id": "Qwen/Qwen3-235B-A22B",
      "description": "Qwen3-235B-A22B is a 235B parameter mixture-of-experts (MoE) model developed by Qwen, activating 22B parameters per forward pass. It supports seamless switching between a \"thinking\" mode for complex reasoning, math, and...",
      "context_length": 131072,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.455,
        "output_per_million": 1.82,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1745875757
    },
    {
      "id": "qwen/qwen3-235b-a22b-2507",
      "name": "Qwen: Qwen3 235B A22B Instruct 2507",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-235b-a22b-07-25",
      "hugging_face_id": "Qwen/Qwen3-235B-A22B-Instruct-2507",
      "description": "Qwen3-235B-A22B-Instruct-2507 is a multilingual, instruction-tuned mixture-of-experts language model based on the Qwen3-235B architecture, with 22B active parameters per forward pass. It is optimized for general-purpose text generation, including instruction following,...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.071,
        "output_per_million": 0.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "reasoning_effort",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1753119555
    },
    {
      "id": "qwen/qwen3-235b-a22b-thinking-2507",
      "name": "Qwen: Qwen3 235B A22B Thinking 2507",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-235b-a22b-thinking-2507",
      "hugging_face_id": "Qwen/Qwen3-235B-A22B-Thinking-2507",
      "description": "Qwen3-235B-A22B-Thinking-2507 is a high-performance, open-weight Mixture-of-Experts (MoE) language model optimized for complex reasoning tasks. It activates 22B of its 235B parameters per forward pass and natively supports up to 262,144...",
      "context_length": 262144,
      "max_completion_tokens": 262144,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.13,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1753449557
    },
    {
      "id": "qwen/qwen3-30b-a3b",
      "name": "Qwen: Qwen3 30B A3B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-30b-a3b-04-28",
      "hugging_face_id": "Qwen/Qwen3-30B-A3B",
      "description": "Qwen3, the latest generation in the Qwen large language model series, features both dense and mixture-of-experts (MoE) architectures to excel in reasoning, multilingual support, and advanced agent tasks. Its unique...",
      "context_length": 40960,
      "max_completion_tokens": 40960,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.08,
        "output_per_million": 0.28,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1745878604
    },
    {
      "id": "qwen/qwen3-30b-a3b-instruct-2507",
      "name": "Qwen: Qwen3 30B A3B Instruct 2507",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-30b-a3b-instruct-2507",
      "hugging_face_id": "Qwen/Qwen3-30B-A3B-Instruct-2507",
      "description": "Qwen3-30B-A3B-Instruct-2507 is a 30.5B-parameter mixture-of-experts language model from Qwen, with 3.3B active parameters per inference. It operates in non-thinking mode and is designed for high-quality instruction following, multilingual understanding, and...",
      "context_length": 262144,
      "max_completion_tokens": 262144,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.09,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1753806965
    },
    {
      "id": "qwen/qwen3-30b-a3b-thinking-2507",
      "name": "Qwen: Qwen3 30B A3B Thinking 2507",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-30b-a3b-thinking-2507",
      "hugging_face_id": "Qwen/Qwen3-30B-A3B-Thinking-2507",
      "description": "Qwen3-30B-A3B-Thinking-2507 is a 30B parameter Mixture-of-Experts reasoning model optimized for complex tasks requiring extended multi-step thinking. The model is designed specifically for “thinking mode,” where internal reasoning traces are separated...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.08,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1756399192
    },
    {
      "id": "qwen/qwen3-32b",
      "name": "Qwen: Qwen3 32B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-32b-04-28",
      "hugging_face_id": "Qwen/Qwen3-32B",
      "description": "Qwen3-32B is a dense 32.8B parameter causal language model from the Qwen3 series, optimized for both complex reasoning and efficient dialogue. It supports seamless switching between a \"thinking\" mode for...",
      "context_length": 40960,
      "max_completion_tokens": 40960,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.08,
        "output_per_million": 0.24,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1745875945
    },
    {
      "id": "qwen/qwen3-8b",
      "name": "Qwen: Qwen3 8B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-8b-04-28",
      "hugging_face_id": "Qwen/Qwen3-8B",
      "description": "Qwen3-8B is a dense 8.2B parameter causal language model from the Qwen3 series, designed for both reasoning-heavy tasks and efficient dialogue. It supports seamless switching between \"thinking\" mode for math,...",
      "context_length": 40960,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.05,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1745876632
    },
    {
      "id": "qwen/qwen3-coder-30b-a3b-instruct",
      "name": "Qwen: Qwen3 Coder 30B A3B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-coder-30b-a3b-instruct",
      "hugging_face_id": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
      "description": "Qwen3-Coder-30B-A3B-Instruct is a 30.5B parameter Mixture-of-Experts (MoE) model with 128 experts (8 active per forward pass), designed for advanced code generation, repository-scale understanding, and agentic tool use. Built on the...",
      "context_length": 160000,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.07,
        "output_per_million": 0.27,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1753972379
    },
    {
      "id": "qwen/qwen3-coder",
      "name": "Qwen: Qwen3 Coder 480B A35B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-coder-480b-a35b-07-25",
      "hugging_face_id": "Qwen/Qwen3-Coder-480B-A35B-Instruct",
      "description": "Qwen3-Coder-480B-A35B-Instruct is a Mixture-of-Experts (MoE) code generation model developed by the Qwen team. It is optimized for agentic coding tasks such as function calling, tool use, and long-context reasoning over...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.22,
        "output_per_million": 1.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1753230546
    },
    {
      "id": "qwen/qwen3-coder:free",
      "name": "Qwen: Qwen3 Coder 480B A35B (free)",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-coder-480b-a35b-07-25",
      "hugging_face_id": "Qwen/Qwen3-Coder-480B-A35B-Instruct",
      "description": "Qwen3-Coder-480B-A35B-Instruct is a Mixture-of-Experts (MoE) code generation model developed by the Qwen team. It is optimized for agentic coding tasks such as function calling, tool use, and long-context reasoning over...",
      "context_length": 262000,
      "max_completion_tokens": 262000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1753230546
    },
    {
      "id": "qwen/qwen3-coder-flash",
      "name": "Qwen: Qwen3 Coder Flash",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-coder-flash",
      "hugging_face_id": "",
      "description": "Qwen3 Coder Flash is Alibaba's fast and cost efficient version of their proprietary Qwen3 Coder Plus. It is a powerful coding agent model specializing in autonomous programming via tool calling...",
      "context_length": 1000000,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.195,
        "output_per_million": 0.975,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1758115536
    },
    {
      "id": "qwen/qwen3-coder-next",
      "name": "Qwen: Qwen3 Coder Next",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-coder-next-2025-02-03",
      "hugging_face_id": "Qwen/Qwen3-Coder-Next",
      "description": "Qwen3-Coder-Next is an open-weight causal language model optimized for coding agents and local development workflows. It uses a sparse MoE design with 80B total parameters and only 3B activated per...",
      "context_length": 262144,
      "max_completion_tokens": 262144,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.8,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1770164101
    },
    {
      "id": "qwen/qwen3-coder-plus",
      "name": "Qwen: Qwen3 Coder Plus",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-coder-plus",
      "hugging_face_id": "",
      "description": "Qwen3 Coder Plus is Alibaba's proprietary version of the Open Source Qwen3 Coder 480B A35B. It is a powerful coding agent model specializing in autonomous programming via tool calling and...",
      "context_length": 1000000,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.65,
        "output_per_million": 3.25,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1758662707
    },
    {
      "id": "qwen/qwen3-max",
      "name": "Qwen: Qwen3 Max",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-max",
      "hugging_face_id": "",
      "description": "Qwen3-Max is an updated release built on the Qwen3 series, offering major improvements in reasoning, instruction following, multilingual support, and long-tail knowledge coverage compared to the January 2025 version. It...",
      "context_length": 262144,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.78,
        "output_per_million": 3.9,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1758662808
    },
    {
      "id": "qwen/qwen3-max-thinking",
      "name": "Qwen: Qwen3 Max Thinking",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-max-thinking-20260123",
      "hugging_face_id": null,
      "description": "Qwen3-Max-Thinking is the flagship reasoning model in the Qwen3 series, designed for high-stakes cognitive tasks that require deep, multi-step reasoning. By significantly scaling model capacity and reinforcement learning compute, it...",
      "context_length": 262144,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.78,
        "output_per_million": 3.9,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1770671901
    },
    {
      "id": "qwen/qwen3-next-80b-a3b-instruct",
      "name": "Qwen: Qwen3 Next 80B A3B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-next-80b-a3b-instruct-2509",
      "hugging_face_id": "Qwen/Qwen3-Next-80B-A3B-Instruct",
      "description": "Qwen3-Next-80B-A3B-Instruct is an instruction-tuned chat model in the Qwen3-Next series optimized for fast, stable responses without “thinking” traces. It targets complex tasks across reasoning, code generation, knowledge QA, and multilingual...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.09,
        "output_per_million": 1.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1757612213
    },
    {
      "id": "qwen/qwen3-next-80b-a3b-instruct:free",
      "name": "Qwen: Qwen3 Next 80B A3B Instruct (free)",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-next-80b-a3b-instruct-2509",
      "hugging_face_id": "Qwen/Qwen3-Next-80B-A3B-Instruct",
      "description": "Qwen3-Next-80B-A3B-Instruct is an instruction-tuned chat model in the Qwen3-Next series optimized for fast, stable responses without “thinking” traces. It targets complex tasks across reasoning, code generation, knowledge QA, and multilingual...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1757612213
    },
    {
      "id": "qwen/qwen3-next-80b-a3b-thinking",
      "name": "Qwen: Qwen3 Next 80B A3B Thinking",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-next-80b-a3b-thinking-2509",
      "hugging_face_id": "Qwen/Qwen3-Next-80B-A3B-Thinking",
      "description": "Qwen3-Next-80B-A3B-Thinking is a reasoning-first chat model in the Qwen3-Next line that outputs structured “thinking” traces by default. It’s designed for hard multi-step problems; math proofs, code synthesis/debugging, logic, and agentic...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.0975,
        "output_per_million": 0.78,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1757612284
    },
    {
      "id": "qwen/qwen3-vl-235b-a22b-instruct",
      "name": "Qwen: Qwen3 VL 235B A22B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-vl-235b-a22b-instruct",
      "hugging_face_id": "Qwen/Qwen3-VL-235B-A22B-Instruct",
      "description": "Qwen3-VL-235B-A22B Instruct is an open-weight multimodal model that unifies strong text generation with visual understanding across images and video. The Instruct model targets general vision-language use (VQA, document parsing, chart/table...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.88,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1758668687
    },
    {
      "id": "qwen/qwen3-vl-235b-a22b-thinking",
      "name": "Qwen: Qwen3 VL 235B A22B Thinking",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-vl-235b-a22b-thinking",
      "hugging_face_id": "Qwen/Qwen3-VL-235B-A22B-Thinking",
      "description": "Qwen3-VL-235B-A22B Thinking is a multimodal model that unifies strong text generation with visual understanding across images and video. The Thinking model is optimized for multimodal reasoning in STEM and math....",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.26,
        "output_per_million": 2.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1758668690
    },
    {
      "id": "qwen/qwen3-vl-30b-a3b-instruct",
      "name": "Qwen: Qwen3 VL 30B A3B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-vl-30b-a3b-instruct",
      "hugging_face_id": "Qwen/Qwen3-VL-30B-A3B-Instruct",
      "description": "Qwen3-VL-30B-A3B-Instruct is a multimodal model that unifies strong text generation with visual understanding for images and videos. Its Instruct variant optimizes instruction-following for general multimodal tasks. It excels in perception...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.13,
        "output_per_million": 0.52,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1759794476
    },
    {
      "id": "qwen/qwen3-vl-30b-a3b-thinking",
      "name": "Qwen: Qwen3 VL 30B A3B Thinking",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-vl-30b-a3b-thinking",
      "hugging_face_id": "Qwen/Qwen3-VL-30B-A3B-Thinking",
      "description": "Qwen3-VL-30B-A3B-Thinking is a multimodal model that unifies strong text generation with visual understanding for images and videos. Its Thinking variant enhances reasoning in STEM, math, and complex tasks. It excels...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.13,
        "output_per_million": 1.56,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1759794479
    },
    {
      "id": "qwen/qwen3-vl-32b-instruct",
      "name": "Qwen: Qwen3 VL 32B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-vl-32b-instruct",
      "hugging_face_id": "Qwen/Qwen3-VL-32B-Instruct",
      "description": "Qwen3-VL-32B-Instruct is a large-scale multimodal vision-language model designed for high-precision understanding and reasoning across text, images, and video. With 32 billion parameters, it combines deep visual perception with advanced text...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.104,
        "output_per_million": 0.416,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1761231332
    },
    {
      "id": "qwen/qwen3-vl-8b-instruct",
      "name": "Qwen: Qwen3 VL 8B Instruct",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-vl-8b-instruct",
      "hugging_face_id": "Qwen/Qwen3-VL-8B-Instruct",
      "description": "Qwen3-VL-8B-Instruct is a multimodal vision-language model from the Qwen3-VL series, built for high-fidelity understanding and reasoning across text, images, and video. It features improved multimodal fusion with Interleaved-MRoPE for long-horizon...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.08,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1760463308
    },
    {
      "id": "qwen/qwen3-vl-8b-thinking",
      "name": "Qwen: Qwen3 VL 8B Thinking",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3-vl-8b-thinking",
      "hugging_face_id": "Qwen/Qwen3-VL-8B-Thinking",
      "description": "Qwen3-VL-8B-Thinking is the reasoning-optimized variant of the Qwen3-VL-8B multimodal model, designed for advanced visual and textual reasoning across complex scenes, documents, and temporal sequences. It integrates enhanced multimodal alignment and...",
      "context_length": 131072,
      "max_completion_tokens": 32768,
      "modality": "text+image->text",
      "input_modalities": [
        "image",
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.117,
        "output_per_million": 1.365,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1760463746
    },
    {
      "id": "qwen/qwen3.5-397b-a17b",
      "name": "Qwen: Qwen3.5 397B A17B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.5-397b-a17b-20260216",
      "hugging_face_id": "Qwen/Qwen3.5-397B-A17B",
      "description": "The Qwen3.5 series 397B-A17B native vision-language model is built on a hybrid architecture that integrates a linear attention mechanism with a sparse mixture-of-experts model, achieving higher inference efficiency. It delivers...",
      "context_length": 262144,
      "max_completion_tokens": 65536,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.39,
        "output_per_million": 2.34,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1771223018
    },
    {
      "id": "qwen/qwen3.5-plus-02-15",
      "name": "Qwen: Qwen3.5 Plus 2026-02-15",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.5-plus-20260216",
      "hugging_face_id": "",
      "description": "The Qwen3.5 native vision-language series Plus models are built on a hybrid architecture that integrates linear attention mechanisms with sparse mixture-of-experts models, achieving higher inference efficiency. In a variety of...",
      "context_length": 1000000,
      "max_completion_tokens": 65536,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.26,
        "output_per_million": 1.56,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1771229416
    },
    {
      "id": "qwen/qwen3.5-122b-a10b",
      "name": "Qwen: Qwen3.5-122B-A10B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.5-122b-a10b-20260224",
      "hugging_face_id": "Qwen/Qwen3.5-122B-A10B",
      "description": "The Qwen3.5 122B-A10B native vision-language model is built on a hybrid architecture that integrates a linear attention mechanism with a sparse mixture-of-experts model, achieving higher inference efficiency. In terms of...",
      "context_length": 262144,
      "max_completion_tokens": 65536,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.26,
        "output_per_million": 2.08,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1772053789
    },
    {
      "id": "qwen/qwen3.5-27b",
      "name": "Qwen: Qwen3.5-27B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.5-27b-20260224",
      "hugging_face_id": "Qwen/Qwen3.5-27B",
      "description": "The Qwen3.5 27B native vision-language Dense model incorporates a linear attention mechanism, delivering fast response times while balancing inference speed and performance. Its overall capabilities are comparable to those of...",
      "context_length": 262144,
      "max_completion_tokens": 65536,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.195,
        "output_per_million": 1.56,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1772053810
    },
    {
      "id": "qwen/qwen3.5-35b-a3b",
      "name": "Qwen: Qwen3.5-35B-A3B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.5-35b-a3b-20260224",
      "hugging_face_id": "Qwen/Qwen3.5-35B-A3B",
      "description": "The Qwen3.5 Series 35B-A3B is a native vision-language model designed with a hybrid architecture that integrates linear attention mechanisms and a sparse mixture-of-experts model, achieving higher inference efficiency. Its overall...",
      "context_length": 262144,
      "max_completion_tokens": 65536,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1625,
        "output_per_million": 1.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1772053822
    },
    {
      "id": "qwen/qwen3.5-9b",
      "name": "Qwen: Qwen3.5-9B",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.5-9b-20260310",
      "hugging_face_id": "Qwen/Qwen3.5-9B",
      "description": "Qwen3.5-9B is a multimodal foundation model from the Qwen3.5 family, designed to deliver strong reasoning, coding, and visual understanding in an efficient 9B-parameter architecture. It uses a unified vision-language design...",
      "context_length": 262144,
      "max_completion_tokens": 0,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.15,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1773152396
    },
    {
      "id": "qwen/qwen3.5-flash-02-23",
      "name": "Qwen: Qwen3.5-Flash",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.5-flash-20260224",
      "hugging_face_id": null,
      "description": "The Qwen3.5 native vision-language Flash models are built on a hybrid architecture that integrates a linear attention mechanism with a sparse mixture-of-experts model, achieving higher inference efficiency. Compared to the...",
      "context_length": 1000000,
      "max_completion_tokens": 65536,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.065,
        "output_per_million": 0.26,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1772053776
    },
    {
      "id": "qwen/qwen3.6-plus",
      "name": "Qwen: Qwen3.6 Plus",
      "provider": "qwen",
      "canonical_slug": "qwen/qwen3.6-plus-04-02",
      "hugging_face_id": "",
      "description": "Qwen 3.6 Plus builds on a hybrid architecture that combines efficient linear attention with sparse mixture-of-experts routing, enabling strong scalability and high-performance inference. Compared to the 3.5 series, it delivers...",
      "context_length": 1000000,
      "max_completion_tokens": 65536,
      "modality": "text+image+video->text",
      "input_modalities": [
        "text",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen3",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.325,
        "output_per_million": 1.95,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1775133557
    },
    {
      "id": "rekaai/reka-edge",
      "name": "Reka Edge",
      "provider": "rekaai",
      "canonical_slug": "rekaai/reka-edge-2603",
      "hugging_face_id": "RekaAI/reka-edge-2603",
      "description": "Reka Edge is an extremely efficient 7B multimodal vision-language model that accepts image/video+text inputs and generates text outputs. This model is optimized specifically to deliver industry-leading performance in image understanding,...",
      "context_length": 16384,
      "max_completion_tokens": 16384,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1774026965
    },
    {
      "id": "rekaai/reka-flash-3",
      "name": "Reka Flash 3",
      "provider": "rekaai",
      "canonical_slug": "rekaai/reka-flash-3",
      "hugging_face_id": "RekaAI/reka-flash-3",
      "description": "Reka Flash 3 is a general-purpose, instruction-tuned large language model with 21 billion parameters, developed by Reka. It excels at general chat, coding tasks, instruction-following, and function calling. Featuring a...",
      "context_length": 65536,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1741812813
    },
    {
      "id": "relace/relace-apply-3",
      "name": "Relace: Relace Apply 3",
      "provider": "relace",
      "canonical_slug": "relace/relace-apply-3",
      "hugging_face_id": "",
      "description": "Relace Apply 3 is a specialized code-patching LLM that merges AI-suggested edits straight into your source files. It can apply updates from GPT-4o, Claude, and others into your files at...",
      "context_length": 256000,
      "max_completion_tokens": 128000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.85,
        "output_per_million": 1.25,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "seed",
        "stop"
      ],
      "created": 1758891572
    },
    {
      "id": "relace/relace-search",
      "name": "Relace: Relace Search",
      "provider": "relace",
      "canonical_slug": "relace/relace-search-20251208",
      "hugging_face_id": null,
      "description": "The relace-search model uses 4-12 `view_file` and `grep` tools in parallel to explore a codebase and return relevant files to the user request. In contrast to RAG, relace-search performs agentic...",
      "context_length": 256000,
      "max_completion_tokens": 128000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.0,
        "output_per_million": 3.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1765213560
    },
    {
      "id": "sao10k/l3-lunaris-8b",
      "name": "Sao10K: Llama 3 8B Lunaris",
      "provider": "sao10k",
      "canonical_slug": "sao10k/l3-lunaris-8b",
      "hugging_face_id": "Sao10K/L3-8B-Lunaris-v1",
      "description": "Lunaris 8B is a versatile generalist and roleplaying model based on Llama 3. It's a strategic merge of multiple models, designed to balance creativity with improved logic and general knowledge....",
      "context_length": 8192,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.04,
        "output_per_million": 0.05,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1723507200
    },
    {
      "id": "sao10k/l3.1-70b-hanami-x1",
      "name": "Sao10K: Llama 3.1 70B Hanami x1",
      "provider": "sao10k",
      "canonical_slug": "sao10k/l3.1-70b-hanami-x1",
      "hugging_face_id": "Sao10K/L3.1-70B-Hanami-x1",
      "description": "This is [Sao10K](/sao10k)'s experiment over [Euryale v2.2](/sao10k/l3.1-euryale-70b).",
      "context_length": 16000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 3.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1736302854
    },
    {
      "id": "sao10k/l3.1-euryale-70b",
      "name": "Sao10K: Llama 3.1 Euryale 70B v2.2",
      "provider": "sao10k",
      "canonical_slug": "sao10k/l3.1-euryale-70b",
      "hugging_face_id": "Sao10K/L3.1-70B-Euryale-v2.2",
      "description": "Euryale L3.1 70B v2.2 is a model focused on creative roleplay from [Sao10k](https://ko-fi.com/sao10k). It is the successor of [Euryale L3 70B v2.1](/models/sao10k/l3-euryale-70b).",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.85,
        "output_per_million": 0.85,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1724803200
    },
    {
      "id": "sao10k/l3.3-euryale-70b",
      "name": "Sao10K: Llama 3.3 Euryale 70B",
      "provider": "sao10k",
      "canonical_slug": "sao10k/l3.3-euryale-70b-v2.3",
      "hugging_face_id": "Sao10K/L3.3-70B-Euryale-v2.3",
      "description": "Euryale L3.3 70B is a model focused on creative roleplay from [Sao10k](https://ko-fi.com/sao10k). It is the successor of [Euryale L3 70B v2.2](/models/sao10k/l3-euryale-70b).",
      "context_length": 131072,
      "max_completion_tokens": 16384,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.65,
        "output_per_million": 0.75,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1734535928
    },
    {
      "id": "sao10k/l3-euryale-70b",
      "name": "Sao10k: Llama 3 Euryale 70B v2.1",
      "provider": "sao10k",
      "canonical_slug": "sao10k/l3-euryale-70b",
      "hugging_face_id": "Sao10K/L3-70B-Euryale-v2.1",
      "description": "Euryale 70B v2.1 is a model focused on creative roleplay from [Sao10k](https://ko-fi.com/sao10k). - Better prompt adherence. - Better anatomy / spatial awareness. - Adapts much better to unique and custom...",
      "context_length": 8192,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama3",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.48,
        "output_per_million": 1.48,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1718668800
    },
    {
      "id": "stepfun/step-3.5-flash",
      "name": "StepFun: Step 3.5 Flash",
      "provider": "stepfun",
      "canonical_slug": "stepfun/step-3.5-flash",
      "hugging_face_id": "stepfun-ai/Step-3.5-Flash",
      "description": "Step 3.5 Flash is StepFun's most capable open-source foundation model. Built on a sparse Mixture of Experts (MoE) architecture, it selectively activates only 11B of its 196B parameters per token....",
      "context_length": 262144,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "reasoning_effort",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1769728337
    },
    {
      "id": "switchpoint/router",
      "name": "Switchpoint Router",
      "provider": "switchpoint",
      "canonical_slug": "switchpoint/router",
      "hugging_face_id": "",
      "description": "Switchpoint AI's router instantly analyzes your request and directs it to the optimal AI from an ever-evolving library. As the world of LLMs advances, our router gets smarter, ensuring you...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.85,
        "output_per_million": 3.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1752272899
    },
    {
      "id": "tencent/hunyuan-a13b-instruct",
      "name": "Tencent: Hunyuan A13B Instruct",
      "provider": "tencent",
      "canonical_slug": "tencent/hunyuan-a13b-instruct",
      "hugging_face_id": "tencent/Hunyuan-A13B-Instruct",
      "description": "Hunyuan-A13B is a 13B active parameter Mixture-of-Experts (MoE) language model developed by Tencent, with a total parameter count of 80B and support for reasoning via Chain-of-Thought. It offers competitive benchmark...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.14,
        "output_per_million": 0.57,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "reasoning",
        "response_format",
        "structured_outputs",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1751987664
    },
    {
      "id": "thedrummer/cydonia-24b-v4.1",
      "name": "TheDrummer: Cydonia 24B V4.1",
      "provider": "thedrummer",
      "canonical_slug": "thedrummer/cydonia-24b-v4.1",
      "hugging_face_id": "thedrummer/cydonia-24b-v4.1",
      "description": "Uncensored and creative writing model based on Mistral Small 3.2 24B with good recall, prompt adherence, and intelligence.",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1758931878
    },
    {
      "id": "thedrummer/rocinante-12b",
      "name": "TheDrummer: Rocinante 12B",
      "provider": "thedrummer",
      "canonical_slug": "thedrummer/rocinante-12b",
      "hugging_face_id": "TheDrummer/Rocinante-12B-v1.1",
      "description": "Rocinante 12B is designed for engaging storytelling and rich prose. Early testers have reported: - Expanded vocabulary with unique and expressive word choices - Enhanced creativity for vivid narratives -...",
      "context_length": 32768,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Qwen",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.17,
        "output_per_million": 0.43,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1727654400
    },
    {
      "id": "thedrummer/skyfall-36b-v2",
      "name": "TheDrummer: Skyfall 36B V2",
      "provider": "thedrummer",
      "canonical_slug": "thedrummer/skyfall-36b-v2",
      "hugging_face_id": "TheDrummer/Skyfall-36B-v2",
      "description": "Skyfall 36B v2 is an enhanced iteration of Mistral Small 2501, specifically fine-tuned for improved creativity, nuanced writing, role-playing, and coherent storytelling.",
      "context_length": 32768,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.55,
        "output_per_million": 0.8,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1741636566
    },
    {
      "id": "thedrummer/unslopnemo-12b",
      "name": "TheDrummer: UnslopNemo 12B",
      "provider": "thedrummer",
      "canonical_slug": "thedrummer/unslopnemo-12b",
      "hugging_face_id": "TheDrummer/UnslopNemo-12B-v4.1",
      "description": "UnslopNemo v4.1 is the latest addition from the creator of Rocinante, designed for adventure writing and role-play scenarios.",
      "context_length": 32768,
      "max_completion_tokens": 32768,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Mistral",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1731103448
    },
    {
      "id": "tngtech/deepseek-r1t2-chimera",
      "name": "TNG: DeepSeek R1T2 Chimera",
      "provider": "tngtech",
      "canonical_slug": "tngtech/deepseek-r1t2-chimera",
      "hugging_face_id": "tngtech/DeepSeek-TNG-R1T2-Chimera",
      "description": "DeepSeek-TNG-R1T2-Chimera is the second-generation Chimera model from TNG Tech. It is a 671 B-parameter mixture-of-experts text-generation model assembled from DeepSeek-AI’s R1-0528, R1, and V3-0324 checkpoints with an Assembly-of-Experts merge. The...",
      "context_length": 163840,
      "max_completion_tokens": 163840,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "DeepSeek",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 1.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1751986985
    },
    {
      "id": "undi95/remm-slerp-l2-13b",
      "name": "ReMM SLERP 13B",
      "provider": "undi95",
      "canonical_slug": "undi95/remm-slerp-l2-13b",
      "hugging_face_id": "Undi95/ReMM-SLERP-L2-13B",
      "description": "A recreation trial of the original MythoMax-L2-B13 but with updated models. #merge",
      "context_length": 6144,
      "max_completion_tokens": 4096,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Llama2",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.45,
        "output_per_million": 0.65,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "top_a",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1689984000
    },
    {
      "id": "upstage/solar-pro-3",
      "name": "Upstage: Solar Pro 3",
      "provider": "upstage",
      "canonical_slug": "upstage/solar-pro-3",
      "hugging_face_id": "",
      "description": "Solar Pro 3 is Upstage's powerful Mixture-of-Experts (MoE) language model. With 102B total parameters and 12B active parameters per forward pass, it delivers exceptional performance while maintaining computational efficiency. Optimized...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.15,
        "output_per_million": 0.6,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools"
      ],
      "created": 1769481200
    },
    {
      "id": "writer/palmyra-x5",
      "name": "Writer: Palmyra X5",
      "provider": "writer",
      "canonical_slug": "writer/palmyra-x5-20250428",
      "hugging_face_id": "",
      "description": "Palmyra X5 is Writer's most advanced model, purpose-built for building and scaling AI agents across the enterprise. It delivers industry-leading speed and efficiency on context windows up to 1 million...",
      "context_length": 1040000,
      "max_completion_tokens": 8192,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": false,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.6,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": true,
      "supported_parameters": [
        "max_tokens",
        "stop",
        "temperature",
        "top_k",
        "top_p"
      ],
      "created": 1769003823
    },
    {
      "id": "x-ai/grok-3",
      "name": "xAI: Grok 3",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-3",
      "hugging_face_id": "",
      "description": "Grok 3 is the latest model from xAI. It's their flagship model that excels at enterprise use cases like data extraction, coding, and text summarization. Possesses deep domain knowledge in...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1749582908
    },
    {
      "id": "x-ai/grok-3-beta",
      "name": "xAI: Grok 3 Beta",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-3-beta",
      "hugging_face_id": "",
      "description": "Grok 3 is the latest model from xAI. It's their flagship model that excels at enterprise use cases like data extraction, coding, and text summarization. Possesses deep domain knowledge in...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "logprobs",
        "max_tokens",
        "presence_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1744240068
    },
    {
      "id": "x-ai/grok-3-mini",
      "name": "xAI: Grok 3 Mini",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-3-mini",
      "hugging_face_id": "",
      "description": "A lightweight model that thinks before responding. Fast, smart, and great for logic-based tasks that do not require deep domain knowledge. The raw thinking traces are accessible.",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1749583245
    },
    {
      "id": "x-ai/grok-3-mini-beta",
      "name": "xAI: Grok 3 Mini Beta",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-3-mini-beta",
      "hugging_face_id": "",
      "description": "Grok 3 Mini is a lightweight, smaller thinking model. Unlike traditional models that generate answers immediately, Grok 3 Mini thinks before responding. It’s ideal for reasoning-heavy tasks that don’t demand...",
      "context_length": 131072,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1744240195
    },
    {
      "id": "x-ai/grok-4",
      "name": "xAI: Grok 4",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-4-07-09",
      "hugging_face_id": "",
      "description": "Grok 4 is xAI's latest reasoning model with a 256k context window. It supports parallel tool calling, structured outputs, and both image and text inputs. Note that reasoning is not...",
      "context_length": 256000,
      "max_completion_tokens": 0,
      "modality": "text+image+file->text",
      "input_modalities": [
        "image",
        "text",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1752087689
    },
    {
      "id": "x-ai/grok-4-fast",
      "name": "xAI: Grok 4 Fast",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-4-fast",
      "hugging_face_id": "",
      "description": "Grok 4 Fast is xAI's latest multimodal model with SOTA cost-efficiency and a 2M token context window. It comes in two flavors: non-reasoning and reasoning. Read more about the model...",
      "context_length": 2000000,
      "max_completion_tokens": 30000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1758240090
    },
    {
      "id": "x-ai/grok-4.1-fast",
      "name": "xAI: Grok 4.1 Fast",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-4.1-fast",
      "hugging_face_id": "",
      "description": "Grok 4.1 Fast is xAI's best agentic tool calling model that shines in real-world use cases like customer support and deep research. 2M context window. Reasoning can be enabled/disabled using...",
      "context_length": 2000000,
      "max_completion_tokens": 30000,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 0.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1763587502
    },
    {
      "id": "x-ai/grok-4.20",
      "name": "xAI: Grok 4.20",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-4.20-20260309",
      "hugging_face_id": "",
      "description": "Grok 4.20 is xAI's newest flagship model with industry-leading speed and agentic tool calling capabilities. It combines the lowest hallucination rate on the market with strict prompt adherance, delivering consistently...",
      "context_length": 2000000,
      "max_completion_tokens": 0,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1774979019
    },
    {
      "id": "x-ai/grok-4.20-multi-agent",
      "name": "xAI: Grok 4.20 Multi-Agent",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-4.20-multi-agent-20260309",
      "hugging_face_id": "",
      "description": "Grok 4.20 Multi-Agent is a variant of xAI’s Grok 4.20 designed for collaborative, agent-based workflows. Multiple agents operate in parallel to conduct deep research, coordinate tool use, and synthesize information...",
      "context_length": 2000000,
      "max_completion_tokens": 0,
      "modality": "text+image+file->text",
      "input_modalities": [
        "text",
        "image",
        "file"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": false,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": true,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 2.0,
        "output_per_million": 6.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "structured_outputs",
        "temperature",
        "top_logprobs",
        "top_p"
      ],
      "created": 1774979158
    },
    {
      "id": "x-ai/grok-code-fast-1",
      "name": "xAI: Grok Code Fast 1",
      "provider": "x-ai",
      "canonical_slug": "x-ai/grok-code-fast-1",
      "hugging_face_id": "",
      "description": "Grok Code Fast 1 is a speedy and economical reasoning model that excels at agentic coding. With reasoning traces visible in the response, developers can steer Grok Code for high-quality...",
      "context_length": 256000,
      "max_completion_tokens": 10000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Grok",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.2,
        "output_per_million": 1.5,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "logprobs",
        "max_tokens",
        "reasoning",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p"
      ],
      "created": 1756238927
    },
    {
      "id": "xiaomi/mimo-v2-flash",
      "name": "Xiaomi: MiMo-V2-Flash",
      "provider": "xiaomi",
      "canonical_slug": "xiaomi/mimo-v2-flash-20251210",
      "hugging_face_id": "XiaomiMiMo/MiMo-V2-Flash",
      "description": "MiMo-V2-Flash is an open-source foundation language model developed by Xiaomi. It is a Mixture-of-Experts model with 309B total parameters and 15B active parameters, adopting hybrid attention architecture. MiMo-V2-Flash supports a...",
      "context_length": 262144,
      "max_completion_tokens": 65536,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.09,
        "output_per_million": 0.29,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1765731308
    },
    {
      "id": "xiaomi/mimo-v2-omni",
      "name": "Xiaomi: MiMo-V2-Omni",
      "provider": "xiaomi",
      "canonical_slug": "xiaomi/mimo-v2-omni-20260318",
      "hugging_face_id": "",
      "description": "MiMo-V2-Omni is a frontier omni-modal model that natively processes image, video, and audio inputs within a unified architecture. It combines strong multimodal perception with agentic capability - visual grounding, multi-step...",
      "context_length": 262144,
      "max_completion_tokens": 65536,
      "modality": "text+image+audio+video->text",
      "input_modalities": [
        "text",
        "audio",
        "image",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": true,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.4,
        "output_per_million": 2.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1773863703
    },
    {
      "id": "xiaomi/mimo-v2-pro",
      "name": "Xiaomi: MiMo-V2-Pro",
      "provider": "xiaomi",
      "canonical_slug": "xiaomi/mimo-v2-pro-20260318",
      "hugging_face_id": "",
      "description": "MiMo-V2-Pro is Xiaomi's flagship foundation model, featuring over 1T total parameters and a 1M context length, deeply optimized for agentic scenarios. It is highly adaptable to general agent frameworks like...",
      "context_length": 1048576,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.0,
        "output_per_million": 3.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "response_format",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1773863643
    },
    {
      "id": "z-ai/glm-4-32b",
      "name": "Z.ai: GLM 4 32B ",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4-32b-0414",
      "hugging_face_id": "",
      "description": "GLM 4 32B is a cost-effective foundation language model. It can efficiently perform complex tasks and has significantly enhanced capabilities in tool use, online search, and code-related intelligent tasks. It...",
      "context_length": 128000,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": false,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.1,
        "output_per_million": 0.1,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "max_tokens",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1753376617
    },
    {
      "id": "z-ai/glm-4.5",
      "name": "Z.ai: GLM 4.5",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.5",
      "hugging_face_id": "zai-org/GLM-4.5",
      "description": "GLM-4.5 is our latest flagship foundation model, purpose-built for agent-based applications. It leverages a Mixture-of-Experts (MoE) architecture and supports a context length of up to 128k tokens. GLM-4.5 delivers significantly...",
      "context_length": 131072,
      "max_completion_tokens": 98304,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.6,
        "output_per_million": 2.2,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1753471347
    },
    {
      "id": "z-ai/glm-4.5-air",
      "name": "Z.ai: GLM 4.5 Air",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.5-air",
      "hugging_face_id": "zai-org/GLM-4.5-Air",
      "description": "GLM-4.5-Air is the lightweight variant of our latest flagship model family, also purpose-built for agent-centric applications. Like GLM-4.5, it adopts the Mixture-of-Experts (MoE) architecture but with a more compact parameter...",
      "context_length": 131072,
      "max_completion_tokens": 98304,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.13,
        "output_per_million": 0.85,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1753471258
    },
    {
      "id": "z-ai/glm-4.5-air:free",
      "name": "Z.ai: GLM 4.5 Air (free)",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.5-air",
      "hugging_face_id": "zai-org/GLM-4.5-Air",
      "description": "GLM-4.5-Air is the lightweight variant of our latest flagship model family, also purpose-built for agent-centric applications. Like GLM-4.5, it adopts the Mixture-of-Experts (MoE) architecture but with a more compact parameter...",
      "context_length": 131072,
      "max_completion_tokens": 96000,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.0,
        "output_per_million": 0.0,
        "is_free": true
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1753471258
    },
    {
      "id": "z-ai/glm-4.5v",
      "name": "Z.ai: GLM 4.5V",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.5v",
      "hugging_face_id": "zai-org/GLM-4.5V",
      "description": "GLM-4.5V is a vision-language foundation model for multimodal agent applications. Built on a Mixture-of-Experts (MoE) architecture with 106B parameters and 12B activated parameters, it achieves state-of-the-art results in video understanding,...",
      "context_length": 65536,
      "max_completion_tokens": 16384,
      "modality": "text+image->text",
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 0.6,
        "output_per_million": 1.8,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1754922288
    },
    {
      "id": "z-ai/glm-4.6",
      "name": "Z.ai: GLM 4.6",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.6",
      "hugging_face_id": "zai-org/GLM-4.6",
      "description": "Compared with GLM-4.5, this generation brings several key improvements: Longer context window: The context window has been expanded from 128K to 200K tokens, enabling the model to handle more complex...",
      "context_length": 204800,
      "max_completion_tokens": 204800,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.39,
        "output_per_million": 1.9,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1759235576
    },
    {
      "id": "z-ai/glm-4.6v",
      "name": "Z.ai: GLM 4.6V",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.6-20251208",
      "hugging_face_id": "zai-org/GLM-4.6V",
      "description": "GLM-4.6V is a large multimodal model designed for high-fidelity visual understanding and long-context reasoning across images, documents, and mixed media. It supports up to 128K tokens, processes complex page layouts...",
      "context_length": 131072,
      "max_completion_tokens": 131072,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.3,
        "output_per_million": 0.9,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1765207462
    },
    {
      "id": "z-ai/glm-4.7",
      "name": "Z.ai: GLM 4.7",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.7-20251222",
      "hugging_face_id": "zai-org/GLM-4.7",
      "description": "GLM-4.7 is Z.ai’s latest flagship model, featuring upgrades in two key areas: enhanced programming capabilities and more stable multi-step reasoning/execution. It demonstrates significant improvements in executing complex agent tasks while...",
      "context_length": 202752,
      "max_completion_tokens": 65535,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.39,
        "output_per_million": 1.75,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1766378014
    },
    {
      "id": "z-ai/glm-4.7-flash",
      "name": "Z.ai: GLM 4.7 Flash",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-4.7-flash-20260119",
      "hugging_face_id": "zai-org/GLM-4.7-Flash",
      "description": "As a 30B-class SOTA model, GLM-4.7-Flash offers a new option that balances performance and efficiency. It is further optimized for agentic coding use cases, strengthening coding capabilities, long-horizon task planning,...",
      "context_length": 202752,
      "max_completion_tokens": 0,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.06,
        "output_per_million": 0.4,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1768833913
    },
    {
      "id": "z-ai/glm-5",
      "name": "Z.ai: GLM 5",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-5-20260211",
      "hugging_face_id": "zai-org/GLM-5",
      "description": "GLM-5 is Z.ai’s flagship open-source foundation model engineered for complex systems design and long-horizon agent workflows. Built for expert developers, it delivers production-grade performance on large-scale programming tasks, rivaling leading...",
      "context_length": 80000,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.72,
        "output_per_million": 2.3,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1770829182
    },
    {
      "id": "z-ai/glm-5-turbo",
      "name": "Z.ai: GLM 5 Turbo",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-5-turbo-20260315",
      "hugging_face_id": "",
      "description": "GLM-5 Turbo is a new model from Z.ai designed for fast inference and strong performance in agent-driven environments such as OpenClaw scenarios. It is deeply optimized for real-world agent workflows...",
      "context_length": 202752,
      "max_completion_tokens": 131072,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.2,
        "output_per_million": 4.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "max_tokens",
        "min_p",
        "presence_penalty",
        "reasoning",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_p"
      ],
      "created": 1773583573
    },
    {
      "id": "z-ai/glm-5.1",
      "name": "Z.ai: GLM 5.1",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-5.1-20260406",
      "hugging_face_id": "zai-org/GLM-5.1",
      "description": "GLM-5.1 delivers a major leap in coding capability, with particularly significant gains in handling long-horizon tasks. Unlike previous models built around minute-level interactions, GLM-5.1 can work independently and continuously on...",
      "context_length": 202752,
      "max_completion_tokens": 65535,
      "modality": "text->text",
      "input_modalities": [
        "text"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": false,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": true,
      "pricing": {
        "input_per_million": 0.95,
        "output_per_million": 3.15,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "logit_bias",
        "logprobs",
        "max_tokens",
        "min_p",
        "parallel_tool_calls",
        "presence_penalty",
        "reasoning",
        "reasoning_effort",
        "repetition_penalty",
        "response_format",
        "seed",
        "stop",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_k",
        "top_logprobs",
        "top_p"
      ],
      "created": 1775578025
    },
    {
      "id": "z-ai/glm-5v-turbo",
      "name": "Z.ai: GLM 5V Turbo",
      "provider": "z-ai",
      "canonical_slug": "z-ai/glm-5v-turbo-20260401",
      "hugging_face_id": "",
      "description": "GLM-5V-Turbo is Z.ai’s first native multimodal agent foundation model, built for vision-based coding and agent-driven tasks. It natively handles image, video, and text inputs, excels at long-horizon planning, complex coding,...",
      "context_length": 202752,
      "max_completion_tokens": 131072,
      "modality": "text+image+video->text",
      "input_modalities": [
        "image",
        "text",
        "video"
      ],
      "output_modalities": [
        "text"
      ],
      "tokenizer": "Other",
      "supports_reasoning": true,
      "supports_tools": true,
      "supports_vision": true,
      "supports_audio": false,
      "supports_files": false,
      "supports_structured_output": false,
      "pricing": {
        "input_per_million": 1.2,
        "output_per_million": 4.0,
        "is_free": false
      },
      "is_moderated": false,
      "supported_parameters": [
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "created": 1775061458
    }
  ]
}
```


---



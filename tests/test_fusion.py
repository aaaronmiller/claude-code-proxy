import json

from src.core.fusion import (
    OPENROUTER_FUSION_MODEL,
    apply_fusion_to_openai_request,
    get_fusion_profile,
    is_fusion_model,
)


def test_fusion_aliases_include_local_and_openrouter_names(clean_env):
    assert is_fusion_model("fusion")
    assert is_fusion_model("ccp/fusion")
    assert is_fusion_model("openrouter/fusion")
    assert is_fusion_model("fusion/research")
    assert not is_fusion_model("openrouter/free")


def test_apply_fusion_uses_extra_body_plugins(clean_env):
    clean_env.setenv("FUSION_FREE_ANALYSIS_MODELS", "openrouter/free,deepseek/deepseek-chat-v3.1:free")
    clean_env.setenv("FUSION_FREE_MODEL", "openrouter/free")
    request = {
        "model": "fusion",
        "messages": [{"role": "user", "content": "Compare options"}],
        "extra_body": {"provider": {"require_parameters": True}},
    }

    mutated, profile = apply_fusion_to_openai_request(request)

    assert profile is not None
    assert profile.name == "free"
    assert mutated["model"] == OPENROUTER_FUSION_MODEL
    assert "plugins" not in mutated
    assert mutated["extra_body"]["provider"] == {"require_parameters": True}
    assert mutated["extra_body"]["plugins"] == [
        {
            "id": "fusion",
            "enabled": True,
            "analysis_models": [
                "openrouter/free",
                "deepseek/deepseek-chat-v3.1:free",
            ],
            "model": "openrouter/free",
        }
    ]


def test_apply_fusion_does_not_force_when_user_tools_exist(clean_env):
    clean_env.setenv("FUSION_FREE_FORCE", "true")
    request = {
        "model": "fusion",
        "messages": [{"role": "user", "content": "Compare options"}],
        "tools": [{"type": "function", "function": {"name": "read_file"}}],
    }

    mutated, profile = apply_fusion_to_openai_request(request)

    assert profile is not None
    assert "tool_choice" not in mutated


def test_fusion_profiles_json_overrides_env(clean_env):
    clean_env.setenv(
        "FUSION_PROFILES",
        json.dumps(
            {
                "research": {
                    "analysis_models": ["openrouter/free"],
                    "model": "openrouter/free",
                    "max_tool_calls": 3,
                    "force": True,
                }
            }
        ),
    )

    profile = get_fusion_profile("research")

    assert profile.analysis_models == ("openrouter/free",)
    assert profile.model == "openrouter/free"
    assert profile.max_tool_calls == 3
    assert profile.force is True


def test_fusion_model_can_select_named_profile(clean_env):
    clean_env.setenv(
        "FUSION_PROFILES",
        json.dumps(
            {
                "research": {
                    "analysis_models": ["deepseek/deepseek-chat-v3.1:free"],
                    "model": "openrouter/free",
                }
            }
        ),
    )

    mutated, profile = apply_fusion_to_openai_request(
        {"model": "fusion/research", "messages": [{"role": "user", "content": "x"}]}
    )

    assert profile is not None
    assert profile.name == "research"
    assert mutated["model"] == OPENROUTER_FUSION_MODEL
    assert mutated["extra_body"]["plugins"][0]["analysis_models"] == [
        "deepseek/deepseek-chat-v3.1:free"
    ]

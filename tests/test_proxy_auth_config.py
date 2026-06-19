from src.core.config import Config


def test_anthropic_api_key_no_longer_enables_proxy_auth_by_default(clean_env):
    clean_env.setenv("BIG_API_KEY", "sk-test-1234567890123456789012345678")
    clean_env.setenv("ANTHROPIC_API_KEY", "sk-ant-client-side-key-1234567890")

    config = Config()

    assert config.anthropic_api_key is None
    assert config.validate_client_api_key("pass") is True


def test_proxy_auth_key_still_enables_proxy_auth(clean_env):
    clean_env.setenv("BIG_API_KEY", "sk-test-1234567890123456789012345678")
    clean_env.setenv("PROXY_AUTH_KEY", "pass")

    config = Config()

    assert config.anthropic_api_key == "pass"
    assert config.validate_client_api_key("pass") is True
    assert config.validate_client_api_key("wrong") is False


def test_legacy_proxy_auth_can_be_explicitly_reenabled(clean_env):
    clean_env.setenv("BIG_API_KEY", "sk-test-1234567890123456789012345678")
    clean_env.setenv("ANTHROPIC_API_KEY", "legacy-secret")
    clean_env.setenv("ENABLE_LEGACY_PROXY_AUTH", "true")

    config = Config()

    assert config.anthropic_api_key == "legacy-secret"
    assert config.validate_client_api_key("legacy-secret") is True
    assert config.validate_client_api_key("pass") is False

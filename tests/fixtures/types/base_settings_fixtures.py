import pytest
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SecretsSettingsSource,
)


@pytest.fixture
def settings_sources() -> dict[str, PydanticBaseSettingsSource]:
    """Fixture that provides all settings sources needed for testing.

    Returns:
        dict[str, PydanticBaseSettingsSource]: Dictionary containing all settings sources.
    """
    return {
        "init_settings": InitSettingsSource(BaseSettings, init_kwargs={}),
        "env_settings": EnvSettingsSource(BaseSettings),
        "dotenv_settings": DotEnvSettingsSource(
            BaseSettings, env_file=None, env_file_encoding=None
        ),
        "file_secret_settings": SecretsSettingsSource(BaseSettings, secrets_dir=None),
    }

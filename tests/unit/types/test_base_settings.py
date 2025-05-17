import pytest
from pydantic_settings import PydanticBaseSettingsSource, TomlConfigSettingsSource

from fastgear.types.base_settings import TomlBaseSettings
from tests.fixtures.types.base_settings_fixtures import settings_sources  # noqa: F401


@pytest.mark.describe("🧪  TomlBaseSettings")
class TestTomlBaseSettings:
    @pytest.mark.it("✅  Should customize settings sources correctly")
    def test_settings_customise_sources(
        self, settings_sources: dict[str, PydanticBaseSettingsSource]
    ) -> None:
        sources = TomlBaseSettings.settings_customise_sources(
            TomlBaseSettings,
            settings_sources["init_settings"],
            settings_sources["env_settings"],
            settings_sources["dotenv_settings"],
            settings_sources["file_secret_settings"],
        )

        assert len(sources) == 2  # noqa: PLR2004
        assert sources[0] == settings_sources["env_settings"]
        assert isinstance(sources[1], TomlConfigSettingsSource)
        assert sources[1].settings_cls == TomlBaseSettings

    @pytest.mark.it("✅  Should prioritize environment variables over TOML config")
    def test_settings_source_priority(
        self, settings_sources: dict[str, PydanticBaseSettingsSource]
    ) -> None:
        sources = TomlBaseSettings.settings_customise_sources(
            TomlBaseSettings,
            settings_sources["init_settings"],
            settings_sources["env_settings"],
            settings_sources["dotenv_settings"],
            settings_sources["file_secret_settings"],
        )

        assert sources[0] == settings_sources["env_settings"]
        assert isinstance(sources[1], TomlConfigSettingsSource)

    @pytest.mark.it("✅  Should exclude init, dotenv, and file secret settings")
    def test_excluded_settings_sources(
        self, settings_sources: dict[str, PydanticBaseSettingsSource]
    ) -> None:
        sources = TomlBaseSettings.settings_customise_sources(
            TomlBaseSettings,
            settings_sources["init_settings"],
            settings_sources["env_settings"],
            settings_sources["dotenv_settings"],
            settings_sources["file_secret_settings"],
        )

        assert settings_sources["init_settings"] not in sources
        assert settings_sources["dotenv_settings"] not in sources
        assert settings_sources["file_secret_settings"] not in sources

from enum import StrEnum
from pathlib import Path

import pytest
from pydantic_settings import PydanticBaseSettingsSource, TomlConfigSettingsSource

from fastgear.utils import TomlBaseSettings
from tests.fixtures.types.base_settings_fixtures import settings_sources
from tests.fixtures.utils import (
    config_dir_with_all_files,
    config_dir_with_base_files,
    config_dir_with_duplicate_candidates,
    config_dir_with_env_files,
    duplicate_env_enum,
    env_enum,
    temp_config_dir,
)


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

        assert len(sources) == 2
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


@pytest.mark.describe("🧪  TomlBaseSettings.get_toml_files")
class TestGetTomlFiles:
    @pytest.mark.it("✅  Should return empty list when config directory does not exist")
    def test_returns_empty_list_when_dir_not_exists(
        self, temp_config_dir: Path, env_enum: type[StrEnum]
    ) -> None:
        result = TomlBaseSettings.get_toml_files(temp_config_dir, env_enum)

        assert result == []

    @pytest.mark.it("✅  Should return only base toml files when they exist")
    def test_returns_base_toml_files(
        self, config_dir_with_base_files: Path, env_enum: type[StrEnum]
    ) -> None:
        result = TomlBaseSettings.get_toml_files(config_dir_with_base_files, env_enum)

        assert len(result) == 2
        assert str(config_dir_with_base_files / "env.toml") in result
        assert str(config_dir_with_base_files / "env.local.toml") in result

    @pytest.mark.it("✅  Should return environment-specific toml files")
    def test_returns_env_specific_files(
        self, config_dir_with_env_files: Path, env_enum: type[StrEnum]
    ) -> None:
        result = TomlBaseSettings.get_toml_files(config_dir_with_env_files, env_enum)

        assert str(config_dir_with_env_files / "env.dev.toml") in result
        assert str(config_dir_with_env_files / "env.dev.local.toml") in result
        assert str(config_dir_with_env_files / "env.prod.toml") in result

    @pytest.mark.it("✅  Should return all toml files in correct order")
    def test_returns_all_files_in_order(
        self, config_dir_with_all_files: Path, env_enum: type[StrEnum]
    ) -> None:
        result = TomlBaseSettings.get_toml_files(config_dir_with_all_files, env_enum)

        assert len(result) == 6
        assert result[0] == str(config_dir_with_all_files / "env.toml")
        assert result[1] == str(config_dir_with_all_files / "env.local.toml")
        assert result[2] == str(config_dir_with_all_files / "env.dev.toml")
        assert result[3] == str(config_dir_with_all_files / "env.dev.local.toml")
        assert result[4] == str(config_dir_with_all_files / "env.prod.toml")
        assert result[5] == str(config_dir_with_all_files / "env.prod.local.toml")

    @pytest.mark.it("✅  Should not include duplicate files")
    def test_excludes_duplicate_files(
        self, config_dir_with_base_files: Path, env_enum: type[StrEnum]
    ) -> None:
        result = TomlBaseSettings.get_toml_files(config_dir_with_base_files, env_enum)
        unique_result = list(dict.fromkeys(result))

        assert result == unique_result

    @pytest.mark.it("✅  Should return paths as strings")
    def test_returns_paths_as_strings(
        self, config_dir_with_base_files: Path, env_enum: type[StrEnum]
    ) -> None:
        result = TomlBaseSettings.get_toml_files(config_dir_with_base_files, env_enum)

        for path in result:
            assert isinstance(path, str)

    @pytest.mark.it("✅  Should skip duplicate paths when enum generates same file as base")
    def test_skips_duplicate_paths_from_enum(
        self, config_dir_with_duplicate_candidates: Path, duplicate_env_enum: type[StrEnum]
    ) -> None:
        result = TomlBaseSettings.get_toml_files(
            config_dir_with_duplicate_candidates, duplicate_env_enum
        )

        assert len(result) == 2
        assert str(config_dir_with_duplicate_candidates / "env.toml") in result
        assert str(config_dir_with_duplicate_candidates / "env.local.toml") in result
        assert result.count(str(config_dir_with_duplicate_candidates / "env.local.toml")) == 1

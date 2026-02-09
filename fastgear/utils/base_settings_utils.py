from enum import StrEnum
from pathlib import Path

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, TomlConfigSettingsSource


class TomlBaseSettings(BaseSettings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, TomlConfigSettingsSource(settings_cls)

    @staticmethod
    def get_toml_files(config_dir: Path, env_enum: type[StrEnum]) -> list[str]:
        candidates: list[Path] = [
            config_dir / "env.toml",
            config_dir / "env.local.toml",
        ]

        for env in env_enum:
            candidates.append(config_dir / f"env.{env.value}.toml")
            candidates.append(config_dir / f"env.{env.value}.local.toml")

        seen: set[Path] = set()
        files: list[str] = []
        for p in candidates:
            if not p.exists():
                continue
            if p in seen:
                continue
            seen.add(p)
            files.append(str(p))

        return files

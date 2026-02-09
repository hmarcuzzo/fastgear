from enum import StrEnum
from pathlib import Path

import pytest


class MockEnvEnum(StrEnum):
    DEV = "dev"
    PROD = "prod"


@pytest.fixture
def env_enum() -> type[StrEnum]:
    return MockEnvEnum


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    return tmp_path / "config"


@pytest.fixture
def config_dir_with_base_files(temp_config_dir: Path) -> Path:
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    (temp_config_dir / "env.toml").touch()
    (temp_config_dir / "env.local.toml").touch()
    return temp_config_dir


@pytest.fixture
def config_dir_with_env_files(temp_config_dir: Path) -> Path:
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    (temp_config_dir / "env.dev.toml").touch()
    (temp_config_dir / "env.dev.local.toml").touch()
    (temp_config_dir / "env.prod.toml").touch()
    return temp_config_dir


@pytest.fixture
def config_dir_with_all_files(temp_config_dir: Path) -> Path:
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    (temp_config_dir / "env.toml").touch()
    (temp_config_dir / "env.local.toml").touch()
    (temp_config_dir / "env.dev.toml").touch()
    (temp_config_dir / "env.dev.local.toml").touch()
    (temp_config_dir / "env.prod.toml").touch()
    (temp_config_dir / "env.prod.local.toml").touch()
    return temp_config_dir


class DuplicateEnvEnum(StrEnum):
    TOML = "toml"
    LOCAL = "local"


@pytest.fixture
def duplicate_env_enum() -> type[StrEnum]:
    return DuplicateEnvEnum


@pytest.fixture
def config_dir_with_duplicate_candidates(temp_config_dir: Path) -> Path:
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    (temp_config_dir / "env.toml").touch()
    (temp_config_dir / "env.local.toml").touch()
    return temp_config_dir

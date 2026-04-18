import importlib.util

_EXTRA_DISPLAY_NAMES = {
    "sqlalchemy": "SQLAlchemy",
    "redis": "Redis",
}


def require_extra(symbol: str, extra: str) -> None:
    display_name = _EXTRA_DISPLAY_NAMES.get(extra, extra)
    raise ImportError(
        f"{symbol!r} requires '{display_name}'. Install it with: pip install fastgear[{extra}]"
    )


def has_extra(extra: str) -> bool:
    return importlib.util.find_spec(extra) is not None

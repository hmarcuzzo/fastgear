import inspect
from collections.abc import Callable
from functools import singledispatchmethod, wraps
from typing import Any, TypeVar, Union, get_args, get_origin

from fastgear.common.database.sqlalchemy.session import AllSessionType, db_session

ClassType = TypeVar("ClassType")


def inject_db_parameter_decorator(cls: type[ClassType]) -> type[ClassType]:
    """Class decorator that modifies methods of the given class to automatically inject a default parameter value
    if it is not already present in the method's arguments. It applies another decorator,
    `inject_db_parameter_if_missing`, to each method.

    Args:
        cls (Type[ClassType]): The class to be decorated.

    Returns:
        Type[ClassType]: The decorated class with methods that automatically inject a default parameter value.

    """

    def _decorate_attr(attr_value: Any) -> Any:
        # staticmethod/classmethod
        if isinstance(attr_value, staticmethod | classmethod):
            fn = attr_value.__func__
            wrapped = inject_db_parameter_if_missing(fn)
            return type(attr_value)(wrapped)

        # singledispatchmethod
        if isinstance(attr_value, singledispatchmethod):
            dispatcher = attr_value.dispatcher
            # Copy and wrap each registered implementation
            for typ, fn in list(dispatcher.registry.items()):
                wrapped = inject_db_parameter_if_missing(fn)
                dispatcher.register(typ, wrapped)
            return singledispatchmethod(dispatcher)

        # Normal method or function
        if inspect.isfunction(attr_value):
            return inject_db_parameter_if_missing(attr_value)

        # Leave other attributes unchanged
        return attr_value

    for name, value in list(cls.__dict__.items()):
        # Ignore special and private attributes
        if name.startswith("__") and name.endswith("__"):
            continue
        setattr(cls, name, _decorate_attr(value))

    return cls


def inject_db_parameter_if_missing(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that injects a Session or AsyncSession instance into the function arguments
    if it is missing and required by the function's signature.
    """
    sig = inspect.signature(func)
    params = tuple(sig.parameters.values())
    is_coro = inspect.iscoroutinefunction(func)

    def _is_valid_session_annotation(annot: Any) -> bool:
        origin = get_origin(annot)
        if origin in (Union, getattr(__import__("types"), "UnionType", Union)):
            return any(
                isinstance(t, type) and issubclass(t, AllSessionType) for t in get_args(annot)
            )
        return isinstance(annot, type) and issubclass(annot, AllSessionType)

    # Discover the first candidate parameter for injection
    candidate_idx: int | None = None
    candidate_name: str | None = None
    for idx, p in enumerate(params):
        if (
            p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            or p.annotation is inspect._empty
            or not _is_valid_session_annotation(p.annotation)
        ):
            continue

        if p.default is inspect._empty or p.default is None:
            candidate_idx, candidate_name = idx, p.name
            break

    # If no candidate found, return the original function
    if candidate_name is None:
        return func

    def _needs_injection(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
        # Already exists in args?
        if any(isinstance(a, AllSessionType) for a in args):
            return False
        # It was passed by name?
        if candidate_name in kwargs and isinstance(kwargs[candidate_name], AllSessionType):
            return False
        # Was it passed positionally?
        # and it was passed positionally and not None, do not inject
        return not (len(args) > candidate_idx and args[candidate_idx] is not None)

    if is_coro:

        @wraps(func)
        async def awrapper(*args: Any, **kwargs: Any) -> Any:
            if _needs_injection(args, kwargs):
                kwargs[candidate_name] = db_session.get()
            return await func(*args, **kwargs)

        return awrapper

    @wraps(func)
    def swrapper(*args: Any, **kwargs: Any) -> Any:
        if _needs_injection(args, kwargs):
            kwargs[candidate_name] = db_session.get()
        return func(*args, **kwargs)

    return swrapper

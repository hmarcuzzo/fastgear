import asyncio
from collections.abc import Callable
from functools import singledispatchmethod, wraps
from inspect import iscoroutinefunction, signature
from types import UnionType
from typing import Any, TypeVar, Union, get_args, get_origin

from fastgear.common.database.sqlalchemy.session import AllSessionType
from fastgear.middlewares.db_session_middleware import db_session

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

    def decorate_method(attr_value):
        if isinstance(attr_value, staticmethod | classmethod):
            func = attr_value.__func__
            decorated_func = inject_db_parameter_if_missing(func)
            return type(attr_value)(decorated_func)

        if isinstance(attr_value, singledispatchmethod):
            dispatcher = attr_value.dispatcher
            # Wrap all registered implementations
            for typ, func in dispatcher.registry.items():
                # Wrap the function
                wrapped_func = inject_db_parameter_if_missing(func)
                # Re-register the function
                dispatcher.register(typ, wrapped_func)
            # Reconstruct the singledispatchmethod
            return singledispatchmethod(dispatcher)

        if callable(attr_value):
            # Regular method
            return inject_db_parameter_if_missing(attr_value)

        return attr_value

    # Iterate over all class attributes to find methods (excluding magic methods)
    for attr_name, attr_value in cls.__dict__.items():
        if attr_name.startswith("__"):
            continue
        new_attr = decorate_method(attr_value)
        setattr(cls, attr_name, new_attr)

    return cls


def inject_db_parameter_if_missing(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that injects a Session or AsyncSession instance into the function arguments
    if it is missing and required by the function's signature.
    """

    def db_session_injection(*args: tuple[Any], **kwargs: Any) -> (tuple[Any], Any):
        sig = signature(func)
        params = list(sig.parameters.values())

        # Check if a Session instance is not among the arguments and if injection is needed
        if not any(isinstance(arg, AllSessionType) for arg in args):
            for i, param in enumerate(params):
                if (
                    param.default is None
                    and param.name not in kwargs
                    and len(args) <= i
                    and is_valid_session_type(param.annotation)
                ):
                    kwargs[param.name] = db_session.get()

        return args, kwargs

    def is_valid_session_type(annotation: Any) -> bool:
        origin = get_origin(annotation)
        if origin in (Union, UnionType):
            return any(
                isinstance(cls, type) and issubclass(cls, AllSessionType)
                for cls in get_args(annotation)
            )
        return isinstance(annotation, type) and issubclass(annotation, AllSessionType)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        args, kwargs = db_session_injection(*args, **kwargs)
        if iscoroutinefunction(func):
            return await func(*args, **kwargs)
        await asyncio.to_thread(func, *args, **kwargs)
        return None

    return wrapper

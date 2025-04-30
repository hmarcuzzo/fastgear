from itertools import chain

from dependency_injector import containers


class DependencyInjectorUtils:
    """
    A utility class for managing dependency injection in a FastAPI application.
    """

    @staticmethod
    def get_aggregated_modules(
        modules_containers: list[type[containers.DeclarativeContainer]],
    ) -> list[str]:
        return list(
            chain.from_iterable(
                c.wiring_config.modules for c in modules_containers if hasattr(c, "wiring_config")
            )
        )

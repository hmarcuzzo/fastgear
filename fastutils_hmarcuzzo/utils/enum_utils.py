import re


class EnumUtils:
    @staticmethod
    def camel_to_snake(name: str) -> str:
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    @staticmethod
    def get_object_name(enum_cls: type) -> str:
        return EnumUtils.camel_to_snake(enum_cls.__name__)

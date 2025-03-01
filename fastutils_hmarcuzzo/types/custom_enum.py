from enum import Enum

from fastutils_hmarcuzzo.utils.enum_utils import EnumUtils


class CustomEnum(Enum):
    @classmethod
    def object_name(cls) -> str:
        return EnumUtils.get_object_name(cls)

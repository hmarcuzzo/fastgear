from datetime import date, datetime

from fastgear.common.schema import DetailResponseSchema


class JsonUtils:
    @staticmethod
    def json_serial(obj: object) -> str | dict:
        """JSON serializer for objects not serializable by default json code.

        Args:
            obj: The object to be serialized. It can be an instance of datetime, date, or DetailResponseSchema.

        Returns:
            str: The ISO format string for datetime or date objects.
            dict: The dictionary representation for DetailResponseSchema objects.

        Raises:
            TypeError: If the object type is not serializable.

        """
        if isinstance(obj, datetime | date):
            return obj.isoformat()
        if isinstance(obj, DetailResponseSchema):
            return obj.dict()
        raise TypeError(f"Type {type(obj)} not serializable")

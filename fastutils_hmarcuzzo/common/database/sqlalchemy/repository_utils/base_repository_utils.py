from pydantic import BaseModel

from fastutils_hmarcuzzo.types.generic_types_var import EntityType


class BaseRepositoryUtils:
    @staticmethod
    def should_be_updated(entity: EntityType, update_schema: BaseModel) -> bool:
        """Determines if the given entity should be updated based on the provided update schema.

        Args:
            entity (EntityType): The entity to check for updates.
            update_schema (BaseModel): The schema containing the update data.

        Returns:
            bool: True if the entity should be updated, False otherwise.

        """
        return any(
            getattr(entity, key) != value
            for key, value in update_schema.model_dump(exclude_unset=True).items()
        )

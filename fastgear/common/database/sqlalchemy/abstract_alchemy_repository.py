from abc import ABC

from fastgear.common.database.abstract_repository import AbstractRepository
from fastgear.common.database.sqlalchemy.repository_utils.base_repository_utils import (
    BaseRepositoryUtils,
)
from fastgear.common.database.sqlalchemy.repository_utils.statement_constructor import (
    StatementConstructor,
)
from fastgear.common.database.sqlalchemy.types import EntityType


class AbstractAlchemyRepository(AbstractRepository[EntityType], ABC):
    def __init__(self, entity: type[EntityType]) -> None:
        super().__init__(entity)
        self.statement_constructor = StatementConstructor(entity)
        self.repo_utils = BaseRepositoryUtils()

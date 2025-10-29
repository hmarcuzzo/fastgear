from datetime import UTC, datetime

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import (
    ColumnElement,
    ForeignKeyConstraint,
    MetaData,
    Table,
    and_,
    exists,
    select,
    true,
)
from sqlalchemy.orm import registry

from fastgear.common.database.sqlalchemy.repository_utils.statement_constructor import (
    StatementConstructor,
)
from fastgear.common.database.sqlalchemy.session import SyncSessionType
from fastgear.types.generic_types_var import EntityType
from fastgear.types.http_exceptions import NotFoundException
from fastgear.types.update_options import UpdateOptions
from fastgear.types.update_result import UpdateResult

logger.bind(name="BaseRepositoryUtils")


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

    @staticmethod
    def soft_delete_cascade_from_parent(
        entity: EntityType,
        *,
        update_filter: str | UpdateOptions,
        deleted_at_column="deleted_at",
        db: SyncSessionType,
    ) -> UpdateResult:
        statement_constructor = StatementConstructor(entity)

        ts = datetime.now(UTC)
        parent_table: Table = entity.__table__
        metadata = parent_table.metadata
        registry = entity.registry

        if deleted_at_column not in parent_table.c:
            raise ValueError(
                f'Parent entity "{entity.__name__}" has no "{deleted_at_column}" column'
            )

        parent_pks = list(parent_table.primary_key.columns)
        if len(parent_pks) != 1:
            raise ValueError("Composite primary keys are not supported")

        if isinstance(update_filter, str):
            update_filter = statement_constructor.build_where_from_id(update_filter, entity)
        update_filter["where"].append(parent_table.c[deleted_at_column].is_(None))

        payload = {deleted_at_column: ts}
        cmp_params = {f"cmp_{k}": v for k, v in payload.items()}
        params = {**payload, **cmp_params}
        stmt = statement_constructor.build_update_statement(
            update_filter, payload=payload
        ).returning(entity)

        result = db.execute(stmt, params)

        objs = result.scalars().all()
        affected = len(objs)

        if not affected:
            entity_name = entity.__name__
            message = f'Could not find any entity of type "{entity_name}" that matches with the search filter'
            logger.debug(message)
            raise NotFoundException(message, [entity_name])

        response = UpdateResult(raw=objs, affected=affected, generated_maps=[])

        frontier: set[Table] = {parent_table}
        visited: set[Table] = {parent_table}
        updated_tables: list[str] = [parent_table.name]

        while frontier:
            next_frontier: set[Table] = set()

            for parent in frontier:
                edges = BaseRepositoryUtils._fk_edges_from(metadata, parent)

                for child, fk in edges:
                    if child in visited:
                        continue

                    if deleted_at_column not in child.c:
                        visited.add(child)
                        next_frontier.add(child)
                        continue

                    fk_match = BaseRepositoryUtils._build_fk_match_condition(fk)
                    exists_parent_marked = exists(
                        select(1)
                        .select_from(parent)
                        .where(parent.c[deleted_at_column].is_not(None), fk_match)
                    ).correlate(child)

                    child_cls = BaseRepositoryUtils.mapped_class_for_table(child, registry)
                    stmt = statement_constructor.build_update_statement(
                        {"where": [child.c[deleted_at_column].is_(None), exists_parent_marked]},
                        payload=payload,
                        new_entity=child_cls,
                    ).returning(child_cls)
                    result = db.execute(stmt, params)

                    objs = result.scalars().all()
                    affected = len(objs)

                    if affected > 0:
                        next_frontier.add(child)
                        updated_tables.append(child.name)
                        response["affected"] += affected
                        response["raw"].extend(objs)

                    visited.add(child)

            frontier = next_frontier

        response["generated_maps"].append(updated_tables)
        return response

    @staticmethod
    def _fk_edges_from(
        metadata: MetaData, parent: Table
    ) -> list[tuple[Table, ForeignKeyConstraint]]:
        edges = []
        for table in metadata.tables.values():
            if table is parent:
                continue

            for fk in table.foreign_key_constraints:
                if fk.referred_table is parent:
                    edges.extend([(table, fk)])
        return edges

    @staticmethod
    def _build_fk_match_condition(fk: ForeignKeyConstraint) -> ColumnElement[bool]:
        conds = []
        for elem in fk.elements:
            child_col = elem.parent
            parent_col = elem.column
            conds.append(child_col == parent_col)
        return and_(*conds) if conds else true()

    @staticmethod
    def mapped_class_for_table(table: Table, registry: registry) -> type | None:
        for mapper in registry.mappers:
            if mapper.local_table is table or mapper.persist_selectable is table:
                return mapper.class_
        return None

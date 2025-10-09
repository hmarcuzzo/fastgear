from datetime import datetime, timezone

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
    update,
)

from fastgear.common.database.sqlalchemy.session import SyncSessionType
from fastgear.types.generic_types_var import EntityType
from fastgear.types.update_result import UpdateResult


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
        parent_entity_id: str,
        deleted_at_column="deleted_at",
        db: SyncSessionType,
    ) -> UpdateResult:
        response = UpdateResult(raw=[], affected=0, generated_maps=[])

        ts = datetime.now(timezone.utc)
        parent_table: Table = entity.__table__
        metadata = parent_table.metadata

        if deleted_at_column not in parent_table.c:
            raise ValueError(
                f'Parent entity "{entity.__name__}" has no "{deleted_at_column}" column'
            )

        parent_pks = list(parent_table.primary_key.columns)
        if len(parent_pks) != 1:
            raise ValueError("Composite primary keys are not supported")
        pk_col = parent_pks[0]

        db.execute(
            update(parent_table)
            .where(pk_col == parent_entity_id, parent_table.c[deleted_at_column].is_(None))
            .values({deleted_at_column: ts})
        )
        response["affected"] += 1
        response["raw"].append({"table": parent_table.name, "id": parent_entity_id})

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
                    )

                    result = db.execute(
                        update(child)
                        .where(child.c[deleted_at_column].is_(None), exists_parent_marked)
                        .values({deleted_at_column: ts})
                    )
                    # If rows were affected, we need to continue the cascade from this child table
                    rowcount = getattr(result, "rowcount", None)
                    if rowcount is None or rowcount > 0:
                        next_frontier.add(child)
                        updated_tables.append(child.name)

                        response["affected"] += result.rowcount

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

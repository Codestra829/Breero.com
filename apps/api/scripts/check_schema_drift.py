"""Fail when application tables/columns/nullability differ from SQLAlchemy metadata.

Supplementary operational indexes and PostGIS-owned objects are intentionally allowed;
they are versioned migrations but are not destructive model drift.
"""

import asyncio

from sqlalchemy import inspect

from app.db.base import Base
from app.db.session import engine
from app.domains.auth import models as _auth  # noqa: F401
from app.domains.booking import models as _booking  # noqa: F401
from app.domains.catalog import models as _catalog  # noqa: F401
from app.domains.common import outbox as _outbox  # noqa: F401
from app.domains.dispatch import models as _dispatch  # noqa: F401
from app.domains.finance import models as _finance  # noqa: F401
from app.domains.jobs import models as _jobs  # noqa: F401
from app.domains.payments import models as _payments  # noqa: F401
from app.domains.workforce import models as _workforce  # noqa: F401


def compare(connection) -> list[str]:
    inspector = inspect(connection)
    database_tables = set(inspector.get_table_names()) - {"alembic_version", "spatial_ref_sys"}
    model_tables = set(Base.metadata.tables)
    errors = [f"unexpected table: {name}" for name in sorted(database_tables - model_tables)]
    errors += [f"missing table: {name}" for name in sorted(model_tables - database_tables)]
    for table_name in sorted(model_tables & database_tables):
        expected = Base.metadata.tables[table_name]
        actual = {column["name"]: column for column in inspector.get_columns(table_name)}
        expected_names = set(expected.columns.keys())
        errors += [
            f"{table_name}: unexpected column {name}" for name in sorted(set(actual) - expected_names)
        ]
        errors += [
            f"{table_name}: missing column {name}" for name in sorted(expected_names - set(actual))
        ]
        for name in sorted(expected_names & set(actual)):
            if bool(expected.columns[name].nullable) != bool(actual[name]["nullable"]):
                errors.append(f"{table_name}.{name}: nullability differs")
    return errors


async def main() -> None:
    async with engine.connect() as connection:
        errors = await connection.run_sync(compare)
    await engine.dispose()
    if errors:
        raise SystemExit("Schema drift detected:\n" + "\n".join(errors))
    print("No destructive schema drift detected")


if __name__ == "__main__":
    asyncio.run(main())

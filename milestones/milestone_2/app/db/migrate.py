"""add columns create_all will not add on a database that already has tables."""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def ensure_columns(engine: Engine) -> None:
    """postgres only.sqlite tests get the columns from create_all."""
    if engine.dialect.name != "postgresql":
        return
    statements = [
        'ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS "Role" VARCHAR(20)',
        """UPDATE "Users" SET "Role" = 'CUSTOMER' WHERE "Role" IS NULL""",
        """ALTER TABLE "Users" ALTER COLUMN "Role" SET DEFAULT 'CUSTOMER'""",
        'ALTER TABLE "Users" ALTER COLUMN "Role" SET NOT NULL',
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_user_role') THEN
                ALTER TABLE "Users" ADD CONSTRAINT ck_user_role
                CHECK ("Role" IN ('CUSTOMER', 'ADMIN', 'SUPPORT'));
            END IF;
        END $$;
        """,
    ]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))

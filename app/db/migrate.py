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
        'ALTER TABLE "Products" ADD COLUMN IF NOT EXISTS "IsActive" BOOLEAN',
        'UPDATE "Products" SET "IsActive" = TRUE WHERE "IsActive" IS NULL',
        'ALTER TABLE "Products" ALTER COLUMN "IsActive" SET DEFAULT TRUE',
        'ALTER TABLE "Products" ALTER COLUMN "IsActive" SET NOT NULL',
        'ALTER TABLE "Orders" ADD COLUMN IF NOT EXISTS "PaymentStatus" VARCHAR(20)',
        # old orders were taken before the gateway existed,so treat them as paid.
        """UPDATE "Orders" SET "PaymentStatus" = 'PAID' WHERE "PaymentStatus" IS NULL""",
        """ALTER TABLE "Orders" ALTER COLUMN "PaymentStatus" SET DEFAULT 'PENDING'""",
        'ALTER TABLE "Orders" ALTER COLUMN "PaymentStatus" SET NOT NULL',
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_order_payment_status') THEN
                ALTER TABLE "Orders" ADD CONSTRAINT ck_order_payment_status
                CHECK ("PaymentStatus" IN ('PENDING', 'PAID', 'FAILED'));
            END IF;
        END $$;
        """,
    ]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))

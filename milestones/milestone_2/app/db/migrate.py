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


def drop_old_cart_shape(engine: Engine) -> None:
    """week 2 cart is CartItemID.drop the basket tables if this db still has CartID on the line."""
    if engine.dialect.name != "postgresql":
        return
    statement = """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'CartItems' AND column_name = 'CartID'
        ) THEN
            ALTER TABLE "Orders" DROP CONSTRAINT IF EXISTS fk_order_cart;
            ALTER TABLE "Orders" DROP CONSTRAINT IF EXISTS uq_order_cart;
            ALTER TABLE "Orders" DROP COLUMN IF EXISTS "CartID";
            DROP TABLE IF EXISTS "CartItems";
            DROP TABLE IF EXISTS "Carts";
        END IF;
    END $$;
    """
    with engine.begin() as conn:
        conn.execute(text(statement))

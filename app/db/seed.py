from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal

CATEGORIES = ["Electronics", "Clothing", "Books", "Home and Kitchen"]

PRODUCTS = [
    ("ELEC-001", "Wireless Headphones", "Over-ear Bluetooth headphones with noise cancellation", "Electronics", "79.99", "25", ""),
    ("ELEC-002", "Smartphone Stand", "Adjustable aluminum stand for smartphones", "Electronics", "18.50", "40", ""),
    ("CLOT-001", "Cotton T-Shirt", "Soft, breathable cotton crew-neck T-shirt", "Clothing", "14.99", "60", ""),
    ("CLOT-002", "Running Shoes", "Lightweight athletic shoes for everyday running", "Clothing", "64.95", "30", ""),
    ("BOOK-001", "Python Programming Guide", "Beginner-friendly guide to Python programming", "Books", "29.99", "20", ""),
    ("BOOK-002", "Mystery Novel", "A suspenseful mystery novel with an unexpected ending", "Books", "12.50", "35", ""),
    ("HOME-001", "Ceramic Coffee Mug", "Durable ceramic mug with a comfortable handle", "Home and Kitchen", "9.99", "50", ""),
    ("HOME-002", "Nonstick Frying Pan", "Durable nonstick pan for everyday cooking", "Home and Kitchen", "34.99", "15", ""),
    ("HOME-003", "LED Desk Lamp", "Adjustable LED lamp with three brightness levels", "Home and Kitchen", "24.75", "28", ""),
    ("ELEC-003", "Portable Power Bank", "Compact power bank with USB-C fast charging", "Electronics", "32.00", "22", ""),
]


def seed_database() -> None:
    """put sample products once.a row that is already there is skipped."""
    # imported here so loading the db package does not pull models while they are still loading.
    from app.models import Category, Product
    from app.repositories import product_repository

    db: Session = SessionLocal()
    try:
        categories: dict[str, Category] = {}
        for name in CATEGORIES:
            category = product_repository.get_category_by_name(db, name)
            if category is None:
                category = Category(category_name=name)
                db.add(category)
                db.flush()
            categories[name] = category
        for sku, name, description, category_name, price, quantity, url in PRODUCTS:
            if product_repository.get_by_sku(db, sku) is not None:
                continue
            if product_repository.get_by_name(db, name) is not None:
                continue
            db.add(
                Product(
                    sku=sku,
                    product_name=name,
                    description=description,
                    category_id=categories[category_name].category_id,
                    price=Decimal(price),
                    available_quantity=int(quantity),
                    product_url=url,
                    is_active=True,
                )
            )
        db.commit()
    finally:
        db.close()


# name, email, password, mobile, role. an existing email is left as it is.
USERS = [
    ("Rudraksh", "rudraksh@example.com", "rudraksh1234", "9000000000", "ADMIN"),
    ("Navya", "navya@example.com", "navya1234", "9000000001", "SUPPORT"),
    ("Het", "het@example.com", "het12345", "9000000002", "CUSTOMER"),
]


def _ensure_user(db: Session, name: str, email: str, password: str, mobile: str, role: str) -> None:
    from app.models import User
    from app.utils import hash_password

    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        return
    db.add(
        User(
            name=name,
            email=email,
            password=hash_password(password),
            mobile=mobile,
            role=role,
        )
    )
    db.commit()


def seed_users() -> None:
    """create Rudraksh, Navya, and Het once.a later boot does not reset their password."""
    db: Session = SessionLocal()
    try:
        for name, email, password, mobile, role in USERS:
            _ensure_user(db, name, email, password, mobile, role)
    finally:
        db.close()


def main() -> None:
    import app.models  # noqa: F401  so create_all sees the tables
    from app.db import Base, engine

    Base.metadata.create_all(bind=engine)
    seed_database()
    seed_users()
    print("Seeded.")


if __name__ == "__main__":
    main()

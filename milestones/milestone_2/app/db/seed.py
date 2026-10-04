import logging
import os
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.utils.helpers import hash_password
from app.utils.permissions import ADMIN, SUPPORT

CATEGORIES = ["Electronics", "Clothing", "Books", "Home and Kitchen"]

PRODUCTS = [
    ("Wireless Headphones", "Over-ear Bluetooth headphones with noise cancellation", "Electronics", "79.99", "25", ""),
    ("Smartphone Stand", "Adjustable aluminum stand for smartphones", "Electronics", "18.50", "40", ""),
    ("Cotton T-Shirt", "Soft, breathable cotton crew-neck T-shirt", "Clothing", "14.99", "60", ""),
    ("Running Shoes", "Lightweight athletic shoes for everyday running", "Clothing", "64.95", "30", ""),
    ("Python Programming Guide", "Beginner-friendly guide to Python programming", "Books", "29.99", "20", ""),
    ("Mystery Novel", "A suspenseful mystery novel with an unexpected ending", "Books", "12.50", "35", ""),
    ("Ceramic Coffee Mug", "Durable ceramic mug with a comfortable handle", "Home and Kitchen", "9.99", "50", ""),
    ("Nonstick Frying Pan", "Durable nonstick pan for everyday cooking", "Home and Kitchen", "34.99", "15", ""),
    ("LED Desk Lamp", "Adjustable LED lamp with three brightness levels", "Home and Kitchen", "24.75", "28", ""),
    ("Portable Power Bank", "Compact power bank with USB-C fast charging", "Electronics", "32.00", "22", ""),
]


def seed_database() -> None:
    """put sample products once.later start should not insert them again."""
    db: Session = SessionLocal()
    try:
        existing = db.scalar(select(Category.category_id).limit(1))
        if existing is not None:
            return
        categories = {name: Category(category_name=name) for name in CATEGORIES}
        db.add_all(categories.values())
        db.flush()
        for name, description, category_name, price, quantity, url in PRODUCTS:
            db.add(
                Product(
                    product_name=name,
                    description=description,
                    category_id=categories[category_name].category_id,
                    price=Decimal(price),
                    available_quantity=int(quantity),
                    product_url=url,
                )
            )
        db.commit()
    finally:
        db.close()


def _ensure_staff(db: Session, email_key: str, password_key: str, name: str, role: str) -> None:
    email = os.getenv(email_key, "").strip().lower()
    password = os.getenv(password_key, "")
    if not email or not password:
        logging.getLogger("shopping").warning("skipped staff seed, %s is empty", email_key)
        return
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        return
    db.add(
        User(
            name=name,
            email=email,
            password=hash_password(password),
            mobile="9000000000" if role == ADMIN else "9000000001",
            role=role,
        )
    )
    db.commit()


def seed_staff() -> None:
    """create admin and support once.a later boot does not reset their password."""
    db: Session = SessionLocal()
    try:
        _ensure_staff(db, "ADMIN_EMAIL", "ADMIN_PASSWORD", "Shop Admin", ADMIN)
        _ensure_staff(db, "SUPPORT_EMAIL", "SUPPORT_PASSWORD", "Shop Support", SUPPORT)
    finally:
        db.close()

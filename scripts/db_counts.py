#!/usr/bin/env python3
from sqlalchemy import text

from packages.shared.db import get_engine


def main():
    en = get_engine()
    with en.connect() as c:

        def count(table):
            try:
                return c.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            except Exception as e:
                return f"error: {e}"

        result = {
            "products": count("products"),
            "suppliers": count("suppliers"),
            "competitors": count("competitors"),
            "price_history": count("price_history"),
            "sales": count("sales"),
        }
        print(result)


if __name__ == "__main__":
    main()

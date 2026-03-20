from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CLEANED_DIR = ROOT / "cleaned_data"


def read_csv(name: str, *, encoding: str = "utf-8-sig") -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name, dtype=str, encoding=encoding)


def normalize_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in result.columns:
        if pd.api.types.is_object_dtype(result[column]):
            result[column] = result[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
            result[column] = result[column].replace("", pd.NA)
    return result


def to_nullable_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def to_decimal(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def assert_primary_key(df: pd.DataFrame, columns: Iterable[str], table_name: str) -> None:
    key_columns = list(columns)
    if df[key_columns].isna().any().any():
        raise ValueError(f"{table_name}: primary key columns contain nulls: {key_columns}")
    duplicate_count = int(df.duplicated(subset=key_columns).sum())
    if duplicate_count:
        raise ValueError(
            f"{table_name}: primary key {key_columns} has {duplicate_count} duplicate rows"
        )


def assert_foreign_key(
    child_df: pd.DataFrame,
    child_column: str,
    parent_df: pd.DataFrame,
    parent_column: str,
    fk_name: str,
) -> None:
    child_values = child_df[child_column].dropna()
    missing = child_values[~child_values.isin(parent_df[parent_column])]
    if not missing.empty:
        raise ValueError(f"{fk_name}: found {missing.nunique()} foreign key values without parents")


def write_csv(df: pd.DataFrame, name: str) -> None:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(
        CLEANED_DIR / name,
        index=False,
        encoding="utf-8",
        na_rep="",
        lineterminator="\n",
    )


def main() -> None:
    customers_raw = normalize_string_columns(read_csv("olist_customers_dataset.csv"))
    orders_raw = normalize_string_columns(read_csv("olist_orders_dataset.csv"))
    order_items_raw = normalize_string_columns(read_csv("olist_order_items_dataset.csv"))
    order_payments_raw = normalize_string_columns(read_csv("olist_order_payments_dataset.csv"))
    order_reviews_raw = normalize_string_columns(read_csv("olist_order_reviews_dataset.csv"))
    products_raw = normalize_string_columns(read_csv("olist_products_dataset.csv"))
    sellers_raw = normalize_string_columns(read_csv("olist_sellers_dataset.csv"))
    translation_raw = normalize_string_columns(read_csv("product_category_name_translation.csv"))

    customers = customers_raw[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ].copy()
    customers["customer_zip_code_prefix"] = customers["customer_zip_code_prefix"].str.zfill(5)

    orders = orders_raw[
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ].copy()
    for column in [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]:
        orders[column] = to_datetime(orders[column])

    translation = translation_raw[
        ["product_category_name", "product_category_name_english"]
    ].drop_duplicates(subset=["product_category_name"])

    product_categories = (
        products_raw[["product_category_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values("product_category_name")
        .merge(translation, on="product_category_name", how="left")
        .reset_index(drop=True)
    )

    products = products_raw[
        [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
    ].rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )
    for column in [
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]:
        products[column] = to_nullable_int(products[column])

    sellers = sellers_raw[
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]
    ].copy()
    sellers["seller_zip_code_prefix"] = sellers["seller_zip_code_prefix"].str.zfill(5)

    order_items = order_items_raw[
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ]
    ].copy()
    order_items["order_item_id"] = to_nullable_int(order_items["order_item_id"])
    order_items["shipping_limit_date"] = to_datetime(order_items["shipping_limit_date"])
    order_items["price"] = to_decimal(order_items["price"])
    order_items["freight_value"] = to_decimal(order_items["freight_value"])

    order_payments = order_payments_raw[
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ]
    ].copy()
    order_payments["payment_sequential"] = to_nullable_int(order_payments["payment_sequential"])
    order_payments["payment_installments"] = to_nullable_int(order_payments["payment_installments"])
    order_payments["payment_value"] = to_decimal(order_payments["payment_value"])

    order_reviews = order_reviews_raw[
        [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ]
    ].copy()
    order_reviews["review_score"] = to_nullable_int(order_reviews["review_score"])
    order_reviews["review_creation_date"] = to_datetime(order_reviews["review_creation_date"])
    order_reviews["review_answer_timestamp"] = to_datetime(order_reviews["review_answer_timestamp"])

    assert_primary_key(customers, ["customer_id"], "customers")
    assert_primary_key(orders, ["order_id"], "orders")
    assert_primary_key(product_categories, ["product_category_name"], "product_categories")
    assert_primary_key(products, ["product_id"], "products")
    assert_primary_key(sellers, ["seller_id"], "sellers")
    assert_primary_key(order_items, ["order_id", "order_item_id"], "order_items")
    assert_primary_key(order_payments, ["order_id", "payment_sequential"], "order_payments")
    assert_primary_key(order_reviews, ["review_id", "order_id"], "order_reviews")

    assert_foreign_key(orders, "customer_id", customers, "customer_id", "orders.customer_id")
    assert_foreign_key(
        products.dropna(subset=["product_category_name"]),
        "product_category_name",
        product_categories,
        "product_category_name",
        "products.product_category_name",
    )
    assert_foreign_key(order_items, "order_id", orders, "order_id", "order_items.order_id")
    assert_foreign_key(order_items, "product_id", products, "product_id", "order_items.product_id")
    assert_foreign_key(order_items, "seller_id", sellers, "seller_id", "order_items.seller_id")
    assert_foreign_key(
        order_payments, "order_id", orders, "order_id", "order_payments.order_id"
    )
    assert_foreign_key(order_reviews, "order_id", orders, "order_id", "order_reviews.order_id")

    write_csv(customers, "customers.csv")
    write_csv(orders, "orders.csv")
    write_csv(product_categories, "product_categories.csv")
    write_csv(products, "products.csv")
    write_csv(sellers, "sellers.csv")
    write_csv(order_items, "order_items.csv")
    write_csv(order_payments, "order_payments.csv")
    write_csv(order_reviews, "order_reviews.csv")

    counts = {
        "customers": len(customers),
        "orders": len(orders),
        "product_categories": len(product_categories),
        "products": len(products),
        "sellers": len(sellers),
        "order_items": len(order_items),
        "order_payments": len(order_payments),
        "order_reviews": len(order_reviews),
    }
    for table_name, row_count in counts.items():
        print(f"{table_name}: {row_count}")


if __name__ == "__main__":
    main()

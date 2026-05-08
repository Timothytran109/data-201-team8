# DATA 201 Olist Final Project Dashboard (Plotly Dash)

## Purpose
This dashboard explores how delivery performance, fulfillment delays, review behavior, product logistics, basket complexity, seller freight efficiency, and payment consistency relate to customer satisfaction in the Olist marketplace.

## Prerequisite
The MySQL Olist database must already be loaded and available in MySQL Workbench.
Schema name expected by default:
- `olist_mid_presentation`

This project does not reload data and does not modify source tables.

## Setup
1. Copy env template:
   - `cp .env.example .env` (or create `.env` manually on Windows)
2. Update `.env` credentials.
3. Install requirements:
   - `pip install -r requirements.txt`

## Run
From the `dashboard/` directory:
- `python app.py`

Expected local URL:
- `http://127.0.0.1:8050/`

## Controls
The dashboard includes exactly three controls:
- Product category dropdown
  - Source: `COALESCE(product_categories.product_category_name_english, products.product_category_name, 'Unknown')`
  - Default: `All`
- Customer state dropdown
  - Source: `customers.customer_state`
  - Default: `All`
- Minimum item count slider
  - Default: `20`
  - Applied to seller outlier chart with `HAVING items_sold >= :min_item_count`

## Sections
- Operations & Reviews
- Product Logistics
- Payment Consistency

## Notes
- Main dashboard analysis uses orders/customers/order_items/products/product_categories/sellers/order_reviews.
- Payment reconciliation is intentionally isolated into its own aggregated view to avoid duplication from many-to-many joins between `order_items` and `order_payments`.
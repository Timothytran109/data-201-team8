CATEGORY_OPTIONS_QUERY = """
SELECT DISTINCT COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown') AS category
FROM products p
LEFT JOIN product_categories pc
    ON p.product_category_name = pc.product_category_name
ORDER BY category;
"""

CUSTOMER_STATE_OPTIONS_QUERY = """
SELECT DISTINCT c.customer_state
FROM customers c
WHERE c.customer_state IS NOT NULL
ORDER BY c.customer_state;
"""

KPI_QUERY = """
SELECT
    COUNT(DISTINCT order_id) AS total_orders,
    AVG(review_score) AS avg_review_score,
    AVG(delivery_delay_days) AS avg_delivery_offset_days,
    AVG(freight_to_price_ratio) AS avg_freight_burden
FROM v_dashboard_main
WHERE (:category IS NULL OR :category = 'All' OR category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR customer_state = :customer_state);
"""

DELIVERY_STATUS_REVIEW_QUERY = """
SELECT
    delivery_status,
    AVG(review_score) AS avg_review_score,
    COUNT(DISTINCT order_id) AS orders_count
FROM v_dashboard_main
WHERE order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL
  AND review_score IS NOT NULL
  AND delivery_status IN ('On Time / Early', 'Late')
  AND (:category IS NULL OR :category = 'All' OR category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR customer_state = :customer_state)
GROUP BY delivery_status
ORDER BY orders_count DESC;
"""

FULFILLMENT_DELAY_BREAKDOWN_QUERY = """
SELECT
    r.review_score,
    COUNT(o.order_id) AS total_orders,
    ROUND(AVG(DATEDIFF(o.order_approved_at, o.order_purchase_timestamp)), 2) AS avg_approval_delay,
    ROUND(AVG(DATEDIFF(o.order_delivered_carrier_date, o.order_approved_at)), 2) AS avg_carrier_delay,
    ROUND(AVG(DATEDIFF(o.order_delivered_customer_date, o.order_delivered_carrier_date)), 2) AS avg_delivery_delay
FROM orders o
JOIN order_reviews r
    ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
  AND o.order_approved_at IS NOT NULL
  AND o.order_delivered_carrier_date IS NOT NULL
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY r.review_score
ORDER BY r.review_score DESC;
"""

REVIEW_RESPONSE_TIME_QUERY = """
SELECT
    sentiment_group,
    AVG(review_response_days) AS avg_review_response_days,
    COUNT(*) AS review_count
FROM (
    SELECT DISTINCT
        order_id,
        CASE
            WHEN review_score >= 4 THEN 'Positive (4-5)'
            WHEN review_score = 3 THEN 'Neutral (3)'
            WHEN review_score <= 2 THEN 'Negative (1-2)'
            ELSE NULL
        END AS sentiment_group,
        TIMESTAMPDIFF(
            DAY,
            review_creation_date,
            review_answer_timestamp
        ) AS review_response_days,
        category,
        customer_state
    FROM v_dashboard_main
    WHERE review_creation_date IS NOT NULL
      AND review_answer_timestamp IS NOT NULL
      AND review_score IS NOT NULL
) r
WHERE sentiment_group IS NOT NULL
  AND (:category IS NULL OR :category = 'All' OR category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR customer_state = :customer_state)
GROUP BY sentiment_group
ORDER BY FIELD(sentiment_group, 'Negative (1-2)', 'Neutral (3)', 'Positive (4-5)');
"""

FREIGHT_BY_WEIGHT_BAND_QUERY = """
SELECT
    weight_band,
    AVG(freight_to_price_ratio) AS avg_freight_burden,
    COUNT(*) AS item_count
FROM (
    SELECT
        order_id,
        freight_to_price_ratio,
        CASE
            WHEN product_weight_g < 500 THEN '< 500g'
            WHEN product_weight_g < 1000 THEN '500g - 1kg'
            WHEN product_weight_g < 5000 THEN '1kg - 5kg'
            ELSE '5kg+'
        END AS weight_band,
        category,
        customer_state
    FROM v_dashboard_main
    WHERE product_weight_g IS NOT NULL
) t
WHERE (:category IS NULL OR :category = 'All' OR category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR customer_state = :customer_state)
GROUP BY weight_band
ORDER BY FIELD(weight_band, '< 500g', '500g - 1kg', '1kg - 5kg', '5kg+');
"""

BASKET_COMPLEXITY_QUERY = """
SELECT
    basket_size_group,
    AVG(review_score) AS avg_review_score,
    AVG(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) AS low_review_rate
FROM (
    SELECT
        order_id,
        CASE
            WHEN items_in_order = 1 THEN '1 item'
            WHEN items_in_order BETWEEN 2 AND 3 THEN '2-3 items'
            ELSE '4+ items'
        END AS basket_size_group,
        avg_review_score AS review_score,
        category,
        customer_state
    FROM (
        SELECT
            order_id,
            COUNT(*) AS items_in_order,
            AVG(review_score) AS avg_review_score,
            MAX(category) AS category,
            MAX(customer_state) AS customer_state
        FROM v_dashboard_main
        GROUP BY order_id
    ) o
) b
WHERE (:category IS NULL OR :category = 'All' OR category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR customer_state = :customer_state)
GROUP BY basket_size_group
ORDER BY FIELD(basket_size_group, '1 item', '2-3 items', '4+ items');
"""

SELLER_OUTLIERS_QUERY = """
SELECT
    seller_id,
    seller_state,
    COUNT(*) AS items_sold,
    AVG(price) AS avg_item_price,
    AVG(freight_value) AS avg_item_freight,
    AVG(freight_to_price_ratio) AS avg_freight_to_price_ratio
FROM v_dashboard_main
WHERE (:category IS NULL OR :category = 'All' OR category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR customer_state = :customer_state)
GROUP BY seller_id, seller_state
HAVING items_sold >= :min_item_count
ORDER BY avg_freight_to_price_ratio DESC
LIMIT 20;
"""

PAYMENT_RECON_KPI_QUERY = """
SELECT
    SUM(CASE WHEN reconciliation_status = 'Matched' THEN 1 ELSE 0 END) AS matched_orders,
    SUM(CASE WHEN reconciliation_status <> 'Matched' THEN 1 ELSE 0 END) AS flagged_orders,
    AVG(abs_difference) AS avg_abs_difference
FROM v_payment_reconciliation;
"""

PAYMENT_RECON_DETAIL_QUERY = """
SELECT
    order_id,
    item_freight_total,
    payment_total,
    difference,
    abs_difference,
    reconciliation_status
FROM v_payment_reconciliation
WHERE reconciliation_status <> 'Matched'
ORDER BY abs_difference DESC
LIMIT 10;
"""

PAYMENT_METHOD_DISTRIBUTION_QUERY = """
SELECT
    payment_type,
    COUNT(*) AS payment_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS payment_pct
FROM order_payments
WHERE payment_type IS NOT NULL
GROUP BY payment_type
ORDER BY payment_count DESC;
"""

CATEGORY_OPTIONS_QUERY = """
SELECT DISTINCT
    COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown') AS category
FROM products p
LEFT JOIN product_categories pc
    ON p.product_category_name = pc.product_category_name
ORDER BY category;
"""

CUSTOMER_STATE_OPTIONS_QUERY = """
SELECT DISTINCT
    c.customer_state
FROM customers c
WHERE c.customer_state IS NOT NULL
ORDER BY c.customer_state;
"""

KPI_QUERY = """
SELECT
    COUNT(DISTINCT v.order_id) AS total_orders,
    ROUND(AVG(v.review_score), 2) AS avg_review_score,
    ROUND(AVG(v.delivery_delay_days), 2) AS avg_delivery_offset_days,
    ROUND(AVG(v.freight_to_price_ratio), 4) AS avg_freight_burden
FROM v_dashboard_main v
WHERE (:category IS NULL OR :category = 'All' OR v.category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR v.customer_state = :customer_state);
"""

DELIVERY_STATUS_REVIEW_QUERY = """
SELECT
    CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN 'On Time / Early'
        ELSE 'Late'
    END AS delivery_status,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(DISTINCT o.order_id) AS orders_count
FROM orders o
JOIN order_reviews r
    ON o.order_id = r.order_id
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN product_categories pc
    ON p.product_category_name = pc.product_category_name
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
  AND r.review_score IS NOT NULL
  AND (
      :category IS NULL
      OR :category = 'All'
      OR COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown') = :category
  )
  AND (
      :customer_state IS NULL
      OR :customer_state = 'All'
      OR c.customer_state = :customer_state
  )
GROUP BY delivery_status
ORDER BY FIELD(delivery_status, 'On Time / Early', 'Late');
"""

FULFILLMENT_DELAY_BREAKDOWN_QUERY = """
WITH fulfillment_stages AS (
    SELECT
        o.order_id,
        DATEDIFF(o.order_approved_at, o.order_purchase_timestamp) AS approval_delay,
        DATEDIFF(o.order_delivered_carrier_date, o.order_approved_at) AS carrier_delay,
        DATEDIFF(o.order_delivered_customer_date, o.order_delivered_carrier_date) AS delivery_delay
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    JOIN order_items oi
        ON o.order_id = oi.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_categories pc
        ON p.product_category_name = pc.product_category_name
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
      AND o.order_approved_at IS NOT NULL
      AND o.order_delivered_carrier_date IS NOT NULL
      AND o.order_delivered_customer_date IS NOT NULL
      AND (
          :category IS NULL
          OR :category = 'All'
          OR COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown') = :category
      )
      AND (
          :customer_state IS NULL
          OR :customer_state = 'All'
          OR c.customer_state = :customer_state
      )
)
SELECT
    ROUND(AVG(approval_delay), 2) AS avg_approval_delay,
    ROUND(AVG(carrier_delay), 2) AS avg_carrier_delay,
    ROUND(AVG(delivery_delay), 2) AS avg_delivery_delay
FROM fulfillment_stages;
"""

REVIEW_RESPONSE_TIME_QUERY = """
SELECT
    CASE
        WHEN r.review_score >= 4 THEN 'Positive (4-5)'
        WHEN r.review_score = 3 THEN 'Neutral (3)'
        WHEN r.review_score <= 2 THEN 'Negative (1-2)'
    END AS sentiment_group,
    ROUND(
        AVG(TIMESTAMPDIFF(DAY, r.review_creation_date, r.review_answer_timestamp)),
        2
    ) AS avg_review_response_days,
    COUNT(*) AS review_count
FROM order_reviews r
JOIN orders o
    ON r.order_id = o.order_id
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN product_categories pc
    ON p.product_category_name = pc.product_category_name
WHERE r.review_creation_date IS NOT NULL
  AND r.review_answer_timestamp IS NOT NULL
  AND r.review_score IS NOT NULL
  AND (
      :category IS NULL
      OR :category = 'All'
      OR COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown') = :category
  )
  AND (
      :customer_state IS NULL
      OR :customer_state = 'All'
      OR c.customer_state = :customer_state
  )
GROUP BY sentiment_group
ORDER BY FIELD(sentiment_group, 'Negative (1-2)', 'Neutral (3)', 'Positive (4-5)');
"""

FREIGHT_BY_WEIGHT_BAND_QUERY = """
WITH product_logistics AS (
    SELECT
        oi.price,
        oi.freight_value,
        p.product_weight_g,
        CASE
            WHEN p.product_weight_g < 500 THEN '< 500g'
            WHEN p.product_weight_g < 1000 THEN '500g - 1kg'
            WHEN p.product_weight_g < 5000 THEN '1kg - 5kg'
            ELSE '5kg+'
        END AS weight_band,
        oi.freight_value / NULLIF(oi.price, 0) AS freight_burden,
        c.customer_state,
        COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown') AS category
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN customers c
        ON o.customer_id = c.customer_id
    JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_categories pc
        ON p.product_category_name = pc.product_category_name
    WHERE p.product_weight_g IS NOT NULL
      AND oi.price IS NOT NULL
      AND oi.price > 0
)
SELECT
    weight_band,
    ROUND(AVG(freight_burden), 4) AS avg_freight_burden,
    COUNT(*) AS item_count
FROM product_logistics
WHERE (:category IS NULL OR :category = 'All' OR category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR customer_state = :customer_state)
GROUP BY weight_band
ORDER BY FIELD(weight_band, '< 500g', '500g - 1kg', '1kg - 5kg', '5kg+');
"""

BASKET_COMPLEXITY_QUERY = """
WITH order_item_counts AS (
    SELECT
        oi.order_id,
        COUNT(*) AS item_count,
        MAX(c.customer_state) AS customer_state,
        MAX(COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown')) AS category
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN customers c
        ON o.customer_id = c.customer_id
    JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_categories pc
        ON p.product_category_name = pc.product_category_name
    GROUP BY oi.order_id
)
SELECT
    CASE
        WHEN oic.item_count = 1 THEN '1 item'
        WHEN oic.item_count BETWEEN 2 AND 3 THEN '2-3 items'
        ELSE '4+ items'
    END AS basket_size_group,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(
        SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*) * 100,
        2
    ) AS low_review_rate_pct
FROM order_item_counts oic
JOIN order_reviews r
    ON oic.order_id = r.order_id
WHERE r.review_score IS NOT NULL
  AND (:category IS NULL OR :category = 'All' OR oic.category = :category)
  AND (:customer_state IS NULL OR :customer_state = 'All' OR oic.customer_state = :customer_state)
GROUP BY basket_size_group
ORDER BY FIELD(basket_size_group, '1 item', '2-3 items', '4+ items');
"""

PRODUCT_WEIGHT_REVIEW_QUERY = """
SELECT
    CASE
        WHEN p.product_weight_g < 500 THEN '< 500g'
        WHEN p.product_weight_g < 1000 THEN '500g - 1kg'
        WHEN p.product_weight_g < 5000 THEN '1kg - 5kg'
        ELSE '5kg+'
    END AS weight_band,
    COUNT(*) AS reviewed_items,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(
        SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*) * 100,
        2
    ) AS low_review_rate_pct
FROM order_items oi
JOIN orders o
    ON oi.order_id = o.order_id
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN product_categories pc
    ON p.product_category_name = pc.product_category_name
JOIN order_reviews r
    ON oi.order_id = r.order_id
WHERE p.product_weight_g IS NOT NULL
  AND r.review_score IS NOT NULL
  AND (
      :category IS NULL
      OR :category = 'All'
      OR COALESCE(pc.product_category_name_english, p.product_category_name, 'Unknown') = :category
  )
  AND (
      :customer_state IS NULL
      OR :customer_state = 'All'
      OR c.customer_state = :customer_state
  )
GROUP BY weight_band
ORDER BY FIELD(weight_band, '< 500g', '500g - 1kg', '1kg - 5kg', '5kg+');
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

PAYMENT_TOP_DIFFERENCES_QUERY = """
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

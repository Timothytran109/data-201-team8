USE BRcustomers;

-- Mid-Presentation Queries

-- which payment type has the most installments?
SELECT payment_type,
       AVG(payment_installments) AS avg_installments,
       AVG(payment_value) AS avg_order_value,
       COUNT(*) AS num_payments
FROM order_payments
GROUP BY payment_type
ORDER BY avg_order_value DESC;


-- Which state generates the most revenue?
SELECT c.customer_state, COUNT(DISTINCT o.order_id)    AS num_orders, ROUND(SUM(p.payment_value),2) AS total_spend
FROM customers c
JOIN orders   o ON c.customer_id = o.customer_id
JOIN order_payments p ON o.order_id    = p.order_id
GROUP BY c.customer_state
ORDER BY total_spend DESC
LIMIT 10;

-- Which state has the most 'high-value' orders? ('high-value' = payment greater than average order payment)
SELECT c.customer_state, COUNT(*) AS high_value_orders
FROM orders o
JOIN order_payments p ON o.order_id = p.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE p.payment_value > 
	(SELECT AVG(payment_value) FROM order_payments)
GROUP BY c.customer_state
ORDER BY high_value_orders DESC
LIMIT 10;

-- Which state has the most 'low-score' orders? ('low-score' = review score lower or equal to 2
SELECT c.customer_state, COUNT(DISTINCT o.order_id) AS low_score_orders
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE EXISTS (
    SELECT 1 FROM order_reviews r
    WHERE r.order_id = o.order_id
      AND r.review_score <= 2
)
GROUP BY c.customer_state
ORDER BY low_score_orders DESC 
LIMIT 10;

-- Which state has the highest customer count?
SELECT c.customer_state, COUNT(*) AS customer_count
FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.customer_id = c.customer_id
)
GROUP BY c.customer_state
ORDER BY customer_count DESC;

-- Final Presentation Queries

-- Basic Query #1: How many orders have multiple payment records?
SELECT COUNT(*) AS orders_with_multiple_payments
FROM (
    SELECT order_id
    FROM order_payments
    GROUP BY order_id
    HAVING COUNT(*) > 1
) AS multi_payment_orders;


-- Basic Query #2: What is the average number of items per order?
WITH items_per_order AS (
    SELECT
        order_id,
        COUNT(*) AS item_count
    FROM order_payments
    GROUP BY order_id
)
SELECT
    ROUND(AVG(item_count), 2) AS avg_items_per_order
FROM items_per_order;


-- Advanced Query #1: Are payment totals consistent with item price + freight totals?
-- CTE 1: Total payment collected per order (across all payment methods/installments)
WITH payment_totals AS (
    SELECT order_id, SUM(payment_value) AS total_paid
    FROM order_payments
    GROUP BY order_id
),

-- CTE 2: Total charged per order (item prices + freight for all line items)
item_totals AS (
    SELECT
        order_id, SUM(price) AS total_item_price, SUM(freight_value) AS total_freight, SUM(price + freight_value) AS total_item_charged
    FROM order_items
    GROUP BY order_id
),

-- CTE 3: Join both sides and compute the gap
reconciliation AS (
    SELECT
        p.order_id, p.total_paid, i.total_item_charged, i.total_item_price, i.total_freight,
        ROUND(p.total_paid - i.total_item_charged, 2)   AS difference,

        -- each order falls in: match within $0.01, small rounding gap, or true mismatch
        CASE
            WHEN ABS(p.total_paid - i.total_item_charged) <= 0.01 THEN 'MATCH'
            WHEN ABS(p.total_paid - i.total_item_charged) <= 1.00 THEN 'ROUNDING_GAP'
            ELSE 'MISMATCH'
        END AS reconciliation_status
    FROM payment_totals  p
    INNER JOIN item_totals i ON p.order_id = i.order_id
)

-- Final output: aggregate summary across all orders
SELECT
    reconciliation_status,
    COUNT(*) AS order_count,
    ROUND(AVG(ABS(difference)), 4) AS avg_abs_difference,
    ROUND(MIN(difference), 2) AS min_difference,
    ROUND(MAX(difference), 2) AS max_difference,
    ROUND(SUM(ABS(difference)), 2) AS total_discrepancy_amount
FROM reconciliation
GROUP BY reconciliation_status
ORDER BY order_count DESC;


-- Advanced Query #2: Which orders have the largest payment-vs-item-total discrepancies?
-- CTE 1: Total payment per order
WITH payment_totals AS (
    SELECT order_id, ROUND(SUM(payment_value), 2) AS total_paid
    FROM order_payments
    GROUP BY order_id
),

-- CTE 2: Total item cost (price + freight) per order
item_totals AS (
    SELECT
        order_id, ROUND(SUM(price + freight_value), 2) AS total_items
    FROM order_items
    GROUP BY order_id
),

-- CTE 3: Join both, compute raw diff and absolute discrepancy
discrepancies AS (
    SELECT
        p.order_id, p.total_paid, i.total_items, ROUND(p.total_paid - i.total_items, 2) AS discrepancy,
        ROUND(ABS(p.total_paid - i.total_items), 2) AS abs_discrepancy
    FROM payment_totals p
    INNER JOIN item_totals i ON p.order_id = i.order_id
)

-- Final: Rank by absolute discrepancy, show top 20
SELECT order_id, total_paid, total_items, discrepancy, abs_discrepancy,
    RANK() 
		OVER (ORDER BY abs_discrepancy DESC)
        AS discrepancy_rank
FROM discrepancies
ORDER BY abs_discrepancy DESC
LIMIT 20;


-- Advanced Query #3: 
-- CTE 1: Aggregate per order — total basket value and number of payment records
WITH basket AS (
    SELECT
        order_id,
        SUM(payment_value) AS basket_total,
        COUNT(payment_sequential) AS payment_count   -- >1 means split payment
    FROM order_payments
    GROUP BY order_id
),

-- CTE 2: Assign each order to a basket-size bucket
bucketed AS (
    SELECT order_id, basket_total, payment_count,
        CASE
            WHEN basket_total <  50 THEN '1. Under $50'
            WHEN basket_total >= 50  AND basket_total < 150 THEN '2. $50–$149'
            WHEN basket_total >= 150 AND basket_total < 300 THEN '3. $150–$299'
            WHEN basket_total >= 300 AND basket_total < 500 THEN '4. $300–$499'
            ELSE '5. $500+'
        END AS basket_tier
    FROM basket
)

-- Final: Per bucket, measure split rate
SELECT basket_tier, COUNT(*) AS total_orders,
    SUM(
		CASE 
			WHEN payment_count > 1 THEN 1 
            ELSE 0 END) AS split_orders,
    ROUND(100.0 * SUM(
		CASE 
			WHEN payment_count > 1 THEN 1 
            ELSE 0 END) / COUNT(*), 2) AS split_rate_pct,
    ROUND(AVG(basket_total), 2) AS avg_basket_value,
    ROUND(AVG(payment_count), 2) AS avg_payment_count
FROM bucketed
GROUP BY basket_tier
ORDER BY basket_tier;


-- Advanced Query #4: Which customer states have unusually high-value orders after controlling for national average order value?
SELECT c.customer_state, COUNT(DISTINCT o.order_id) AS total_orders, ROUND(AVG(op.payment_value), 2) AS avg_order_value,
    ROUND((SELECT AVG(payment_value) FROM order_payments), 2) AS national_avg_value,
    ROUND(AVG(op.payment_value) / (SELECT AVG(payment_value) FROM order_payments), 2) AS ratio_to_national_avg
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_payments op ON o.order_id = op.order_id
GROUP BY c.customer_state
HAVING AVG(op.payment_value) > 1.25 * (SELECT AVG(payment_value) FROM order_payments)
ORDER BY avg_order_value DESC;


-- Advanced Query #5: How do payment installments relate to order value?
-- Step 1: CTE collapses multi-row payments to one record per order
WITH payments AS (
    SELECT order_id, MAX(payment_installments) AS installments, SUM(payment_value) AS order_value
    FROM order_payments
    WHERE payment_type = 'credit_card'
    GROUP BY order_id
),

-- Step 2: separate installments into labels
installment_labels AS (
    SELECT order_value, installments,
        CASE
            WHEN installments = 1            THEN 'Paid in Full'
            WHEN installments BETWEEN 2 AND 3 THEN 'Short-term'
            WHEN installments BETWEEN 4 AND 6 THEN 'Medium-term'
            WHEN installments BETWEEN 7 AND 12 THEN 'Long-term'
            ELSE                                  'Extended'
        END AS installment_type
    FROM payments
)

-- Step 3: Aggregate order value metrics by bucket
SELECT installment_type, COUNT(*) AS order_count,
    ROUND(AVG(order_value), 2) AS avg_order_value,
    ROUND(MIN(order_value), 2) AS min_order_value,
    ROUND(MAX(order_value), 2) AS max_order_value,
    ROUND(SUM(order_value), 2) AS total_revenue,
    ROUND(AVG(installments), 1) AS avg_installments
FROM installment_labels
GROUP BY installment_type
ORDER BY MIN(installments);
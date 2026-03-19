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


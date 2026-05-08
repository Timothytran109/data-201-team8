#SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM orders
#UNION ALL
#SELECT 'customers', COUNT(*) FROM customers
#UNION ALL
#SELECT 'order_items', COUNT(*) FROM order_items
#UNION ALL
#SELECT 'order_payments', COUNT(*) FROM order_payments
#UNION ALL
#SELECT 'order_reviews', COUNT(*) FROM order_reviews
#UNION ALL
#SELECT 'products', COUNT(*) FROM products
#UNION ALL
#SELECT 'sellers', COUNT(*) FROM sellers;





SELECT 
    order_status,
    COUNT(*) AS total_orders,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) AS percentage
FROM orders
GROUP BY order_status
ORDER BY total_orders DESC;













SELECT 
   payment_type,
   COUNT(*) AS total_transactions,
    ROUND(AVG(payment_value), 2) AS avg_payment_value,
    ROUND(SUM(payment_value), 2) AS total_revenue
FROM order_payments
GROUP BY payment_type
ORDER BY total_transactions DESC;



WITH customer_orders AS (
    SELECT 
        c.customer_unique_id,
        c.customer_state,
        COUNT(o.order_id) AS total_orders
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id, c.customer_state
)
SELECT 
    customer_state,
    COUNT(*) AS repeat_customers
FROM customer_orders
WHERE total_orders > 1
GROUP BY customer_state
ORDER BY repeat_customers DESC
LIMIT 10;

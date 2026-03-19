# What percentage of orders were delivered and what were cancelled
#SELECT 
#    order_status,
#    COUNT(*) AS total_orders,
#    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) AS percentage
#FROM orders
#GROUP BY order_status
#ORDER BY total_orders DESC;

#What payment method do the customers prefer to use
#SELECT 
#   payment_type,
#   COUNT(*) AS total_transactions,
#    ROUND(AVG(payment_value), 2) AS avg_payment_value,
#    ROUND(SUM(payment_value), 2) AS total_revenue
#FROM order_payments
#GROUP BY payment_type
#ORDER BY total_transactions DESC;

#Which states tend to have the most repeat customers 

#WITH customer_orders AS (
#    SELECT 
#        c.customer_unique_id,
#        c.customer_state,
#        COUNT(o.order_id) AS total_orders
#    FROM customers c
#    JOIN orders o ON c.customer_id = o.customer_id
#    GROUP BY c.customer_unique_id, c.customer_state
#)
#SELECT 
#    customer_state,
#    COUNT(*) AS repeat_customers
#FROM customer_orders
#WHERE total_orders > 1
#GROUP BY customer_state
#ORDER BY repeat_customers DESC
#LIMIT 10;

#What are the peak shopping days.
#SELECT 
#    DAYNAME(order_purchase_timestamp) AS day_of_week,
#    COUNT(*) AS total_orders
#FROM orders
#WHERE order_status = 'delivered'
#GROUP BY day_of_week
#ORDER BY total_orders DESC;

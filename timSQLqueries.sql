# Order volume change

SELECT DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS order_month,
       COUNT(*) AS total_orders
FROM ORDERS
GROUP BY order_month
ORDER BY order_month;

# Order status

SELECT order_status,
       COUNT(*) AS total_orders
FROM ORDERS
GROUP BY order_status
ORDER BY total_orders DESC;

# Which product categories generate the most revenue

SELECT pc.product_category_name_english,
       ROUND(SUM(oi.price), 2) AS total_revenue,
       COUNT(*) AS items_sold
FROM ORDER_ITEMS oi
JOIN PRODUCTS p
  ON oi.product_id = p.product_id
LEFT JOIN PRODUCT_CATEGORIES pc
  ON p.product_category_name = pc.product_category_name
GROUP BY pc.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 10;

# Which sellers rank highest within each state?

WITH seller_sales AS (
  SELECT s.seller_state,
         oi.seller_id,
         ROUND(SUM(oi.price), 2) AS total_revenue
  FROM ORDER_ITEMS oi
  JOIN SELLERS s
    ON oi.seller_id = s.seller_id
  GROUP BY s.seller_state, oi.seller_id
)
SELECT seller_state,
       seller_id,
       total_revenue,
       RANK() OVER (PARTITION BY seller_state ORDER BY total_revenue DESC) AS revenue_rank
FROM seller_sales;
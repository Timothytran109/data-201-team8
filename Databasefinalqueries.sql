#Delivery Performance (Final Queries)
SELECT 
    CASE 
        WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 'On Time'
        ELSE 'Late'
    END AS delivery_status,
    COUNT(order_id) AS total_orders,
    ROUND(COUNT(order_id) * 100.0 / SUM(COUNT(order_id)) OVER(), 2) AS percentage
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
GROUP BY 1;





# Average Delivery Delay 
SELECT 
    ROUND(AVG(DATEDIFF(order_delivered_customer_date, order_estimated_delivery_date)), 2) AS avg_delay_days
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date > order_estimated_delivery_date;














# Do late deliveries get lower review scores?
SELECT 
    CASE 
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On Time'
        ELSE 'Late'
    END AS delivery_status,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM orders o
JOIN order_reviews r 
    ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY delivery_status;




# Which fulfillment stage contributes most to delay?

SELECT 
    r.review_score,
    COUNT(o.order_id) AS total_orders,
    ROUND(AVG(DATEDIFF(o.order_approved_at, o.order_purchase_timestamp)), 2) AS avg_approval_delay,
    ROUND(AVG(DATEDIFF(o.order_delivered_carrier_date, o.order_approved_at)), 2) AS avg_carrier_delay,
    ROUND(AVG(DATEDIFF(o.order_delivered_customer_date, o.order_delivered_carrier_date)), 2) AS avg_delivery_delay
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY r.review_score
ORDER BY r.review_score DESC;




#Does review response time differ by sentiment?
SELECT 
    CASE 
        WHEN review_score >= 4 THEN 'Positive'
        WHEN review_score = 3 THEN 'Neutral'
        ELSE 'Negative'
    END AS sentiment,
    ROUND(AVG(DATEDIFF(review_answer_timestamp, review_creation_date)), 2) AS avg_response_days
FROM order_reviews
GROUP BY sentiment;



SELECT 
    a.product_id, 
    a.seller_id AS seller_1, 
    a.price AS price_1, 
    b.seller_id AS seller_2, 
    b.price AS price_2, 
    ABS(a.price - b.price) AS price_difference 
FROM order_items a 
JOIN order_items b 
     ON a.product_id = b.product_id 
    AND a.seller_id <> b.seller_id 
WHERE a.price > b.price 
ORDER BY price_difference DESC 
LIMIT 10;





#Late deliveries but HIGH reviews
SELECT 
    o.order_id,
    r.review_score,
    DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date) AS delay_days
FROM orders o
JOIN order_reviews r 
    ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date > o.order_estimated_delivery_date
  AND r.review_score >= 4
ORDER BY delay_days DESC;









#On time but low reviews 
SELECT 
    o.order_id,
    r.review_score
FROM orders o
JOIN order_reviews r 
    ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date <= o.order_estimated_delivery_date
  AND r.review_score <= 2
ORDER BY r.review_score ASC;